from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.bidding import PlaceBidRequest, StartRoundRequest, CloseRoundRequest
from app.services.bidding_service import BiddingService
from app.middlewares.auth_middleware import get_current_user, require_admin
from app.models.models import User

router = APIRouter(prefix="/api/bids", tags=["Bidding System"])


@router.post("/start-round")
def start_round(
    request: StartRoundRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return BiddingService.start_round(db, request.committee_id, admin)


@router.post("/place")
def place_bid(
    request: PlaceBidRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return BiddingService.place_bid(db, request.round_id, request.bid_amount, current_user)


@router.post("/close-round")
def close_round(
    request: CloseRoundRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return BiddingService.close_round(db, request.round_id, admin)


@router.get("/history")
def bid_history(
    committee_id: int = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return BiddingService.get_bid_history(db, committee_id, current_user, page, page_size)
