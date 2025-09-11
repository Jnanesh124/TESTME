import json
import os
import datetime
import logging
import asyncio
from typing import Dict, Optional
from info import VERIFY

logger = logging.getLogger(__name__)

class JSONVerificationStorage:
    def __init__(self, file_path: str = "verified_users.json"):
        self.file_path = file_path
        self.verified_users: Dict[str, dict] = {}
        self.load_verified_users()

    def load_verified_users(self):
        """Load verified users from JSON file"""
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r') as f:
                    data = json.load(f)
                    # Convert string timestamps back to datetime objects
                    for user_id, user_data in data.items():
                        if 'expiry_time' in user_data:
                            user_data['expiry_time'] = datetime.datetime.fromisoformat(user_data['expiry_time'])
                        if 'verification_time' in user_data:
                            user_data['verification_time'] = datetime.datetime.fromisoformat(user_data['verification_time'])
                    self.verified_users = data
                    logger.info(f"Loaded {len(self.verified_users)} verified users from {self.file_path}")
            else:
                self.verified_users = {}
                logger.info(f"No existing verification file found. Starting with empty verification storage.")
        except Exception as e:
            logger.error(f"Error loading verification data: {e}")
            self.verified_users = {}

    def save_verified_users(self):
        """Save verified users to JSON file"""
        try:
            # Convert datetime objects to strings for JSON serialization
            data_to_save = {}
            for user_id, user_data in self.verified_users.items():
                data_copy = user_data.copy()
                if 'expiry_time' in data_copy and isinstance(data_copy['expiry_time'], datetime.datetime):
                    data_copy['expiry_time'] = data_copy['expiry_time'].isoformat()
                if 'verification_time' in data_copy and isinstance(data_copy['verification_time'], datetime.datetime):
                    data_copy['verification_time'] = data_copy['verification_time'].isoformat()
                data_to_save[user_id] = data_copy
            
            with open(self.file_path, 'w') as f:
                json.dump(data_to_save, f, indent=2)
            logger.info(f"Saved {len(self.verified_users)} verified users to {self.file_path}")
        except Exception as e:
            logger.error(f"Error saving verification data: {e}")

    def add_verified_user(self, user_id: int, token: str, hours: int = 24):
        """Add a verified user with expiration time"""
        user_id_str = str(user_id)
        current_time = datetime.datetime.now()
        expiry_time = current_time + datetime.timedelta(hours=hours)

        self.verified_users[user_id_str] = {
            "user_id": user_id,
            "token": token,
            "verification_time": current_time,
            "expiry_time": expiry_time
        }

        self.save_verified_users()
        logger.info(f"Added verified user {user_id} with expiry at {expiry_time}")

    def is_user_verified(self, user_id: int) -> bool:
        """Check if user is verified and not expired"""
        if not VERIFY:
            return True

        user_id_str = str(user_id)
        if user_id_str in self.verified_users:
            user_data = self.verified_users[user_id_str]
            expiry_time = user_data.get('expiry_time')

            if isinstance(expiry_time, datetime.datetime):
                if datetime.datetime.now() <= expiry_time:
                    return True
                else:
                    # User verification expired, remove them
                    self.remove_verified_user(user_id)
                    return False

        return False

    def remove_verified_user(self, user_id: int):
        """Remove a verified user"""
        user_id_str = str(user_id)
        if user_id_str in self.verified_users:
            del self.verified_users[user_id_str]
            self.save_verified_users()
            logger.info(f"Removed verified user {user_id}")

    def cleanup_expired_users(self):
        """Remove all expired users"""
        current_time = datetime.datetime.now()
        expired_users = []

        for user_id_str, user_data in self.verified_users.items():
            expiry_time = user_data.get('expiry_time')
            if isinstance(expiry_time, datetime.datetime) and current_time > expiry_time:
                expired_users.append(user_id_str)

        for user_id_str in expired_users:
            del self.verified_users[user_id_str]

        if expired_users:
            self.save_verified_users()
            logger.info(f"Cleaned up {len(expired_users)} expired verifications")

        return len(expired_users)

    def get_verified_users_count(self) -> int:
        """Get count of currently verified users"""
        return len(self.verified_users)

    def get_user_expiry(self, user_id: int) -> Optional[datetime.datetime]:
        """Get user's verification expiry time"""
        user_id_str = str(user_id)
        if user_id_str in self.verified_users:
            return self.verified_users[user_id_str].get('expiry_time')
        return None

# Global instance
verification_storage = JSONVerificationStorage()