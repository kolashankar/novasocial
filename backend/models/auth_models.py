from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum

class AccountStatus(str, Enum):
    ACTIVE = "active"
    DEACTIVATED = "deactivated" 
    DELETED = "deleted"
    SUSPENDED = "suspended"

class SecurityEventType(str, Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET_REQUEST = "password_reset_request"
    PASSWORD_RESET_COMPLETE = "password_reset_complete"
    ACCOUNT_DEACTIVATED = "account_deactivated"
    ACCOUNT_DELETED = "account_deleted"
    FAILED_LOGIN = "failed_login"
    ACCOUNT_LOCKED = "account_locked"

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class PasswordResetRequest(BaseModel):
    email: EmailStr
    verification_code: str
    new_password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class VerificationCode(BaseModel):
    id: Optional[str] = None
    email: str
    code: str
    purpose: str  # "password_reset", "email_verification"
    expires_at: datetime
    used: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SecurityAuditLog(BaseModel):
    id: Optional[str] = None
    user_id: str
    event_type: SecurityEventType
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class AccountDeactivationRequest(BaseModel):
    reason: Optional[str] = None
    confirm: bool = True

class AccountDeletionRequest(BaseModel):
    password: str
    export_data: bool = False
    confirm: bool = True

class UserAccountStatus(BaseModel):
    id: Optional[str] = None
    user_id: str
    status: AccountStatus = AccountStatus.ACTIVE
    deactivated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    deletion_scheduled_at: Optional[datetime] = None  # For 30-day grace period
    reactivated_at: Optional[datetime] = None
    deactivation_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PasswordHistoryEntry(BaseModel):
    id: Optional[str] = None
    user_id: str
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class EmailVerificationResponse(BaseModel):
    success: bool
    message: str
    requires_verification: bool = False

class PasswordStrengthResult(BaseModel):
    is_valid: bool
    score: int  # 0-4 (weak to strong)
    feedback: list[str]