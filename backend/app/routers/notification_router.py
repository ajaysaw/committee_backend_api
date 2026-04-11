from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.notification import MarkReadRequest
from app.services.notification_service import NotificationService
from app.middlewares.auth_middleware import get_current_user
from app.models.models import User

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("")
def get_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return NotificationService.get_notifications(db, current_user, page, page_size)


@router.post("/mark-read")
def mark_read(
    request: MarkReadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return NotificationService.mark_read(db, current_user, request.notification_ids)


@router.post("/mark-all-read")
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return NotificationService.mark_all_read(db, current_user)
