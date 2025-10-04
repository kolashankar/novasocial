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

# Start cleanup task
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_expired_stories())

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
