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

# Create the main app without a prefix
app = FastAPI()

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


# Original routes
@api_router.get("/")
async def root():
    return {"message": "NovaSocial API"}

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
