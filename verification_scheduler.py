
import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from verification_storage import verification_storage
from bot.verification import verification_manager

logger = logging.getLogger(__name__)

class VerificationScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.setup_jobs()
    
    def setup_jobs(self):
        """Setup scheduled jobs for verification cleanup"""
        # Run cleanup every hour
        self.scheduler.add_job(
            self.cleanup_expired_verifications,
            'interval',
            hours=1,
            id='cleanup_verifications',
            replace_existing=True
        )
        
        # Run cleanup on startup (after 5 minutes)
        self.scheduler.add_job(
            self.cleanup_expired_verifications,
            'date',
            run_date=None,
            id='startup_cleanup',
            replace_existing=True
        )
    
    async def cleanup_expired_verifications(self):
        """Cleanup expired verifications"""
        try:
            await verification_manager.cleanup_expired_verifications()
            logger.info("Automatic verification cleanup completed")
        except Exception as e:
            logger.error(f"Error during automatic verification cleanup: {e}")
    
    def start(self):
        """Start the scheduler"""
        try:
            self.scheduler.start()
            logger.info("Verification cleanup scheduler started")
        except Exception as e:
            logger.error(f"Error starting verification scheduler: {e}")
    
    def shutdown(self):
        """Shutdown the scheduler"""
        try:
            self.scheduler.shutdown()
            logger.info("Verification cleanup scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping verification scheduler: {e}")

# Global scheduler instance
verification_scheduler = VerificationScheduler()
