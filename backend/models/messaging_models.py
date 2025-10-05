from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .user_models import UserResponse


class ConversationCreate(BaseModel):
    participantIds: List[str]
    isGroup: bool = False
    name: Optional[str] = None
    description: Optional[str] = None
    groupImage: Optional[str] = None  # base64 for group photo


class MessageCreate(BaseModel):
    conversationId: str
    text: Optional[str] = None
    messageType: str = "text"  # "text", "image", "video", "emoji", "audio", "file"
    media: Optional[str] = None  # base64 encoded media
    fileName: Optional[str] = None  # For file messages
    fileSize: Optional[int] = None  # File size in bytes
    replyTo: Optional[str] = None  # Reply to message ID
    forwardedFrom: Optional[str] = None  # Original message ID if forwarded


class MessageResponse(BaseModel):
    id: str
    conversationId: str
    senderId: str
    sender: UserResponse
    text: Optional[str]
    messageType: str
    media: Optional[str]
    fileName: Optional[str]
    fileSize: Optional[int]
    replyTo: Optional[str]
    forwardedFrom: Optional[str]
    readBy: List[dict]  # [{"userId": str, "readAt": datetime}]
    deliveredTo: List[dict]  # [{"userId": str, "deliveredAt": datetime}]
    isEdited: bool
    editedAt: Optional[datetime]
    createdAt: datetime
    updatedAt: datetime


class ConversationResponse(BaseModel):
    id: str
    participantIds: List[str]
    participants: List[UserResponse]
    isGroup: bool
    name: Optional[str]
    description: Optional[str]
    groupImage: Optional[str]
    lastMessage: Optional[MessageResponse]
    unreadCount: int
    isArchived: bool
    isMuted: bool
    muteUntil: Optional[datetime]
    createdAt: datetime
    updatedAt: datetime


class TypingIndicator(BaseModel):
    conversationId: str
    userId: str
    isTyping: bool


class MessageEdit(BaseModel):
    messageId: str
    newText: str


class MessageDelete(BaseModel):
    messageId: str
    deleteForEveryone: bool = False


class ConversationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    groupImage: Optional[str] = None


# Phase 14 - Enhanced Messaging Models
class MessageStatus(BaseModel):
    id: Optional[str] = None
    messageId: str
    userId: str
    status: str  # "sent", "delivered", "read"
    timestamp: datetime


class UserActivity(BaseModel):
    id: Optional[str] = None
    userId: str
    status: str  # "online", "offline", "away", "busy"
    lastSeen: datetime
    deviceInfo: Optional[str] = None
    socketId: Optional[str] = None
    isTyping: bool = False
    typingIn: Optional[str] = None  # conversationId if typing


class ChatFilter(BaseModel):
    id: Optional[str] = None
    userId: str
    filterType: str  # "all", "unread", "groups", "direct", "archived", "muted"
    searchQuery: Optional[str] = None
    isActive: bool = True
    lastUsed: datetime


class MessageDeliveryStatus(BaseModel):
    messageId: str
    status: str  # "sent", "delivered", "read"
    userId: str
    timestamp: datetime


class OnlineStatus(BaseModel):
    userId: str
    isOnline: bool
    lastSeen: datetime
    status: str = "online"  # "online", "offline", "away", "busy"


class MessageFilter(BaseModel):
    filterType: str = "all"  # "all", "unread", "groups", "direct"
    searchQuery: Optional[str] = None
    participantIds: Optional[List[str]] = None


class ConversationSettings(BaseModel):
    conversationId: str
    isArchived: bool = False
    isMuted: bool = False
    muteUntil: Optional[datetime] = None
    customNotificationSound: Optional[str] = None
    isBlocked: bool = False


class MessageQueue(BaseModel):
    id: Optional[str] = None
    userId: str
    conversationId: str
    messageData: dict
    retryCount: int = 0
    maxRetries: int = 3
    nextRetryAt: Optional[datetime] = None
    createdAt: datetime
    status: str = "pending"  # "pending", "sent", "failed"
