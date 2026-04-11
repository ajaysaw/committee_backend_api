from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class PlaceBidRequest(BaseModel):
    round_id: int
    bid_amount: Decimal = Field(..., gt=0)


class StartRoundRequest(BaseModel):
    committee_id: int


class CloseRoundRequest(BaseModel):
    round_id: int


class BidResponse(BaseModel):
    id: int
    round_id: int
    user_id: int
    committee_id: int
    bid_amount: Decimal
    is_winner: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RoundResponse(BaseModel):
    id: int
    committee_id: int
    round_number: int
    status: str
    scheduled_date: Optional[str] = None
    completed_date: Optional[str] = None
    pool_amount: Decimal
    winner_member_id: Optional[int] = None
    winner_amount: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
