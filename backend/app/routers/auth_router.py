from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.auth import (
    RegisterRequest, LoginRequest, OTPVerifyRequest,
    ResendOTPRequest, RefreshTokenRequest, ForgotPasswordRequest, ResetPasswordRequest,
)
from app.schemas.common import APIResponse
from app.services.auth_service import AuthService
from app.middlewares.auth_middleware import get_current_user
from app.models.models import User

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer()


@router.post("/register", response_model=APIResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    result = AuthService.register(db, request)
    return result


@router.post("/login")
def login(request: LoginRequest, req: Request, db: Session = Depends(get_db)):
    ip = req.client.host if req.client else None
    device = req.headers.get("User-Agent")
    result = AuthService.login(db, request, ip_address=ip, device_info=device)
    return result


@router.post("/logout", response_model=APIResponse)
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = AuthService.logout(db, current_user, credentials.credentials)
    return result


@router.post("/verify-otp", response_model=APIResponse)
def verify_otp(request: OTPVerifyRequest, db: Session = Depends(get_db)):
    result = AuthService.verify_otp(db, request)
    return result


@router.post("/resend-otp", response_model=APIResponse)
def resend_otp(request: ResendOTPRequest, db: Session = Depends(get_db)):
    result = AuthService.resend_otp(db, request)
    return result


@router.post("/refresh-token")
def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    result = AuthService.refresh_token(db, request)
    return result


@router.post("/forgot-password", response_model=APIResponse)
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    result = AuthService.forgot_password(db, request)
    return result


@router.post("/reset-password", response_model=APIResponse)
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    result = AuthService.reset_password(db, request)
    return result


@router.get("/me")
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = AuthService.get_me(db, current_user)
    return result
