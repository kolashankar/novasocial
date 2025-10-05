from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
import re
import hashlib
import base64
import socketio
import asyncio
from contextlib import asynccontextmanager


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

security = HTTPBearer()

# Create Socket.IO server
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins="*")

# Create the main app without a prefix
app = FastAPI()

# Mount Socket.IO
socket_app = socketio.ASGIApp(sio, app)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# User Models
class UserRegister(BaseModel):
    fullName: str
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserProfile(BaseModel):
    profileImage: Optional[str] = None
    bio: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    fullName: str
    profileImage: Optional[str] = None
    bio: Optional[str] = None
    createdAt: datetime

class AuthResponse(BaseModel):
    user: UserResponse
    token: str

# Post Models
class PostCreate(BaseModel):
    caption: str
    media: List[str]  # List of base64 images/videos
    mediaTypes: List[str]  # ["image", "video", ...]
    hashtags: Optional[List[str]] = []
    taggedUsers: Optional[List[str]] = []

class PostResponse(BaseModel):
    id: str
    authorId: str
    author: UserResponse
    caption: str
    media: List[str]
    mediaTypes: List[str]
    hashtags: List[str]
    taggedUsers: List[str]
    likes: List[str]  # List of user IDs who liked
    likesCount: int
    comments: List[dict]  # Will be populated separately
    commentsCount: int
    createdAt: datetime
    updatedAt: datetime

class CommentCreate(BaseModel):
    text: str
    postId: str

class CommentResponse(BaseModel):
    id: str
    postId: str
    authorId: str
    author: UserResponse
    text: str
    likes: List[str]
    likesCount: int
    createdAt: datetime

class LikeToggle(BaseModel):
    targetId: str  # Post or Comment ID
    targetType: str  # "post" or "comment"

class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

# Chat Models
class ConversationCreate(BaseModel):
    participantIds: List[str]
    isGroup: bool = False
    name: Optional[str] = None
    description: Optional[str] = None

# Import Phase 14 models from messaging_models.py

class MessageCreate(BaseModel):
    conversationId: str
    text: Optional[str] = None
    messageType: str = "text"  # "text", "image", "video", "emoji"
    media: Optional[str] = None  # base64 encoded media
    replyTo: Optional[str] = None  # Reply to message ID

class MessageResponse(BaseModel):
    id: str
    conversationId: str
    senderId: str
    sender: UserResponse
    text: Optional[str]
    messageType: str
    media: Optional[str]
    replyTo: Optional[str]
    readBy: List[dict]  # [{"userId": str, "readAt": datetime}]
    createdAt: datetime
    updatedAt: datetime

class ConversationResponse(BaseModel):
    id: str
    participantIds: List[str]
    participants: List[UserResponse]
    isGroup: bool
    name: Optional[str]
    description: Optional[str]
    lastMessage: Optional[MessageResponse]
    unreadCount: int
    createdAt: datetime
    updatedAt: datetime

# Stories Models
class StoryCreate(BaseModel):
    media: str  # base64 encoded image/video
    mediaType: str  # "image" or "video"
    text: Optional[str] = None
    textPosition: Optional[dict] = None  # {"x": 0.5, "y": 0.3}
    textStyle: Optional[dict] = None  # {"color": "#fff", "fontSize": 24}
    duration: Optional[int] = 24  # hours

class StoryResponse(BaseModel):
    id: str
    authorId: str
    author: UserResponse
    media: str
    mediaType: str
    text: Optional[str]
    textPosition: Optional[dict]
    textStyle: Optional[dict]
    duration: int
    viewers: List[str]  # User IDs who viewed
    viewersCount: int
    createdAt: datetime
    expiresAt: datetime

# Notification Models
class NotificationCreate(BaseModel):
    recipientId: str
    type: str  # "like", "comment", "follow", "mention"
    title: str
    message: str
    relatedId: Optional[str] = None  # Post/Comment/User ID
    relatedType: Optional[str] = None  # "post", "comment", "user"

class NotificationResponse(BaseModel):
    id: str
    recipientId: str
    senderId: Optional[str]
    sender: Optional[UserResponse]
    type: str
    title: str
    message: str
    relatedId: Optional[str]
    relatedType: Optional[str]
    isRead: bool
    createdAt: datetime

# Search Models
class FollowRequest(BaseModel):
    targetUserId: str

class SearchQuery(BaseModel):
    query: str
    type: Optional[str] = "all"  # "users", "posts", "hashtags", "all"

class SearchResponse(BaseModel):
    users: List[UserResponse]
    posts: List[PostResponse]
    hashtags: List[str]


# Utility Functions
def _pre_hash_password(password: str) -> bytes:
    """Pre-hash password to avoid bcrypt 72-byte limit"""
    hashed_pw = hashlib.sha256(password.encode('utf-8')).digest()
    return base64.b64encode(hashed_pw)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    pre_hashed = _pre_hash_password(plain_password)
    return bcrypt.checkpw(pre_hashed, hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    pre_hashed = _pre_hash_password(password)
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pre_hashed, salt)
    return hashed.decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def validate_username(username: str) -> bool:
    return bool(re.match(r'^[a-zA-Z0-9_]{3,20}$', username))

def validate_password(password: str) -> bool:
    return len(password) >= 8

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"email": email})
    if user is None:
        raise credentials_exception
    
    return user

# Socket.IO Events
@sio.event
async def connect(sid, environ):
    print(f"Client {sid} connected")

@sio.event
async def disconnect(sid):
    print(f"Client {sid} disconnected")

@sio.event
async def join_conversation(sid, data):
    """Join a conversation room"""
    conversation_id = data.get('conversationId')
    if conversation_id:
        await sio.enter_room(sid, f"conversation_{conversation_id}")
        print(f"Client {sid} joined conversation {conversation_id}")

@sio.event
async def leave_conversation(sid, data):
    """Leave a conversation room"""
    conversation_id = data.get('conversationId')
    if conversation_id:
        await sio.leave_room(sid, f"conversation_{conversation_id}")
        print(f"Client {sid} left conversation {conversation_id}")

@sio.event
async def send_message(sid, data):
    """Handle real-time message sending"""
    try:
        conversation_id = data.get('conversationId')
        message_data = data.get('message')
        
        if conversation_id and message_data:
            # Emit to all clients in the conversation room
            await sio.emit('new_message', {
                'conversationId': conversation_id,
                'message': message_data
            }, room=f"conversation_{conversation_id}")
            
    except Exception as e:
        print(f"Error sending message: {e}")

@sio.event
async def typing_start(sid, data):
    """Handle typing indicator"""
    conversation_id = data.get('conversationId')
    user_id = data.get('userId')
    if conversation_id and user_id:
        await sio.emit('user_typing', {
            'conversationId': conversation_id,
            'userId': user_id,
            'typing': True
        }, room=f"conversation_{conversation_id}", skip_sid=sid)

@sio.event
async def typing_stop(sid, data):
    """Handle stop typing"""
    conversation_id = data.get('conversationId')
    user_id = data.get('userId')
    if conversation_id and user_id:
        await sio.emit('user_typing', {
            'conversationId': conversation_id,
            'userId': user_id,
            'typing': False
        }, room=f"conversation_{conversation_id}", skip_sid=sid)

@sio.event
async def mark_read(sid, data):
    """Mark messages as read"""
    conversation_id = data.get('conversationId')
    user_id = data.get('userId')
    message_ids = data.get('messageIds', [])
    
    if conversation_id and user_id:
        # Update read receipts in database
        for message_id in message_ids:
            await db.messages.update_one(
                {"id": message_id, "conversationId": conversation_id},
                {
                    "$addToSet": {
                        "readBy": {
                            "userId": user_id,
                            "readAt": datetime.utcnow()
                        }
                    }
                }
            )
        
        # Emit read receipt to other users
        await sio.emit('messages_read', {
            'conversationId': conversation_id,
            'userId': user_id,
            'messageIds': message_ids
        }, room=f"conversation_{conversation_id}", skip_sid=sid)


# Auth Routes
@api_router.post("/auth/register", response_model=AuthResponse)
async def register_user(user_data: UserRegister):
    # Validate input
    if not validate_username(user_data.username):
        raise HTTPException(
            status_code=400,
            detail="Username must be 3-20 characters, alphanumeric and underscores only"
        )
    
    if not validate_password(user_data.password):
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters long"
        )
    
    # Check if user exists
    existing_user = await db.users.find_one({
        "$or": [
            {"email": user_data.email},
            {"username": user_data.username}
        ]
    })
    
    if existing_user:
        if existing_user["email"] == user_data.email:
            raise HTTPException(status_code=400, detail="Email already registered")
        else:
            raise HTTPException(status_code=400, detail="Username already taken")
    
    # Create new user
    user_id = str(uuid.uuid4())
    hashed_password = get_password_hash(user_data.password)
    
    new_user = {
        "id": user_id,
        "email": user_data.email,
        "username": user_data.username.lower(),
        "fullName": user_data.fullName,
        "password": hashed_password,
        "profileImage": None,
        "bio": None,
        "createdAt": datetime.utcnow()
    }
    
    await db.users.insert_one(new_user)
    
    # Create token
    access_token = create_access_token(data={"sub": user_data.email})
    
    # Return user without password
    user_response = UserResponse(**{k: v for k, v in new_user.items() if k != "password"})
    
    return AuthResponse(user=user_response, token=access_token)

@api_router.post("/auth/login", response_model=AuthResponse)
async def login_user(user_data: UserLogin):
    # Find user
    user = await db.users.find_one({"email": user_data.email})
    
    if not user or not verify_password(user_data.password, user["password"]):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )
    
    # Create token
    access_token = create_access_token(data={"sub": user_data.email})
    
    # Return user without password
    user_response = UserResponse(**{k: v for k, v in user.items() if k != "password"})
    
    return AuthResponse(user=user_response, token=access_token)

@api_router.put("/auth/profile", response_model=UserResponse)
async def update_profile(profile_data: UserProfile, current_user = Depends(get_current_user)):
    # Update user profile
    update_data = {}
    if profile_data.profileImage is not None:
        update_data["profileImage"] = profile_data.profileImage
    if profile_data.bio is not None:
        update_data["bio"] = profile_data.bio
    
    if update_data:
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$set": update_data}
        )
        
        # Get updated user
        updated_user = await db.users.find_one({"id": current_user["id"]})
        return UserResponse(**{k: v for k, v in updated_user.items() if k != "password"})
    
    return UserResponse(**{k: v for k, v in current_user.items() if k != "password"})

@api_router.get("/auth/me", response_model=UserResponse)
async def get_current_user_profile(current_user = Depends(get_current_user)):
    return UserResponse(**{k: v for k, v in current_user.items() if k != "password"})


# PHASE 11: Authentication Enhancements
from models.auth_models import *
from utils.email_service import email_service

# PHASE 14: Enhanced Messaging Imports
from models.messaging_models import ConversationSettings, TypingIndicator

@api_router.post("/auth/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """Send password reset verification code via email"""
    user = await db.users.find_one({"email": request.email})
    
    if not user:
        # Return success even if user not found for security
        return {"success": True, "message": "If the email exists, a reset code has been sent"}
    
    # Generate verification code
    verification_code = email_service.generate_verification_code()
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    # Store verification code
    code_data = VerificationCode(
        id=str(uuid.uuid4()),
        email=request.email,
        code=verification_code,
        purpose="password_reset",
        expires_at=expires_at
    )
    
    await db.verification_codes.insert_one(code_data.dict())
    
    # Send email
    success = email_service.send_password_reset_email(
        request.email, 
        verification_code, 
        user.get("fullName", "User")
    )
    
    # Log security event
    audit_log = SecurityAuditLog(
        id=str(uuid.uuid4()),
        user_id=user["id"],
        event_type=SecurityEventType.PASSWORD_RESET_REQUEST,
        metadata={"email": request.email, "success": success}
    )
    await db.security_audit_logs.insert_one(audit_log.dict())
    
    return {"success": True, "message": "If the email exists, a reset code has been sent"}

@api_router.post("/auth/reset-password")
async def reset_password(request: PasswordResetRequest):
    """Reset password using verification code"""
    # Find valid verification code
    code = await db.verification_codes.find_one({
        "email": request.email,
        "code": request.verification_code,
        "purpose": "password_reset",
        "used": False,
        "expires_at": {"$gt": datetime.utcnow()}
    })
    
    if not code:
        raise HTTPException(
            status_code=400, 
            detail="Invalid or expired verification code"
        )
    
    # Validate new password
    if not validate_password(request.new_password):
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters long"
        )
    
    # Find user
    user = await db.users.find_one({"email": request.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update password
    new_password_hash = get_password_hash(request.new_password)
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"password": new_password_hash}}
    )
    
    # Mark verification code as used
    await db.verification_codes.update_one(
        {"id": code["id"]},
        {"$set": {"used": True}}
    )
    
    # Store password history
    password_history = PasswordHistoryEntry(
        id=str(uuid.uuid4()),
        user_id=user["id"],
        password_hash=new_password_hash
    )
    await db.password_history.insert_one(password_history.dict())
    
    # Log security event
    audit_log = SecurityAuditLog(
        id=str(uuid.uuid4()),
        user_id=user["id"],
        event_type=SecurityEventType.PASSWORD_RESET_COMPLETE,
        metadata={"email": request.email}
    )
    await db.security_audit_logs.insert_one(audit_log.dict())
    
    return {"success": True, "message": "Password reset successfully"}

@api_router.post("/auth/change-password")
async def change_password(request: ChangePasswordRequest, current_user = Depends(get_current_user)):
    """Change password with current password confirmation"""
    # Verify current password
    if not verify_password(request.current_password, current_user["password"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Validate new password
    if not validate_password(request.new_password):
        raise HTTPException(
            status_code=400,
            detail="New password must be at least 8 characters long"
        )
    
    # Check if new password is different from current
    if verify_password(request.new_password, current_user["password"]):
        raise HTTPException(
            status_code=400,
            detail="New password must be different from current password"
        )
    
    # Update password
    new_password_hash = get_password_hash(request.new_password)
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": {"password": new_password_hash}}
    )
    
    # Store password history
    password_history = PasswordHistoryEntry(
        id=str(uuid.uuid4()),
        user_id=current_user["id"],
        password_hash=new_password_hash
    )
    await db.password_history.insert_one(password_history.dict())
    
    # Send confirmation email
    email_service.send_password_change_confirmation(
        current_user["email"],
        current_user.get("fullName", "User")
    )
    
    # Log security event
    audit_log = SecurityAuditLog(
        id=str(uuid.uuid4()),
        user_id=current_user["id"],
        event_type=SecurityEventType.PASSWORD_CHANGE,
        metadata={"email": current_user["email"]}
    )
    await db.security_audit_logs.insert_one(audit_log.dict())
    
    return {"success": True, "message": "Password changed successfully"}

@api_router.post("/auth/deactivate-account")
async def deactivate_account(
    request: AccountDeactivationRequest, 
    current_user = Depends(get_current_user)
):
    """Deactivate user account temporarily"""
    if not request.confirm:
        raise HTTPException(status_code=400, detail="Account deactivation must be confirmed")
    
    # Update account status
    now = datetime.utcnow()
    account_status = UserAccountStatus(
        id=str(uuid.uuid4()),
        user_id=current_user["id"],
        status=AccountStatus.DEACTIVATED,
        deactivated_at=now,
        deactivation_reason=request.reason
    )
    
    await db.user_account_status.replace_one(
        {"user_id": current_user["id"]},
        account_status.dict(),
        upsert=True
    )
    
    # Log security event
    audit_log = SecurityAuditLog(
        id=str(uuid.uuid4()),
        user_id=current_user["id"],
        event_type=SecurityEventType.ACCOUNT_DEACTIVATED,
        metadata={"reason": request.reason}
    )
    await db.security_audit_logs.insert_one(audit_log.dict())
    
    return {"success": True, "message": "Account deactivated successfully"}

@api_router.post("/auth/delete-account")
async def delete_account(
    request: AccountDeletionRequest,
    current_user = Depends(get_current_user)
):
    """Schedule account for permanent deletion"""
    if not request.confirm:
        raise HTTPException(status_code=400, detail="Account deletion must be confirmed")
    
    # Verify password
    if not verify_password(request.password, current_user["password"]):
        raise HTTPException(status_code=400, detail="Password is incorrect")
    
    # Schedule deletion (30 days from now)
    now = datetime.utcnow()
    deletion_date = now + timedelta(days=30)
    
    account_status = UserAccountStatus(
        id=str(uuid.uuid4()),
        user_id=current_user["id"],
        status=AccountStatus.DELETED,
        deleted_at=now,
        deletion_scheduled_at=deletion_date
    )
    
    await db.user_account_status.replace_one(
        {"user_id": current_user["id"]},
        account_status.dict(),
        upsert=True
    )
    
    # Send confirmation email
    email_service.send_account_deletion_confirmation(
        current_user["email"],
        current_user.get("fullName", "User"),
        deletion_date
    )
    
    # Log security event
    audit_log = SecurityAuditLog(
        id=str(uuid.uuid4()),
        user_id=current_user["id"],
        event_type=SecurityEventType.ACCOUNT_DELETED,
        metadata={"scheduled_deletion": deletion_date.isoformat()}
    )
    await db.security_audit_logs.insert_one(audit_log.dict())
    
    export_data = None
    if request.export_data:
        # Generate user data export
        user_posts = await db.posts.find({"authorId": current_user["id"]}).to_list(None)
        user_comments = await db.comments.find({"authorId": current_user["id"]}).to_list(None)
        user_stories = await db.stories.find({"authorId": current_user["id"]}).to_list(None)
        
        export_data = {
            "user_profile": {k: v for k, v in current_user.items() if k != "password"},
            "posts": user_posts,
            "comments": user_comments,
            "stories": user_stories,
            "export_date": now.isoformat()
        }
    
    return {
        "success": True,
        "message": f"Account scheduled for deletion on {deletion_date.strftime('%B %d, %Y')}",
        "deletion_date": deletion_date.isoformat(),
        "export_data": export_data
    }

@api_router.get("/auth/security-logs")
async def get_security_logs(
    current_user = Depends(get_current_user),
    skip: int = 0,
    limit: int = 50
):
    """Get user's security audit logs"""
    logs = await db.security_audit_logs.find({
        "user_id": current_user["id"]
    }).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
    
    return logs


# PHASE 12: Profile & Account Management
from models.settings_models import *

# PHASE 15: UI/UX & Accessibility Improvements
from models.settings_models import SupportTicket, FAQ, AppInfo, UserThemeSettings, ReportedContent

class ProfileEditRequest(BaseModel):
    username: Optional[str] = None
    fullName: Optional[str] = None
    bio: Optional[str] = None
    profileImage: Optional[str] = None  # base64
    interests: Optional[List[str]] = None

class PrivacySettings(BaseModel):
    isPrivateAccount: bool = False
    allowDataSharing: bool = True
    enableTwoFactorAuth: bool = False
    showOnlineStatus: bool = True
    allowDirectMessages: str = "everyone"  # "everyone", "followers", "none"
    allowTagging: str = "everyone"  # "everyone", "followers", "none"

@api_router.put("/profile/edit", response_model=UserResponse)
async def edit_profile(request: ProfileEditRequest, current_user = Depends(get_current_user)):
    """Edit user profile information"""
    update_data = {}
    
    # Validate and update username if provided
    if request.username is not None:
        if not validate_username(request.username):
            raise HTTPException(
                status_code=400,
                detail="Username must be 3-20 characters, alphanumeric and underscores only"
            )
        
        # Check if username is already taken
        existing_user = await db.users.find_one({
            "username": request.username.lower(),
            "id": {"$ne": current_user["id"]}
        })
        
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already taken")
        
        update_data["username"] = request.username.lower()
    
    # Update other fields
    if request.fullName is not None:
        update_data["fullName"] = request.fullName
    if request.bio is not None:
        update_data["bio"] = request.bio
    if request.profileImage is not None:
        update_data["profileImage"] = request.profileImage
    if request.interests is not None:
        update_data["interests"] = request.interests
    
    # Update in database
    if update_data:
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$set": update_data}
        )
    
    # Get updated user
    updated_user = await db.users.find_one({"id": current_user["id"]})
    return UserResponse(**{k: v for k, v in updated_user.items() if k != "password"})

@api_router.get("/profile/privacy-settings")
async def get_privacy_settings(current_user = Depends(get_current_user)):
    """Get user's privacy settings"""
    settings = await db.privacy_settings.find_one({"userId": current_user["id"]})
    
    if not settings:
        # Return default settings
        default_settings = PrivacySettings()
        return default_settings.dict()
    
    return settings

@api_router.put("/profile/privacy-settings")
async def update_privacy_settings(
    settings: PrivacySettings, 
    current_user = Depends(get_current_user)
):
    """Update user's privacy settings"""
    settings_data = settings.dict()
    settings_data.update({
        "userId": current_user["id"],
        "updatedAt": datetime.utcnow()
    })
    
    await db.privacy_settings.replace_one(
        {"userId": current_user["id"]},
        settings_data,
        upsert=True
    )
    
    return {"success": True, "message": "Privacy settings updated successfully"}

@api_router.post("/profile/private-account-toggle")
async def toggle_private_account(current_user = Depends(get_current_user)):
    """Toggle private account status"""
    # Get current privacy settings
    privacy_settings = await db.privacy_settings.find_one({"userId": current_user["id"]})
    
    current_status = False
    if privacy_settings:
        current_status = privacy_settings.get("isPrivateAccount", False)
    
    new_status = not current_status
    
    # Update privacy settings
    await db.privacy_settings.update_one(
        {"userId": current_user["id"]},
        {
            "$set": {
                "isPrivateAccount": new_status,
                "updatedAt": datetime.utcnow()
            }
        },
        upsert=True
    )
    
    return {
        "success": True,
        "isPrivateAccount": new_status,
        "message": f"Account is now {'private' if new_status else 'public'}"
    }

class FollowRequestResponse(BaseModel):
    id: str
    requesterId: str
    requester: UserResponse
    targetUserId: str
    status: str
    createdAt: datetime

@api_router.get("/profile/follow-requests", response_model=List[FollowRequestResponse])
async def get_follow_requests(current_user = Depends(get_current_user)):
    """Get pending follow requests for private account"""
    requests = await db.follow_requests.find({
        "targetUserId": current_user["id"],
        "status": "pending"
    }).sort("createdAt", -1).to_list(None)
    
    # Get requester info
    requester_ids = [req["requesterId"] for req in requests]
    requesters = await db.users.find({"id": {"$in": requester_ids}}).to_list(None)
    requesters_map = {user["id"]: user for user in requesters}
    
    result = []
    for request in requests:
        requester_data = requesters_map.get(request["requesterId"])
        if requester_data:
            requester = UserResponse(**{k: v for k, v in requester_data.items() if k != "password"})
            result.append(FollowRequestResponse(
                **request,
                requester=requester
            ))
    
    return result

@api_router.post("/profile/follow-request/{request_id}/approve")
async def approve_follow_request(request_id: str, current_user = Depends(get_current_user)):
    """Approve a follow request"""
    # Find the request
    follow_request = await db.follow_requests.find_one({
        "id": request_id,
        "targetUserId": current_user["id"],
        "status": "pending"
    })
    
    if not follow_request:
        raise HTTPException(status_code=404, detail="Follow request not found")
    
    # Create follow relationship
    follow_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    new_follow = {
        "id": follow_id,
        "followerId": follow_request["requesterId"],
        "followingId": current_user["id"],
        "createdAt": now
    }
    
    await db.follows.insert_one(new_follow)
    
    # Update request status
    await db.follow_requests.update_one(
        {"id": request_id},
        {"$set": {"status": "approved", "updatedAt": now}}
    )
    
    # Create notification
    notification = {
        "id": str(uuid.uuid4()),
        "recipientId": follow_request["requesterId"],
        "senderId": current_user["id"],
        "type": "follow_request_approved",
        "title": "Follow Request Approved",
        "message": f"{current_user['username']} approved your follow request",
        "relatedId": current_user["id"],
        "relatedType": "user",
        "isRead": False,
        "createdAt": now
    }
    
    await db.notifications.insert_one(notification)
    
    return {"success": True, "message": "Follow request approved"}

@api_router.post("/profile/follow-request/{request_id}/deny")
async def deny_follow_request(request_id: str, current_user = Depends(get_current_user)):
    """Deny a follow request"""
    result = await db.follow_requests.update_one(
        {"id": request_id, "targetUserId": current_user["id"], "status": "pending"},
        {"$set": {"status": "denied", "updatedAt": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Follow request not found")
    
    return {"success": True, "message": "Follow request denied"}

class CreatorAccountRequest(BaseModel):
    accountType: str = "creator"  # "creator", "business"
    category: str  # "fitness", "food", "travel", etc.
    description: str
    websiteUrl: Optional[str] = None
    contactEmail: Optional[str] = None

@api_router.post("/profile/creator-verification")
async def request_creator_verification(
    request: CreatorAccountRequest,
    current_user = Depends(get_current_user)
):
    """Request creator account verification"""
    verification_request = {
        "id": str(uuid.uuid4()),
        "userId": current_user["id"],
        "accountType": request.accountType,
        "category": request.category,
        "description": request.description,
        "websiteUrl": request.websiteUrl,
        "contactEmail": request.contactEmail,
        "status": "pending",
        "createdAt": datetime.utcnow(),
        "reviewedAt": None,
        "reviewedBy": None
    }
    
    await db.creator_verification_requests.insert_one(verification_request)
    
    return {
        "success": True,
        "message": "Creator verification request submitted. You'll be notified when reviewed.",
        "requestId": verification_request["id"]
    }

@api_router.get("/profile/creator-status")
async def get_creator_status(current_user = Depends(get_current_user)):
    """Get creator account status"""
    creator_profile = await db.creator_profiles.find_one({"userId": current_user["id"]})
    verification_request = await db.creator_verification_requests.find_one({
        "userId": current_user["id"]
    }, sort=[("createdAt", -1)])
    
    return {
        "isCreator": creator_profile is not None,
        "verificationStatus": verification_request.get("status") if verification_request else None,
        "creatorProfile": creator_profile,
        "lastRequest": verification_request
    }


# Posts Routes
@api_router.post("/posts", response_model=PostResponse)
async def create_post(post_data: PostCreate, current_user = Depends(get_current_user)):
    # Validate media count
    if len(post_data.media) == 0:
        raise HTTPException(status_code=400, detail="At least one media item is required")
    
    if len(post_data.media) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 media items allowed")
    
    # Create post
    post_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    new_post = {
        "id": post_id,
        "authorId": current_user["id"],
        "caption": post_data.caption,
        "media": post_data.media,
        "mediaTypes": post_data.mediaTypes,
        "hashtags": post_data.hashtags or [],
        "taggedUsers": post_data.taggedUsers or [],
        "likes": [],
        "likesCount": 0,
        "commentsCount": 0,
        "createdAt": now,
        "updatedAt": now
    }
    
    await db.posts.insert_one(new_post)
    
    # Get author info for response
    author = UserResponse(**{k: v for k, v in current_user.items() if k != "password"})
    
    return PostResponse(
        **new_post,
        author=author,
        comments=[]  # Will be loaded separately
    )

@api_router.get("/posts/feed", response_model=List[PostResponse])
async def get_feed(current_user = Depends(get_current_user), skip: int = 0, limit: int = 20):
    # Get posts with author info
    posts = await db.posts.find().sort("createdAt", -1).skip(skip).limit(limit).to_list(limit)
    
    # Get all unique author IDs
    author_ids = list(set(post["authorId"] for post in posts))
    
    # Get all authors in one query
    authors = await db.users.find({"id": {"$in": author_ids}}).to_list(len(author_ids))
    authors_map = {author["id"]: author for author in authors}
    
    # Build response
    result = []
    for post in posts:
        author_data = authors_map.get(post["authorId"])
        if author_data:
            author = UserResponse(**{k: v for k, v in author_data.items() if k != "password"})
            result.append(PostResponse(
                **post,
                author=author,
                comments=[]  # Will be loaded separately when needed
            ))
    
    return result

@api_router.post("/posts/{post_id}/like")
async def toggle_post_like(post_id: str, current_user = Depends(get_current_user)):
    post = await db.posts.find_one({"id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    user_id = current_user["id"]
    likes = post.get("likes", [])
    
    if user_id in likes:
        # Unlike
        await db.posts.update_one(
            {"id": post_id},
            {
                "$pull": {"likes": user_id},
                "$inc": {"likesCount": -1}
            }
        )
        liked = False
    else:
        # Like
        await db.posts.update_one(
            {"id": post_id},
            {
                "$addToSet": {"likes": user_id},
                "$inc": {"likesCount": 1}
            }
        )
        liked = True
        
        # Create notification if liking someone else's post
        if post["authorId"] != user_id:
            notification = {
                "id": str(uuid.uuid4()),
                "recipientId": post["authorId"],
                "senderId": current_user["id"],
                "type": "like",
                "title": "Post Liked",
                "message": f"{current_user['username']} liked your post",
                "relatedId": post_id,
                "relatedType": "post",
                "isRead": False,
                "createdAt": datetime.utcnow()
            }
            await db.notifications.insert_one(notification)
    
    return {"liked": liked, "likesCount": post.get("likesCount", 0) + (1 if liked else -1)}

@api_router.post("/posts/{post_id}/comments", response_model=CommentResponse)
async def create_comment(post_id: str, comment_data: CommentCreate, current_user = Depends(get_current_user)):
    post = await db.posts.find_one({"id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Create comment
    comment_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    new_comment = {
        "id": comment_id,
        "postId": post_id,
        "authorId": current_user["id"],
        "text": comment_data.text,
        "likes": [],
        "likesCount": 0,
        "createdAt": now
    }
    
    await db.comments.insert_one(new_comment)
    
    # Update post comments count
    await db.posts.update_one(
        {"id": post_id},
        {"$inc": {"commentsCount": 1}}
    )
    
    # Get author info for response
    author = UserResponse(**{k: v for k, v in current_user.items() if k != "password"})
    
    return CommentResponse(**new_comment, author=author)

@api_router.get("/posts/{post_id}/comments", response_model=List[CommentResponse])
async def get_post_comments(post_id: str, current_user = Depends(get_current_user), skip: int = 0, limit: int = 50):
    # Get comments with author info
    comments = await db.comments.find({"postId": post_id}).sort("createdAt", 1).skip(skip).limit(limit).to_list(limit)
    
    # Get all unique author IDs
    author_ids = list(set(comment["authorId"] for comment in comments))
    
    # Get all authors in one query
    authors = await db.users.find({"id": {"$in": author_ids}}).to_list(len(author_ids))
    authors_map = {author["id"]: author for author in authors}
    
    # Build response
    result = []
    for comment in comments:
        author_data = authors_map.get(comment["authorId"])
        if author_data:
            author = UserResponse(**{k: v for k, v in author_data.items() if k != "password"})
            result.append(CommentResponse(**comment, author=author))
    
    return result

@api_router.post("/comments/{comment_id}/like")
async def toggle_comment_like(comment_id: str, current_user = Depends(get_current_user)):
    comment = await db.comments.find_one({"id": comment_id})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    user_id = current_user["id"]
    likes = comment.get("likes", [])
    
    if user_id in likes:
        # Unlike
        await db.comments.update_one(
            {"id": comment_id},
            {
                "$pull": {"likes": user_id},
                "$inc": {"likesCount": -1}
            }
        )
        liked = False
    else:
        # Like
        await db.comments.update_one(
            {"id": comment_id},
            {
                "$addToSet": {"likes": user_id},
                "$inc": {"likesCount": 1}
            }
        )
        liked = True
        
        # Create notification if liking someone else's comment
        if comment["authorId"] != user_id:
            notification = {
                "id": str(uuid.uuid4()),
                "recipientId": comment["authorId"],
                "senderId": current_user["id"],
                "type": "like",
                "title": "Comment Liked",
                "message": f"{current_user['username']} liked your comment",
                "relatedId": comment_id,
                "relatedType": "comment",
                "isRead": False,
                "createdAt": datetime.utcnow()
            }
            await db.notifications.insert_one(notification)
    
    return {"liked": liked, "likesCount": comment.get("likesCount", 0) + (1 if liked else -1)}


# Chat Routes
@api_router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(conversation_data: ConversationCreate, current_user = Depends(get_current_user)):
    # Validate participants
    if current_user["id"] not in conversation_data.participantIds:
        conversation_data.participantIds.append(current_user["id"])
    
    # Check if conversation already exists between these users (for non-group chats)
    if not conversation_data.isGroup and len(conversation_data.participantIds) == 2:
        existing = await db.conversations.find_one({
            "participantIds": {"$all": conversation_data.participantIds, "$size": 2},
            "isGroup": False
        })
        if existing:
            # Return existing conversation
            participants = await db.users.find({"id": {"$in": existing["participantIds"]}}).to_list(len(existing["participantIds"]))
            participants_response = [UserResponse(**{k: v for k, v in p.items() if k != "password"}) for p in participants]
            
            return ConversationResponse(
                **existing,
                participants=participants_response,
                lastMessage=None,
                unreadCount=0
            )
    
    # Create new conversation
    conversation_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    new_conversation = {
        "id": conversation_id,
        "participantIds": conversation_data.participantIds,
        "isGroup": conversation_data.isGroup,
        "name": conversation_data.name,
        "description": conversation_data.description,
        "createdAt": now,
        "updatedAt": now
    }
    
    await db.conversations.insert_one(new_conversation)
    
    # Get participants info
    participants = await db.users.find({"id": {"$in": conversation_data.participantIds}}).to_list(len(conversation_data.participantIds))
    participants_response = [UserResponse(**{k: v for k, v in p.items() if k != "password"}) for p in participants]
    
    return ConversationResponse(
        **new_conversation,
        participants=participants_response,
        lastMessage=None,
        unreadCount=0
    )

@api_router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(current_user = Depends(get_current_user), skip: int = 0, limit: int = 50):
    # Get user's conversations
    conversations = await db.conversations.find({
        "participantIds": current_user["id"]
    }).sort("updatedAt", -1).skip(skip).limit(limit).to_list(limit)
    
    result = []
    for conv in conversations:
        # Get participants
        participants = await db.users.find({"id": {"$in": conv["participantIds"]}}).to_list(len(conv["participantIds"]))
        participants_response = [UserResponse(**{k: v for k, v in p.items() if k != "password"}) for p in participants]
        
        # Get last message
        last_message = await db.messages.find_one(
            {"conversationId": conv["id"]},
            sort=[("createdAt", -1)]
        )
        
        last_message_response = None
        if last_message:
            sender = await db.users.find_one({"id": last_message["senderId"]})
            if sender:
                sender_response = UserResponse(**{k: v for k, v in sender.items() if k != "password"})
                last_message_response = MessageResponse(**last_message, sender=sender_response)
        
        # Calculate unread count
        unread_count = await db.messages.count_documents({
            "conversationId": conv["id"],
            "senderId": {"$ne": current_user["id"]},
            "readBy.userId": {"$ne": current_user["id"]}
        })
        
        result.append(ConversationResponse(
            **conv,
            participants=participants_response,
            lastMessage=last_message_response,
            unreadCount=unread_count
        ))
    
    return result

@api_router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(conversation_id: str, message_data: MessageCreate, current_user = Depends(get_current_user)):
    # Validate conversation exists and user is participant
    conversation = await db.conversations.find_one({
        "id": conversation_id,
        "participantIds": current_user["id"]
    })
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found or access denied")
    
    # Create message
    message_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    new_message = {
        "id": message_id,
        "conversationId": conversation_id,
        "senderId": current_user["id"],
        "text": message_data.text,
        "messageType": message_data.messageType,
        "media": message_data.media,
        "replyTo": message_data.replyTo,
        "readBy": [{
            "userId": current_user["id"],
            "readAt": now
        }],
        "createdAt": now,
        "updatedAt": now
    }
    
    await db.messages.insert_one(new_message)
    
    # Update conversation's last activity
    await db.conversations.update_one(
        {"id": conversation_id},
        {"$set": {"updatedAt": now}}
    )
    
    # Get sender info for response
    sender = UserResponse(**{k: v for k, v in current_user.items() if k != "password"})
    
    message_response = MessageResponse(**new_message, sender=sender)
    
    # Emit real-time message via Socket.IO
    await sio.emit('new_message', {
        'conversationId': conversation_id,
        'message': message_response.dict()
    }, room=f"conversation_{conversation_id}")
    
    return message_response

@api_router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(conversation_id: str, current_user = Depends(get_current_user), skip: int = 0, limit: int = 50):
    # Validate conversation access
    conversation = await db.conversations.find_one({
        "id": conversation_id,
        "participantIds": current_user["id"]
    })
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found or access denied")
    
    # Get messages
    messages = await db.messages.find({
        "conversationId": conversation_id
    }).sort("createdAt", -1).skip(skip).limit(limit).to_list(limit)
    
    # Get all unique sender IDs
    sender_ids = list(set(msg["senderId"] for msg in messages))
    
    # Get all senders in one query
    senders = await db.users.find({"id": {"$in": sender_ids}}).to_list(len(sender_ids))
    senders_map = {sender["id"]: sender for sender in senders}
    
    # Build response
    result = []
    for message in reversed(messages):  # Reverse to show oldest first
        sender_data = senders_map.get(message["senderId"])
        if sender_data:
            sender = UserResponse(**{k: v for k, v in sender_data.items() if k != "password"})
            result.append(MessageResponse(**message, sender=sender))
    
    return result


# PHASE 14: Enhanced Messaging & Real-time Features

@api_router.get("/conversations/filters", response_model=List[ConversationResponse])
async def get_filtered_conversations(
    filter_type: str = "all",  # "all", "unread", "groups", "direct", "archived", "muted"
    search_query: str = None,
    current_user = Depends(get_current_user),
    skip: int = 0,
    limit: int = 50
):
    """Get conversations with advanced filters"""
    # Build filter query
    base_filter = {"participantIds": current_user["id"]}
    
    if filter_type == "groups":
        base_filter["isGroup"] = True
    elif filter_type == "direct":
        base_filter["isGroup"] = False
    elif filter_type == "archived":
        base_filter["isArchived"] = True
    elif filter_type == "muted":
        base_filter["isMuted"] = True
    
    # For unread, we'll filter after getting conversations
    conversations = await db.conversations.find(base_filter).sort("updatedAt", -1).skip(skip).limit(limit).to_list(limit)
    
    # Apply search filter
    if search_query:
        # Search in conversation names and participant names
        participant_ids = []
        for conv in conversations:
            participant_ids.extend(conv["participantIds"])
        
        matching_users = await db.users.find({
            "$or": [
                {"fullName": {"$regex": search_query, "$options": "i"}},
                {"username": {"$regex": search_query, "$options": "i"}}
            ]
        }).to_list(None)
        
        matching_user_ids = [user["id"] for user in matching_users]
        conversations = [conv for conv in conversations if 
                        (conv.get("name") and search_query.lower() in conv["name"].lower()) or
                        any(pid in matching_user_ids for pid in conv["participantIds"])]
    
    result = []
    for conv in conversations:
        # Get participants
        participants = await db.users.find({"id": {"$in": conv["participantIds"]}}).to_list(len(conv["participantIds"]))
        participants_response = [UserResponse(**{k: v for k, v in p.items() if k != "password"}) for p in participants]
        
        # Get last message
        last_message = await db.messages.find_one(
            {"conversationId": conv["id"]},
            sort=[("createdAt", -1)]
        )
        
        last_message_response = None
        if last_message:
            sender = await db.users.find_one({"id": last_message["senderId"]})
            if sender:
                sender_response = UserResponse(**{k: v for k, v in sender.items() if k != "password"})
                last_message_response = MessageResponse(**last_message, sender=sender_response)
        
        # Calculate unread count
        unread_count = await db.messages.count_documents({
            "conversationId": conv["id"],
            "senderId": {"$ne": current_user["id"]},
            "readBy.userId": {"$ne": current_user["id"]}
        })
        
        # Apply unread filter
        if filter_type == "unread" and unread_count == 0:
            continue
        
        result.append(ConversationResponse(
            **conv,
            participants=participants_response,
            lastMessage=last_message_response,
            unreadCount=unread_count
        ))
    
    return result

@api_router.put("/conversations/{conversation_id}/settings")
async def update_conversation_settings(
    conversation_id: str,
    settings: ConversationSettings,
    current_user = Depends(get_current_user)
):
    """Update conversation settings (archive, mute, etc.)"""
    # Verify user is participant
    conversation = await db.conversations.find_one({
        "id": conversation_id,
        "participantIds": current_user["id"]
    })
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Update conversation settings
    update_data = {
        "isArchived": settings.isArchived,
        "isMuted": settings.isMuted,
        "updatedAt": datetime.utcnow()
    }
    
    if settings.muteUntil:
        update_data["muteUntil"] = settings.muteUntil
    
    await db.conversations.update_one(
        {"id": conversation_id},
        {"$set": update_data}
    )
    
    return {"success": True, "message": "Conversation settings updated"}

@api_router.post("/conversations/{conversation_id}/typing")
async def send_typing_indicator(
    conversation_id: str,
    typing_data: TypingIndicator,
    current_user = Depends(get_current_user)
):
    """Send typing indicator to conversation participants"""
    # Verify user is participant
    conversation = await db.conversations.find_one({
        "id": conversation_id,
        "participantIds": current_user["id"]
    })
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Emit typing indicator via Socket.IO
    await sio.emit('user_typing', {
        'conversationId': conversation_id,
        'userId': current_user["id"],
        'username': current_user["username"],
        'isTyping': typing_data.isTyping
    }, room=f"conversation_{conversation_id}")
    
    return {"success": True}

@api_router.put("/messages/{message_id}/read")
async def mark_message_read(
    message_id: str,
    current_user = Depends(get_current_user)
):
    """Mark a specific message as read"""
    message = await db.messages.find_one({"id": message_id})
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Check if user is participant
    conversation = await db.conversations.find_one({
        "id": message["conversationId"],
        "participantIds": current_user["id"]
    })
    
    if not conversation:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update read status
    await db.messages.update_one(
        {"id": message_id},
        {
            "$addToSet": {
                "readBy": {
                    "userId": current_user["id"],
                    "readAt": datetime.utcnow()
                }
            }
        }
    )
    
    # Emit read receipt
    await sio.emit('message_read', {
        'messageId': message_id,
        'conversationId': message["conversationId"],
        'userId': current_user["id"]
    }, room=f"conversation_{message['conversationId']}")
    
    return {"success": True}

@api_router.put("/conversations/{conversation_id}/read-all")
async def mark_all_messages_read(
    conversation_id: str,
    current_user = Depends(get_current_user)
):
    """Mark all messages in a conversation as read"""
    # Verify user is participant
    conversation = await db.conversations.find_one({
        "id": conversation_id,
        "participantIds": current_user["id"]
    })
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get all unread messages
    unread_messages = await db.messages.find({
        "conversationId": conversation_id,
        "senderId": {"$ne": current_user["id"]},
        "readBy.userId": {"$ne": current_user["id"]}
    }).to_list(None)
    
    # Mark all as read
    for message in unread_messages:
        await db.messages.update_one(
            {"id": message["id"]},
            {
                "$addToSet": {
                    "readBy": {
                        "userId": current_user["id"],
                        "readAt": datetime.utcnow()
                    }
                }
            }
        )
    
    # Emit batch read receipt
    if unread_messages:
        message_ids = [msg["id"] for msg in unread_messages]
        await sio.emit('messages_read_batch', {
            'messageIds': message_ids,
            'conversationId': conversation_id,
            'userId': current_user["id"]
        }, room=f"conversation_{conversation_id}")
    
    return {"success": True, "messagesRead": len(unread_messages)}

@api_router.get("/users/{user_id}/activity")
async def get_user_activity(user_id: str, current_user = Depends(get_current_user)):
    """Get user's online status and activity"""
    # Check if users are connected (followers, mutual follows, or in same conversation)
    # For now, allowing all users to see activity status
    
    activity = await db.user_activities.find_one({"userId": user_id})
    
    if not activity:
        # Return default offline status
        return {
            "userId": user_id,
            "status": "offline",
            "lastSeen": datetime.utcnow() - timedelta(hours=1),
            "isOnline": False
        }
    
    return {
        "userId": user_id,
        "status": activity.get("status", "offline"),
        "lastSeen": activity.get("lastSeen"),
        "isOnline": activity.get("status") == "online"
    }

@api_router.put("/user/activity")
async def update_user_activity(
    status: str,  # "online", "offline", "away", "busy"
    current_user = Depends(get_current_user)
):
    """Update current user's activity status"""
    now = datetime.utcnow()
    
    activity_data = {
        "userId": current_user["id"],
        "status": status,
        "lastSeen": now,
        "updatedAt": now
    }
    
    await db.user_activities.replace_one(
        {"userId": current_user["id"]},
        activity_data,
        upsert=True
    )
    
    # Broadcast status to relevant conversations
    # Get user's conversations
    conversations = await db.conversations.find({
        "participantIds": current_user["id"]
    }).to_list(None)
    
    for conv in conversations:
        await sio.emit('user_status_change', {
            'userId': current_user["id"],
            'status': status,
            'lastSeen': now.isoformat()
        }, room=f"conversation_{conv['id']}")
    
    return {"success": True, "status": status}

@api_router.post("/messages/queue")
async def queue_offline_message(
    message_data: MessageCreate,
    current_user = Depends(get_current_user)
):
    """Queue message for offline sending"""
    # Create message queue entry
    queue_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    queue_entry = {
        "id": queue_id,
        "userId": current_user["id"],
        "conversationId": message_data.conversationId,
        "messageData": message_data.dict(),
        "retryCount": 0,
        "maxRetries": 3,
        "nextRetryAt": now + timedelta(seconds=30),
        "createdAt": now,
        "status": "pending"
    }
    
    await db.message_queue.insert_one(queue_entry)
    
    return {"success": True, "queueId": queue_id}

@api_router.post("/messages/sync")
async def sync_offline_messages(current_user = Depends(get_current_user)):
    """Sync and send queued messages when back online"""
    # Get pending messages for user
    pending_messages = await db.message_queue.find({
        "userId": current_user["id"],
        "status": "pending"
    }).to_list(None)
    
    sent_count = 0
    failed_count = 0
    
    for queue_entry in pending_messages:
        try:
            # Extract message data
            message_data = MessageCreate(**queue_entry["messageData"])
            
            # Send the message (reuse existing send_message logic)
            message_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            new_message = {
                "id": message_id,
                "conversationId": message_data.conversationId,
                "senderId": current_user["id"],
                "text": message_data.text,
                "messageType": message_data.messageType,
                "media": message_data.media,
                "replyTo": message_data.replyTo,
                "readBy": [{
                    "userId": current_user["id"],
                    "readAt": now
                }],
                "createdAt": now,
                "updatedAt": now
            }
            
            await db.messages.insert_one(new_message)
            
            # Update conversation
            await db.conversations.update_one(
                {"id": message_data.conversationId},
                {"$set": {"updatedAt": now}}
            )
            
            # Mark queue entry as sent
            await db.message_queue.update_one(
                {"id": queue_entry["id"]},
                {"$set": {"status": "sent", "sentAt": now}}
            )
            
            # Emit real-time message
            sender = UserResponse(**{k: v for k, v in current_user.items() if k != "password"})
            message_response = MessageResponse(**new_message, sender=sender)
            
            await sio.emit('new_message', {
                'conversationId': message_data.conversationId,
                'message': message_response.dict()
            }, room=f"conversation_{message_data.conversationId}")
            
            sent_count += 1
            
        except Exception as e:
            # Increment retry count
            retry_count = queue_entry["retryCount"] + 1
            next_retry = datetime.utcnow() + timedelta(seconds=30 * retry_count)
            
            if retry_count >= queue_entry["maxRetries"]:
                # Mark as failed
                await db.message_queue.update_one(
                    {"id": queue_entry["id"]},
                    {"$set": {"status": "failed", "error": str(e)}}
                )
                failed_count += 1
            else:
                # Schedule retry
                await db.message_queue.update_one(
                    {"id": queue_entry["id"]},
                    {
                        "$set": {
                            "retryCount": retry_count,
                            "nextRetryAt": next_retry,
                            "lastError": str(e)
                        }
                    }
                )
    
    return {
        "success": True,
        "sentCount": sent_count,
        "failedCount": failed_count,
        "totalProcessed": len(pending_messages)
    }


# Stories Routes
@api_router.post("/stories", response_model=StoryResponse)
async def create_story(story_data: StoryCreate, current_user = Depends(get_current_user)):
    # Calculate expiry time
    expire_hours = story_data.duration or 24
    expires_at = datetime.utcnow() + timedelta(hours=expire_hours)
    
    # Create story
    story_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    new_story = {
        "id": story_id,
        "authorId": current_user["id"],
        "media": story_data.media,
        "mediaType": story_data.mediaType,
        "text": story_data.text,
        "textPosition": story_data.textPosition,
        "textStyle": story_data.textStyle,
        "duration": expire_hours,
        "viewers": [],
        "viewersCount": 0,
        "createdAt": now,
        "expiresAt": expires_at
    }
    
    await db.stories.insert_one(new_story)
    
    # Get author info for response
    author = UserResponse(**{k: v for k, v in current_user.items() if k != "password"})
    
    return StoryResponse(**new_story, author=author)

@api_router.get("/stories/feed", response_model=List[StoryResponse])
async def get_stories_feed(current_user = Depends(get_current_user), skip: int = 0, limit: int = 50):
    # Get active stories (not expired)
    now = datetime.utcnow()
    stories = await db.stories.find({
        "expiresAt": {"$gt": now}
    }).sort("createdAt", -1).skip(skip).limit(limit).to_list(limit)
    
    # Get all unique author IDs
    author_ids = list(set(story["authorId"] for story in stories))
    
    # Get all authors in one query
    authors = await db.users.find({"id": {"$in": author_ids}}).to_list(len(author_ids))
    authors_map = {author["id"]: author for author in authors}
    
    # Build response
    result = []
    for story in stories:
        author_data = authors_map.get(story["authorId"])
        if author_data:
            author = UserResponse(**{k: v for k, v in author_data.items() if k != "password"})
            result.append(StoryResponse(**story, author=author))
    
    return result

@api_router.post("/stories/{story_id}/view")
async def view_story(story_id: str, current_user = Depends(get_current_user)):
    # Check if story exists and is not expired
    now = datetime.utcnow()
    story = await db.stories.find_one({
        "id": story_id,
        "expiresAt": {"$gt": now}
    })
    
    if not story:
        raise HTTPException(status_code=404, detail="Story not found or expired")
    
    # Add viewer if not already viewed
    if current_user["id"] not in story.get("viewers", []):
        await db.stories.update_one(
            {"id": story_id},
            {
                "$addToSet": {"viewers": current_user["id"]},
                "$inc": {"viewersCount": 1}
            }
        )
    
    return {"viewed": True}

@api_router.delete("/stories/{story_id}")
async def delete_story(story_id: str, current_user = Depends(get_current_user)):
    # Check if story exists and belongs to user
    story = await db.stories.find_one({
        "id": story_id,
        "authorId": current_user["id"]
    })
    
    if not story:
        raise HTTPException(status_code=404, detail="Story not found or access denied")
    
    await db.stories.delete_one({"id": story_id})
    return {"deleted": True}


# Engagement Routes - Follow/Unfollow
@api_router.post("/users/{user_id}/follow")
async def follow_user(user_id: str, current_user = Depends(get_current_user)):
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")
    
    # Check if target user exists
    target_user = await db.users.find_one({"id": user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already following
    existing_follow = await db.follows.find_one({
        "followerId": current_user["id"],
        "followingId": user_id
    })
    
    if existing_follow:
        raise HTTPException(status_code=400, detail="Already following this user")
    
    # Create follow relationship
    follow_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    new_follow = {
        "id": follow_id,
        "followerId": current_user["id"],
        "followingId": user_id,
        "createdAt": now
    }
    
    await db.follows.insert_one(new_follow)
    
    # Create notification
    notification = {
        "id": str(uuid.uuid4()),
        "recipientId": user_id,
        "senderId": current_user["id"],
        "type": "follow",
        "title": "New Follower",
        "message": f"{current_user['username']} started following you",
        "relatedId": current_user["id"],
        "relatedType": "user",
        "isRead": False,
        "createdAt": now
    }
    
    await db.notifications.insert_one(notification)
    
    return {"followed": True}

@api_router.delete("/users/{user_id}/follow")
async def unfollow_user(user_id: str, current_user = Depends(get_current_user)):
    result = await db.follows.delete_one({
        "followerId": current_user["id"],
        "followingId": user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Follow relationship not found")
    
    return {"unfollowed": True}

@api_router.get("/users/{user_id}/followers", response_model=List[UserResponse])
async def get_user_followers(user_id: str, current_user = Depends(get_current_user), skip: int = 0, limit: int = 50):
    # Get follower IDs
    follows = await db.follows.find({"followingId": user_id}).skip(skip).limit(limit).to_list(limit)
    follower_ids = [follow["followerId"] for follow in follows]
    
    if not follower_ids:
        return []
    
    # Get follower users
    followers = await db.users.find({"id": {"$in": follower_ids}}).to_list(len(follower_ids))
    return [UserResponse(**{k: v for k, v in user.items() if k != "password"}) for user in followers]

@api_router.get("/users/{user_id}/following", response_model=List[UserResponse])
async def get_user_following(user_id: str, current_user = Depends(get_current_user), skip: int = 0, limit: int = 50):
    # Get following IDs
    follows = await db.follows.find({"followerId": user_id}).skip(skip).limit(limit).to_list(limit)
    following_ids = [follow["followingId"] for follow in follows]
    
    if not following_ids:
        return []
    
    # Get following users
    following = await db.users.find({"id": {"$in": following_ids}}).to_list(len(following_ids))
    return [UserResponse(**{k: v for k, v in user.items() if k != "password"}) for user in following]


# Notifications Routes
@api_router.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications(current_user = Depends(get_current_user), skip: int = 0, limit: int = 50):
    notifications = await db.notifications.find({
        "recipientId": current_user["id"]
    }).sort("createdAt", -1).skip(skip).limit(limit).to_list(limit)
    
    # Get all unique sender IDs
    sender_ids = list(set(notification.get("senderId") for notification in notifications if notification.get("senderId")))
    
    # Get all senders in one query
    senders = await db.users.find({"id": {"$in": sender_ids}}).to_list(len(sender_ids)) if sender_ids else []
    senders_map = {sender["id"]: sender for sender in senders}
    
    # Build response
    result = []
    for notification in notifications:
        sender_data = None
        if notification.get("senderId"):
            sender_data = senders_map.get(notification["senderId"])
            sender = UserResponse(**{k: v for k, v in sender_data.items() if k != "password"}) if sender_data else None
        else:
            sender = None
        
        result.append(NotificationResponse(**notification, sender=sender))
    
    return result

@api_router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user = Depends(get_current_user)):
    result = await db.notifications.update_one(
        {"id": notification_id, "recipientId": current_user["id"]},
        {"$set": {"isRead": True}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"read": True}

@api_router.put("/notifications/read-all")
async def mark_all_notifications_read(current_user = Depends(get_current_user)):
    await db.notifications.update_many(
        {"recipientId": current_user["id"], "isRead": False},
        {"$set": {"isRead": True}}
    )
    
    return {"allRead": True}


# PHASE 13: Engagement & Interactions

class CommentCreate(BaseModel):
    content: str
    parentId: Optional[str] = None  # For threaded replies

class CommentUpdate(BaseModel):
    content: str

class CommentReport(BaseModel):
    reason: str
    details: Optional[str] = None

class CommentResponse(BaseModel):
    id: str
    postId: str
    authorId: str
    author: UserResponse
    content: str
    parentId: Optional[str]
    replies: List['CommentResponse'] = []
    likesCount: int = 0
    isLiked: bool = False
    createdAt: datetime
    updatedAt: Optional[datetime] = None

@api_router.get("/user/liked-posts", response_model=List[PostResponse])
async def get_liked_posts(
    current_user = Depends(get_current_user),
    skip: int = 0,
    limit: int = 20
):
    """Get all posts liked by current user with infinite scroll"""
    liked_posts = await db.posts.find({
        "likes": current_user["id"]
    }).sort("createdAt", -1).skip(skip).limit(limit).to_list(limit)
    
    # Get authors
    author_ids = list(set(post["authorId"] for post in liked_posts))
    authors = await db.users.find({"id": {"$in": author_ids}}).to_list(len(author_ids)) if author_ids else []
    authors_map = {author["id"]: author for author in authors}
    
    result = []
    for post in liked_posts:
        author_data = authors_map.get(post["authorId"])
        if author_data:
            author = UserResponse(**{k: v for k, v in author_data.items() if k != "password"})
            result.append(PostResponse(**post, author=author, comments=[]))
    
    return result

@api_router.delete("/posts/{post_id}/unlike")
async def unlike_post(post_id: str, current_user = Depends(get_current_user)):
    """Remove like from a post"""
    post = await db.posts.find_one({"id": post_id})
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Remove like
    await db.posts.update_one(
        {"id": post_id},
        {
            "$pull": {"likes": current_user["id"]},
            "$inc": {"likesCount": -1}
        }
    )
    
    # Remove notification
    await db.notifications.delete_one({
        "senderId": current_user["id"],
        "relatedId": post_id,
        "type": "like"
    })
    
    return {"success": True, "message": "Post unliked"}

@api_router.get("/posts/{post_id}/comments", response_model=List[CommentResponse])
async def get_post_comments(
    post_id: str,
    current_user = Depends(get_current_user),
    skip: int = 0,
    limit: int = 50
):
    """Get comments for a post with threaded replies"""
    # Get top-level comments
    comments = await db.comments.find({
        "postId": post_id,
        "parentId": {"$exists": False}
    }).sort("createdAt", -1).skip(skip).limit(limit).to_list(limit)
    
    if not comments:
        return []
    
    comment_ids = [comment["id"] for comment in comments]
    
    # Get replies for these comments
    replies = await db.comments.find({
        "parentId": {"$in": comment_ids}
    }).sort("createdAt", 1).to_list(None)
    
    # Group replies by parent
    replies_map = {}
    for reply in replies:
        parent_id = reply["parentId"]
        if parent_id not in replies_map:
            replies_map[parent_id] = []
        replies_map[parent_id].append(reply)
    
    # Get all authors
    all_comment_ids = comment_ids + [reply["id"] for reply in replies]
    author_ids = list(set(comment["authorId"] for comment in comments + replies))
    authors = await db.users.find({"id": {"$in": author_ids}}).to_list(len(author_ids)) if author_ids else []
    authors_map = {author["id"]: author for author in authors}
    
    # Get comment likes
    comment_likes = await db.comment_likes.find({
        "commentId": {"$in": all_comment_ids}
    }).to_list(None)
    likes_map = {}
    for like in comment_likes:
        comment_id = like["commentId"]
        if comment_id not in likes_map:
            likes_map[comment_id] = []
        likes_map[comment_id].append(like["userId"])
    
    # Build response
    result = []
    for comment in comments:
        author_data = authors_map.get(comment["authorId"])
        if author_data:
            author = UserResponse(**{k: v for k, v in author_data.items() if k != "password"})
            
            # Build replies
            comment_replies = []
            for reply in replies_map.get(comment["id"], []):
                reply_author_data = authors_map.get(reply["authorId"])
                if reply_author_data:
                    reply_author = UserResponse(**{k: v for k, v in reply_author_data.items() if k != "password"})
                    reply_likes = likes_map.get(reply["id"], [])
                    comment_replies.append(CommentResponse(
                        **reply,
                        author=reply_author,
                        likesCount=len(reply_likes),
                        isLiked=current_user["id"] in reply_likes,
                        replies=[]
                    ))
            
            comment_likes_list = likes_map.get(comment["id"], [])
            result.append(CommentResponse(
                **comment,
                author=author,
                replies=comment_replies,
                likesCount=len(comment_likes_list),
                isLiked=current_user["id"] in comment_likes_list
            ))
    
    return result

@api_router.post("/posts/{post_id}/comments")
async def create_comment(
    post_id: str,
    comment_data: CommentCreate,
    current_user = Depends(get_current_user)
):
    """Create a new comment or reply"""
    # Verify post exists
    post = await db.posts.find_one({"id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # If it's a reply, verify parent comment exists
    if comment_data.parentId:
        parent_comment = await db.comments.find_one({"id": comment_data.parentId})
        if not parent_comment:
            raise HTTPException(status_code=404, detail="Parent comment not found")
    
    # Create comment
    comment_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    new_comment = {
        "id": comment_id,
        "postId": post_id,
        "authorId": current_user["id"],
        "content": comment_data.content,
        "parentId": comment_data.parentId,
        "createdAt": now
    }
    
    await db.comments.insert_one(new_comment)
    
    # Create notification for post author (if not commenting on own post)
    if post["authorId"] != current_user["id"]:
        notification = {
            "id": str(uuid.uuid4()),
            "recipientId": post["authorId"],
            "senderId": current_user["id"],
            "type": "comment",
            "title": "New Comment",
            "message": f"{current_user['username']} commented on your post",
            "relatedId": post_id,
            "relatedType": "post",
            "isRead": False,
            "createdAt": now
        }
        
        await db.notifications.insert_one(notification)
        
        # Real-time notification via Socket.IO
        await sio.emit('new_notification', notification, room=f"user_{post['authorId']}")
    
    return {"success": True, "commentId": comment_id, "message": "Comment created"}

@api_router.put("/comments/{comment_id}")
async def edit_comment(
    comment_id: str,
    comment_data: CommentUpdate,
    current_user = Depends(get_current_user)
):
    """Edit a comment"""
    comment = await db.comments.find_one({
        "id": comment_id,
        "authorId": current_user["id"]
    })
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found or access denied")
    
    await db.comments.update_one(
        {"id": comment_id},
        {
            "$set": {
                "content": comment_data.content,
                "updatedAt": datetime.utcnow()
            }
        }
    )
    
    return {"success": True, "message": "Comment updated"}

@api_router.delete("/comments/{comment_id}")
async def delete_comment(comment_id: str, current_user = Depends(get_current_user)):
    """Delete a comment"""
    comment = await db.comments.find_one({
        "id": comment_id,
        "authorId": current_user["id"]
    })
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found or access denied")
    
    # Delete comment and its replies
    await db.comments.delete_many({
        "$or": [
            {"id": comment_id},
            {"parentId": comment_id}
        ]
    })
    
    # Delete comment likes
    await db.comment_likes.delete_many({
        "commentId": {"$in": [comment_id]}
    })
    
    return {"success": True, "message": "Comment deleted"}

@api_router.post("/comments/{comment_id}/like")
async def like_comment(comment_id: str, current_user = Depends(get_current_user)):
    """Like a comment"""
    comment = await db.comments.find_one({"id": comment_id})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check if already liked
    existing_like = await db.comment_likes.find_one({
        "commentId": comment_id,
        "userId": current_user["id"]
    })
    
    if existing_like:
        raise HTTPException(status_code=400, detail="Comment already liked")
    
    # Add like
    like_id = str(uuid.uuid4())
    new_like = {
        "id": like_id,
        "commentId": comment_id,
        "userId": current_user["id"],
        "createdAt": datetime.utcnow()
    }
    
    await db.comment_likes.insert_one(new_like)
    
    return {"success": True, "message": "Comment liked"}

@api_router.delete("/comments/{comment_id}/like")
async def unlike_comment(comment_id: str, current_user = Depends(get_current_user)):
    """Remove like from comment"""
    result = await db.comment_likes.delete_one({
        "commentId": comment_id,
        "userId": current_user["id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Like not found")
    
    return {"success": True, "message": "Comment unliked"}

@api_router.post("/comments/{comment_id}/report")
async def report_comment(
    comment_id: str,
    report_data: CommentReport,
    current_user = Depends(get_current_user)
):
    """Report a comment"""
    comment = await db.comments.find_one({"id": comment_id})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Create report
    report_id = str(uuid.uuid4())
    report = {
        "id": report_id,
        "commentId": comment_id,
        "reportedBy": current_user["id"],
        "reason": report_data.reason,
        "details": report_data.details,
        "status": "pending",
        "createdAt": datetime.utcnow()
    }
    
    await db.comment_reports.insert_one(report)
    
    return {"success": True, "message": "Comment reported successfully"}

@api_router.get("/user/followers-list", response_model=List[UserResponse])
async def get_followers_list(
    current_user = Depends(get_current_user),
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
):
    """Get followers list with search and pagination"""
    # Get follower IDs
    follows = await db.follows.find({"followingId": current_user["id"]}).skip(skip).limit(limit).to_list(limit)
    follower_ids = [follow["followerId"] for follow in follows]
    
    if not follower_ids:
        return []
    
    # Build search query
    query = {"id": {"$in": follower_ids}}
    if search:
        query["$or"] = [
            {"username": {"$regex": search, "$options": "i"}},
            {"fullName": {"$regex": search, "$options": "i"}}
        ]
    
    # Get followers
    followers = await db.users.find(query).to_list(len(follower_ids))
    return [UserResponse(**{k: v for k, v in user.items() if k != "password"}) for user in followers]

@api_router.get("/user/following-list", response_model=List[UserResponse])
async def get_following_list(
    current_user = Depends(get_current_user),
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
):
    """Get following list with search and pagination"""
    # Get following IDs
    follows = await db.follows.find({"followerId": current_user["id"]}).skip(skip).limit(limit).to_list(limit)
    following_ids = [follow["followingId"] for follow in follows]
    
    if not following_ids:
        return []
    
    # Build search query
    query = {"id": {"$in": following_ids}}
    if search:
        query["$or"] = [
            {"username": {"$regex": search, "$options": "i"}},
            {"fullName": {"$regex": search, "$options": "i"}}
        ]
    
    # Get following users
    following = await db.users.find(query).to_list(len(following_ids))
    return [UserResponse(**{k: v for k, v in user.items() if k != "password"}) for user in following]

@api_router.post("/users/{user_id}/block")
async def block_user(user_id: str, current_user = Depends(get_current_user)):
    """Block a user"""
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot block yourself")
    
    # Check if user exists
    target_user = await db.users.find_one({"id": user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already blocked
    existing_block = await db.user_blocks.find_one({
        "blockerId": current_user["id"],
        "blockedId": user_id
    })
    
    if existing_block:
        raise HTTPException(status_code=400, detail="User already blocked")
    
    # Create block
    block_id = str(uuid.uuid4())
    block = {
        "id": block_id,
        "blockerId": current_user["id"],
        "blockedId": user_id,
        "createdAt": datetime.utcnow()
    }
    
    await db.user_blocks.insert_one(block)
    
    # Remove follow relationship if exists
    await db.follows.delete_many({
        "$or": [
            {"followerId": current_user["id"], "followingId": user_id},
            {"followerId": user_id, "followingId": current_user["id"]}
        ]
    })
    
    return {"success": True, "message": "User blocked successfully"}

@api_router.delete("/users/{user_id}/block")
async def unblock_user(user_id: str, current_user = Depends(get_current_user)):
    """Unblock a user"""
    result = await db.user_blocks.delete_one({
        "blockerId": current_user["id"],
        "blockedId": user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Block not found")
    
    return {"success": True, "message": "User unblocked successfully"}

@api_router.get("/user/engagement-analytics")
async def get_engagement_analytics(current_user = Depends(get_current_user)):
    """Get engagement analytics for creator accounts"""
    # Check if user is a creator
    creator_profile = await db.creator_profiles.find_one({"userId": current_user["id"]})
    if not creator_profile:
        raise HTTPException(status_code=403, detail="Creator account required")
    
    # Get analytics data
    user_posts = await db.posts.find({"authorId": current_user["id"]}).to_list(None)
    
    total_posts = len(user_posts)
    total_likes = sum(post.get("likesCount", 0) for post in user_posts)
    total_comments = await db.comments.count_documents({"postId": {"$in": [post["id"] for post in user_posts]}})
    
    # Get follower count
    followers_count = await db.follows.count_documents({"followingId": current_user["id"]})
    
    # Calculate engagement rate
    engagement_rate = 0
    if total_posts > 0 and followers_count > 0:
        engagement_rate = ((total_likes + total_comments) / total_posts / followers_count) * 100
    
    # Get recent performance (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_posts = [post for post in user_posts if post["createdAt"] >= thirty_days_ago]
    recent_likes = sum(post.get("likesCount", 0) for post in recent_posts)
    
    return {
        "totalPosts": total_posts,
        "totalLikes": total_likes,
        "totalComments": total_comments,
        "followersCount": followers_count,
        "engagementRate": round(engagement_rate, 2),
        "recentPosts": len(recent_posts),
        "recentLikes": recent_likes,
        "analytics": {
            "averageLikesPerPost": round(total_likes / total_posts, 2) if total_posts > 0 else 0,
            "averageCommentsPerPost": round(total_comments / total_posts, 2) if total_posts > 0 else 0
        }
    }


# Search and Discovery Routes
@api_router.get("/search", response_model=SearchResponse)
async def search(q: str, type: str = "all", current_user = Depends(get_current_user), limit: int = 20):
    users = []
    posts = []
    hashtags = []
    
    if type in ["all", "users"]:
        # Search users by username or fullName
        users_cursor = await db.users.find({
            "$or": [
                {"username": {"$regex": q, "$options": "i"}},
                {"fullName": {"$regex": q, "$options": "i"}}
            ]
        }).limit(limit).to_list(limit)
        users = [UserResponse(**{k: v for k, v in user.items() if k != "password"}) for user in users_cursor]
    
    if type in ["all", "posts"]:
        # Search posts by caption
        posts_cursor = await db.posts.find({
            "caption": {"$regex": q, "$options": "i"}
        }).sort("createdAt", -1).limit(limit).to_list(limit)
        
        # Get authors for posts
        author_ids = list(set(post["authorId"] for post in posts_cursor))
        authors = await db.users.find({"id": {"$in": author_ids}}).to_list(len(author_ids)) if author_ids else []
        authors_map = {author["id"]: author for author in authors}
        
        for post in posts_cursor:
            author_data = authors_map.get(post["authorId"])
            if author_data:
                author = UserResponse(**{k: v for k, v in author_data.items() if k != "password"})
                posts.append(PostResponse(**post, author=author, comments=[]))
    
    if type in ["all", "hashtags"]:
        # Search hashtags
        hashtag_posts = await db.posts.find({
            "hashtags": {"$regex": q, "$options": "i"}
        }).limit(limit).to_list(limit)
        
        hashtag_set = set()
        for post in hashtag_posts:
            for hashtag in post.get("hashtags", []):
                if q.lower() in hashtag.lower():
                    hashtag_set.add(hashtag)
        
        hashtags = list(hashtag_set)[:limit]
    
    return SearchResponse(users=users, posts=posts, hashtags=hashtags)

@api_router.get("/trending/hashtags")
async def get_trending_hashtags(current_user = Depends(get_current_user), limit: int = 20):
    # Aggregate hashtags from recent posts (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    posts = await db.posts.find({
        "createdAt": {"$gte": seven_days_ago}
    }).to_list(None)
    
    # Count hashtag usage
    hashtag_counts = {}
    for post in posts:
        for hashtag in post.get("hashtags", []):
            hashtag_counts[hashtag] = hashtag_counts.get(hashtag, 0) + 1
    
    # Sort by popularity and return top hashtags
    trending = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    return [{"hashtag": tag, "count": count} for tag, count in trending]

@api_router.get("/feed/recommendations", response_model=List[PostResponse])
async def get_recommended_feed(current_user = Depends(get_current_user), skip: int = 0, limit: int = 20):
    # Simple recommendation algorithm based on user's activity
    
    # 1. Get user's recent likes to understand interests
    recent_likes = await db.posts.find({
        "likes": current_user["id"]
    }).sort("createdAt", -1).limit(10).to_list(10)
    
    # 2. Get hashtags from liked posts
    liked_hashtags = set()
    for post in recent_likes:
        liked_hashtags.update(post.get("hashtags", []))
    
    # 3. Get users the current user follows
    follows = await db.follows.find({"followerId": current_user["id"]}).to_list(None)
    following_ids = [follow["followingId"] for follow in follows]
    
    # 4. Build recommendation query
    recommendation_query = {
        "$or": []
    }
    
    # Posts from followed users (higher priority)
    if following_ids:
        recommendation_query["$or"].append({"authorId": {"$in": following_ids}})
    
    # Posts with similar hashtags
    if liked_hashtags:
        recommendation_query["$or"].append({"hashtags": {"$in": list(liked_hashtags)}})
    
    # If no specific interests, get popular posts (posts with most likes)
    if not recommendation_query["$or"]:
        recommendation_query = {"likesCount": {"$gte": 1}}
    
    # Get recommended posts
    posts = await db.posts.find(recommendation_query).sort([
        ("likesCount", -1),  # Sort by popularity first
        ("createdAt", -1)    # Then by recency
    ]).skip(skip).limit(limit).to_list(limit)
    
    # Get authors
    author_ids = list(set(post["authorId"] for post in posts))
    authors = await db.users.find({"id": {"$in": author_ids}}).to_list(len(author_ids)) if author_ids else []
    authors_map = {author["id"]: author for author in authors}
    
    # Build response
    result = []
    for post in posts:
        author_data = authors_map.get(post["authorId"])
        if author_data:
            author = UserResponse(**{k: v for k, v in author_data.items() if k != "password"})
            result.append(PostResponse(**post, author=author, comments=[]))
    
    return result

@api_router.get("/users/suggestions", response_model=List[UserResponse])
async def get_user_suggestions(current_user = Depends(get_current_user), limit: int = 20):
    # Get users that current user is not following
    follows = await db.follows.find({"followerId": current_user["id"]}).to_list(None)
    following_ids = [follow["followingId"] for follow in follows]
    following_ids.append(current_user["id"])  # Exclude self
    
    # Get suggested users (users with most followers that current user doesn't follow)
    pipeline = [
        {"$match": {"id": {"$nin": following_ids}}},
        {
            "$lookup": {
                "from": "follows",
                "localField": "id",
                "foreignField": "followingId",
                "as": "followers"
            }
        },
        {"$addFields": {"followerCount": {"$size": "$followers"}}},
        {"$sort": {"followerCount": -1}},
        {"$limit": limit}
    ]
    
    suggested_users = await db.users.aggregate(pipeline).to_list(limit)
    
    return [UserResponse(**{k: v for k, v in user.items() if k not in ["password", "followers"]}) for user in suggested_users]


# Background task to clean expired stories
async def cleanup_expired_stories():
    """Background task to remove expired stories"""
    while True:
        try:
            now = datetime.utcnow()
            result = await db.stories.delete_many({"expiresAt": {"$lt": now}})
            if result.deleted_count > 0:
                print(f"Cleaned up {result.deleted_count} expired stories")
            await asyncio.sleep(3600)  # Run every hour
        except Exception as e:
            print(f"Error cleaning up stories: {e}")
            await asyncio.sleep(300)  # Wait 5 minutes on error


# User Posts endpoint
@api_router.get("/users/{user_id}/posts", response_model=List[PostResponse])
async def get_user_posts(user_id: str, skip: int = 0, limit: int = 20):
    """Get posts by a specific user"""
    try:
        # Validate user exists
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's posts
        posts = await db.posts.find(
            {"authorId": user_id}
        ).sort("createdAt", -1).skip(skip).limit(limit).to_list(length=limit)
        
        # Get authors info and format response
        result = []
        for post in posts:
            author = await db.users.find_one({"id": post["authorId"]})
            if author:
                author_response = UserResponse(
                    id=str(author["_id"]),
                    email=author["email"],
                    username=author["username"],
                    fullName=author["fullName"],
                    profileImage=author.get("profileImage"),
                    bio=author.get("bio"),
                    createdAt=author["createdAt"]
                )
                
                post_response = PostResponse(
                    id=str(post["_id"]),
                    authorId=post["authorId"],
                    author=author_response,
                    caption=post["caption"],
                    media=post["media"],
                    mediaTypes=post["mediaTypes"],
                    hashtags=post.get("hashtags", []),
                    taggedUsers=post.get("taggedUsers", []),
                    likes=post.get("likes", []),
                    likesCount=len(post.get("likes", [])),
                    comments=[],  # Will be loaded separately if needed
                    commentsCount=await db.comments.count_documents({"postId": str(post["_id"])}),
                    createdAt=post["createdAt"]
                )
                result.append(post_response)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user posts: {str(e)}")

# User Stats endpoint
@api_router.get("/users/{user_id}/stats")
async def get_user_stats(user_id: str):
    """Get user statistics (posts count, followers, following)"""
    try:
        # Validate user exists
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get counts
        posts_count = await db.posts.count_documents({"authorId": user_id})
        followers_count = await db.follows.count_documents({"followingId": user_id})
        following_count = await db.follows.count_documents({"followerId": user_id})
        
        return {
            "postsCount": posts_count,
            "followersCount": followers_count,
            "followingCount": following_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user stats: {str(e)}")

# PHASE 15: UI/UX & ACCESSIBILITY IMPROVEMENTS ENDPOINTS

class SupportTicketCreate(BaseModel):
    category: str  # "bug", "feature_request", "account_issue", "harassment", "technical", "other"
    subject: str
    description: str
    attachments: Optional[List[str]] = []  # Base64 images/files

class ThemeSettingsUpdate(BaseModel):
    themeMode: Optional[str] = None  # "light", "dark", "system"
    primaryColor: Optional[str] = None
    accentColor: Optional[str] = None
    fontSize: Optional[str] = None
    fontFamily: Optional[str] = None
    highContrast: Optional[bool] = None
    reduceMotion: Optional[bool] = None
    colorBlindMode: Optional[str] = None

class ContentReportCreate(BaseModel):
    contentType: str  # "post", "comment", "user", "message"
    contentId: str
    reason: str  # "spam", "harassment", "inappropriate", "violence", etc.
    description: Optional[str] = None

@api_router.post("/support/tickets", response_model=dict)
async def create_support_ticket(ticket_data: SupportTicketCreate, current_user = Depends(get_current_user)):
    """Create a new support ticket"""
    ticket_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    new_ticket = {
        "id": ticket_id,
        "userId": current_user["id"],
        "user": {k: v for k, v in current_user.items() if k not in ["password", "_id"]},
        "category": ticket_data.category,
        "subject": ticket_data.subject,
        "description": ticket_data.description,
        "priority": "medium",
        "status": "open",
        "attachments": ticket_data.attachments or [],
        "assignedTo": None,
        "tags": [],
        "createdAt": now,
        "updatedAt": now,
        "resolvedAt": None
    }
    
    await db.support_tickets.insert_one(new_ticket)
    
    return {
        "success": True,
        "message": "Support ticket created successfully",
        "ticketId": ticket_id
    }

@api_router.get("/support/tickets", response_model=List[dict])
async def get_user_support_tickets(current_user = Depends(get_current_user), skip: int = 0, limit: int = 50):
    """Get user's support tickets"""
    tickets = await db.support_tickets.find({
        "userId": current_user["id"]
    }, {"_id": 0}).sort("createdAt", -1).skip(skip).limit(limit).to_list(limit)
    
    # Clean up tickets to remove any ObjectId fields
    cleaned_tickets = []
    for ticket in tickets:
        if "user" in ticket and isinstance(ticket["user"], dict):
            # Remove any ObjectId fields from user object
            ticket["user"] = {k: v for k, v in ticket["user"].items() if k != "_id"}
        cleaned_tickets.append(ticket)
    
    return cleaned_tickets

@api_router.get("/support/faq", response_model=List[dict])
async def get_faq():
    """Get FAQ entries"""
    faqs = await db.faqs.find({"isActive": True}).sort("order", 1).to_list(None)
    
    if not faqs:
        # Return default FAQs if none exist
        default_faqs = [
            {
                "id": "faq_1",
                "category": "account",
                "question": "How do I reset my password?",
                "answer": "Go to the login screen and tap 'Forgot Password'. Enter your email and follow the instructions sent to your inbox.",
                "keywords": ["password", "reset", "forgot", "login"],
                "isActive": True,
                "order": 1,
                "views": 0,
                "helpful": 0,
                "notHelpful": 0,
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            },
            {
                "id": "faq_2",
                "category": "privacy",
                "question": "How do I make my account private?",
                "answer": "Go to Settings > Privacy and toggle 'Private Account'. When your account is private, only approved followers can see your posts.",
                "keywords": ["private", "account", "privacy", "followers"],
                "isActive": True,
                "order": 2,
                "views": 0,
                "helpful": 0,
                "notHelpful": 0,
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            },
            {
                "id": "faq_3",
                "category": "posting",
                "question": "How many photos can I post at once?",
                "answer": "You can share up to 10 photos or videos in a single post. Select multiple media items when creating your post.",
                "keywords": ["photos", "videos", "posting", "multiple", "limit"],
                "isActive": True,
                "order": 3,
                "views": 0,
                "helpful": 0,
                "notHelpful": 0,
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            }
        ]
        return default_faqs
    
    return faqs

@api_router.get("/support/faq/search")
async def search_faq(q: str):
    """Search FAQ entries"""
    if not q or len(q.strip()) < 2:
        return {"results": []}
    
    # Search in questions, answers, and keywords
    results = await db.faqs.find({
        "$and": [
            {"isActive": True},
            {
                "$or": [
                    {"question": {"$regex": q, "$options": "i"}},
                    {"answer": {"$regex": q, "$options": "i"}},
                    {"keywords": {"$regex": q, "$options": "i"}}
                ]
            }
        ]
    }).to_list(None)
    
    return {"results": results}

@api_router.get("/app/info")
async def get_app_info():
    """Get app information for About screen"""
    return {
        "version": "1.0.0",
        "buildNumber": "100",
        "releaseDate": datetime.utcnow(),
        "platform": "mobile",
        "minOSVersion": "iOS 12.0 / Android 6.0",
        "features": [
            "Photo & Video Sharing",
            "Stories",
            "Direct Messaging",
            "Live Chat",
            "Reels",
            "Push Notifications",
            "Dark Mode"
        ],
        "privacyPolicyUrl": "https://novasocial.app/privacy",
        "termsOfServiceUrl": "https://novasocial.app/terms",
        "supportEmail": "support@novasocial.app",
        "website": "https://novasocial.app"
    }

@api_router.get("/settings/theme", response_model=dict)
async def get_theme_settings(current_user = Depends(get_current_user)):
    """Get user's theme settings"""
    settings = await db.user_theme_settings.find_one({"userId": current_user["id"]}, {"_id": 0})
    
    if not settings:
        # Return default theme settings
        default_settings = {
            "userId": current_user["id"],
            "themeMode": "system",
            "primaryColor": "#007AFF",
            "accentColor": "#FF3B30",
            "fontSize": "medium",
            "fontFamily": "system",
            "highContrast": False,
            "reduceMotion": False,
            "colorBlindMode": None,
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
        return default_settings
    
    return settings

@api_router.put("/settings/theme")
async def update_theme_settings(
    theme_data: ThemeSettingsUpdate,
    current_user = Depends(get_current_user)
):
    """Update user's theme settings"""
    now = datetime.utcnow()
    
    # Get current settings or create new
    current_settings = await db.user_theme_settings.find_one({"userId": current_user["id"]})
    
    if current_settings:
        # Update existing settings
        update_data = {}
        if theme_data.themeMode is not None:
            update_data["themeMode"] = theme_data.themeMode
        if theme_data.primaryColor is not None:
            update_data["primaryColor"] = theme_data.primaryColor
        if theme_data.accentColor is not None:
            update_data["accentColor"] = theme_data.accentColor
        if theme_data.fontSize is not None:
            update_data["fontSize"] = theme_data.fontSize
        if theme_data.fontFamily is not None:
            update_data["fontFamily"] = theme_data.fontFamily
        if theme_data.highContrast is not None:
            update_data["highContrast"] = theme_data.highContrast
        if theme_data.reduceMotion is not None:
            update_data["reduceMotion"] = theme_data.reduceMotion
        if theme_data.colorBlindMode is not None:
            update_data["colorBlindMode"] = theme_data.colorBlindMode
        
        update_data["updatedAt"] = now
        
        await db.user_theme_settings.update_one(
            {"userId": current_user["id"]},
            {"$set": update_data}
        )
    else:
        # Create new settings
        new_settings = {
            "userId": current_user["id"],
            "themeMode": theme_data.themeMode or "system",
            "primaryColor": theme_data.primaryColor or "#007AFF",
            "accentColor": theme_data.accentColor or "#FF3B30",
            "fontSize": theme_data.fontSize or "medium",
            "fontFamily": theme_data.fontFamily or "system",
            "highContrast": theme_data.highContrast or False,
            "reduceMotion": theme_data.reduceMotion or False,
            "colorBlindMode": theme_data.colorBlindMode,
            "createdAt": now,
            "updatedAt": now
        }
        
        await db.user_theme_settings.insert_one(new_settings)
    
    return {"success": True, "message": "Theme settings updated successfully"}

@api_router.post("/auth/sign-out")
async def sign_out(current_user = Depends(get_current_user)):
    """Sign out user with session cleanup"""
    now = datetime.utcnow()
    
    # Update user activity status to offline
    await db.user_activities.update_one(
        {"userId": current_user["id"]},
        {
            "$set": {
                "status": "offline",
                "lastSeen": now,
                "updatedAt": now
            }
        },
        upsert=True
    )
    
    # Log security event
    audit_log = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "event_type": "SIGN_OUT",
        "timestamp": now,
        "metadata": {"email": current_user["email"]}
    }
    await db.security_audit_logs.insert_one(audit_log)
    
    return {
        "success": True,
        "message": "Successfully signed out"
    }

@api_router.post("/reports/content")
async def report_content(report_data: ContentReportCreate, current_user = Depends(get_current_user)):
    """Report problematic content"""
    report_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    new_report = {
        "id": report_id,
        "reporterId": current_user["id"],
        "reporter": {k: v for k, v in current_user.items() if k != "password"},
        "contentType": report_data.contentType,
        "contentId": report_data.contentId,
        "reason": report_data.reason,
        "description": report_data.description,
        "status": "pending",
        "createdAt": now,
        "resolvedAt": None
    }
    
    await db.reported_content.insert_one(new_report)
    
    return {
        "success": True,
        "message": "Content report submitted successfully",
        "reportId": report_id
    }

# Original routes
@api_router.get("/")
async def root():
    return {"message": "NovaSocial API - Phase 15 Complete"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]


# Start cleanup task and include router
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_expired_stories())

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# PHASE 16: POSTING & MEDIA ENHANCEMENTS ENDPOINTS

from models.posting_models import (
    PostTag, LocationTag, UserTag, StoryReel, PostCreate, 
    LocationSearchResult, TagSearchResult, UploadProgress,
    MediaCompression, StoryReelCreate, TagValidation, PrivacyCheck
)
import json
import re

# Mock location service (replace with real API later)
MOCK_LOCATIONS = [
    {
        "id": "loc_1",
        "name": "Central Park",
        "displayName": "Central Park, New York",
        "address": "Central Park, New York, NY 10024, USA",
        "coordinates": {"lat": 40.785091, "lng": -73.968285},
        "category": "park",
        "city": "New York",
        "country": "USA"
    },
    {
        "id": "loc_2", 
        "name": "Times Square",
        "displayName": "Times Square, New York",
        "address": "Times Square, New York, NY 10036, USA",
        "coordinates": {"lat": 40.758896, "lng": -73.985130},
        "category": "landmark",
        "city": "New York",
        "country": "USA"
    },
    {
        "id": "loc_3",
        "name": "Golden Gate Bridge", 
        "displayName": "Golden Gate Bridge, San Francisco",
        "address": "Golden Gate Bridge, San Francisco, CA, USA",
        "coordinates": {"lat": 37.819929, "lng": -122.478255},
        "category": "landmark",
        "city": "San Francisco", 
        "country": "USA"
    }
]

@api_router.get("/search/tags")
async def search_tags(
    q: str,
    type: Optional[str] = None,  # "users", "locations", "all"
    current_user = Depends(get_current_user),
    limit: int = 10
):
    """Search for users and locations to tag"""
    if not q or len(q.strip()) < 2:
        return TagSearchResult(users=[], locations=[])
    
    query_lower = q.lower()
    results = TagSearchResult(users=[], locations=[])
    
    # Search users
    if type != "locations":
        users = await db.users.find({
            "$or": [
                {"username": {"$regex": query_lower, "$options": "i"}},
                {"fullName": {"$regex": query_lower, "$options": "i"}}
            ]
        }).limit(limit).to_list(limit)
        
        results.users = [
            UserResponse(**{k: v for k, v in user.items() if k != "password"}) 
            for user in users if user["id"] != current_user["id"]
        ]
    
    # Search locations (mock data)
    if type != "users":
        matching_locations = [
            loc for loc in MOCK_LOCATIONS
            if query_lower in loc["name"].lower() or 
               query_lower in loc["displayName"].lower() or
               query_lower in loc["address"].lower()
        ]
        
        results.locations = [
            LocationSearchResult(**loc) for loc in matching_locations[:limit]
        ]
    
    return results

@api_router.post("/posts/enhanced", response_model=dict)
async def create_enhanced_post(
    post_data: PostCreate, 
    current_user = Depends(get_current_user)
):
    """Create post with tagging and location features"""
    post_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    # Validate tags (max 10 people)
    if post_data.taggedUsers and len(post_data.taggedUsers) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 people can be tagged")
    
    # Create the post
    new_post = {
        "id": post_id,
        "authorId": current_user["id"],
        "caption": post_data.caption,
        "media": post_data.media,
        "mediaTypes": post_data.mediaTypes,
        "hashtags": post_data.hashtags or [],
        "taggedUsers": post_data.taggedUsers or [],
        "location": post_data.location,
        "likes": [],
        "likesCount": 0,
        "commentsCount": 0,
        "createdAt": now,
        "updatedAt": now
    }
    
    await db.posts.insert_one(new_post)
    
    # Create user tags
    if post_data.taggedUsers:
        for tag_data in post_data.taggedUsers:
            # Check privacy - if tagged user has private account, create pending tag
            tagged_user = await db.users.find_one({"id": tag_data["userId"]})
            if tagged_user:
                user_tag = {
                    "id": str(uuid.uuid4()),
                    "postId": post_id,
                    "taggerId": current_user["id"],
                    "taggedUserId": tag_data["userId"],
                    "position": tag_data.get("position"),
                    "isApproved": True,  # Auto-approve for now, implement privacy later
                    "createdAt": now
                }
                await db.user_tags.insert_one(user_tag)
                
                # Create notification for tagged user
                notification = {
                    "id": str(uuid.uuid4()),
                    "type": "tag",
                    "senderId": current_user["id"],
                    "recipientId": tag_data["userId"],
                    "relatedId": post_id,
                    "content": f"{current_user['username']} tagged you in a post",
                    "isRead": False,
                    "createdAt": now
                }
                await db.notifications.insert_one(notification)
    
    # Create location tag
    if post_data.location:
        location_tag = {
            "id": str(uuid.uuid4()),
            "postId": post_id,
            "tagType": "location",
            "locationId": post_data.location.get("id"),
            "locationName": post_data.location.get("name"),
            "locationCoordinates": post_data.location.get("coordinates"),
            "createdAt": now
        }
        await db.post_tags.insert_one(location_tag)
    
    return {
        "success": True,
        "postId": post_id,
        "message": "Post created successfully with tags"
    }

@api_router.get("/locations/{location_id}/posts", response_model=List[PostResponse])
async def get_posts_by_location(
    location_id: str,
    current_user = Depends(get_current_user),
    skip: int = 0,
    limit: int = 20
):
    """Get all posts tagged at a specific location"""
    # Find posts with this location tag
    location_tags = await db.post_tags.find({
        "locationId": location_id,
        "tagType": "location"
    }).skip(skip).limit(limit).to_list(limit)
    
    if not location_tags:
        return []
    
    post_ids = [tag["postId"] for tag in location_tags]
    posts = await db.posts.find({"id": {"$in": post_ids}}).to_list(len(post_ids))
    
    # Get authors
    author_ids = list(set(post["authorId"] for post in posts))
    authors = await db.users.find({"id": {"$in": author_ids}}).to_list(len(author_ids)) if author_ids else []
    authors_map = {author["id"]: author for author in authors}
    
    result = []
    for post in posts:
        author_data = authors_map.get(post["authorId"])
        if author_data:
            author = UserResponse(**{k: v for k, v in author_data.items() if k != "password"})
            result.append(PostResponse(**post, author=author, comments=[]))
    
    return result

@api_router.post("/stories/enhanced", response_model=dict)
async def create_enhanced_story_reel(
    story_data: StoryReelCreate,
    current_user = Depends(get_current_user)
):
    """Create story/reel with enhanced features and retry logic"""
    story_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    # Set expiration for stories (24 hours)
    expires_at = None
    if story_data.contentType in ["story", "story_reel"]:
        expires_at = story_data.expiresAt or datetime.utcnow() + timedelta(hours=24)
    
    # Create story/reel
    new_story_reel = {
        "id": story_id,
        "authorId": current_user["id"],
        "contentType": story_data.contentType,
        "media": story_data.media,
        "mediaType": story_data.mediaType,
        "duration": story_data.duration,
        "text": story_data.text,
        "textPosition": story_data.textPosition,
        "textStyle": story_data.textStyle,
        "music": story_data.music,
        "effects": story_data.effects or [],
        "tags": story_data.tags or [],
        "stickers": story_data.stickers or [],
        "viewers": [],
        "viewersCount": 0,
        "likesCount": 0,
        "likes": [],
        "commentsCount": 0,
        "isHighlight": False,
        "expiresAt": expires_at,
        "createdAt": now,
        "updatedAt": now
    }
    
    # Store in appropriate collection based on type
    if story_data.contentType == "reel":
        await db.reels.insert_one(new_story_reel)
    else:
        await db.stories.insert_one(new_story_reel)
    
    # Create upload progress record
    progress_record = {
        "id": str(uuid.uuid4()),
        "userId": current_user["id"],
        "fileName": f"{story_data.contentType}_{story_id}",
        "totalSize": len(story_data.media) if story_data.media else 0,
        "uploadedSize": len(story_data.media) if story_data.media else 0,
        "progress": 100.0,
        "status": "completed",
        "retryCount": 0,
        "maxRetries": 3,
        "createdAt": now,
        "updatedAt": now
    }
    await db.upload_progress.insert_one(progress_record)
    
    return {
        "success": True,
        "storyId": story_id,
        "contentType": story_data.contentType,
        "uploadProgress": progress_record,
        "message": f"{story_data.contentType.title()} created successfully"
    }

@api_router.get("/upload/progress/{upload_id}", response_model=UploadProgress)
async def get_upload_progress(
    upload_id: str,
    current_user = Depends(get_current_user)
):
    """Get upload progress for media uploads"""
    progress = await db.upload_progress.find_one({
        "id": upload_id,
        "userId": current_user["id"]
    })
    
    if not progress:
        raise HTTPException(status_code=404, detail="Upload progress not found")
    
    return UploadProgress(**progress)

@api_router.post("/upload/retry/{upload_id}")
async def retry_upload(
    upload_id: str,
    current_user = Depends(get_current_user)
):
    """Retry failed upload"""
    progress = await db.upload_progress.find_one({
        "id": upload_id,
        "userId": current_user["id"]
    })
    
    if not progress:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    if progress["status"] != "failed":
        raise HTTPException(status_code=400, detail="Upload is not in failed state")
    
    if progress["retryCount"] >= progress["maxRetries"]:
        raise HTTPException(status_code=400, detail="Maximum retry attempts exceeded")
    
    # Update retry count and status
    await db.upload_progress.update_one(
        {"id": upload_id},
        {
            "$set": {
                "status": "uploading",
                "retryCount": progress["retryCount"] + 1,
                "updatedAt": datetime.utcnow()
            }
        }
    )
    
    return {"success": True, "message": "Upload retry initiated"}

@api_router.post("/posts/validate-tags")
async def validate_post_tags(
    post_id: str,
    tagged_user_ids: List[str],
    location_id: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """Validate tags before posting"""
    validation = TagValidation(
        postId=post_id,
        taggedUserIds=tagged_user_ids,
        locationId=location_id,
        isValid=True,
        errors=[],
        warnings=[]
    )
    
    # Check maximum users limit
    if len(tagged_user_ids) > 10:
        validation.isValid = False
        validation.errors.append("Cannot tag more than 10 users in a single post")
    
    # Check if users exist and privacy settings
    for user_id in tagged_user_ids:
        user = await db.users.find_one({"id": user_id})
        if not user:
            validation.isValid = False
            validation.errors.append(f"User {user_id} not found")
        else:
            # Check if user has blocked the current user
            # (This would be implemented with actual privacy settings)
            pass
    
    # Validate location if provided
    if location_id:
        # Check if location exists in our mock data
        location_exists = any(loc["id"] == location_id for loc in MOCK_LOCATIONS)
        if not location_exists:
            validation.warnings.append("Location not found in database")
    
    return validation

@api_router.post("/privacy/check")
async def check_privacy_permissions(
    target_user_id: str,
    action: str,  # "tag", "mention", "view_post"
    current_user = Depends(get_current_user)
):
    """Check if current user can perform action on target user"""
    
    # Get target user
    target_user = await db.users.find_one({"id": target_user_id})
    if not target_user:
        return PrivacyCheck(
            userId=current_user["id"],
            targetUserId=target_user_id,
            action=action,
            isAllowed=False,
            reason="User not found"
        )
    
    # For now, allow all actions (implement proper privacy rules later)
    return PrivacyCheck(
        userId=current_user["id"],
        targetUserId=target_user_id,
        action=action,
        isAllowed=True
    )

# PHASE 17: STORY & CREATIVE TOOLS ENDPOINTS

from models.story_creative_models import (
    StorySticker, MusicLibraryItem, GIFLibraryItem, FrameTemplate,
    TextStyle, ColorPalette, InteractiveElement, CollaborativePrompt,
    ECommerceLink, StoryTemplate, StickerCreate, StickerUpdate,
    TextStyleCreate, InteractiveElementCreate, InteractiveResponse,
    CollaborativePromptCreate, PromptParticipation, MOCK_MUSIC_LIBRARY,
    MOCK_GIF_LIBRARY, MOCK_FRAMES, MOCK_COLOR_PALETTES
)

@api_router.get("/stories/{story_id}/stickers", response_model=List[StorySticker])
async def get_story_stickers(
    story_id: str,
    current_user = Depends(get_current_user)
):
    """Get all stickers for a story"""
    stickers = await db.story_stickers.find({"storyId": story_id}).to_list(None)
    return [StorySticker(**sticker) for sticker in stickers]

@api_router.post("/stories/{story_id}/stickers", response_model=dict)
async def add_story_sticker(
    story_id: str,
    sticker_data: StickerCreate,
    current_user = Depends(get_current_user)
):
    """Add sticker to story"""
    # Verify user owns the story
    story = await db.stories.find_one({"id": story_id, "authorId": current_user["id"]})
    if not story:
        raise HTTPException(status_code=404, detail="Story not found or not owned by user")
    
    sticker_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    new_sticker = {
        "id": sticker_id,
        "storyId": story_id,
        "type": sticker_data.type,
        "data": sticker_data.data,
        "position": sticker_data.position,
        "zIndex": sticker_data.zIndex or 0,
        "isInteractive": sticker_data.isInteractive or False,
        "expiresAt": sticker_data.expiresAt,
        "createdAt": now
    }
    
    await db.story_stickers.insert_one(new_sticker)
    
    return {
        "success": True,
        "stickerId": sticker_id,
        "message": "Sticker added successfully"
    }

@api_router.put("/stories/stickers/{sticker_id}")
async def update_story_sticker(
    sticker_id: str,
    update_data: StickerUpdate,
    current_user = Depends(get_current_user)
):
    """Update sticker position or data"""
    sticker = await db.story_stickers.find_one({"id": sticker_id})
    if not sticker:
        raise HTTPException(status_code=404, detail="Sticker not found")
    
    # Verify user owns the story
    story = await db.stories.find_one({"id": sticker["storyId"], "authorId": current_user["id"]})
    if not story:
        raise HTTPException(status_code=403, detail="Not authorized to edit this sticker")
    
    update_fields = {}
    if update_data.position is not None:
        update_fields["position"] = update_data.position
    if update_data.data is not None:
        update_fields["data"] = update_data.data
    if update_data.zIndex is not None:
        update_fields["zIndex"] = update_data.zIndex
    
    await db.story_stickers.update_one(
        {"id": sticker_id},
        {"$set": update_fields}
    )
    
    return {"success": True, "message": "Sticker updated successfully"}

@api_router.delete("/stories/stickers/{sticker_id}")
async def delete_story_sticker(
    sticker_id: str,
    current_user = Depends(get_current_user)
):
    """Delete sticker from story"""
    sticker = await db.story_stickers.find_one({"id": sticker_id})
    if not sticker:
        raise HTTPException(status_code=404, detail="Sticker not found")
    
    # Verify user owns the story
    story = await db.stories.find_one({"id": sticker["storyId"], "authorId": current_user["id"]})
    if not story:
        raise HTTPException(status_code=403, detail="Not authorized to delete this sticker")
    
    await db.story_stickers.delete_one({"id": sticker_id})
    
    return {"success": True, "message": "Sticker deleted successfully"}

@api_router.get("/creative/music", response_model=List[MusicLibraryItem])
async def get_music_library(
    category: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 20
):
    """Get music library for story stickers"""
    music_items = MOCK_MUSIC_LIBRARY.copy()
    
    # Filter by category
    if category:
        music_items = [item for item in music_items if item.get("category") == category]
    
    # Filter by search query
    if search:
        search_lower = search.lower()
        music_items = [
            item for item in music_items
            if search_lower in item["title"].lower() or search_lower in item["artist"].lower()
        ]
    
    return [MusicLibraryItem(**item) for item in music_items[:limit]]

@api_router.get("/creative/gifs", response_model=List[GIFLibraryItem])
async def get_gif_library(
    category: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 20
):
    """Get GIF library for story stickers"""
    gif_items = MOCK_GIF_LIBRARY.copy()
    
    # Filter by category
    if category:
        gif_items = [item for item in gif_items if item.get("category") == category]
    
    # Filter by search query
    if search:
        search_lower = search.lower()
        gif_items = [
            item for item in gif_items
            if search_lower in item["title"].lower() or 
               any(search_lower in tag.lower() for tag in item["tags"])
        ]
    
    return [GIFLibraryItem(**item) for item in gif_items[:limit]]

@api_router.get("/creative/frames", response_model=List[FrameTemplate])
async def get_frame_templates(category: Optional[str] = None):
    """Get frame templates for story borders"""
    frames = MOCK_FRAMES.copy()
    
    if category:
        frames = [frame for frame in frames if frame.get("category") == category]
    
    return [FrameTemplate(**frame) for frame in frames]

@api_router.get("/creative/colors", response_model=List[ColorPalette])
async def get_color_palettes(category: Optional[str] = None):
    """Get color palettes for text styling"""
    palettes = MOCK_COLOR_PALETTES.copy()
    
    if category:
        palettes = [palette for palette in palettes if palette.get("category") == category]
    
    return [ColorPalette(**palette) for palette in palettes]

@api_router.post("/stories/{story_id}/interactive", response_model=dict)
async def add_interactive_element(
    story_id: str,
    element_data: InteractiveElementCreate,
    current_user = Depends(get_current_user)
):
    """Add interactive element (poll, quiz, question) to story"""
    # Verify user owns the story
    story = await db.stories.find_one({"id": story_id, "authorId": current_user["id"]})
    if not story:
        raise HTTPException(status_code=404, detail="Story not found or not owned by user")
    
    element_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    new_element = {
        "id": element_id,
        "storyId": story_id,
        "type": element_data.type,
        "question": element_data.question,
        "options": element_data.options,
        "correctAnswer": element_data.correctAnswer,
        "responses": [],
        "expiresAt": element_data.expiresAt,
        "isActive": True,
        "createdAt": now
    }
    
    await db.interactive_elements.insert_one(new_element)
    
    return {
        "success": True,
        "elementId": element_id,
        "message": "Interactive element added successfully"
    }

@api_router.post("/interactive/{element_id}/respond")
async def respond_to_interactive_element(
    element_id: str,
    response_data: InteractiveResponse,
    current_user = Depends(get_current_user)
):
    """Respond to interactive element"""
    element = await db.interactive_elements.find_one({"id": element_id})
    if not element:
        raise HTTPException(status_code=404, detail="Interactive element not found")
    
    if not element.get("isActive"):
        raise HTTPException(status_code=400, detail="Interactive element is no longer active")
    
    # Check if user already responded
    existing_response = next(
        (r for r in element.get("responses", []) if r.get("userId") == current_user["id"]),
        None
    )
    
    if existing_response:
        raise HTTPException(status_code=400, detail="You have already responded to this element")
    
    # Add response
    new_response = {
        "userId": current_user["id"],
        "response": response_data.response,
        "timestamp": datetime.utcnow()
    }
    
    await db.interactive_elements.update_one(
        {"id": element_id},
        {"$push": {"responses": new_response}}
    )
    
    return {
        "success": True,
        "message": "Response recorded successfully"
    }

@api_router.get("/interactive/{element_id}/results")
async def get_interactive_results(
    element_id: str,
    current_user = Depends(get_current_user)
):
    """Get results for interactive element"""
    element = await db.interactive_elements.find_one({"id": element_id})
    if not element:
        raise HTTPException(status_code=404, detail="Interactive element not found")
    
    # Check if user is the story owner or has responded
    story = await db.stories.find_one({"id": element["storyId"]})
    has_responded = any(r.get("userId") == current_user["id"] for r in element.get("responses", []))
    
    if story["authorId"] != current_user["id"] and not has_responded:
        raise HTTPException(status_code=403, detail="Not authorized to view results")
    
    responses = element.get("responses", [])
    
    # Calculate results based on type
    if element["type"] == "poll":
        results = {}
        for option in element.get("options", []):
            results[option] = 0
        
        for response in responses:
            selected_option = response["response"].get("selectedOption")
            if selected_option in results:
                results[selected_option] += 1
    
    elif element["type"] == "quiz":
        correct_count = 0
        total_count = len(responses)
        
        for response in responses:
            if response["response"].get("selectedAnswer") == element.get("correctAnswer"):
                correct_count += 1
        
        results = {
            "totalResponses": total_count,
            "correctResponses": correct_count,
            "correctPercentage": (correct_count / total_count * 100) if total_count > 0 else 0
        }
    
    else:  # question type
        results = {
            "totalResponses": len(responses),
            "responses": [r["response"] for r in responses[-10:]]  # Last 10 responses
        }
    
    return {
        "element": InteractiveElement(**element),
        "results": results
    }

@api_router.post("/collaborative/prompts", response_model=dict)
async def create_collaborative_prompt(
    prompt_data: CollaborativePromptCreate,
    current_user = Depends(get_current_user)
):
    """Create collaborative prompt for 'Add Yours' sticker"""
    prompt_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    new_prompt = {
        "id": prompt_id,
        "creatorId": current_user["id"],
        "promptText": prompt_data.promptText,
        "template": prompt_data.template,
        "participants": [],
        "responses": [],
        "maxParticipants": prompt_data.maxParticipants,
        "expiresAt": prompt_data.expiresAt,
        "category": prompt_data.category or "general",
        "tags": prompt_data.tags or [],
        "isActive": True,
        "createdAt": now
    }
    
    await db.collaborative_prompts.insert_one(new_prompt)
    
    return {
        "success": True,
        "promptId": prompt_id,
        "message": "Collaborative prompt created successfully"
    }

@api_router.post("/collaborative/prompts/{prompt_id}/participate")
async def participate_in_prompt(
    prompt_id: str,
    participation_data: PromptParticipation,
    current_user = Depends(get_current_user)
):
    """Participate in collaborative prompt"""
    prompt = await db.collaborative_prompts.find_one({"id": prompt_id})
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    if not prompt.get("isActive"):
        raise HTTPException(status_code=400, detail="Prompt is no longer active")
    
    # Check if already participated
    if current_user["id"] in prompt.get("participants", []):
        raise HTTPException(status_code=400, detail="You have already participated in this prompt")
    
    # Check max participants
    if prompt.get("maxParticipants") and len(prompt.get("participants", [])) >= prompt["maxParticipants"]:
        raise HTTPException(status_code=400, detail="Maximum participants reached")
    
    # Add participation
    new_response = {
        "userId": current_user["id"],
        "response": participation_data.response,
        "timestamp": datetime.utcnow()
    }
    
    await db.collaborative_prompts.update_one(
        {"id": prompt_id},
        {
            "$push": {
                "participants": current_user["id"],
                "responses": new_response
            }
        }
    )
    
    return {
        "success": True,
        "message": "Successfully participated in prompt"
    }

@api_router.get("/collaborative/prompts/trending", response_model=List[CollaborativePrompt])
async def get_trending_prompts(
    category: Optional[str] = None,
    limit: int = 10
):
    """Get trending collaborative prompts"""
    match_conditions = {"isActive": True}
    if category:
        match_conditions["category"] = category
    
    prompts = await db.collaborative_prompts.find(match_conditions)\
        .sort([("participants", -1), ("createdAt", -1)])\
        .limit(limit).to_list(limit)
    
    # Get creator information
    creator_ids = [prompt["creatorId"] for prompt in prompts]
    creators = await db.users.find({"id": {"$in": creator_ids}}).to_list(len(creator_ids)) if creator_ids else []
    creators_map = {creator["id"]: creator for creator in creators}
    
    result = []
    for prompt in prompts:
        creator_data = creators_map.get(prompt["creatorId"])
        creator = UserResponse(**{k: v for k, v in creator_data.items() if k != "password"}) if creator_data else None
        result.append(CollaborativePrompt(**prompt, creator=creator))
    
    return result

@api_router.get("/stories/{story_id}/analytics")
async def get_story_analytics(
    story_id: str,
    current_user = Depends(get_current_user)
):
    """Get analytics for story (views, interactions, etc.)"""
    story = await db.stories.find_one({"id": story_id, "authorId": current_user["id"]})
    if not story:
        raise HTTPException(status_code=404, detail="Story not found or not owned by user")
    
    # Get sticker interactions
    stickers = await db.story_stickers.find({"storyId": story_id}).to_list(None)
    interactive_elements = await db.interactive_elements.find({"storyId": story_id}).to_list(None)
    
    total_interactions = 0
    for element in interactive_elements:
        total_interactions += len(element.get("responses", []))
    
    analytics = {
        "views": story.get("viewersCount", 0),
        "uniqueViewers": len(story.get("viewers", [])),
        "stickersCount": len(stickers),
        "interactiveElements": len(interactive_elements),
        "totalInteractions": total_interactions,
        "completionRate": 0.8,  # Mock completion rate
        "averageViewTime": 5.2,  # Mock average view time in seconds
        "topLocations": ["New York", "San Francisco", "Los Angeles"],  # Mock locations
        "demographics": {
            "ageGroups": {"18-24": 45, "25-34": 35, "35-44": 20},
            "genders": {"female": 60, "male": 40}
        }
    }
    
    return analytics

# ====================================================================
# PHASE 18: VIDEO FILTERS & AR EFFECTS FOR REELS
# ====================================================================

from models.reels_models import *
import json

# Mock cloud storage service for video processing
class MockVideoProcessor:
    """Mock video processing service for filters and AR effects"""
    
    @staticmethod
    async def apply_filters_and_effects(video_data: str, filters: List[VideoFilter], ar_effects: List[AREffect]) -> dict:
        """Mock video processing with filters and AR effects"""
        # Simulate processing time
        await asyncio.sleep(0.5)
        
        # Generate mock processed video URL
        processed_video_id = str(uuid.uuid4())
        processed_video_url = f"https://cdn.example.com/processed_videos/{processed_video_id}.mp4"
        thumbnail_url = f"https://cdn.example.com/thumbnails/{processed_video_id}.jpg"
        
        return {
            "processedVideoUrl": processed_video_url,
            "thumbnailUrl": thumbnail_url,
            "processingId": processed_video_id
        }

@api_router.post("/reels/upload")
async def upload_reel_with_filters(
    reel_data: ReelUploadRequest,
    current_user = Depends(get_current_user)
):
    """Upload reel video with filters and AR effects"""
    try:
        reel_id = str(uuid.uuid4())
        
        # Validate video data
        if not reel_data.videoData:
            raise HTTPException(status_code=400, detail="Video data is required")
        
        # Mock original video upload
        original_video_url = f"https://cdn.example.com/original_videos/{reel_id}.mp4"
        
        # Create metadata
        metadata = ReelMetadata(
            userId=current_user["id"],
            videoUrl=original_video_url,
            duration=15.0,  # Mock 15 seconds
            resolution={"width": 720, "height": 1280},
            fileSize=len(reel_data.videoData) * 3 // 4,  # Estimate from base64
            format="mp4"
        )
        
        # Process filters and effects
        filters_and_effects = ReelFiltersAndEffects(
            filters=reel_data.filters,
            arEffects=reel_data.arEffects
        )
        
        # Create reel object
        new_reel = {
            "id": reel_id,
            "userId": current_user["id"],
            "user": {k: v for k, v in current_user.items() if k not in ["password", "_id"]},
            "caption": reel_data.caption,
            "hashtags": reel_data.hashtags,
            "videoUrl": original_video_url,
            "processedVideoUrl": None,  # Will be set after processing
            "thumbnailUrl": f"https://cdn.example.com/thumbnails/{reel_id}.jpg",
            "metadata": metadata.dict(),
            "filtersAndEffects": filters_and_effects.dict(),
            "tags": reel_data.tags,
            "locationTag": reel_data.locationTag,
            "musicTrack": reel_data.musicTrack,
            "privacy": reel_data.privacy,
            "likes": [],
            "likesCount": 0,
            "comments": [],
            "commentsCount": 0,
            "shares": [],
            "sharesCount": 0,
            "views": [],
            "viewsCount": 0,
            "isProcessing": True,
            "processingStatus": "processing",
            "processingProgress": 0.0,
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
        
        # Save to database
        await db.reels.insert_one(new_reel)
        
        # Start background processing
        asyncio.create_task(process_reel_video(reel_id, reel_data.videoData, reel_data.filters, reel_data.arEffects))
        
        return {
            "success": True,
            "reelId": reel_id,
            "message": "Reel uploaded successfully, processing filters and effects...",
            "reel": {k: v for k, v in new_reel.items() if k != "_id"}
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

async def process_reel_video(reel_id: str, video_data: str, filters: List[VideoFilter], ar_effects: List[AREffect]):
    """Background task to process reel video with filters and AR effects"""
    try:
        # Update processing progress
        await db.reels.update_one(
            {"id": reel_id},
            {"$set": {"processingProgress": 25.0, "updatedAt": datetime.utcnow()}}
        )
        
        # Simulate video processing
        processed_result = await MockVideoProcessor.apply_filters_and_effects(video_data, filters, ar_effects)
        
        # Update progress to 75%
        await db.reels.update_one(
            {"id": reel_id},
            {"$set": {"processingProgress": 75.0, "updatedAt": datetime.utcnow()}}
        )
        
        # Complete processing
        await db.reels.update_one(
            {"id": reel_id},
            {"$set": {
                "processedVideoUrl": processed_result["processedVideoUrl"],
                "thumbnailUrl": processed_result["thumbnailUrl"],
                "isProcessing": False,
                "processingStatus": "completed",
                "processingProgress": 100.0,
                "updatedAt": datetime.utcnow()
            }}
        )
        
    except Exception as e:
        # Mark as failed
        await db.reels.update_one(
            {"id": reel_id},
            {"$set": {
                "isProcessing": False,
                "processingStatus": "failed",
                "processingProgress": 0.0,
                "updatedAt": datetime.utcnow()
            }}
        )

@api_router.get("/reels/processing/{reel_id}")
async def get_reel_processing_status(
    reel_id: str,
    current_user = Depends(get_current_user)
):
    """Get processing status of a reel"""
    reel = await db.reels.find_one({"id": reel_id}, {"_id": 0})
    
    if not reel:
        raise HTTPException(status_code=404, detail="Reel not found")
    
    # Check if user owns the reel or if it's public
    if reel["userId"] != current_user["id"] and reel["privacy"] != "public":
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "reelId": reel_id,
        "isProcessing": reel["isProcessing"],
        "processingStatus": reel["processingStatus"],
        "processingProgress": reel["processingProgress"],
        "processedVideoUrl": reel.get("processedVideoUrl"),
        "thumbnailUrl": reel["thumbnailUrl"]
    }

@api_router.get("/reels/filters/presets")
async def get_filter_presets():
    """Get available filter presets"""
    return {
        "filters": [filter_data.dict() for filter_data in PRESET_FILTERS.values()],
        "arEffects": [effect_data.dict() for effect_data in PRESET_AR_EFFECTS.values()]
    }

@api_router.get("/reels/feed")
async def get_reels_feed(
    skip: int = 0,
    limit: int = 20,
    current_user = Depends(get_current_user)
):
    """Get personalized reels feed"""
    # Get reels with privacy filtering
    reels_cursor = db.reels.find({
        "$or": [
            {"privacy": "public"},
            {"userId": current_user["id"]},
            {"privacy": "followers", "userId": {"$in": []}}  # TODO: Add follower logic
        ],
        "processingStatus": "completed"
    }).sort("createdAt", -1).skip(skip).limit(limit)
    
    reels = await reels_cursor.to_list(limit)
    
    # Clean up reels data
    cleaned_reels = []
    for reel in reels:
        cleaned_reel = {k: v for k, v in reel.items() if k != "_id"}
        cleaned_reels.append(cleaned_reel)
    
    return cleaned_reels

@api_router.post("/reels/{reel_id}/like")
async def toggle_reel_like(
    reel_id: str,
    current_user = Depends(get_current_user)
):
    """Toggle like on a reel"""
    reel = await db.reels.find_one({"id": reel_id})
    
    if not reel:
        raise HTTPException(status_code=404, detail="Reel not found")
    
    user_id = current_user["id"]
    likes = reel.get("likes", [])
    
    if user_id in likes:
        # Unlike
        await db.reels.update_one(
            {"id": reel_id},
            {
                "$pull": {"likes": user_id},
                "$inc": {"likesCount": -1},
                "$set": {"updatedAt": datetime.utcnow()}
            }
        )
        action = "unliked"
    else:
        # Like
        await db.reels.update_one(
            {"id": reel_id},
            {
                "$addToSet": {"likes": user_id},
                "$inc": {"likesCount": 1},
                "$set": {"updatedAt": datetime.utcnow()}
            }
        )
        action = "liked"
    
    return {"success": True, "action": action}

@api_router.post("/reels/{reel_id}/view")
async def add_reel_view(
    reel_id: str,
    current_user = Depends(get_current_user)
):
    """Add a view to a reel"""
    reel = await db.reels.find_one({"id": reel_id})
    
    if not reel:
        raise HTTPException(status_code=404, detail="Reel not found")
    
    user_id = current_user["id"]
    views = reel.get("views", [])
    
    # Only count unique views
    if user_id not in views:
        await db.reels.update_one(
            {"id": reel_id},
            {
                "$addToSet": {"views": user_id},
                "$inc": {"viewsCount": 1},
                "$set": {"updatedAt": datetime.utcnow()}
            }
        )
    
    return {"success": True, "message": "View recorded"}

@api_router.delete("/reels/{reel_id}")
async def delete_reel(
    reel_id: str,
    current_user = Depends(get_current_user)
):
    """Delete a reel"""
    reel = await db.reels.find_one({"id": reel_id})
    
    if not reel:
        raise HTTPException(status_code=404, detail="Reel not found")
    
    if reel["userId"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Can only delete your own reels")
    
    # Delete the reel
    await db.reels.delete_one({"id": reel_id})
    
    # TODO: Delete associated files from cloud storage
    
    return {"success": True, "message": "Reel deleted successfully"}

#====================================================================================================
# PHASE 19 - END-TO-END ENCRYPTED CHATS
#====================================================================================================

# Pydantic models for encrypted messaging
class EncryptedMessage(BaseModel):
    conversationId: str
    encryptedContent: str  # Base64 encoded encrypted message
    messageType: str = "text"  # "text", "image", "voice"
    nonce: str  # Base64 encoded nonce for encryption
    recipientId: str

class EncryptedMessageResponse(BaseModel):
    id: str
    conversationId: str
    senderId: str
    recipientId: str
    encryptedContent: str
    messageType: str
    nonce: str
    timestamp: datetime
    delivered: bool = False
    read: bool = False

class OfflineMessageQueue(BaseModel):
    id: str
    recipientId: str
    messages: List[EncryptedMessageResponse]
    createdAt: datetime

# Socket.IO connection manager for encrypted chats
connected_users = {}

@sio.event
async def connect(sid, environ):
    """Handle client connection"""
    print(f"Client {sid} connected")

@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    print(f"Client {sid} disconnected")
    # Remove from connected users
    user_id = None
    for uid, user_sid in connected_users.items():
        if user_sid == sid:
            user_id = uid
            break
    if user_id:
        del connected_users[user_id]

@sio.event
async def join_user(sid, data):
    """Join user to their personal room for receiving messages"""
    user_id = data.get('userId')
    if user_id:
        connected_users[user_id] = sid
        await sio.enter_room(sid, f"user_{user_id}")
        print(f"User {user_id} joined room user_{user_id}")

@sio.event
async def send_encrypted_message(sid, data):
    """Handle sending encrypted messages via Socket.IO"""
    try:
        # Validate message data
        message_data = EncryptedMessage(**data)
        
        # Store encrypted message in database
        message_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        encrypted_message = {
            "id": message_id,
            "conversationId": message_data.conversationId,
            "senderId": data.get("senderId"),
            "recipientId": message_data.recipientId,
            "encryptedContent": message_data.encryptedContent,
            "messageType": message_data.messageType,
            "nonce": message_data.nonce,
            "timestamp": now,
            "delivered": False,
            "read": False
        }
        
        await db.encrypted_messages.insert_one(encrypted_message)
        
        # Try to deliver message in real-time
        recipient_sid = connected_users.get(message_data.recipientId)
        if recipient_sid:
            # Recipient is online, deliver immediately
            await sio.emit('new_encrypted_message', {
                "id": message_id,
                "conversationId": message_data.conversationId,
                "senderId": data.get("senderId"),
                "encryptedContent": message_data.encryptedContent,
                "messageType": message_data.messageType,
                "nonce": message_data.nonce,
                "timestamp": now.isoformat()
            }, room=f"user_{message_data.recipientId}")
            
            # Mark as delivered
            await db.encrypted_messages.update_one(
                {"id": message_id},
                {"$set": {"delivered": True}}
            )
        else:
            # Recipient is offline, add to offline queue
            await add_to_offline_queue(message_data.recipientId, encrypted_message)
        
        # Confirm to sender
        await sio.emit('message_sent', {
            "messageId": message_id,
            "delivered": recipient_sid is not None
        }, room=sid)
        
    except Exception as e:
        await sio.emit('error', {"message": str(e)}, room=sid)

async def add_to_offline_queue(recipient_id: str, message: dict):
    """Add message to offline queue for later delivery"""
    # Check if offline queue exists for user
    offline_queue = await db.offline_message_queues.find_one({"recipientId": recipient_id})
    
    if offline_queue:
        # Add to existing queue
        await db.offline_message_queues.update_one(
            {"recipientId": recipient_id},
            {"$push": {"messages": message}}
        )
    else:
        # Create new queue
        queue_id = str(uuid.uuid4())
        new_queue = {
            "id": queue_id,
            "recipientId": recipient_id,
            "messages": [message],
            "createdAt": datetime.utcnow()
        }
        await db.offline_message_queues.insert_one(new_queue)

@api_router.get("/encrypted-chats/{conversation_id}/messages")
async def get_encrypted_messages(
    conversation_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user = Depends(get_current_user)
):
    """Get encrypted messages for a conversation"""
    # Verify user has access to this conversation
    conversation = await db.conversations.find_one({"id": conversation_id})
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if current_user["id"] not in conversation.get("participants", []):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get encrypted messages
    cursor = db.encrypted_messages.find(
        {"conversationId": conversation_id}
    ).sort("timestamp", -1).skip(offset).limit(limit)
    
    messages = []
    async for message in cursor:
        messages.append(EncryptedMessageResponse(**message))
    
    return {"messages": messages[::-1]}  # Return in chronological order

@api_router.post("/encrypted-chats/offline-messages")
async def get_offline_messages(current_user = Depends(get_current_user)):
    """Get and clear offline messages for current user"""
    user_id = current_user["id"]
    
    # Get offline queue
    offline_queue = await db.offline_message_queues.find_one({"recipientId": user_id})
    
    if not offline_queue:
        return {"messages": []}
    
    messages = offline_queue.get("messages", [])
    
    # Clear offline queue
    await db.offline_message_queues.delete_one({"recipientId": user_id})
    
    # Mark messages as delivered
    message_ids = [msg["id"] for msg in messages]
    await db.encrypted_messages.update_many(
        {"id": {"$in": message_ids}},
        {"$set": {"delivered": True}}
    )
    
    return {"messages": messages}

@api_router.put("/encrypted-chats/messages/{message_id}/read")
async def mark_encrypted_message_read(
    message_id: str,
    current_user = Depends(get_current_user)
):
    """Mark an encrypted message as read"""
    # Verify message belongs to current user
    message = await db.encrypted_messages.find_one({
        "id": message_id,
        "recipientId": current_user["id"]
    })
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Mark as read
    await db.encrypted_messages.update_one(
        {"id": message_id},
        {"$set": {"read": True}}
    )
    
    # Notify sender via Socket.IO
    sender_sid = connected_users.get(message["senderId"])
    if sender_sid:
        await sio.emit('message_read', {
            "messageId": message_id,
            "conversationId": message["conversationId"]
        }, room=f"user_{message['senderId']}")
    
    return {"success": True}

#====================================================================================================
# PHASE 20 - AI-BASED CAPTION & HASHTAG GENERATOR
#====================================================================================================

class CaptionGenerationRequest(BaseModel):
    mediaUrl: str
    mediaType: str = "image"  # "image" or "video"
    context: Optional[str] = None  # Optional context for better captions

class CaptionSuggestion(BaseModel):
    id: str
    caption: str
    hashtags: List[str]
    confidence: float
    category: str  # "lifestyle", "travel", "food", etc.

class CaptionGenerationResponse(BaseModel):
    suggestions: List[CaptionSuggestion]
    mediaUrl: str
    generatedAt: datetime

@api_router.post("/ai/caption")
async def generate_caption_and_hashtags(
    request: CaptionGenerationRequest,
    current_user = Depends(get_current_user)
):
    """Generate AI-powered captions and hashtags for media"""
    try:
        # Get the Emergent LLM key for AI integration
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        # Initialize AI client with Emergent LLM key
        emergent_llm_key = os.getenv("EMERGENT_LLM_KEY")
        ai_client = LlmChat(
            api_key=emergent_llm_key,
            session_id=f"caption_gen_{current_user['id']}_{str(uuid.uuid4())}",
            system_message="You are an AI assistant that generates engaging social media captions and hashtags."
        ).with_model("openai", "gpt-4o-mini")
        
        # Analyze the media content (mock analysis for now since we can't process actual images)
        media_analysis_prompt = f"""
        Analyze this {request.mediaType} and generate 3 different engaging social media captions with relevant hashtags.
        
        Media URL: {request.mediaUrl}
        Context: {request.context or "General social media post"}
        
        For each caption, provide:
        1. An engaging caption (20-50 words)
        2. 5-8 relevant hashtags
        3. A category (lifestyle, travel, food, fashion, fitness, etc.)
        4. A confidence score (0.0-1.0)
        
        Format the response as JSON with this structure:
        {
            "suggestions": [
                {
                    "caption": "Your engaging caption here...",
                    "hashtags": ["hashtag1", "hashtag2", "hashtag3"],
                    "category": "lifestyle",
                    "confidence": 0.95
                }
            ]
        }
        """
        
        # Generate captions using AI
        user_message = UserMessage(text=media_analysis_prompt)
        response = await ai_client.send_message(user_message)
        
        # Parse AI response (simplified - in production you'd have better parsing)
        import json
        try:
            ai_result = json.loads(response)
            suggestions = []
            
            for idx, suggestion in enumerate(ai_result.get("suggestions", [])):
                suggestions.append(CaptionSuggestion(
                    id=str(uuid.uuid4()),
                    caption=suggestion["caption"],
                    hashtags=suggestion["hashtags"],
                    confidence=suggestion["confidence"],
                    category=suggestion["category"]
                ))
        except:
            # Fallback suggestions if AI parsing fails
            suggestions = [
                CaptionSuggestion(
                    id=str(uuid.uuid4()),
                    caption="Capturing the moment ✨",
                    hashtags=["moment", "memories", "life", "photooftheday", "instagood"],
                    confidence=0.85,
                    category="lifestyle"
                ),
                CaptionSuggestion(
                    id=str(uuid.uuid4()),
                    caption="Living my best life! 🌟",
                    hashtags=["bestlife", "happiness", "vibes", "positivity", "blessed"],
                    confidence=0.80,
                    category="lifestyle"
                ),
                CaptionSuggestion(
                    id=str(uuid.uuid4()),
                    caption="Here's to new adventures! 🚀",
                    hashtags=["adventure", "newbeginnings", "explore", "journey", "wanderlust"],
                    confidence=0.75,
                    category="travel"
                )
            ]
        
        # Store generation history
        generation_id = str(uuid.uuid4())
        generation_record = {
            "id": generation_id,
            "userId": current_user["id"],
            "mediaUrl": request.mediaUrl,
            "mediaType": request.mediaType,
            "context": request.context,
            "suggestions": [suggestion.dict() for suggestion in suggestions],
            "generatedAt": datetime.utcnow()
        }
        
        await db.caption_generations.insert_one(generation_record)
        
        return CaptionGenerationResponse(
            suggestions=suggestions,
            mediaUrl=request.mediaUrl,
            generatedAt=datetime.utcnow()
        )
        
    except Exception as e:
        print(f"Caption generation error: {e}")
        # Return fallback captions on error
        fallback_suggestions = [
            CaptionSuggestion(
                id=str(uuid.uuid4()),
                caption="Making memories ✨",
                hashtags=["memories", "life", "moments", "photooftheday"],
                confidence=0.70,
                category="general"
            ),
            CaptionSuggestion(
                id=str(uuid.uuid4()),
                caption="Good vibes only! 🌟",
                hashtags=["goodvibes", "positivity", "happy", "blessed"],
                confidence=0.65,
                category="lifestyle"
            )
        ]
        
        return CaptionGenerationResponse(
            suggestions=fallback_suggestions,
            mediaUrl=request.mediaUrl,
            generatedAt=datetime.utcnow()
        )

@api_router.get("/ai/caption/history")
async def get_caption_generation_history(
    limit: int = 20,
    current_user = Depends(get_current_user)
):
    """Get user's caption generation history"""
    cursor = db.caption_generations.find(
        {"userId": current_user["id"]}
    ).sort("generatedAt", -1).limit(limit)
    
    history = []
    async for record in cursor:
        history.append(CaptionGenerationResponse(**record))
    
    return {"history": history}

#====================================================================================================
# PHASE 21 - STORY HIGHLIGHTS & MEMORIES
#====================================================================================================

class HighlightCreate(BaseModel):
    title: str
    coverImageUrl: str
    storyIds: List[str]
    description: Optional[str] = None

class HighlightResponse(BaseModel):
    id: str
    userId: str
    title: str
    coverImageUrl: str
    description: Optional[str]
    storyIds: List[str]
    storiesCount: int
    createdAt: datetime
    updatedAt: datetime

class MemoryResponse(BaseModel):
    id: str
    type: str  # "story", "post"
    contentId: str
    content: dict  # The actual story or post content
    originalDate: datetime  # When it was originally created
    anniversaryDate: datetime  # Current anniversary date

@api_router.post("/highlights/create")
async def create_story_highlight(
    highlight_data: HighlightCreate,
    current_user = Depends(get_current_user)
):
    """Create a new story highlight"""
    # Verify all stories belong to current user and exist
    user_id = current_user["id"]
    
    for story_id in highlight_data.storyIds:
        story = await db.stories.find_one({"id": story_id, "authorId": user_id})
        if not story:
            raise HTTPException(
                status_code=400, 
                detail=f"Story {story_id} not found or doesn't belong to you"
            )
    
    # Create highlight
    highlight_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    highlight = {
        "id": highlight_id,
        "userId": user_id,
        "title": highlight_data.title,
        "coverImageUrl": highlight_data.coverImageUrl,
        "description": highlight_data.description,
        "storyIds": highlight_data.storyIds,
        "storiesCount": len(highlight_data.storyIds),
        "createdAt": now,
        "updatedAt": now
    }
    
    await db.highlights.insert_one(highlight)
    
    return HighlightResponse(**highlight)

@api_router.get("/highlights/fetch")
async def get_user_highlights(
    user_id: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """Get highlights for a user (current user if no user_id specified)"""
    target_user_id = user_id or current_user["id"]
    
    cursor = db.highlights.find({"userId": target_user_id}).sort("createdAt", -1)
    
    highlights = []
    async for highlight in cursor:
        highlights.append(HighlightResponse(**highlight))
    
    return {"highlights": highlights}

@api_router.put("/highlights/{highlight_id}")
async def update_highlight(
    highlight_id: str,
    highlight_data: HighlightCreate,
    current_user = Depends(get_current_user)
):
    """Update an existing highlight"""
    # Verify highlight belongs to current user
    highlight = await db.highlights.find_one({
        "id": highlight_id,
        "userId": current_user["id"]
    })
    
    if not highlight:
        raise HTTPException(status_code=404, detail="Highlight not found")
    
    # Verify all stories belong to current user
    for story_id in highlight_data.storyIds:
        story = await db.stories.find_one({"id": story_id, "authorId": current_user["id"]})
        if not story:
            raise HTTPException(
                status_code=400,
                detail=f"Story {story_id} not found or doesn't belong to you"
            )
    
    # Update highlight
    update_data = {
        "title": highlight_data.title,
        "coverImageUrl": highlight_data.coverImageUrl,
        "description": highlight_data.description,
        "storyIds": highlight_data.storyIds,
        "storiesCount": len(highlight_data.storyIds),
        "updatedAt": datetime.utcnow()
    }
    
    await db.highlights.update_one(
        {"id": highlight_id},
        {"$set": update_data}
    )
    
    # Return updated highlight
    updated_highlight = await db.highlights.find_one({"id": highlight_id})
    return HighlightResponse(**updated_highlight)

@api_router.delete("/highlights/{highlight_id}")
async def delete_highlight(
    highlight_id: str,
    current_user = Depends(get_current_user)
):
    """Delete a highlight"""
    result = await db.highlights.delete_one({
        "id": highlight_id,
        "userId": current_user["id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Highlight not found")
    
    return {"success": True, "message": "Highlight deleted"}

@api_router.get("/memories/fetch")
async def get_memories(
    date: Optional[str] = None,  # Format: YYYY-MM-DD
    current_user = Depends(get_current_user)
):
    """Get memories for a specific date or today's date"""
    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        target_date = datetime.utcnow()
    
    user_id = current_user["id"]
    
    # Calculate date range for memories (same day in previous years)
    current_year = target_date.year
    target_day = target_date.day
    target_month = target_date.month
    
    memories = []
    
    # Look for memories from previous years (up to 5 years back)
    for year_offset in range(1, 6):
        memory_year = current_year - year_offset
        
        try:
            memory_date_start = datetime(memory_year, target_month, target_day)
            memory_date_end = datetime(memory_year, target_month, target_day, 23, 59, 59)
            
            # Find stories from this date
            story_cursor = db.stories.find({
                "authorId": user_id,
                "createdAt": {
                    "$gte": memory_date_start,
                    "$lte": memory_date_end
                }
            })
            
            async for story in story_cursor:
                memories.append(MemoryResponse(
                    id=str(uuid.uuid4()),
                    type="story",
                    contentId=story["id"],
                    content=story,
                    originalDate=story["createdAt"],
                    anniversaryDate=target_date
                ))
            
            # Find posts from this date
            post_cursor = db.posts.find({
                "authorId": user_id,
                "createdAt": {
                    "$gte": memory_date_start,
                    "$lte": memory_date_end
                }
            })
            
            async for post in post_cursor:
                memories.append(MemoryResponse(
                    id=str(uuid.uuid4()),
                    type="post",
                    contentId=post["id"],
                    content=post,
                    originalDate=post["createdAt"],
                    anniversaryDate=target_date
                ))
                
        except ValueError:
            # Skip February 29th for non-leap years
            continue
    
    # Sort memories by original date
    memories.sort(key=lambda x: x.originalDate, reverse=True)
    
    return {"memories": memories, "date": date or target_date.strftime("%Y-%m-%d")}

#====================================================================================================
# PHASE 22 - LIVE VIDEO STREAMING
#====================================================================================================

class LiveStreamCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category: str = "general"
    isPrivate: bool = False
    maxViewers: Optional[int] = None

class LiveStreamResponse(BaseModel):
    id: str
    userId: str
    title: str
    description: Optional[str]
    category: str
    isPrivate: bool
    maxViewers: Optional[int]
    streamKey: str
    rtmpUrl: str
    playbackUrl: str
    status: str  # "preparing", "live", "ended"
    viewerCount: int
    totalViewers: int
    startedAt: Optional[datetime]
    endedAt: Optional[datetime]
    createdAt: datetime

class LiveStreamViewer(BaseModel):
    userId: str
    username: str
    joinedAt: datetime

# Live stream management
active_streams = {}  # stream_id -> {viewers: set(), chat_room: str}

@api_router.post("/live/start")
async def start_live_stream(
    stream_data: LiveStreamCreate,
    current_user = Depends(get_current_user)
):
    """Start a new live stream"""
    # Check if user already has an active stream
    existing_stream = await db.live_streams.find_one({
        "userId": current_user["id"],
        "status": {"$in": ["preparing", "live"]}
    })
    
    if existing_stream:
        raise HTTPException(
            status_code=400, 
            detail="You already have an active stream"
        )
    
    # Create stream record
    stream_id = str(uuid.uuid4())
    stream_key = str(uuid.uuid4())
    now = datetime.utcnow()
    
    # Mock RTMP URLs (in production, use actual streaming service)
    rtmp_url = f"rtmp://streaming-server.example.com/live/{stream_key}"
    playback_url = f"https://streaming-server.example.com/hls/{stream_id}/playlist.m3u8"
    
    stream = {
        "id": stream_id,
        "userId": current_user["id"],
        "title": stream_data.title,
        "description": stream_data.description,
        "category": stream_data.category,
        "isPrivate": stream_data.isPrivate,
        "maxViewers": stream_data.maxViewers,
        "streamKey": stream_key,
        "rtmpUrl": rtmp_url,
        "playbackUrl": playback_url,
        "status": "preparing",
        "viewerCount": 0,
        "totalViewers": 0,
        "startedAt": None,
        "endedAt": None,
        "createdAt": now
    }
    
    await db.live_streams.insert_one(stream)
    
    # Initialize stream in memory
    active_streams[stream_id] = {
        "viewers": set(),
        "chat_room": f"live_stream_{stream_id}"
    }
    
    return LiveStreamResponse(**stream)

@api_router.put("/live/{stream_id}/go-live")
async def go_live(
    stream_id: str,
    current_user = Depends(get_current_user)
):
    """Mark stream as live (called when RTMP connection starts)"""
    stream = await db.live_streams.find_one({
        "id": stream_id,
        "userId": current_user["id"]
    })
    
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    if stream["status"] != "preparing":
        raise HTTPException(status_code=400, detail="Stream is not in preparing state")
    
    # Update stream status
    now = datetime.utcnow()
    await db.live_streams.update_one(
        {"id": stream_id},
        {
            "$set": {
                "status": "live",
                "startedAt": now
            }
        }
    )
    
    # Notify followers that stream is live (simplified notification)
    # In production, you'd send push notifications to followers
    
    return {"success": True, "message": "Stream is now live"}

@api_router.get("/live/{stream_id}")
async def get_live_stream(stream_id: str):
    """Get live stream details"""
    stream = await db.live_streams.find_one({"id": stream_id})
    
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    # Update viewer count from active streams
    if stream_id in active_streams:
        stream["viewerCount"] = len(active_streams[stream_id]["viewers"])
    
    return LiveStreamResponse(**stream)

@api_router.post("/live/{stream_id}/join")
async def join_live_stream(
    stream_id: str,
    current_user = Depends(get_current_user)
):
    """Join a live stream as a viewer"""
    stream = await db.live_streams.find_one({"id": stream_id})
    
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    if stream["status"] != "live":
        raise HTTPException(status_code=400, detail="Stream is not live")
    
    # Check if private stream and user has permission
    if stream["isPrivate"]:
        # Add permission logic here (follow check, etc.)
        pass
    
    # Check max viewers limit
    if stream.get("maxViewers"):
        current_viewers = len(active_streams.get(stream_id, {}).get("viewers", set()))
        if current_viewers >= stream["maxViewers"]:
            raise HTTPException(status_code=400, detail="Stream is at maximum capacity")
    
    # Add viewer to active stream
    user_id = current_user["id"]
    if stream_id not in active_streams:
        active_streams[stream_id] = {"viewers": set(), "chat_room": f"live_stream_{stream_id}"}
    
    active_streams[stream_id]["viewers"].add(user_id)
    
    # Update total viewers count
    await db.live_streams.update_one(
        {"id": stream_id},
        {
            "$inc": {"totalViewers": 1},
            "$set": {"viewerCount": len(active_streams[stream_id]["viewers"])}
        }
    )
    
    # Add viewer to chat room via Socket.IO
    user_sid = connected_users.get(user_id)
    if user_sid:
        await sio.enter_room(user_sid, active_streams[stream_id]["chat_room"])
    
    return {
        "success": True,
        "playbackUrl": stream["playbackUrl"],
        "chatRoom": active_streams[stream_id]["chat_room"]
    }

@api_router.post("/live/{stream_id}/leave")
async def leave_live_stream(
    stream_id: str,
    current_user = Depends(get_current_user)
):
    """Leave a live stream"""
    user_id = current_user["id"]
    
    if stream_id in active_streams and user_id in active_streams[stream_id]["viewers"]:
        active_streams[stream_id]["viewers"].remove(user_id)
        
        # Update viewer count
        await db.live_streams.update_one(
            {"id": stream_id},
            {"$set": {"viewerCount": len(active_streams[stream_id]["viewers"])}}
        )
        
        # Remove from chat room
        user_sid = connected_users.get(user_id)
        if user_sid:
            await sio.leave_room(user_sid, active_streams[stream_id]["chat_room"])
    
    return {"success": True}

@api_router.put("/live/{stream_id}/end")
async def end_live_stream(
    stream_id: str,
    current_user = Depends(get_current_user)
):
    """End a live stream"""
    stream = await db.live_streams.find_one({
        "id": stream_id,
        "userId": current_user["id"]
    })
    
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    if stream["status"] != "live":
        raise HTTPException(status_code=400, detail="Stream is not live")
    
    # Update stream status
    now = datetime.utcnow()
    await db.live_streams.update_one(
        {"id": stream_id},
        {
            "$set": {
                "status": "ended",
                "endedAt": now,
                "viewerCount": 0
            }
        }
    )
    
    # Clean up active stream
    if stream_id in active_streams:
        # Notify all viewers that stream ended
        chat_room = active_streams[stream_id]["chat_room"]
        await sio.emit('stream_ended', {
            "streamId": stream_id,
            "message": "The live stream has ended"
        }, room=chat_room)
        
        del active_streams[stream_id]
    
    return {"success": True, "message": "Stream ended"}

@api_router.get("/live/active")
async def get_active_streams(
    category: Optional[str] = None,
    limit: int = 20
):
    """Get list of active live streams"""
    query = {"status": "live"}
    if category:
        query["category"] = category
    
    cursor = db.live_streams.find(query).sort("startedAt", -1).limit(limit)
    
    streams = []
    async for stream in cursor:
        # Update viewer count from active streams
        if stream["id"] in active_streams:
            stream["viewerCount"] = len(active_streams[stream["id"]]["viewers"])
        
        streams.append(LiveStreamResponse(**stream))
    
    return {"streams": streams}

# Live stream chat via Socket.IO
@sio.event
async def send_live_chat_message(sid, data):
    """Send message in live stream chat"""
    try:
        stream_id = data.get("streamId")
        message = data.get("message")
        user_id = data.get("userId")
        
        if not all([stream_id, message, user_id]):
            await sio.emit('error', {"message": "Missing required fields"}, room=sid)
            return
        
        # Verify stream exists and is live
        stream = await db.live_streams.find_one({"id": stream_id, "status": "live"})
        if not stream:
            await sio.emit('error', {"message": "Stream not found or not live"}, room=sid)
            return
        
        # Verify user is in the stream
        if stream_id not in active_streams or user_id not in active_streams[stream_id]["viewers"]:
            await sio.emit('error', {"message": "You are not viewing this stream"}, room=sid)
            return
        
        # Get user info
        user = await db.users.find_one({"id": user_id})
        if not user:
            await sio.emit('error', {"message": "User not found"}, room=sid)
            return
        
        # Broadcast message to all viewers
        chat_message = {
            "id": str(uuid.uuid4()),
            "userId": user_id,
            "username": user["username"],
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await sio.emit('live_chat_message', chat_message, 
                      room=active_streams[stream_id]["chat_room"])
        
    except Exception as e:
        await sio.emit('error', {"message": str(e)}, room=sid)

# Export the Socket.IO ASGI app for uvicorn
# This enables Socket.IO functionality
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(socket_app, host="0.0.0.0", port=8001)