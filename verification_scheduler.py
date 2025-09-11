import asyncio
import json
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VerificationScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.storage_file = "verified_users.json"
        self.verification_duration = timedelta(hours=24)  # Global 24-hour verification

    def start(self):
        """Start the scheduler and add cleanup job"""
        try:
            # Add a job to run cleanup immediately after startup
            self.scheduler.add_job(
                func=self.cleanup_expired_verifications,
                trigger=DateTrigger(run_date=datetime.now()),
                id="startup_cleanup",
                replace_existing=True
            )

            # Add recurring cleanup job every 30 minutes for better accuracy
            self.scheduler.add_job(
                func=self.cleanup_expired_verifications,
                trigger=IntervalTrigger(minutes=30),
                id="verification_cleanup",
                replace_existing=True
            )

            self.scheduler.start()
            logger.info("Verification cleanup scheduler started with 24-hour global verification")
        except Exception as e:
            logger.error(f"Error starting verification scheduler: {e}")

    async def cleanup_expired_verifications(self):
        """Remove expired verifications based on global 24-hour limit"""
        try:
            with open(self.storage_file, 'r') as f:
                verified_users = json.load(f)

            current_time = datetime.now()
            expired_users = []

            for user_id, verification_time_str in verified_users.items():
                try:
                    verification_time = datetime.fromisoformat(verification_time_str)
                    # Check if verification has expired (24 hours)
                    if current_time - verification_time >= self.verification_duration:
                        expired_users.append(user_id)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid verification time for user {user_id}: {e}")
                    expired_users.append(user_id)  # Remove invalid entries

            # Remove expired users
            for user_id in expired_users:
                del verified_users[user_id]

            # Save updated data
            with open(self.storage_file, 'w') as f:
                json.dump(verified_users, f, indent=2, default=str)

            if expired_users:
                logger.info(f"Removed {len(expired_users)} expired verifications (24-hour limit)")
            else:
                logger.info("Automatic verification cleanup completed - no expired verifications found")

        except FileNotFoundError:
            logger.info("Verified users file not found, creating new one")
            with open(self.storage_file, 'w') as f:
                json.dump({}, f)
        except Exception as e:
            logger.error(f"Error during verification cleanup: {e}")

    def is_user_verified(self, user_id):
        """Check if user is still verified (within 24 hours)"""
        try:
            with open(self.storage_file, 'r') as f:
                verified_users = json.load(f)

            if str(user_id) not in verified_users:
                return False

            verification_time = datetime.fromisoformat(verified_users[str(user_id)])
            current_time = datetime.now()

            # Check if verification is still valid (within 24 hours)
            return current_time - verification_time < self.verification_duration

        except Exception as e:
            logger.error(f"Error checking user verification: {e}")
            return False

    def stop(self):
        """Stop the scheduler"""
        try:
            self.scheduler.shutdown()
            logger.info("Verification cleanup scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping verification scheduler: {e}")

# Global scheduler instance
verification_scheduler = VerificationScheduler()