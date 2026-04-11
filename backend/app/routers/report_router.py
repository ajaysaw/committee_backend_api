from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.report_service import ReportService
from app.middlewares.auth_middleware import get_current_user, require_admin
from app.models.models import User

router = APIRouter(prefix="/api/reports", tags=["Reporting"])


@router.get("/member-statement")
def member_statement(
    committee_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ReportService.get_member_statement(db, current_user, committee_id)


@router.get("/committee")
def committee_report(
    committee_id: int = Query(...),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return ReportService.get_committee_report(db, committee_id)


@router.get("/admin-dashboard")
def admin_dashboard(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return ReportService.get_admin_dashboard(db)


@router.get("/member-dashboard")
def member_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ReportService.get_member_dashboard(db, current_user)
