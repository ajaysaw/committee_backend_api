from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.models import (
    Committee, CommitteeMember, User, AuditLog, Notification,
)
from app.models.enums import (
    MembershipStatus, CommitteeStatus, AuditAction,
    NotificationType, UserRole,
)


class MemberService:

    @staticmethod
    def join_committee(db: Session, committee_id: int, user: User) -> dict:
        committee = (
            db.query(Committee)
            .filter(Committee.id == committee_id, Committee.deleted_at == None)
            .first()
        )
        if not committee:
            raise HTTPException(status_code=404, detail="Committee not found")

        if committee.status not in (CommitteeStatus.DRAFT, CommitteeStatus.ACTIVE):
            raise HTTPException(status_code=400, detail="Committee is not accepting members")

        # Check if already a member
        existing = (
            db.query(CommitteeMember)
            .filter(
                CommitteeMember.committee_id == committee_id,
                CommitteeMember.user_id == user.id,
                CommitteeMember.deleted_at == None,
                CommitteeMember.membership_status.notin_([
                    MembershipStatus.REJECTED, MembershipStatus.LEFT, MembershipStatus.REMOVED
                ]),
            )
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="Already requested or member of this committee")

        # Check member capacity
        current_count = (
            db.query(CommitteeMember)
            .filter(
                CommitteeMember.committee_id == committee_id,
                CommitteeMember.membership_status.in_([MembershipStatus.PENDING, MembershipStatus.APPROVED]),
                CommitteeMember.deleted_at == None,
            )
            .count()
        )
        if current_count >= committee.total_members:
            raise HTTPException(status_code=400, detail="Committee is full")

        member = CommitteeMember(
            committee_id=committee_id,
            user_id=user.id,
            membership_status=MembershipStatus.PENDING,
        )
        db.add(member)

        # Notify admin
        db.add(Notification(
            user_id=committee.created_by,
            title="New Member Request",
            message=f"{user.name} requested to join {committee.name}",
            notification_type=NotificationType.GENERAL,
            reference_id=committee.id,
            reference_type="committee",
        ))

        db.commit()
        db.refresh(member)

        return {
            "status": True,
            "message": "Join request submitted. Waiting for admin approval.",
            "data": {"member_id": member.id, "status": member.membership_status.value},
        }

    @staticmethod
    def list_members(db: Session, committee_id: int, user: User, page: int = 1, page_size: int = 20) -> dict:
        committee = (
            db.query(Committee)
            .filter(Committee.id == committee_id, Committee.deleted_at == None)
            .first()
        )
        if not committee:
            raise HTTPException(status_code=404, detail="Committee not found")

        query = (
            db.query(CommitteeMember, User)
            .join(User, CommitteeMember.user_id == User.id)
            .filter(
                CommitteeMember.committee_id == committee_id,
                CommitteeMember.deleted_at == None,
            )
        )

        # Non-admin only sees approved members
        if user.role != UserRole.ADMIN:
            query = query.filter(CommitteeMember.membership_status == MembershipStatus.APPROVED)

        total = query.count()
        results = query.offset((page - 1) * page_size).limit(page_size).all()

        data = []
        for member, u in results:
            data.append({
                "id": member.id,
                "committee_id": member.committee_id,
                "user_id": member.user_id,
                "user_name": u.name,
                "user_email": u.email,
                "user_phone": u.phone,
                "slot_number": member.slot_number,
                "membership_status": member.membership_status.value,
                "has_received_payout": member.has_received_payout,
                "payout_round": member.payout_round,
                "total_paid": str(member.total_paid),
                "total_received": str(member.total_received),
                "joined_at": str(member.joined_at) if member.joined_at else None,
            })

        return {
            "status": True,
            "message": "Members fetched",
            "data": data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    @staticmethod
    def approve_member(db: Session, member_id: int, admin: User, slot_number: int = None) -> dict:
        member = (
            db.query(CommitteeMember)
            .filter(CommitteeMember.id == member_id, CommitteeMember.deleted_at == None)
            .first()
        )
        if not member:
            raise HTTPException(status_code=404, detail="Member request not found")

        if member.membership_status != MembershipStatus.PENDING:
            raise HTTPException(status_code=400, detail="Member request is not pending")

        # Assign slot
        if slot_number:
            member.slot_number = slot_number
        else:
            max_slot = (
                db.query(CommitteeMember.slot_number)
                .filter(
                    CommitteeMember.committee_id == member.committee_id,
                    CommitteeMember.slot_number != None,
                    CommitteeMember.deleted_at == None,
                )
                .order_by(CommitteeMember.slot_number.desc())
                .first()
            )
            member.slot_number = (max_slot[0] + 1) if max_slot and max_slot[0] else 1

        member.membership_status = MembershipStatus.APPROVED
        member.joined_at = datetime.now(timezone.utc)

        # Notify member
        db.add(Notification(
            user_id=member.user_id,
            title="Membership Approved",
            message=f"Your membership has been approved. Slot #{member.slot_number}",
            notification_type=NotificationType.COMMITTEE_JOINED,
            reference_id=member.committee_id,
            reference_type="committee",
        ))

        db.add(AuditLog(
            user_id=admin.id,
            action=AuditAction.UPDATE,
            entity_type="committee_member",
            entity_id=member.id,
            new_values=f'{{"status": "approved", "slot": {member.slot_number}}}',
        ))

        db.commit()

        return {
            "status": True,
            "message": "Member approved successfully",
            "data": {"member_id": member.id, "slot_number": member.slot_number},
        }

    @staticmethod
    def reject_member(db: Session, member_id: int, admin: User) -> dict:
        member = (
            db.query(CommitteeMember)
            .filter(CommitteeMember.id == member_id, CommitteeMember.deleted_at == None)
            .first()
        )
        if not member:
            raise HTTPException(status_code=404, detail="Member request not found")

        if member.membership_status != MembershipStatus.PENDING:
            raise HTTPException(status_code=400, detail="Member request is not pending")

        member.membership_status = MembershipStatus.REJECTED

        db.add(Notification(
            user_id=member.user_id,
            title="Membership Rejected",
            message="Your membership request has been rejected.",
            notification_type=NotificationType.GENERAL,
            reference_id=member.committee_id,
            reference_type="committee",
        ))

        db.commit()

        return {"status": True, "message": "Member rejected"}
