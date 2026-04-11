"""
Automatic Calculation Engine for Committee Financial Operations.

Handles:
- Monthly pool amount calculation
- Winner payout calculation
- Dividend distribution (bidding committees)
- Interest payment calculation (percentage committees)
- Member profit/loss tracking
"""

from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.orm import Session

from app.models.models import (
    Committee, CommitteeMember, CommitteeRound, Payment,
    Transaction, Dividend, InterestDistribution,
    FinancialSummary, MemberStatement,
)
from app.models.enums import (
    PaymentStatus, MembershipStatus, TransactionType, CommitteeType,
)


class CalculationEngine:

    @staticmethod
    def calculate_pool_amount(total_members: int, monthly_contribution: Decimal) -> Decimal:
        """Pool amount = members × monthlyContribution"""
        return (Decimal(str(total_members)) * monthly_contribution).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    @staticmethod
    def calculate_winner_payout(committee_amount: Decimal, bid_discount: Decimal) -> Decimal:
        """Winner payout = committeeAmount − bidDiscount"""
        return (committee_amount - bid_discount).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    @staticmethod
    def calculate_dividend_per_member(discount: Decimal, remaining_members: int) -> Decimal:
        """Dividend per member = discount ÷ remainingMembers"""
        if remaining_members <= 0:
            return Decimal("0")
        return (discount / Decimal(str(remaining_members))).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    @staticmethod
    def calculate_interest_payment(committee_amount: Decimal, interest_rate: Decimal) -> Decimal:
        """Interest payment = committeeAmount × (interestRate / 100)"""
        return (committee_amount * interest_rate / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    @staticmethod
    def update_financial_summary(db: Session, committee_id: int, round_number: int) -> None:
        """Recalculate and store financial summary for a committee round."""
        committee = db.query(Committee).filter(Committee.id == committee_id).first()
        if not committee:
            return

        # Total collected this round
        total_collected = Decimal("0")
        payments = (
            db.query(Payment)
            .filter(
                Payment.committee_id == committee_id,
                Payment.round_number == round_number,
                Payment.payment_status == PaymentStatus.PAID,
                Payment.deleted_at == None,
            )
            .all()
        )
        for p in payments:
            total_collected += p.amount

        # Total paid out this round
        round_obj = (
            db.query(CommitteeRound)
            .filter(
                CommitteeRound.committee_id == committee_id,
                CommitteeRound.round_number == round_number,
            )
            .first()
        )
        total_paid_out = round_obj.winner_amount if round_obj and round_obj.winner_amount else Decimal("0")
        total_discount = round_obj.discount_amount if round_obj and round_obj.discount_amount else Decimal("0")

        # Total dividends
        total_dividends = Decimal("0")
        if round_obj:
            dividends = db.query(Dividend).filter(Dividend.round_id == round_obj.id).all()
            for d in dividends:
                total_dividends += d.amount

        # Total interest
        total_interest = Decimal("0")
        if round_obj:
            interests = db.query(InterestDistribution).filter(
                InterestDistribution.round_id == round_obj.id
            ).all()
            for i in interests:
                total_interest += i.interest_amount

        # Total penalties
        total_penalties = Decimal("0")
        for p in payments:
            total_penalties += p.late_fee

        # Upsert summary
        summary = (
            db.query(FinancialSummary)
            .filter(
                FinancialSummary.committee_id == committee_id,
                FinancialSummary.round_number == round_number,
            )
            .first()
        )
        if not summary:
            summary = FinancialSummary(
                committee_id=committee_id,
                round_number=round_number,
            )
            db.add(summary)

        summary.total_collected = total_collected
        summary.total_paid_out = total_paid_out
        summary.total_dividends = total_dividends
        summary.total_interest = total_interest
        summary.total_penalties = total_penalties
        summary.balance = total_collected - total_paid_out

        db.flush()

    @staticmethod
    def update_member_statement(db: Session, member_id: int, committee_id: int) -> None:
        """Recalculate member statement for a specific committee."""
        member = db.query(CommitteeMember).filter(CommitteeMember.id == member_id).first()
        if not member:
            return

        # Total contributions
        total_contributions = Decimal("0")
        payments = (
            db.query(Payment)
            .filter(
                Payment.user_id == member.user_id,
                Payment.committee_id == committee_id,
                Payment.payment_status == PaymentStatus.PAID,
                Payment.deleted_at == None,
            )
            .all()
        )
        for p in payments:
            total_contributions += p.amount

        # Total payouts
        total_payouts = Decimal("0")
        payout_txns = (
            db.query(Transaction)
            .filter(
                Transaction.user_id == member.user_id,
                Transaction.committee_id == committee_id,
                Transaction.transaction_type == TransactionType.PAYOUT,
                Transaction.deleted_at == None,
            )
            .all()
        )
        for t in payout_txns:
            total_payouts += t.amount

        # Total dividends
        total_dividends = Decimal("0")
        dividend_txns = (
            db.query(Transaction)
            .filter(
                Transaction.user_id == member.user_id,
                Transaction.committee_id == committee_id,
                Transaction.transaction_type == TransactionType.DIVIDEND,
                Transaction.deleted_at == None,
            )
            .all()
        )
        for t in dividend_txns:
            total_dividends += t.amount

        # Total interest
        total_interest = Decimal("0")
        interest_txns = (
            db.query(Transaction)
            .filter(
                Transaction.user_id == member.user_id,
                Transaction.committee_id == committee_id,
                Transaction.transaction_type == TransactionType.INTEREST,
                Transaction.deleted_at == None,
            )
            .all()
        )
        for t in interest_txns:
            total_interest += t.amount

        # Total penalties
        total_penalties = Decimal("0")
        penalty_txns = (
            db.query(Transaction)
            .filter(
                Transaction.user_id == member.user_id,
                Transaction.committee_id == committee_id,
                Transaction.transaction_type == TransactionType.PENALTY,
                Transaction.deleted_at == None,
            )
            .all()
        )
        for t in penalty_txns:
            total_penalties += t.amount

        net_profit_loss = total_payouts + total_dividends + total_interest - total_contributions - total_penalties

        # Upsert statement
        statement = (
            db.query(MemberStatement)
            .filter(
                MemberStatement.member_id == member_id,
                MemberStatement.committee_id == committee_id,
            )
            .first()
        )
        if not statement:
            statement = MemberStatement(
                member_id=member_id,
                committee_id=committee_id,
            )
            db.add(statement)

        statement.total_contributions = total_contributions
        statement.total_payouts = total_payouts
        statement.total_dividends = total_dividends
        statement.total_interest_earned = total_interest
        statement.total_penalties = total_penalties
        statement.net_profit_loss = net_profit_loss

        db.flush()

    @staticmethod
    def process_percentage_round(db: Session, committee_id: int, round_id: int) -> dict:
        """Process a percentage/interest based committee round."""
        committee = db.query(Committee).filter(
            Committee.id == committee_id,
            Committee.committee_type == CommitteeType.PERCENTAGE,
        ).first()
        if not committee:
            return {"status": False, "message": "Percentage committee not found"}

        round_obj = db.query(CommitteeRound).filter(CommitteeRound.id == round_id).first()
        if not round_obj:
            return {"status": False, "message": "Round not found"}

        interest_rate = committee.interest_rate or Decimal("0")
        pool = round_obj.pool_amount

        # The winner (by slot order or admin assignment) gets pool minus interest
        interest_amount = CalculationEngine.calculate_interest_payment(pool, interest_rate)
        winner_gets = pool - interest_amount

        # Distribute interest to all other members
        members = (
            db.query(CommitteeMember)
            .filter(
                CommitteeMember.committee_id == committee_id,
                CommitteeMember.membership_status == MembershipStatus.APPROVED,
                CommitteeMember.deleted_at == None,
            )
            .all()
        )

        winner = None
        if round_obj.winner_member_id:
            winner = db.query(CommitteeMember).filter(
                CommitteeMember.id == round_obj.winner_member_id
            ).first()

        remaining = [m for m in members if not winner or m.id != winner.id]

        if remaining and interest_amount > 0:
            interest_per_member = (interest_amount / Decimal(str(len(remaining)))).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            for m in remaining:
                db.add(InterestDistribution(
                    committee_id=committee_id,
                    round_id=round_id,
                    member_id=m.id,
                    principal_amount=pool,
                    interest_rate=interest_rate,
                    interest_amount=interest_per_member,
                ))
                db.add(Transaction(
                    user_id=m.user_id,
                    committee_id=committee_id,
                    transaction_type=TransactionType.INTEREST,
                    amount=interest_per_member,
                    description=f"Round {round_obj.round_number} interest distribution",
                    round_number=round_obj.round_number,
                ))

        round_obj.winner_amount = winner_gets
        round_obj.discount_amount = interest_amount

        db.flush()

        return {
            "status": True,
            "message": "Percentage round processed",
            "data": {
                "pool_amount": str(pool),
                "interest_rate": str(interest_rate),
                "interest_total": str(interest_amount),
                "winner_gets": str(winner_gets),
                "interest_per_member": str(interest_per_member) if remaining else "0",
            },
        }
