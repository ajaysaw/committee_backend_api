from datetime import datetime, timezone, date
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.models import (
    Payment, PaymentSchedule, Transaction, Committee,
    CommitteeMember, AuditLog, Notification, User,
)
from app.models.enums import (
    PaymentStatus, TransactionType, MembershipStatus,
    AuditAction, NotificationType,
)
from app.schemas.payment import PaymentCreate


class PaymentService:

    @staticmethod
    def make_payment(db: Session, request: PaymentCreate, user: User) -> dict:
        committee = (
            db.query(Committee)
            .filter(Committee.id == request.committee_id, Committee.deleted_at == None)
            .first()
        )
        if not committee:
            raise HTTPException(status_code=404, detail="Committee not found")

        member = (
            db.query(CommitteeMember)
            .filter(
                CommitteeMember.committee_id == request.committee_id,
                CommitteeMember.user_id == user.id,
                CommitteeMember.membership_status == MembershipStatus.APPROVED,
                CommitteeMember.deleted_at == None,
            )
            .first()
        )
        if not member:
            raise HTTPException(status_code=403, detail="Not a member of this committee")

        # Check for duplicate payment
        existing = (
            db.query(Payment)
            .filter(
                Payment.user_id == user.id,
                Payment.committee_id == request.committee_id,
                Payment.round_number == request.round_number,
                Payment.payment_status == PaymentStatus.PAID,
                Payment.deleted_at == None,
            )
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="Payment already made for this round")

        # Get schedule for due date
        schedule = (
            db.query(PaymentSchedule)
            .filter(
                PaymentSchedule.committee_id == request.committee_id,
                PaymentSchedule.round_number == request.round_number,
            )
            .first()
        )

        due_date = schedule.due_date if schedule else date.today()
        now = datetime.now(timezone.utc)

        # Calculate late fee
        late_fee = Decimal("0")
        if schedule and date.today() > schedule.due_date:
            days_late = (date.today() - schedule.due_date).days
            late_fee = Decimal(str(days_late)) * Decimal("10")  # ₹10 per day late

        payment = Payment(
            user_id=user.id,
            committee_id=request.committee_id,
            round_number=request.round_number,
            amount=request.amount,
            payment_status=PaymentStatus.PAID,
            payment_method=request.payment_method,
            payment_date=now,
            due_date=due_date,
            late_fee=late_fee,
            reference_number=request.reference_number,
            notes=request.notes,
        )
        db.add(payment)

        # Update member total
        member.total_paid += request.amount

        # Create transaction
        db.add(Transaction(
            user_id=user.id,
            committee_id=request.committee_id,
            transaction_type=TransactionType.CONTRIBUTION,
            amount=request.amount,
            description=f"Round {request.round_number} contribution",
            reference_id=request.reference_number,
            round_number=request.round_number,
        ))

        # Audit
        db.add(AuditLog(
            user_id=user.id,
            action=AuditAction.PAYMENT,
            entity_type="payment",
            new_values=f'{{"amount": "{request.amount}", "round": {request.round_number}}}',
        ))

        # Notify admin
        db.add(Notification(
            user_id=committee.created_by,
            title="Payment Received",
            message=f"{user.name} paid ₹{request.amount} for round {request.round_number}",
            notification_type=NotificationType.PAYMENT_RECEIVED,
            reference_id=request.committee_id,
            reference_type="committee",
        ))

        db.commit()
        db.refresh(payment)

        return {
            "status": True,
            "message": "Payment successful",
            "data": {
                "payment_id": payment.id,
                "amount": str(payment.amount),
                "late_fee": str(payment.late_fee),
                "payment_status": payment.payment_status.value,
                "round_number": payment.round_number,
            },
        }

    @staticmethod
    def get_payment_history(
        db: Session, user: User, committee_id: int = None,
        page: int = 1, page_size: int = 20,
    ) -> dict:
        query = db.query(Payment).filter(Payment.user_id == user.id, Payment.deleted_at == None)
        if committee_id:
            query = query.filter(Payment.committee_id == committee_id)

        total = query.count()
        payments = query.order_by(Payment.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

        data = []
        for p in payments:
            data.append({
                "id": p.id,
                "committee_id": p.committee_id,
                "round_number": p.round_number,
                "amount": str(p.amount),
                "payment_status": p.payment_status.value,
                "payment_method": p.payment_method.value if p.payment_method else None,
                "payment_date": str(p.payment_date) if p.payment_date else None,
                "due_date": str(p.due_date) if p.due_date else None,
                "late_fee": str(p.late_fee),
                "reference_number": p.reference_number,
                "created_at": str(p.created_at),
            })

        return {
            "status": True,
            "message": "Payment history",
            "data": data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    @staticmethod
    def get_payment_schedule(db: Session, committee_id: int) -> dict:
        schedules = (
            db.query(PaymentSchedule)
            .filter(PaymentSchedule.committee_id == committee_id, PaymentSchedule.is_active == True)
            .order_by(PaymentSchedule.round_number)
            .all()
        )

        data = []
        for s in schedules:
            data.append({
                "id": s.id,
                "round_number": s.round_number,
                "due_date": str(s.due_date),
                "amount": str(s.amount),
            })

        return {"status": True, "message": "Payment schedule", "data": data}
