from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.models import User, UserProfile, UserSession, OTPVerification, AuditLog
from app.models.enums import UserRole, UserStatus, AuditAction
from app.schemas.auth import (
    RegisterRequest, LoginRequest, OTPVerifyRequest, UserResponse,
    ResendOTPRequest, RefreshTokenRequest, ForgotPasswordRequest, ResetPasswordRequest,
)
from app.utils.hashing import hash_password, verify_password
from app.utils.security import create_access_token, create_refresh_token, decode_token
from app.utils.otp import generate_otp, get_otp_expiry
from app.config.settings import settings


class AuthService:

    @staticmethod
    def register(db: Session, request: RegisterRequest) -> dict:
        # Check existing email
        if db.query(User).filter(User.email == request.email, User.deleted_at == None).first():
            raise HTTPException(status_code=400, detail="Email already registered")

        # Check existing phone
        if db.query(User).filter(User.phone == request.phone, User.deleted_at == None).first():
            raise HTTPException(status_code=400, detail="Phone number already registered")

        user = User(
            name=request.name,
            email=request.email,
            phone=request.phone,
            password_hash=hash_password(request.password),
            role=request.role or UserRole.MEMBER,
            status=UserStatus.PENDING,
            is_verified=False,
        )
        db.add(user)
        db.flush()

        # Create default profile
        profile = UserProfile(user_id=user.id)
        db.add(profile)

        # Generate OTP
        otp_code = generate_otp()
        otp = OTPVerification(
            user_id=user.id,
            otp_code=otp_code,
            otp_type="registration",
            expires_at=get_otp_expiry(),
        )
        db.add(otp)

        # Audit log
        db.add(AuditLog(
            user_id=user.id,
            action=AuditAction.CREATE,
            entity_type="user",
            entity_id=user.id,
            new_values=f'{{"name": "{user.name}", "email": "{user.email}"}}',
        ))

        db.commit()
        db.refresh(user)

        return {
            "status": True,
            "message": "Registration successful. Please verify your OTP.",
            "data": {
                "user_id": user.id,
                "otp_sent": True,
                "otp_code": otp_code,  # In production, send via SMS/email, not in response
            },
        }

    @staticmethod
    def login(db: Session, request: LoginRequest, ip_address: str = None, device_info: str = None) -> dict:
        user = db.query(User).filter(User.phone == request.phone, User.deleted_at == None).first()
        if not user or not verify_password(request.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid phone number or password")

        if user.status == UserStatus.SUSPENDED:
            raise HTTPException(status_code=403, detail="Account suspended")

        if not user.is_verified:
            raise HTTPException(status_code=403, detail="Account not verified. Please verify OTP first.")

        # Create tokens
        token_data = {"sub": str(user.id), "role": user.role.value}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        # Create session
        session = UserSession(
            user_id=user.id,
            token=access_token,
            refresh_token=refresh_token,
            device_info=device_info,
            ip_address=ip_address,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
            is_active=True,
        )
        db.add(session)

        # Audit log
        db.add(AuditLog(
            user_id=user.id,
            action=AuditAction.LOGIN,
            entity_type="user",
            entity_id=user.id,
            ip_address=ip_address,
        ))

        db.commit()
        db.refresh(user)

        return {
            "status": True,
            "message": "Login successful",
            "token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "phone": user.phone,
                "role": user.role.value,
                "status": user.status.value,
                "is_verified": user.is_verified,
                "avatar_url": user.avatar_url,
            },
        }

    @staticmethod
    def logout(db: Session, user: User, token: str) -> dict:
        session = db.query(UserSession).filter(
            UserSession.user_id == user.id,
            UserSession.token == token,
            UserSession.is_active == True,
        ).first()

        if session:
            session.is_active = False
            db.add(AuditLog(
                user_id=user.id,
                action=AuditAction.LOGOUT,
                entity_type="user",
                entity_id=user.id,
            ))
            db.commit()

        return {"status": True, "message": "Logged out successfully"}

    @staticmethod
    def verify_otp(db: Session, request: OTPVerifyRequest) -> dict:
        user = db.query(User).filter(User.id == request.user_id, User.deleted_at == None).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        otp = (
            db.query(OTPVerification)
            .filter(
                OTPVerification.user_id == request.user_id,
                OTPVerification.otp_type == request.otp_type,
                OTPVerification.is_used == False,
                OTPVerification.expires_at > datetime.now(timezone.utc),
            )
            .order_by(OTPVerification.created_at.desc())
            .first()
        )

        if not otp:
            raise HTTPException(status_code=400, detail="OTP expired or not found")

        otp.attempts += 1
        if otp.attempts > 5:
            raise HTTPException(status_code=429, detail="Too many OTP attempts")

        if otp.otp_code != request.otp_code:
            db.commit()
            raise HTTPException(status_code=400, detail="Invalid OTP")

        otp.is_used = True
        user.is_verified = True
        user.status = UserStatus.ACTIVE

        db.commit()

        return {"status": True, "message": "OTP verified successfully. Account activated."}

    @staticmethod
    def resend_otp(db: Session, request: ResendOTPRequest) -> dict:
        user = db.query(User).filter(User.id == request.user_id, User.deleted_at == None).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Invalidate all previous unused OTPs of same type
        db.query(OTPVerification).filter(
            OTPVerification.user_id == request.user_id,
            OTPVerification.otp_type == request.otp_type,
            OTPVerification.is_used == False,
        ).update({"is_used": True})

        otp_code = generate_otp()
        otp = OTPVerification(
            user_id=user.id,
            otp_code=otp_code,
            otp_type=request.otp_type,
            expires_at=get_otp_expiry(),
        )
        db.add(otp)
        db.commit()

        return {
            "status": True,
            "message": "OTP resent successfully.",
            "data": {
                "user_id": user.id,
                "otp_sent": True,
                "otp_code": otp_code,  # In production, send via SMS/email
            },
        }

    @staticmethod
    def refresh_token(db: Session, request: RefreshTokenRequest) -> dict:
        payload = decode_token(request.refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

        user_id = payload.get("sub")
        session = db.query(UserSession).filter(
            UserSession.refresh_token == request.refresh_token,
            UserSession.is_active == True,
            UserSession.deleted_at == None,
        ).first()

        if not session:
            raise HTTPException(status_code=401, detail="Refresh token not found or session expired")

        user = db.query(User).filter(User.id == int(user_id), User.deleted_at == None).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        token_data = {"sub": str(user.id), "role": user.role.value}
        new_access_token = create_access_token(token_data)

        session.token = new_access_token
        session.expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        db.commit()

        return {
            "status": True,
            "message": "Token refreshed successfully",
            "token": new_access_token,
        }

    @staticmethod
    def forgot_password(db: Session, request: ForgotPasswordRequest) -> dict:
        user = db.query(User).filter(User.phone == request.phone, User.deleted_at == None).first()
        if not user:
            raise HTTPException(status_code=404, detail="No account found with this phone number")

        if user.status == UserStatus.SUSPENDED:
            raise HTTPException(status_code=403, detail="Account suspended")

        # Invalidate existing forgot_password OTPs
        db.query(OTPVerification).filter(
            OTPVerification.user_id == user.id,
            OTPVerification.otp_type == "forgot_password",
            OTPVerification.is_used == False,
        ).update({"is_used": True})

        otp_code = generate_otp()
        otp = OTPVerification(
            user_id=user.id,
            otp_code=otp_code,
            otp_type="forgot_password",
            expires_at=get_otp_expiry(),
        )
        db.add(otp)
        db.commit()

        return {
            "status": True,
            "message": "OTP sent to your registered phone number.",
            "data": {
                "user_id": user.id,
                "otp_sent": True,
                "otp_code": otp_code,  # In production, send via SMS
            },
        }

    @staticmethod
    def reset_password(db: Session, request: ResetPasswordRequest) -> dict:
        user = db.query(User).filter(User.id == request.user_id, User.deleted_at == None).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        otp = (
            db.query(OTPVerification)
            .filter(
                OTPVerification.user_id == request.user_id,
                OTPVerification.otp_type == "forgot_password",
                OTPVerification.is_used == False,
                OTPVerification.expires_at > datetime.now(timezone.utc),
            )
            .order_by(OTPVerification.created_at.desc())
            .first()
        )

        if not otp:
            raise HTTPException(status_code=400, detail="OTP expired or not found")

        otp.attempts += 1
        if otp.attempts > 5:
            raise HTTPException(status_code=429, detail="Too many OTP attempts")

        if otp.otp_code != request.otp_code:
            db.commit()
            raise HTTPException(status_code=400, detail="Invalid OTP")

        otp.is_used = True
        user.password_hash = hash_password(request.new_password)

        # Invalidate all active sessions
        db.query(UserSession).filter(
            UserSession.user_id == user.id,
            UserSession.is_active == True,
        ).update({"is_active": False})

        db.add(AuditLog(
            user_id=user.id,
            action=AuditAction.UPDATE,
            entity_type="user",
            entity_id=user.id,
            new_values='{"action": "password_reset"}',
        ))

        db.commit()

        return {"status": True, "message": "Password reset successfully. Please log in again."}

    @staticmethod
    def get_me(db: Session, user: User) -> dict:
        return {
            "status": True,
            "message": "Profile fetched successfully",
            "data": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "phone": user.phone,
                "role": user.role.value,
                "status": user.status.value,
                "is_verified": user.is_verified,
                "avatar_url": user.avatar_url,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            },
        }
