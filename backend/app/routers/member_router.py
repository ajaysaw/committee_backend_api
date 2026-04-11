from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.member import MemberJoinRequest, MemberApproveRequest
from app.services.member_service import MemberService
from app.middlewares.auth_middleware import get_current_user, require_admin
from app.models.models import User

router = APIRouter(prefix="/api/members", tags=["Member Management"])


@router.post("/join")
def join_committee(
    request: MemberJoinRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return MemberService.join_committee(db, request.committee_id, current_user)


@router.get("/list")
def list_members(
    committee_id: int = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return MemberService.list_members(db, committee_id, current_user, page, page_size)


@router.post("/approve")
def approve_member(
    request: MemberApproveRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return MemberService.approve_member(db, request.member_id, admin, request.slot_number)


@router.post("/reject")
def reject_member(
    member_id: int = Query(...),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return MemberService.reject_member(db, member_id, admin)
