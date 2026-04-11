from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.models import (
    Committee, CommitteeMember, CommitteeRound, Payment,
    Transaction, FinancialSummary, MemberStatement, User,
)
from app.models.enums import (
    CommitteeStatus, MembershipStatus, PaymentStatus,
    TransactionType, UserRole,
)
from app.services.calculation_engine import CalculationEngine


class ReportService:

    @staticmethod
    def get_member_statement(db: Session, user: User, committee_id: int) -> dict:
        member = (
            db.query(CommitteeMember)
            .filter(
                CommitteeMember.user_id == user.id,
                CommitteeMember.committee_id == committee_id,
                CommitteeMember.membership_status == MembershipStatus.APPROVED,
                CommitteeMember.deleted_at == None,
            )
            .first()
        )
        if not member:
            return {"status": False, "message": "Not a member of this committee"}

        # Update statement first
        CalculationEngine.update_member_statement(db, member.id, committee_id)
        db.commit()

        statement = (
            db.query(MemberStatement)
            .filter(
                MemberStatement.member_id == member.id,
                MemberStatement.committee_id == committee_id,
            )
            .first()
        )

        committee = db.query(Committee).filter(Committee.id == committee_id).first()

        data = {
            "member_id": member.id,
            "committee_id": committee_id,
            "user_name": user.name,
            "committee_name": committee.name if committee else None,
            "total_contributions": str(statement.total_contributions) if statement else "0",
            "total_payouts": str(statement.total_payouts) if statement else "0",
            "total_dividends": str(statement.total_dividends) if statement else "0",
            "total_interest_earned": str(statement.total_interest_earned) if statement else "0",
            "total_penalties": str(statement.total_penalties) if statement else "0",
            "net_profit_loss": str(statement.net_profit_loss) if statement else "0",
        }

        # Transaction history
        txns = (
            db.query(Transaction)
            .filter(
                Transaction.user_id == user.id,
                Transaction.committee_id == committee_id,
                Transaction.deleted_at == None,
            )
            .order_by(Transaction.created_at.desc())
            .all()
        )
        data["transactions"] = [
            {
                "id": t.id,
                "type": t.transaction_type.value,
                "amount": str(t.amount),
                "description": t.description,
                "round_number": t.round_number,
                "date": str(t.created_at),
            }
            for t in txns
        ]

        return {"status": True, "message": "Member statement", "data": data}

    @staticmethod
    def get_committee_report(db: Session, committee_id: int) -> dict:
        committee = (
            db.query(Committee)
            .filter(Committee.id == committee_id, Committee.deleted_at == None)
            .first()
        )
        if not committee:
            return {"status": False, "message": "Committee not found"}

        # Aggregate summaries
        summaries = (
            db.query(FinancialSummary)
            .filter(FinancialSummary.committee_id == committee_id)
            .all()
        )

        total_collected = sum(s.total_collected for s in summaries) if summaries else Decimal("0")
        total_paid_out = sum(s.total_paid_out for s in summaries) if summaries else Decimal("0")
        total_dividends = sum(s.total_dividends for s in summaries) if summaries else Decimal("0")
        total_interest = sum(s.total_interest for s in summaries) if summaries else Decimal("0")
        total_penalties = sum(s.total_penalties for s in summaries) if summaries else Decimal("0")
        balance = total_collected - total_paid_out

        rounds_completed = (
            db.query(CommitteeRound)
            .filter(
                CommitteeRound.committee_id == committee_id,
                CommitteeRound.status == "completed",
            )
            .count()
        )

        return {
            "status": True,
            "message": "Committee report",
            "data": {
                "committee_id": committee_id,
                "committee_name": committee.name,
                "total_collected": str(total_collected),
                "total_paid_out": str(total_paid_out),
                "total_dividends": str(total_dividends),
                "total_interest": str(total_interest),
                "total_penalties": str(total_penalties),
                "balance": str(balance),
                "rounds_completed": rounds_completed,
                "total_rounds": committee.duration_months,
            },
        }

    @staticmethod
    def get_admin_dashboard(db: Session) -> dict:
        total_committees = db.query(Committee).filter(Committee.deleted_at == None).count()
        active_committees = (
            db.query(Committee)
            .filter(Committee.status == CommitteeStatus.ACTIVE, Committee.deleted_at == None)
            .count()
        )
        total_members = (
            db.query(CommitteeMember)
            .filter(
                CommitteeMember.membership_status == MembershipStatus.APPROVED,
                CommitteeMember.deleted_at == None,
            )
            .count()
        )

        total_collections_row = (
            db.query(func.coalesce(func.sum(Payment.amount), 0))
            .filter(Payment.payment_status == PaymentStatus.PAID, Payment.deleted_at == None)
            .scalar()
        )
        total_collections = Decimal(str(total_collections_row or 0))

        total_payouts_row = (
            db.query(func.coalesce(func.sum(Transaction.amount), 0))
            .filter(
                Transaction.transaction_type == TransactionType.PAYOUT,
                Transaction.deleted_at == None,
            )
            .scalar()
        )
        total_payouts = Decimal(str(total_payouts_row or 0))

        pending_payments = (
            db.query(Payment)
            .filter(Payment.payment_status == PaymentStatus.PENDING, Payment.deleted_at == None)
            .count()
        )
        overdue_payments = (
            db.query(Payment)
            .filter(Payment.payment_status == PaymentStatus.LATE, Payment.deleted_at == None)
            .count()
        )

        return {
            "status": True,
            "message": "Admin dashboard",
            "data": {
                "total_committees": total_committees,
                "active_committees": active_committees,
                "total_members": total_members,
                "total_collections": str(total_collections),
                "total_payouts": str(total_payouts),
                "pending_payments": pending_payments,
                "overdue_payments": overdue_payments,
            },
        }

    @staticmethod
    def get_member_dashboard(db: Session, user: User) -> dict:
        memberships = (
            db.query(CommitteeMember)
            .filter(
                CommitteeMember.user_id == user.id,
                CommitteeMember.membership_status == MembershipStatus.APPROVED,
                CommitteeMember.deleted_at == None,
            )
            .all()
        )

        total_committees = len(memberships)
        active_committees = 0
        total_invested = Decimal("0")
        total_earned = Decimal("0")
        pending_payments = 0

        for m in memberships:
            committee = db.query(Committee).filter(Committee.id == m.committee_id).first()
            if committee and committee.status == CommitteeStatus.ACTIVE:
                active_committees += 1

            total_invested += m.total_paid
            total_earned += m.total_received

            pp = (
                db.query(Payment)
                .filter(
                    Payment.user_id == user.id,
                    Payment.committee_id == m.committee_id,
                    Payment.payment_status == PaymentStatus.PENDING,
                    Payment.deleted_at == None,
                )
                .count()
            )
            pending_payments += pp

        return {
            "status": True,
            "message": "Member dashboard",
            "data": {
                "total_committees": total_committees,
                "active_committees": active_committees,
                "total_invested": str(total_invested),
                "total_earned": str(total_earned),
                "pending_payments": pending_payments,
            },
        }
