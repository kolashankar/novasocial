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
