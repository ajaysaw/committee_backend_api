from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.models import (
    Committee, CommitteeMember, CommitteeRound, Bid,
    Dividend, Payout, Transaction, AuditLog, Notification,
)
from app.models.enums import (
    CommitteeType, CommitteeStatus, RoundStatus, MembershipStatus,
    TransactionType, AuditAction, NotificationType,
)
from app.models.models import User


class BiddingService:

    @staticmethod
    def start_round(db: Session, committee_id: int, admin: User) -> dict:
        committee = (
            db.query(Committee)
            .filter(
                Committee.id == committee_id,
                Committee.committee_type == CommitteeType.BIDDING,
                Committee.status == CommitteeStatus.ACTIVE,
                Committee.deleted_at == None,
            )
            .first()
        )
        if not committee:
            raise HTTPException(status_code=404, detail="Active bidding committee not found")

        next_round_num = committee.current_round + 1
        if next_round_num > committee.duration_months:
            raise HTTPException(status_code=400, detail="All rounds completed")

        round_obj = (
            db.query(CommitteeRound)
            .filter(
                CommitteeRound.committee_id == committee_id,
                CommitteeRound.round_number == next_round_num,
            )
            .first()
        )
        if not round_obj:
            raise HTTPException(status_code=404, detail="Round not found")

        if round_obj.status != RoundStatus.PENDING:
            raise HTTPException(status_code=400, detail="Round is not in pending state")

        round_obj.status = RoundStatus.IN_PROGRESS
        committee.current_round = next_round_num

        # Notify all members
        members = (
            db.query(CommitteeMember)
            .filter(
                CommitteeMember.committee_id == committee_id,
                CommitteeMember.membership_status == MembershipStatus.APPROVED,
                CommitteeMember.deleted_at == None,
            )
            .all()
        )
        for m in members:
            db.add(Notification(
                user_id=m.user_id,
                title="Bidding Round Started",
                message=f"Round {next_round_num} bidding is now open for {committee.name}",
                notification_type=NotificationType.BID_STARTED,
                reference_id=round_obj.id,
                reference_type="round",
            ))

        db.commit()
        db.refresh(round_obj)

        return {
            "status": True,
            "message": f"Round {next_round_num} bidding started",
            "data": {
                "round_id": round_obj.id,
                "round_number": round_obj.round_number,
                "pool_amount": str(round_obj.pool_amount),
                "status": round_obj.status.value,
            },
        }

    @staticmethod
    def place_bid(db: Session, round_id: int, bid_amount: Decimal, user: User) -> dict:
        round_obj = (
            db.query(CommitteeRound)
            .filter(CommitteeRound.id == round_id, CommitteeRound.status == RoundStatus.IN_PROGRESS)
            .first()
        )
        if not round_obj:
            raise HTTPException(status_code=404, detail="Active bidding round not found")

        committee = db.query(Committee).filter(Committee.id == round_obj.committee_id).first()

        # Verify user is an approved member
        member = (
            db.query(CommitteeMember)
            .filter(
                CommitteeMember.committee_id == committee.id,
                CommitteeMember.user_id == user.id,
                CommitteeMember.membership_status == MembershipStatus.APPROVED,
                CommitteeMember.has_received_payout == False,
                CommitteeMember.deleted_at == None,
            )
            .first()
        )
        if not member:
            raise HTTPException(status_code=403, detail="Not eligible to bid (not a member or already received payout)")

        # Validate bid amount
        if committee.min_bid_amount and bid_amount < committee.min_bid_amount:
            raise HTTPException(status_code=400, detail=f"Bid must be at least {committee.min_bid_amount}")
        if committee.max_bid_amount and bid_amount > committee.max_bid_amount:
            raise HTTPException(status_code=400, detail=f"Bid must not exceed {committee.max_bid_amount}")
        if bid_amount > round_obj.pool_amount:
            raise HTTPException(status_code=400, detail="Bid cannot exceed pool amount")

        bid = Bid(
            round_id=round_id,
            user_id=user.id,
            committee_id=committee.id,
            bid_amount=bid_amount,
        )
        db.add(bid)

        db.add(AuditLog(
            user_id=user.id,
            action=AuditAction.BID,
            entity_type="bid",
            entity_id=round_id,
            new_values=f'{{"amount": "{bid_amount}"}}',
        ))

        db.commit()
        db.refresh(bid)

        return {
            "status": True,
            "message": "Bid placed successfully",
            "data": {
                "bid_id": bid.id,
                "bid_amount": str(bid.bid_amount),
                "round_number": round_obj.round_number,
            },
        }

    @staticmethod
    def close_round(db: Session, round_id: int, admin: User) -> dict:
        round_obj = (
            db.query(CommitteeRound)
            .filter(CommitteeRound.id == round_id, CommitteeRound.status == RoundStatus.IN_PROGRESS)
            .first()
        )
        if not round_obj:
            raise HTTPException(status_code=404, detail="Active bidding round not found")

        committee = db.query(Committee).filter(Committee.id == round_obj.committee_id).first()

        # Find lowest bid (winner takes lowest amount = highest discount)
        bids = (
            db.query(Bid)
            .filter(Bid.round_id == round_id)
            .order_by(Bid.bid_amount.asc())
            .all()
        )
        if not bids:
            raise HTTPException(status_code=400, detail="No bids placed in this round")

        winning_bid = bids[0]
        winning_bid.is_winner = True

        # The winner gets bid_amount, difference is discount
        discount = round_obj.pool_amount - winning_bid.bid_amount

        winner_member = (
            db.query(CommitteeMember)
            .filter(
                CommitteeMember.committee_id == committee.id,
                CommitteeMember.user_id == winning_bid.user_id,
                CommitteeMember.deleted_at == None,
            )
            .first()
        )

        round_obj.status = RoundStatus.COMPLETED
        round_obj.winner_member_id = winner_member.id
        round_obj.winner_amount = winning_bid.bid_amount
        round_obj.discount_amount = discount
        from datetime import date
        round_obj.completed_date = date.today()

        # Mark winner as received payout
        winner_member.has_received_payout = True
        winner_member.payout_round = round_obj.round_number
        winner_member.total_received += winning_bid.bid_amount

        # Create payout record
        payout = Payout(
            committee_id=committee.id,
            round_id=round_obj.id,
            member_id=winner_member.id,
            gross_amount=round_obj.pool_amount,
            discount_amount=discount,
            net_amount=winning_bid.bid_amount,
            is_processed=True,
        )
        db.add(payout)

        # Create transaction for winner
        db.add(Transaction(
            user_id=winning_bid.user_id,
            committee_id=committee.id,
            transaction_type=TransactionType.PAYOUT,
            amount=winning_bid.bid_amount,
            description=f"Round {round_obj.round_number} payout (bid winner)",
            round_number=round_obj.round_number,
        ))

        # Distribute dividend to remaining members
        remaining_members = (
            db.query(CommitteeMember)
            .filter(
                CommitteeMember.committee_id == committee.id,
                CommitteeMember.membership_status == MembershipStatus.APPROVED,
                CommitteeMember.id != winner_member.id,
                CommitteeMember.deleted_at == None,
            )
            .all()
        )

        if remaining_members and discount > 0:
            dividend_per_member = discount / len(remaining_members)
            for m in remaining_members:
                db.add(Dividend(
                    round_id=round_obj.id,
                    committee_id=committee.id,
                    member_id=m.id,
                    amount=dividend_per_member,
                ))
                db.add(Transaction(
                    user_id=m.user_id,
                    committee_id=committee.id,
                    transaction_type=TransactionType.DIVIDEND,
                    amount=dividend_per_member,
                    description=f"Round {round_obj.round_number} dividend",
                    round_number=round_obj.round_number,
                ))

        # Notify winner
        db.add(Notification(
            user_id=winning_bid.user_id,
            title="You Won the Bid!",
            message=f"You won round {round_obj.round_number} with bid amount {winning_bid.bid_amount}",
            notification_type=NotificationType.BID_WON,
            reference_id=round_obj.id,
            reference_type="round",
        ))

        db.add(AuditLog(
            user_id=admin.id,
            action=AuditAction.PAYOUT,
            entity_type="round",
            entity_id=round_obj.id,
            new_values=f'{{"winner": {winning_bid.user_id}, "amount": "{winning_bid.bid_amount}"}}',
        ))

        db.commit()

        return {
            "status": True,
            "message": f"Round {round_obj.round_number} closed. Winner: member #{winner_member.slot_number}",
            "data": {
                "round_number": round_obj.round_number,
                "winner_member_id": winner_member.id,
                "winning_bid": str(winning_bid.bid_amount),
                "discount": str(discount),
                "dividend_per_member": str(discount / len(remaining_members)) if remaining_members else "0",
            },
        }

    @staticmethod
    def get_bid_history(db: Session, committee_id: int, user: User, page: int = 1, page_size: int = 20) -> dict:
        query = db.query(Bid).filter(Bid.committee_id == committee_id)

        total = query.count()
        bids = query.order_by(Bid.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

        data = []
        for b in bids:
            data.append({
                "id": b.id,
                "round_id": b.round_id,
                "user_id": b.user_id,
                "bid_amount": str(b.bid_amount),
                "is_winner": b.is_winner,
                "created_at": str(b.created_at),
            })

        return {
            "status": True,
            "message": "Bid history fetched",
            "data": data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }
