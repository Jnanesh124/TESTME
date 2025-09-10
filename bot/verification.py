
import time
import hashlib
import datetime
import logging
from info import *
from utils import temp
from database.users_chats_db import db

logger = logging.getLogger(__name__)

class VerificationManager:
    def __init__(self):
        self.verification_collection = db.db.verification_users
    
    async def check_verification(self, user_id):
        """Check if user has valid verification token"""
        if not VERIFY:
            return True
        
        # Check database for valid verification
        verification_data = await self.verification_collection.find_one({"user_id": user_id})
        
        if verification_data:
            expiry_time = verification_data.get("expiry_time")
            if isinstance(expiry_time, datetime.datetime) and datetime.datetime.now() <= expiry_time:
                return True
            else:
                # Remove expired verification
                await self.verification_collection.delete_one({"user_id": user_id})
                
        return False
    
    def generate_verification_token(self, user_id):
        """Generate verification token for user"""
        import random
        import string
        # Generate the same format as get_token function
        return ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    
    async def verify_user(self, user_id, token, client):
        """Verify user with token and store in database"""
        try:
            # Token validation is already done in check_token function
            # So we can proceed with verification
            
            # Set 24-hour expiry from now
            expiry_time = datetime.datetime.now() + datetime.timedelta(hours=24)
            verification_time = datetime.datetime.now()
            
            # Store verification in database
            verification_data = {
                "user_id": user_id,
                "verification_time": verification_time,
                "expiry_time": expiry_time,
                "token": token
            }
            
            await self.verification_collection.update_one(
                {"user_id": user_id},
                {"$set": verification_data},
                upsert=True
            )
            
            # Send notification to admins
            try:
                user = await client.get_users(user_id)
                admin_notification = (
                    f"🔐 <b>New User Verified</b>\n\n"
                    f"👤 <b>User:</b> {user.first_name} (@{user.username or 'N/A'})\n"
                    f"🆔 <b>User ID:</b> <code>{user_id}</code>\n"
                    f"⏰ <b>Verified Time:</b> {verification_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"⏳ <b>Expires At:</b> {expiry_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"🕐 <b>Valid For:</b> 24 hours"
                )
                
                # Send to log channel
                if LOG_CHANNEL:
                    await client.send_message(LOG_CHANNEL, admin_notification)
                
                # Send to admins
                for admin_id in ADMINS:
                    try:
                        await client.send_message(admin_id, admin_notification)
                    except Exception as e:
                        logger.error(f"Failed to send notification to admin {admin_id}: {e}")
                        
                # Log the verification
                logger.info(f"User {user_id} ({user.first_name}) verified successfully. Expires at {expiry_time}")
                
            except Exception as e:
                logger.error(f"Error sending admin notification: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in verify_user: {e}")
            return False
    
    async def get_verified_users_count(self, hours=24):
        """Get count of users verified in last N hours"""
        time_threshold = datetime.datetime.now() - datetime.timedelta(hours=hours)
        count = await self.verification_collection.count_documents({
            "verification_time": {"$gte": time_threshold}
        })
        return count
    
    async def get_verified_users_list(self, hours=24):
        """Get list of users verified in last N hours"""
        time_threshold = datetime.datetime.now() - datetime.timedelta(hours=hours)
        cursor = self.verification_collection.find({
            "verification_time": {"$gte": time_threshold}
        }).sort("verification_time", -1)
        
        verified_users = []
        async for doc in cursor:
            verified_users.append({
                "user_id": doc["user_id"],
                "verification_time": doc["verification_time"],
                "expiry_time": doc["expiry_time"]
            })
        
        return verified_users
    
    async def cleanup_expired_verifications(self):
        """Remove expired verifications from database"""
        current_time = datetime.datetime.now()
        result = await self.verification_collection.delete_many({
            "expiry_time": {"$lt": current_time}
        })
        if result.deleted_count > 0:
            logger.info(f"Cleaned up {result.deleted_count} expired verifications")

# Global verification manager instance
verification_manager = VerificationManager()

# Backward compatibility functions
async def check_verification(user_id):
    return await verification_manager.check_verification(user_id)

def generate_verification_token(user_id):
    return verification_manager.generate_verification_token(user_id)

async def verify_user(user_id, token, client):
    return await verification_manager.verify_user(user_id, token, client)

def is_verification_required():
    return VERIFY
