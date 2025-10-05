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

# Original routes
@api_router.get("/")
async def root():
    return {"message": "NovaSocial API - Phases 1-7 Complete"}

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

# Export the Socket.IO ASGI app for uvicorn
# This enables Socket.IO functionality
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(socket_app, host="0.0.0.0", port=8001)