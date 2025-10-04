from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import os

# Load environment variables
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'novasocial')]


async def create_indexes():
    """Create database indexes for better performance"""
    try:
        # User indexes
        await db.users.create_index("id", unique=True)
        await db.users.create_index("email", unique=True)
        await db.users.create_index("username", unique=True)
        
        # Post indexes
        await db.posts.create_index("authorId")
        await db.posts.create_index("createdAt")
        await db.posts.create_index("hashtags")
        
        # Comment indexes
        await db.comments.create_index("postId")
        await db.comments.create_index("userId")
        await db.comments.create_index("createdAt")
        
        # Follow indexes
        await db.follows.create_index("followerId")
        await db.follows.create_index("followingId")
        await db.follows.create_index([("followerId", 1), ("followingId", 1)], unique=True)
        
        # Conversation indexes
        await db.conversations.create_index("participants")
        await db.conversations.create_index("createdAt")
        
        # Message indexes
        await db.messages.create_index("conversationId")
        await db.messages.create_index("senderId")
        await db.messages.create_index("createdAt")
        
        # Story indexes
        await db.stories.create_index("authorId")
        await db.stories.create_index("createdAt")
        await db.stories.create_index("expiresAt")
        
        # Notification indexes
        await db.notifications.create_index("userId")
        await db.notifications.create_index("createdAt")
        await db.notifications.create_index("read")
        
        print("✅ Database indexes created successfully")
        
    except Exception as e:
        print(f"❌ Error creating indexes: {e}")


async def cleanup_expired_stories():
    """Clean up expired stories from database"""
    try:
        from datetime import datetime
        result = await db.stories.delete_many({
            "expiresAt": {"$lte": datetime.utcnow()}
        })
        print(f"🧹 Cleaned up {result.deleted_count} expired stories")
    except Exception as e:
        print(f"❌ Error cleaning up stories: {e}")


# Database collections for easy access
users_collection = db.users
posts_collection = db.posts
comments_collection = db.comments
follows_collection = db.follows
conversations_collection = db.conversations
messages_collection = db.messages
stories_collection = db.stories
notifications_collection = db.notifications