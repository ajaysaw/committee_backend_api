from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.payment import PaymentCreate
from app.services.payment_service import PaymentService
from app.middlewares.auth_middleware import get_current_user
from app.models.models import User

router = APIRouter(prefix="/api/payments", tags=["Payment Management"])


@router.post("/pay")
def make_payment(
    request: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return PaymentService.make_payment(db, request, current_user)


@router.get("/history")
def payment_history(
    committee_id: int = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return PaymentService.get_payment_history(db, current_user, committee_id, page, page_size)


@router.get("/schedule")
def payment_schedule(
    committee_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return PaymentService.get_payment_schedule(db, committee_id)
