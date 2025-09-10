
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from info import ADMINS
from verification_storage import verification_storage
from bot.verification import verification_manager

logger = logging.getLogger(__name__)

@Client.on_message(filters.command("verified_users") & filters.user(ADMINS))
async def verified_users_cmd(client: Client, message: Message):
    """Show verified users count and details"""
    try:
        count = verification_storage.get_verified_users_count()
        
        if count == 0:
            await message.reply_text("📊 **Verification Status**\n\n❌ No users currently verified")
            return
        
        text = f"📊 **Verification Status**\n\n✅ **Total Verified Users:** {count}\n\n"
        
        # Show some details about verified users
        for user_id_str, user_data in verification_storage.verified_users.items():
            expiry = user_data.get('expiry_time')
            if expiry:
                if isinstance(expiry, str):
                    import datetime
                    expiry = datetime.datetime.fromisoformat(expiry)
                remaining = expiry - datetime.datetime.now()
                hours_left = max(0, remaining.total_seconds() / 3600)
                text += f"👤 **User {user_id_str}:** {hours_left:.1f} hours left\n"
        
        await message.reply_text(text)
        
    except Exception as e:
        logger.error(f"Error in verified_users_cmd: {e}")
        await message.reply_text(f"❌ Error getting verification data: {e}")

@Client.on_message(filters.command("cleanup_verifications") & filters.user(ADMINS))
async def cleanup_verifications_cmd(client: Client, message: Message):
    """Manually cleanup expired verifications"""
    try:
        await verification_manager.cleanup_expired_verifications()
        count = verification_storage.get_verified_users_count()
        await message.reply_text(f"✅ **Cleanup completed**\n\n📊 Active verified users: {count}")
        
    except Exception as e:
        logger.error(f"Error in cleanup_verifications_cmd: {e}")
        await message.reply_text(f"❌ Error during cleanup: {e}")

@Client.on_message(filters.command("remove_verification") & filters.user(ADMINS))
async def remove_verification_cmd(client: Client, message: Message):
    """Remove verification for a specific user"""
    try:
        if len(message.command) < 2:
            await message.reply_text("❌ Usage: `/remove_verification <user_id>`")
            return
        
        user_id = int(message.command[1])
        verification_storage.remove_verified_user(user_id)
        
        await message.reply_text(f"✅ **Verification removed** for user `{user_id}`")
        
    except ValueError:
        await message.reply_text("❌ Invalid user ID. Please provide a valid number.")
    except Exception as e:
        logger.error(f"Error in remove_verification_cmd: {e}")
        await message.reply_text(f"❌ Error removing verification: {e}")

@Client.on_message(filters.command("verify_user") & filters.user(ADMINS))
async def verify_user_cmd(client: Client, message: Message):
    """Manually verify a user"""
    try:
        if len(message.command) < 2:
            await message.reply_text("❌ Usage: `/verify_user <user_id> [hours]`")
            return
        
        user_id = int(message.command[1])
        hours = 24  # default
        
        if len(message.command) > 2:
            hours = int(message.command[2])
        
        verification_storage.add_verified_user(user_id, "admin_verified", hours)
        
        await message.reply_text(f"✅ **User verified**\n\n👤 User ID: `{user_id}`\n⏰ Duration: {hours} hours")
        
    except ValueError:
        await message.reply_text("❌ Invalid input. Please provide valid numbers.")
    except Exception as e:
        logger.error(f"Error in verify_user_cmd: {e}")
        await message.reply_text(f"❌ Error verifying user: {e}")
