from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.transaction_service import TransactionService
from app.middlewares.auth_middleware import get_current_user, require_admin
from app.models.models import User

router = APIRouter(prefix="/api/transactions", tags=["Financial Transactions"])


@router.get("/member")
def member_transactions(
    committee_id: int = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return TransactionService.get_member_transactions(db, current_user, committee_id, page, page_size)


@router.get("/committee")
def committee_transactions(
    committee_id: int = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return TransactionService.get_committee_transactions(db, committee_id, current_user, page, page_size)
