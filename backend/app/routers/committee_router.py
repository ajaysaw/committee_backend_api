from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.committee import CommitteeCreate, CommitteeUpdate
from app.schemas.common import APIResponse
from app.services.committee_service import CommitteeService
from app.middlewares.auth_middleware import get_current_user, require_admin
from app.models.models import User

router = APIRouter(prefix="/api/committees", tags=["Committee Management"])


@router.post("/create")
def create_committee(
    request: CommitteeCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return CommitteeService.create_committee(db, request, admin)


@router.get("")
def get_committees(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    my_committees_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CommitteeService.get_committees(db, current_user, page, page_size, my_committees_only)


@router.get("/{committee_id}")
def get_committee(
    committee_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CommitteeService.get_committee(db, committee_id, current_user)


@router.put("/update")
def update_committee(
    committee_id: int = Query(...),
    request: CommitteeUpdate = ...,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return CommitteeService.update_committee(db, committee_id, request, admin)


@router.delete("/delete")
def delete_committee(
    committee_id: int = Query(...),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return CommitteeService.delete_committee(db, committee_id, admin)
