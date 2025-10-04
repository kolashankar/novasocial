from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime


class UserSettings(BaseModel):
    userId: str
    # Privacy Settings
    profilePrivacy: str = "public"  # "public", "private"
    storiesPrivacy: str = "followers"  # "public", "followers", "close_friends"
    whoCanMessage: str = "everyone"  # "everyone", "followers", "following", "none"
    whoCanTag: str = "everyone"  # "everyone", "followers", "none"
    whoCanMention: str = "everyone"  # "everyone", "followers", "none"
    
    # Notification Settings
    pushNotifications: bool = True
    emailNotifications: bool = True
    smsNotifications: bool = False
    
    # Specific Notification Types
    notifyLikes: bool = True
    notifyComments: bool = True
    notifyFollows: bool = True
    notifyMentions: bool = True
    notifyMessages: bool = True
    notifyStoryViews: bool = False
    
    # Content Settings
    autoPlayVideos: bool = True
    showSensitiveContent: bool = False
    dataUsage: str = "wifi_only"  # "wifi_only", "wifi_and_cellular", "never"
    
    # Language and Region
    language: str = "en"
    timezone: str = "UTC"
    dateFormat: str = "MM/DD/YYYY"
    timeFormat: str = "12h"  # "12h", "24h"
    
    # Accessibility
    fontSize: str = "medium"  # "small", "medium", "large", "extra_large"
    highContrast: bool = False
    reduceMotion: bool = False
    screenReader: bool = False
    
    # Safety and Security
    twoFactorEnabled: bool = False
    loginNotifications: bool = True
    showActiveStatus: bool = True
    allowLocationSharing: bool = False
    
    # Content Preferences
    interests: List[str] = []
    blockedKeywords: List[str] = []
    
    createdAt: datetime
    updatedAt: datetime


class NotificationSettings(BaseModel):
    # Push Notification Settings
    pushEnabled: bool = True
    quietHours: Optional[Dict[str, str]] = None  # {"start": "22:00", "end": "08:00"}
    
    # Email Settings
    emailDigest: str = "weekly"  # "never", "daily", "weekly", "monthly"
    marketingEmails: bool = False
    
    # Mobile Settings
    vibration: bool = True
    sound: bool = True
    badge: bool = True


class PrivacySettings(BaseModel):
    # Account Privacy
    isPrivate: bool = False
    approveFollowers: bool = False
    
    # Content Privacy
    hideLikesCounts: bool = False
    hideFollowersCount: bool = False
    hideLastSeen: bool = False
    
    # Story Privacy
    storyViewers: str = "followers"  # "public", "followers", "close_friends", "custom"
    allowStoryReshare: bool = True
    
    # Search Privacy
    indexProfile: bool = True  # Allow profile to be found in search engines
    suggestAccount: bool = True  # Suggest account to others


class BlockedUser(BaseModel):
    id: str
    userId: str  # User who blocked
    blockedUserId: str  # User who was blocked
    blockedUser: Optional[dict] = None  # User info
    reason: Optional[str] = None
    createdAt: datetime


class ReportedContent(BaseModel):
    id: str
    reporterId: str  # User who reported
    reporter: Optional[dict] = None
    contentType: str  # "post", "comment", "user", "message"
    contentId: str
    reason: str  # "spam", "harassment", "inappropriate", "violence", etc.
    description: Optional[str] = None
    status: str = "pending"  # "pending", "reviewed", "resolved", "dismissed"
    createdAt: datetime
    resolvedAt: Optional[datetime] = None


class DeviceInfo(BaseModel):
    id: str
    userId: str
    deviceType: str  # "ios", "android", "web"
    deviceName: str
    deviceId: str  # Unique device identifier
    pushToken: Optional[str] = None  # For push notifications
    appVersion: str
    osVersion: str
    isActive: bool = True
    lastSeen: datetime
    createdAt: datetime
