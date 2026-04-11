import secrets
import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.models import (
    Committee, CommitteeMember, CommitteeRound,
    LuckyDraw, LuckyDrawHistory, Payout, Transaction,
    AuditLog, Notification, User,
)
from app.models.enums import (
    CommitteeType, CommitteeStatus, RoundStatus, MembershipStatus,
    TransactionType, AuditAction, NotificationType,
)


class LuckyDrawService:

    @staticmethod
    def run_draw(db: Session, committee_id: int, round_id: int, admin: User) -> dict:
        committee = (
            db.query(Committee)
            .filter(
                Committee.id == committee_id,
                Committee.committee_type == CommitteeType.LUCKY_DRAW,
                Committee.status == CommitteeStatus.ACTIVE,
                Committee.deleted_at == None,
            )
            .first()
        )
        if not committee:
            raise HTTPException(status_code=404, detail="Active lucky draw committee not found")

        # UI payloads often send round_number (1, 2, 3...) instead of round table PK.
        # First resolve by round PK; if not found, fallback to round_number for the committee.
        round_obj = (
            db.query(CommitteeRound)
            .filter(
                CommitteeRound.id == round_id,
                CommitteeRound.committee_id == committee_id,
            )
            .first()
        )
        if not round_obj:
            round_obj = (
                db.query(CommitteeRound)
                .filter(
                    CommitteeRound.round_number == round_id,
                    CommitteeRound.committee_id == committee_id,
                )
                .first()
            )

        if not round_obj:
            raise HTTPException(status_code=404, detail="Round not found for this committee")

        if round_obj.status != RoundStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail=f"Round {round_obj.round_number} is {round_obj.status.value} and cannot run lucky draw",
            )

        # Get eligible members (approved & haven't received payout)
        eligible_members = (
            db.query(CommitteeMember)
            .filter(
                CommitteeMember.committee_id == committee_id,
                CommitteeMember.membership_status == MembershipStatus.APPROVED,
                CommitteeMember.has_received_payout == False,
                CommitteeMember.deleted_at == None,
            )
            .all()
        )

        if not eligible_members:
            raise HTTPException(status_code=400, detail="No eligible members for draw")

        # Cryptographic random selection
        draw_seed = secrets.token_hex(32)
        winner_index = secrets.randbelow(len(eligible_members))
        winner = eligible_members[winner_index]

        draw_timestamp = datetime.now(timezone.utc)

        # Create lucky draw record
        lucky_draw = LuckyDraw(
            round_id=round_obj.id,
            committee_id=committee_id,
            winner_member_id=winner.id,
            draw_seed=draw_seed,
            draw_timestamp=draw_timestamp,
            eligible_member_ids=json.dumps([m.id for m in eligible_members]),
        )
        db.add(lucky_draw)
        db.flush()

        # Record history for each member
        for m in eligible_members:
            db.add(LuckyDrawHistory(
                lucky_draw_id=lucky_draw.id,
                member_id=m.id,
                was_eligible=True,
                was_winner=(m.id == winner.id),
            ))

        # Update round
        round_obj.status = RoundStatus.COMPLETED
        round_obj.winner_member_id = winner.id
        round_obj.winner_amount = round_obj.pool_amount
        round_obj.discount_amount = 0
        from datetime import date
        round_obj.completed_date = date.today()

        # Update committee round counter
        committee.current_round = round_obj.round_number

        # Mark winner
        winner.has_received_payout = True
        winner.payout_round = round_obj.round_number
        winner.total_received += round_obj.pool_amount

        # Create payout
        db.add(Payout(
            committee_id=committee_id,
            round_id=round_obj.id,
            member_id=winner.id,
            gross_amount=round_obj.pool_amount,
            discount_amount=0,
            net_amount=round_obj.pool_amount,
            is_processed=True,
            processed_at=draw_timestamp,
        ))

        # Transaction
        db.add(Transaction(
            user_id=winner.user_id,
            committee_id=committee_id,
            transaction_type=TransactionType.PAYOUT,
            amount=round_obj.pool_amount,
            description=f"Round {round_obj.round_number} lucky draw payout",
            round_number=round_obj.round_number,
        ))

        # Winner user info
        winner_user = db.query(User).filter(User.id == winner.user_id).first()

        # Notify all members
        all_members = (
            db.query(CommitteeMember)
            .filter(
                CommitteeMember.committee_id == committee_id,
                CommitteeMember.membership_status == MembershipStatus.APPROVED,
                CommitteeMember.deleted_at == None,
            )
            .all()
        )
        for m in all_members:
            db.add(Notification(
                user_id=m.user_id,
                title="Lucky Draw Result",
                message=f"Round {round_obj.round_number} winner: {winner_user.name if winner_user else 'Member'}",
                notification_type=NotificationType.LUCKY_DRAW_RESULT,
                reference_id=lucky_draw.id,
                reference_type="lucky_draw",
            ))

        db.add(AuditLog(
            user_id=admin.id,
            action=AuditAction.DRAW,
            entity_type="lucky_draw",
            entity_id=lucky_draw.id,
            new_values=f'{{"winner_member_id": {winner.id}, "amount": "{round_obj.pool_amount}"}}',
        ))

        db.commit()

        return {
            "status": True,
            "message": f"Lucky draw completed! Winner: {winner_user.name if winner_user else 'Member'}",
            "data": {
                "lucky_draw_id": lucky_draw.id,
                "round_number": round_obj.round_number,
                "winner_member_id": winner.id,
                "winner_name": winner_user.name if winner_user else None,
                "winner_slot": winner.slot_number,
                "pool_amount": str(round_obj.pool_amount),
                "eligible_count": len(eligible_members),
                "draw_timestamp": str(draw_timestamp),
            },
        }

    @staticmethod
    def get_history(db: Session, committee_id: int, page: int = 1, page_size: int = 20) -> dict:
        query = (
            db.query(LuckyDraw)
            .filter(LuckyDraw.committee_id == committee_id)
            .order_by(LuckyDraw.draw_timestamp.desc())
        )

        total = query.count()
        draws = query.offset((page - 1) * page_size).limit(page_size).all()

        data = []
        for d in draws:
            winner_user = None
            if d.winner_member_id:
                member = db.query(CommitteeMember).filter(CommitteeMember.id == d.winner_member_id).first()
                if member:
                    winner_user = db.query(User).filter(User.id == member.user_id).first()

            round_obj = db.query(CommitteeRound).filter(CommitteeRound.id == d.round_id).first()

            data.append({
                "id": d.id,
                "round_id": d.round_id,
                "round_number": round_obj.round_number if round_obj else None,
                "winner_member_id": d.winner_member_id,
                "winner_name": winner_user.name if winner_user else None,
                "pool_amount": str(round_obj.pool_amount) if round_obj else None,
                "draw_timestamp": str(d.draw_timestamp),
            })

        return {
            "status": True,
            "message": "Lucky draw history",
            "data": data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }
