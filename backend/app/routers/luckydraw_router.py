from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.luckydraw import RunLuckyDrawRequest
from app.services.luckydraw_service import LuckyDrawService
from app.middlewares.auth_middleware import get_current_user, require_admin
from app.models.models import User

router = APIRouter(prefix="/api/luckydraw", tags=["Lucky Draw System"])


@router.post("/run")
def run_lucky_draw(
    request: RunLuckyDrawRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return LuckyDrawService.run_draw(db, request.committee_id, request.round_id, admin)


@router.get("/history")
def lucky_draw_history(
    committee_id: int = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return LuckyDrawService.get_history(db, committee_id, page, page_size)
