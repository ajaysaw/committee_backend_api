from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from decimal import Decimal


class MemberStatementResponse(BaseModel):
    member_id: int
    committee_id: int
    user_name: Optional[str] = None
    committee_name: Optional[str] = None
    total_contributions: Decimal
    total_payouts: Decimal
    total_dividends: Decimal
    total_interest_earned: Decimal
    total_penalties: Decimal
    net_profit_loss: Decimal

    class Config:
        from_attributes = True


class CommitteeReportResponse(BaseModel):
    committee_id: int
    committee_name: str
    total_collected: Decimal
    total_paid_out: Decimal
    total_dividends: Decimal
    total_interest: Decimal
    total_penalties: Decimal
    balance: Decimal
    rounds_completed: int
    total_rounds: int

    class Config:
        from_attributes = True


class AdminDashboardResponse(BaseModel):
    total_committees: int
    active_committees: int
    total_members: int
    total_collections: Decimal
    total_payouts: Decimal
    pending_payments: int
    overdue_payments: int


class MemberDashboardResponse(BaseModel):
    total_committees: int
    active_committees: int
    total_invested: Decimal
    total_earned: Decimal
    pending_payments: int
    next_payment_date: Optional[date] = None
