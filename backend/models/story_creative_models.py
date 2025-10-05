from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from .user_models import UserResponse


# Phase 17: Story & Creative Tools Models

class StorySticker(BaseModel):
    id: Optional[str] = None
    storyId: str
    type: str  # "location", "mention", "music", "photo", "whatsapp", "gif", "frame", "question", "notify", "cutout", "avatar", "poll", "quiz", "link", "hashtag", "countdown", "like_percentage"
    data: Dict[str, Any]  # Sticker-specific data
    position: Dict[str, float]  # {"x": float, "y": float, "rotation": float, "scale": float}
    zIndex: int = 0  # Layer ordering
    isInteractive: bool = False  # For polls, questions, etc.
    expiresAt: Optional[datetime] = None  # For countdown stickers
    createdAt: datetime


class MusicLibraryItem(BaseModel):
    id: str
    title: str
    artist: str
    duration: int  # Duration in seconds
    previewUrl: Optional[str] = None
    albumArt: Optional[str] = None
    genre: Optional[str] = None
    isPopular: bool = False
    category: str = "trending"  # "trending", "new", "pop", "hip-hop", etc.


class GIFLibraryItem(BaseModel):
    id: str
    title: str
    url: str
    thumbnailUrl: str
    width: int
    height: int
    category: str
    tags: List[str] = []
    isPopular: bool = False


class FrameTemplate(BaseModel):
    id: str
    name: str
    category: str  # "borders", "vintage", "modern", "seasonal"
    previewUrl: str
    frameData: Dict[str, Any]  # SVG or image data
    isPremium: bool = False


class TextStyle(BaseModel):
    id: Optional[str] = None
    fontFamily: str = "system"
    fontSize: int = 24
    fontWeight: str = "normal"  # "normal", "bold", "light"
    color: str = "#ffffff"
    backgroundColor: Optional[str] = None
    borderColor: Optional[str] = None
    borderWidth: int = 0
    shadowColor: Optional[str] = None
    shadowOffset: Dict[str, int] = {"x": 0, "y": 0}
    shadowBlur: int = 0
    textAlign: str = "center"  # "left", "center", "right"
    lineHeight: float = 1.2
    letterSpacing: float = 0
    textTransform: str = "none"  # "none", "uppercase", "lowercase", "capitalize"
    animation: Optional[str] = None  # "fade", "slide", "bounce", "typewriter"


class ColorPalette(BaseModel):
    id: str
    name: str
    colors: List[str]  # Hex color codes
    category: str = "general"
    isGradient: bool = False


class InteractiveElement(BaseModel):
    id: Optional[str] = None
    storyId: str
    type: str  # "poll", "quiz", "question", "slider", "countdown", "like_percentage"
    question: str
    options: Optional[List[str]] = None  # For polls/quiz
    correctAnswer: Optional[int] = None  # For quiz (index of correct option)
    responses: List[Dict[str, Any]] = []  # User responses
    expiresAt: Optional[datetime] = None
    isActive: bool = True
    createdAt: datetime


class CollaborativePrompt(BaseModel):
    id: Optional[str] = None
    creatorId: str
    creator: Optional[UserResponse] = None
    promptText: str
    template: Optional[Dict[str, Any]] = None
    participants: List[str] = []  # User IDs who participated
    responses: List[Dict[str, Any]] = []
    maxParticipants: Optional[int] = None
    expiresAt: Optional[datetime] = None
    category: str = "general"
    tags: List[str] = []
    isActive: bool = True
    createdAt: datetime


class ECommerceLink(BaseModel):
    id: Optional[str] = None
    storyId: str
    productName: str
    productUrl: str
    price: Optional[str] = None
    currency: str = "USD"
    imageUrl: Optional[str] = None
    description: Optional[str] = None
    merchantName: Optional[str] = None
    category: Optional[str] = None


class StoryTemplate(BaseModel):
    id: str
    name: str
    category: str  # "business", "personal", "creative", "holiday"
    previewUrl: str
    elements: List[Dict[str, Any]]  # Pre-positioned elements
    isPremium: bool = False
    usageCount: int = 0


class StickerCreate(BaseModel):
    storyId: str
    type: str
    data: Dict[str, Any]
    position: Dict[str, float]
    zIndex: Optional[int] = 0
    isInteractive: Optional[bool] = False
    expiresAt: Optional[datetime] = None


class StickerUpdate(BaseModel):
    position: Optional[Dict[str, float]] = None
    data: Optional[Dict[str, Any]] = None
    zIndex: Optional[int] = None


class TextStyleCreate(BaseModel):
    fontFamily: Optional[str] = "system"
    fontSize: Optional[int] = 24
    fontWeight: Optional[str] = "normal"
    color: Optional[str] = "#ffffff"
    backgroundColor: Optional[str] = None
    textAlign: Optional[str] = "center"
    animation: Optional[str] = None


class InteractiveElementCreate(BaseModel):
    storyId: str
    type: str
    question: str
    options: Optional[List[str]] = None
    correctAnswer: Optional[int] = None
    expiresAt: Optional[datetime] = None


class InteractiveResponse(BaseModel):
    elementId: str
    response: Dict[str, Any]  # Flexible response data


class CollaborativePromptCreate(BaseModel):
    promptText: str
    template: Optional[Dict[str, Any]] = None
    maxParticipants: Optional[int] = None
    expiresAt: Optional[datetime] = None
    category: Optional[str] = "general"
    tags: Optional[List[str]] = []


class PromptParticipation(BaseModel):
    promptId: str
    response: Dict[str, Any]


# Mock data for creative tools
MOCK_MUSIC_LIBRARY = [
    {
        "id": "music_1",
        "title": "Upbeat Summer",
        "artist": "Audio Library",
        "duration": 30,
        "genre": "Pop",
        "category": "trending",
        "isPopular": True
    },
    {
        "id": "music_2", 
        "title": "Chill Vibes",
        "artist": "Lofi Beats",
        "duration": 45,
        "genre": "Lofi",
        "category": "chill",
        "isPopular": True
    },
    {
        "id": "music_3",
        "title": "Epic Adventure",
        "artist": "Cinematic Sounds", 
        "duration": 60,
        "genre": "Cinematic",
        "category": "epic",
        "isPopular": False
    }
]

MOCK_GIF_LIBRARY = [
    {
        "id": "gif_1",
        "title": "Happy Dance",
        "url": "https://media.giphy.com/media/l3q2K5jinAlChoCLS/giphy.gif",
        "thumbnailUrl": "https://media.giphy.com/media/l3q2K5jinAlChoCLS/200_s.gif",
        "width": 480,
        "height": 270,
        "category": "emotions",
        "tags": ["happy", "dance", "celebration"],
        "isPopular": True
    },
    {
        "id": "gif_2",
        "title": "Mind Blown",
        "url": "https://media.giphy.com/media/xT0xeJpnrWC4XWblEk/giphy.gif", 
        "thumbnailUrl": "https://media.giphy.com/media/xT0xeJpnrWC4XWblEk/200_s.gif",
        "width": 480,
        "height": 270,
        "category": "reactions",
        "tags": ["wow", "amazed", "reaction"],
        "isPopular": True
    }
]

MOCK_FRAMES = [
    {
        "id": "frame_1",
        "name": "Classic Border",
        "category": "borders",
        "previewUrl": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjMDAwIiBzdHJva2Utd2lkdGg9IjEwIi8+PC9zdmc+",
        "frameData": {"type": "border", "width": 10, "color": "#000000"},
        "isPremium": False
    },
    {
        "id": "frame_2", 
        "name": "Vintage Frame",
        "category": "vintage",
        "previewUrl": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjOEI0NTEzIiBzdHJva2Utd2lkdGg9IjE1IiBzdHJva2UtZGFzaGFycmF5PSI1LDUiLz48L3N2Zz4=",
        "frameData": {"type": "vintage", "width": 15, "color": "#8B4513"},
        "isPremium": True
    }
]

MOCK_COLOR_PALETTES = [
    {
        "id": "palette_1",
        "name": "Ocean Blues",
        "colors": ["#000080", "#0066CC", "#0099FF", "#66CCFF", "#B3E5FF"],
        "category": "blues"
    },
    {
        "id": "palette_2",
        "name": "Sunset Vibes", 
        "colors": ["#FF6B35", "#F7931E", "#FFD23F", "#FFF056", "#FFEF9F"],
        "category": "warm"
    },
    {
        "id": "palette_3",
        "name": "Nature Greens",
        "colors": ["#2E8B57", "#3CB371", "#90EE90", "#98FB98", "#F0FFF0"],
        "category": "greens"
    }
]