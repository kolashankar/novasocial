from typing import List, Dict, Optional
from datetime import datetime
import asyncio
import logging
from ..models.settings_models import NotificationSettings
from ..models.engagement_models import NotificationCreate, NotificationResponse

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for handling push notifications and in-app notifications"""
    
    def __init__(self, db):
        self.db = db
    
    async def create_notification(
        self,
        recipient_id: str,
        sender_id: Optional[str],
        notification_type: str,
        title: str,
        message: str,
        related_id: Optional[str] = None,
        related_type: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """Create a new notification"""
        try:
            notification_id = self._generate_id()
            
            notification = {
                "id": notification_id,
                "recipientId": recipient_id,
                "senderId": sender_id,
                "type": notification_type,
                "title": title,
                "message": message,
                "relatedId": related_id,
                "relatedType": related_type,
                "metadata": metadata or {},
                "isRead": False,
                "createdAt": datetime.utcnow()
            }
            
            await self.db.notifications.insert_one(notification)
            
            # Check user's notification settings
            settings = await self._get_notification_settings(recipient_id)
            
            if settings and self._should_send_notification(settings, notification_type):
                # Send push notification
                await self._send_push_notification(recipient_id, notification)
            
            return notification_id
            
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            raise
    
    async def _get_notification_settings(self, user_id: str) -> Optional[Dict]:
        """Get user's notification preferences"""
        user = await self.db.users.find_one({"id": user_id})
        if user:
            return user.get("notificationSettings", {})
        return None
    
    def _should_send_notification(self, settings: Dict, notification_type: str) -> bool:
        """Check if notification should be sent based on user settings"""
        if not settings.get("pushNotifications", True):
            return False
        
        type_settings = {
            "like": settings.get("notifyLikes", True),
            "comment": settings.get("notifyComments", True),
            "follow": settings.get("notifyFollows", True),
            "mention": settings.get("notifyMentions", True),
            "message": settings.get("notifyMessages", True),
            "story_view": settings.get("notifyStoryViews", False)
        }
        
        return type_settings.get(notification_type, True)
    
    async def _send_push_notification(self, user_id: str, notification: Dict):
        """Send push notification to user's devices"""
        try:
            # Get user's active devices with push tokens
            devices = await self.db.devices.find({
                "userId": user_id,
                "isActive": True,
                "pushToken": {"$exists": True, "$ne": None}
            }).to_list(length=None)
            
            if not devices:
                return
            
            # Prepare push notification payload
            payload = {
                "title": notification["title"],
                "body": notification["message"],
                "data": {
                    "notificationId": notification["id"],
                    "type": notification["type"],
                    "relatedId": notification.get("relatedId"),
                    "relatedType": notification.get("relatedType")
                }
            }
            
            # Send to each device
            for device in devices:
                await self._send_to_device(device["pushToken"], payload, device["deviceType"])
                
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
    
    async def _send_to_device(self, push_token: str, payload: Dict, device_type: str):
        """Send notification to specific device"""
        try:
            # In a real implementation, this would use FCM for Android or APNS for iOS
            # For now, we'll log the notification
            logger.info(f"Push notification sent to {device_type} device: {payload['title']}")
            
            # TODO: Implement actual push notification sending
            # Example for FCM:
            # from firebase_admin import messaging
            # message = messaging.Message(
            #     data=payload["data"],
            #     notification=messaging.Notification(
            #         title=payload["title"],
            #         body=payload["body"]
            #     ),
            #     token=push_token
            # )
            # response = messaging.send(message)
            
        except Exception as e:
            logger.error(f"Error sending to device {push_token}: {e}")
    
    async def mark_notifications_as_read(self, user_id: str, notification_ids: List[str]):
        """Mark specific notifications as read"""
        try:
            result = await self.db.notifications.update_many(
                {
                    "id": {"$in": notification_ids},
                    "recipientId": user_id
                },
                {"$set": {"isRead": True, "readAt": datetime.utcnow()}}
            )
            return result.modified_count
        except Exception as e:
            logger.error(f"Error marking notifications as read: {e}")
            raise
    
    async def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications for user"""
        try:
            count = await self.db.notifications.count_documents({
                "recipientId": user_id,
                "isRead": False
            })
            return count
        except Exception as e:
            logger.error(f"Error getting unread count: {e}")
            return 0
    
    async def cleanup_old_notifications(self, days: int = 30):
        """Remove old notifications"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            result = await self.db.notifications.delete_many({
                "createdAt": {"$lt": cutoff_date}
            })
            logger.info(f"Cleaned up {result.deleted_count} old notifications")
            return result.deleted_count
        except Exception as e:
            logger.error(f"Error cleaning up notifications: {e}")
            return 0
    
    def _generate_id(self) -> str:
        """Generate unique ID"""
        import uuid
        return str(uuid.uuid4())


# Notification helper functions
class NotificationTypes:
    LIKE = "like"
    COMMENT = "comment"
    FOLLOW = "follow"
    MENTION = "mention"
    MESSAGE = "message"
    STORY_VIEW = "story_view"
    POST_SHARE = "post_share"
    ACHIEVEMENT = "achievement"
    SYSTEM = "system"


class NotificationTemplates:
    """Pre-defined notification message templates"""
    
    @staticmethod
    def get_template(notification_type: str, sender_name: str, **kwargs) -> Dict[str, str]:
        templates = {
            NotificationTypes.LIKE: {
                "title": "New Like",
                "message": f"{sender_name} liked your post"
            },
            NotificationTypes.COMMENT: {
                "title": "New Comment", 
                "message": f"{sender_name} commented on your post"
            },
            NotificationTypes.FOLLOW: {
                "title": "New Follower",
                "message": f"{sender_name} started following you"
            },
            NotificationTypes.MENTION: {
                "title": "Mention",
                "message": f"{sender_name} mentioned you in a post"
            },
            NotificationTypes.MESSAGE: {
                "title": "New Message",
                "message": f"{sender_name} sent you a message"
            },
            NotificationTypes.STORY_VIEW: {
                "title": "Story View",
                "message": f"{sender_name} viewed your story"
            }
        }
        
        return templates.get(notification_type, {
            "title": "Notification",
            "message": "You have a new notification"
        })
