from datetime import date
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException

from app.models.models import (
    Committee, CommitteeMember, CommitteeRound, PaymentSchedule,
    AuditLog, CommitteeSetting,
)
from app.models.enums import (
    CommitteeStatus, MembershipStatus, RoundStatus, AuditAction, UserRole,
)
from app.schemas.committee import CommitteeCreate, CommitteeUpdate
from app.models.models import User


class CommitteeService:

    @staticmethod
    def create_committee(db: Session, request: CommitteeCreate, admin: User) -> dict:
        total_amount = request.monthly_contribution * request.total_members

        if request.status in (CommitteeStatus.COMPLETED, CommitteeStatus.CANCELLED):
            raise HTTPException(
                status_code=400,
                detail="Committee cannot be created with completed or cancelled status",
            )

        end_date = None
        if request.start_date and request.status == CommitteeStatus.ACTIVE:
            end_date = request.start_date + relativedelta(months=request.duration_months)

        committee = Committee(
            name=request.name,
            description=request.description,
            committee_type=request.committee_type,
            status=request.status,
            created_by=admin.id,
            total_members=request.total_members,
            monthly_contribution=request.monthly_contribution,
            total_amount=total_amount,
            duration_months=request.duration_months,
            start_date=request.start_date,
            end_date=end_date,
            interest_rate=request.interest_rate,
            min_bid_amount=request.min_bid_amount,
            max_bid_amount=request.max_bid_amount,
            rules=request.rules,
        )
        db.add(committee)
        db.flush()

        # Auto-add admin as member
        admin_member = CommitteeMember(
            committee_id=committee.id,
            user_id=admin.id,
            slot_number=1,
            membership_status=MembershipStatus.APPROVED,
        )
        db.add(admin_member)

        # Create rounds
        for i in range(1, request.duration_months + 1):
            scheduled = None
            if request.start_date:
                scheduled = request.start_date + relativedelta(months=i - 1)
            round_obj = CommitteeRound(
                committee_id=committee.id,
                round_number=i,
                status=RoundStatus.PENDING,
                scheduled_date=scheduled,
                pool_amount=total_amount,
            )
            db.add(round_obj)

        # Create payment schedules
        for i in range(1, request.duration_months + 1):
            due = None
            if request.start_date:
                due = request.start_date + relativedelta(months=i - 1)
            schedule = PaymentSchedule(
                committee_id=committee.id,
                round_number=i,
                due_date=due or date.today(),
                amount=request.monthly_contribution,
            )
            db.add(schedule)

        db.add(AuditLog(
            user_id=admin.id,
            action=AuditAction.CREATE,
            entity_type="committee",
            entity_id=committee.id,
            new_values=f'{{"name": "{committee.name}", "type": "{committee.committee_type.value}"}}',
        ))

        db.commit()
        db.refresh(committee)

        return {
            "status": True,
            "message": "Committee created successfully",
            "data": {
                "id": committee.id,
                "name": committee.name,
                "committee_type": committee.committee_type.value,
                "total_members": committee.total_members,
                "monthly_contribution": str(committee.monthly_contribution),
                "total_amount": str(committee.total_amount),
                "duration_months": committee.duration_months,
                "status": committee.status.value,
            },
        }

    @staticmethod
    def get_committees(
        db: Session,
        user: User,
        page: int = 1,
        page_size: int = 20,
        my_committees_only: bool = False,
    ) -> dict:
        query = db.query(Committee).filter(Committee.deleted_at == None)

        if user.role != UserRole.ADMIN:
            # Members should be able to browse committees that are accepting joins.
            query = query.filter(Committee.status.in_([CommitteeStatus.DRAFT, CommitteeStatus.ACTIVE]))

            if my_committees_only:
                member_committee_ids = (
                    db.query(CommitteeMember.committee_id)
                    .filter(
                        CommitteeMember.user_id == user.id,
                        CommitteeMember.membership_status == MembershipStatus.APPROVED,
                        CommitteeMember.deleted_at == None,
                    )
                    .subquery()
                )
                query = query.filter(Committee.id.in_(member_committee_ids))

        total = query.count()
        committees = query.order_by(Committee.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

        committee_ids = [c.id for c in committees]
        member_status_map: dict[int, MembershipStatus] = {}
        approved_member_counts: dict[int, int] = {}

        if committee_ids:
            count_rows = (
                db.query(CommitteeMember.committee_id, func.count(CommitteeMember.id))
                .filter(
                    CommitteeMember.committee_id.in_(committee_ids),
                    CommitteeMember.membership_status == MembershipStatus.APPROVED,
                    CommitteeMember.deleted_at == None,
                )
                .group_by(CommitteeMember.committee_id)
                .all()
            )
            approved_member_counts = {committee_id: count for committee_id, count in count_rows}

            if user.role != UserRole.ADMIN:
                membership_rows = (
                    db.query(CommitteeMember.committee_id, CommitteeMember.membership_status)
                    .filter(
                        CommitteeMember.user_id == user.id,
                        CommitteeMember.committee_id.in_(committee_ids),
                        CommitteeMember.deleted_at == None,
                    )
                    .all()
                )
                member_status_map = {
                    committee_id: membership_status
                    for committee_id, membership_status in membership_rows
                }

        data = []
        for c in committees:
            current_members = approved_member_counts.get(c.id, 0)
            item = {
                "id": c.id,
                "name": c.name,
                "committee_type": c.committee_type.value,
                "status": c.status.value,
                "total_members": c.total_members,
                "current_members": current_members,
                "monthly_contribution": str(c.monthly_contribution),
                "total_amount": str(c.total_amount),
                "current_round": c.current_round,
                "duration_months": c.duration_months,
                "start_date": str(c.start_date) if c.start_date else None,
            }

            if user.role != UserRole.ADMIN:
                membership_status = member_status_map.get(c.id)
                item["membership_status"] = membership_status.value if membership_status else None
                item["can_request_join"] = (
                    membership_status is None and current_members < c.total_members
                )

            data.append(item)

        return {
            "status": True,
            "message": "Committees fetched",
            "data": data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    @staticmethod
    def get_committee(db: Session, committee_id: int, user: User) -> dict:
        committee = (
            db.query(Committee)
            .filter(Committee.id == committee_id, Committee.deleted_at == None)
            .first()
        )
        if not committee:
            raise HTTPException(status_code=404, detail="Committee not found")

        if user.role != UserRole.ADMIN:
            membership = (
                db.query(CommitteeMember)
                .filter(
                    CommitteeMember.committee_id == committee_id,
                    CommitteeMember.user_id == user.id,
                    CommitteeMember.membership_status == MembershipStatus.APPROVED,
                    CommitteeMember.deleted_at == None,
                )
                .first()
            )
            if not membership:
                raise HTTPException(status_code=403, detail="Not a member of this committee")

        members_count = (
            db.query(CommitteeMember)
            .filter(
                CommitteeMember.committee_id == committee_id,
                CommitteeMember.membership_status == MembershipStatus.APPROVED,
                CommitteeMember.deleted_at == None,
            )
            .count()
        )

        return {
            "status": True,
            "message": "Committee details",
            "data": {
                "id": committee.id,
                "name": committee.name,
                "description": committee.description,
                "committee_type": committee.committee_type.value,
                "status": committee.status.value,
                "created_by": committee.created_by,
                "total_members": committee.total_members,
                "current_members": members_count,
                "monthly_contribution": str(committee.monthly_contribution),
                "total_amount": str(committee.total_amount),
                "duration_months": committee.duration_months,
                "start_date": str(committee.start_date) if committee.start_date else None,
                "end_date": str(committee.end_date) if committee.end_date else None,
                "current_round": committee.current_round,
                "interest_rate": str(committee.interest_rate) if committee.interest_rate else None,
                "min_bid_amount": str(committee.min_bid_amount) if committee.min_bid_amount else None,
                "max_bid_amount": str(committee.max_bid_amount) if committee.max_bid_amount else None,
                "rules": committee.rules,
                "created_at": str(committee.created_at),
            },
        }

    @staticmethod
    def update_committee(db: Session, committee_id: int, request: CommitteeUpdate, admin: User) -> dict:
        committee = (
            db.query(Committee)
            .filter(Committee.id == committee_id, Committee.deleted_at == None)
            .first()
        )
        if not committee:
            raise HTTPException(status_code=404, detail="Committee not found")

        update_data = request.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(committee, key, value)

        if request.start_date and request.status == CommitteeStatus.ACTIVE:
            committee.end_date = request.start_date + relativedelta(months=committee.duration_months)

        db.add(AuditLog(
            user_id=admin.id,
            action=AuditAction.UPDATE,
            entity_type="committee",
            entity_id=committee.id,
        ))

        db.commit()
        db.refresh(committee)

        return {
            "status": True,
            "message": "Committee updated successfully",
            "data": {"id": committee.id, "name": committee.name, "status": committee.status.value},
        }

    @staticmethod
    def delete_committee(db: Session, committee_id: int, admin: User) -> dict:
        committee = (
            db.query(Committee)
            .filter(Committee.id == committee_id, Committee.deleted_at == None)
            .first()
        )
        if not committee:
            raise HTTPException(status_code=404, detail="Committee not found")

        if committee.status == CommitteeStatus.ACTIVE:
            raise HTTPException(status_code=400, detail="Cannot delete an active committee")

        from datetime import datetime, timezone
        committee.deleted_at = datetime.now(timezone.utc)

        db.add(AuditLog(
            user_id=admin.id,
            action=AuditAction.DELETE,
            entity_type="committee",
            entity_id=committee.id,
        ))

        db.commit()

        return {"status": True, "message": "Committee deleted successfully"}
