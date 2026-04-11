from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from decimal import Decimal
from app.models.enums import PaymentStatus, PaymentMethod, TransactionType


class PaymentCreate(BaseModel):
    committee_id: int
    round_number: int
    amount: Decimal = Field(..., gt=0)
    payment_method: PaymentMethod
    reference_number: Optional[str] = None
    notes: Optional[str] = None


class PaymentResponse(BaseModel):
    id: int
    user_id: int
    committee_id: int
    round_number: int
    amount: Decimal
    payment_status: PaymentStatus
    payment_method: Optional[PaymentMethod] = None
    payment_date: Optional[datetime] = None
    due_date: Optional[date] = None
    late_fee: Decimal
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaymentScheduleResponse(BaseModel):
    id: int
    committee_id: int
    round_number: int
    due_date: date
    amount: Decimal
    is_active: bool

    class Config:
        from_attributes = True


class TransactionResponse(BaseModel):
    id: int
    user_id: int
    committee_id: int
    transaction_type: TransactionType
    amount: Decimal
    balance_after: Optional[Decimal] = None
    description: Optional[str] = None
    reference_id: Optional[str] = None
    round_number: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
