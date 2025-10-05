# Phase 18: Video Filters & AR Effects for Reels Models

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

class VideoFilter(BaseModel):
    """Video filter configuration"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # brightness, contrast, sepia, blur, vignette, etc.
    type: str  # "adjustment" or "effect"
    parameters: Dict[str, float]  # filter parameters (e.g., intensity: 0.5)
    presetName: Optional[str] = None  # preset filter name
    
class AREffect(BaseModel):
    """AR effect configuration"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # face_tracking, sticker_overlay, mask, etc.
    type: str  # "face_tracking", "sticker", "mask", "animation"
    assetUrl: Optional[str] = None  # URL to AR asset/sticker
    position: Optional[Dict[str, float]] = None  # x, y coordinates
    scale: Optional[float] = 1.0
    rotation: Optional[float] = 0.0
    parameters: Dict[str, Any] = {}  # additional AR parameters

class ReelMetadata(BaseModel):
    """Reel video metadata"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    userId: str
    videoUrl: str  # URL to the uploaded video file
    thumbnailUrl: Optional[str] = None
    duration: float  # video duration in seconds
    resolution: Dict[str, int]  # width, height
    fileSize: int  # in bytes
    format: str = "mp4"  # video format
    
class ReelFiltersAndEffects(BaseModel):
    """Applied filters and AR effects to a reel"""
    filters: List[VideoFilter] = []
    arEffects: List[AREffect] = []
    processingVersion: str = "1.0"  # version of processing pipeline
    
class Reel(BaseModel):
    """Enhanced Reel model with filters and AR effects"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    userId: str
    user: Optional[Dict[str, Any]] = None  # populated user data
    caption: str = ""
    hashtags: List[str] = []
    videoUrl: str  # original video URL
    processedVideoUrl: Optional[str] = None  # URL with filters/effects applied
    thumbnailUrl: str
    metadata: ReelMetadata
    filtersAndEffects: ReelFiltersAndEffects
    tags: List[str] = []  # user tags
    locationTag: Optional[Dict[str, Any]] = None
    musicTrack: Optional[Dict[str, Any]] = None  # background music
    privacy: str = "public"  # public, followers, private
    
    # Engagement
    likes: List[str] = []  # user IDs who liked
    likesCount: int = 0
    comments: List[str] = []  # comment IDs
    commentsCount: int = 0
    shares: List[str] = []  # user IDs who shared
    sharesCount: int = 0
    views: List[str] = []  # user IDs who viewed
    viewsCount: int = 0
    
    # Status
    isProcessing: bool = False  # true while applying filters/effects
    processingStatus: str = "completed"  # queued, processing, completed, failed
    processingProgress: float = 100.0  # 0-100%
    
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

class ReelUploadRequest(BaseModel):
    """Request model for uploading reel with filters and effects"""
    videoData: str  # base64 encoded video
    caption: str = ""
    hashtags: List[str] = []
    tags: List[str] = []
    locationTag: Optional[Dict[str, Any]] = None
    musicTrack: Optional[Dict[str, Any]] = None
    filters: List[VideoFilter] = []
    arEffects: List[AREffect] = []
    privacy: str = "public"

class ReelProcessingUpdate(BaseModel):
    """Model for updating reel processing status"""
    reelId: str
    status: str  # queued, processing, completed, failed
    progress: float  # 0-100%
    processedVideoUrl: Optional[str] = None
    error: Optional[str] = None

# Preset filter configurations
PRESET_FILTERS = {
    "vintage": VideoFilter(
        name="vintage",
        type="effect",
        parameters={
            "sepia": 0.7,
            "contrast": 1.2,
            "vignette": 0.4,
            "noise": 0.1
        },
        presetName="vintage"
    ),
    "dramatic": VideoFilter(
        name="dramatic",
        type="adjustment",
        parameters={
            "contrast": 1.5,
            "brightness": 0.9,
            "saturation": 1.3,
            "shadows": 0.7
        },
        presetName="dramatic"
    ),
    "soft_glow": VideoFilter(
        name="soft_glow",
        type="effect",
        parameters={
            "blur": 0.3,
            "brightness": 1.1,
            "glow_intensity": 0.6
        },
        presetName="soft_glow"
    ),
    "black_white": VideoFilter(
        name="black_white",
        type="adjustment",
        parameters={
            "saturation": 0.0,
            "contrast": 1.2
        },
        presetName="black_white"
    )
}

# Preset AR effects
PRESET_AR_EFFECTS = {
    "heart_eyes": AREffect(
        name="heart_eyes",
        type="face_tracking",
        assetUrl="/ar_assets/heart_eyes.png",
        parameters={
            "facial_landmark": "eyes",
            "tracking_confidence": 0.8
        }
    ),
    "dog_ears": AREffect(
        name="dog_ears",
        type="face_tracking", 
        assetUrl="/ar_assets/dog_ears.png",
        parameters={
            "facial_landmark": "head_top",
            "tracking_confidence": 0.7
        }
    ),
    "sparkles": AREffect(
        name="sparkles",
        type="animation",
        assetUrl="/ar_assets/sparkles.json",
        parameters={
            "animation_duration": 2.0,
            "particle_count": 50
        }
    )
}