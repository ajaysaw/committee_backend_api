from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal
from app.models.enums import MembershipStatus


class MemberJoinRequest(BaseModel):
    committee_id: int


class MemberApproveRequest(BaseModel):
    member_id: int
    slot_number: Optional[int] = None


class MemberResponse(BaseModel):
    id: int
    committee_id: int
    user_id: int
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    user_phone: Optional[str] = None
    slot_number: Optional[int] = None
    membership_status: MembershipStatus
    has_received_payout: bool
    payout_round: Optional[int] = None
    total_paid: Decimal
    total_received: Decimal
    joined_at: Optional[datetime] = None

    class Config:
        from_attributes = True
