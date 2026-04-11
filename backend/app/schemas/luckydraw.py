from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class RunLuckyDrawRequest(BaseModel):
    committee_id: int
    round_id: int


class LuckyDrawResponse(BaseModel):
    id: int
    round_id: int
    committee_id: int
    winner_member_id: Optional[int] = None
    winner_name: Optional[str] = None
    draw_timestamp: Optional[datetime] = None
    pool_amount: Optional[Decimal] = None

    class Config:
        from_attributes = True


class LuckyDrawHistoryResponse(BaseModel):
    id: int
    lucky_draw_id: int
    member_id: int
    member_name: Optional[str] = None
    was_eligible: bool
    was_winner: bool

    class Config:
        from_attributes = True
