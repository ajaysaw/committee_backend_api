from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from app.models.enums import CommitteeType, CommitteeStatus


class CommitteeCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    committee_type: CommitteeType
    status: CommitteeStatus = CommitteeStatus.DRAFT
    total_members: int = Field(..., ge=2, le=100)
    monthly_contribution: Decimal = Field(..., gt=0)
    duration_months: int = Field(..., ge=2, le=100)
    start_date: Optional[date] = None
    interest_rate: Optional[Decimal] = Field(default=Decimal("0"), ge=0, le=100)
    min_bid_amount: Optional[Decimal] = None
    max_bid_amount: Optional[Decimal] = None
    rules: Optional[str] = None


class CommitteeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    status: Optional[CommitteeStatus] = None
    start_date: Optional[date] = None
    interest_rate: Optional[Decimal] = None
    min_bid_amount: Optional[Decimal] = None
    max_bid_amount: Optional[Decimal] = None
    rules: Optional[str] = None


class CommitteeResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    committee_type: CommitteeType
    status: CommitteeStatus
    created_by: int
    total_members: int
    monthly_contribution: Decimal
    total_amount: Decimal
    duration_months: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    current_round: int
    interest_rate: Optional[Decimal] = None
    min_bid_amount: Optional[Decimal] = None
    max_bid_amount: Optional[Decimal] = None
    rules: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CommitteeListResponse(BaseModel):
    id: int
    name: str
    committee_type: CommitteeType
    status: CommitteeStatus
    total_members: int
    monthly_contribution: Decimal
    total_amount: Decimal
    current_round: int
    duration_months: int
    start_date: Optional[date] = None

    class Config:
        from_attributes = True
