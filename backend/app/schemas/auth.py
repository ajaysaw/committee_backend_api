from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, date
from app.models.enums import UserRole, UserStatus


# ── Auth Schemas ──────────────────────────────────────────
class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=20)
    password: str = Field(..., min_length=6, max_length=128)
    role: Optional[UserRole] = UserRole.MEMBER


class LoginRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=20)
    password: str


class OTPVerifyRequest(BaseModel):
    user_id: int
    otp_code: str = Field(..., min_length=4, max_length=10)
    otp_type: str = "registration"


class ResendOTPRequest(BaseModel):
    user_id: int
    otp_type: str = "registration"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=20)


class ResetPasswordRequest(BaseModel):
    user_id: int
    otp_code: str = Field(..., min_length=4, max_length=10)
    new_password: str = Field(..., min_length=6, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    role: UserRole
    status: UserStatus
    is_verified: bool
    avatar_url: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    status: bool = True
    message: str = "Login successful"
    token: str
    refresh_token: Optional[str] = None
    user: UserResponse


class UserProfileUpdate(BaseModel):
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    aadhar_number: Optional[str] = None
    pan_number: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_ifsc: Optional[str] = None
    upi_id: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
