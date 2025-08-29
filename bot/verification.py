
# Token Verification Module
import time
import hashlib
from info import *
from utils import temp

async def check_verification(user_id):
    """Check if user has valid verification token"""
    if not VERIFY:
        return True
    
    # Check if user has valid verification
    if user_id in temp.VERIFIED_USERS:
        return True
    return False

def generate_verification_token(user_id):
    """Generate verification token for user"""
    timestamp = str(int(time.time()))
    data = f"{user_id}:{timestamp}:{VERIFY_TOKEN}"
    return hashlib.md5(data.encode()).hexdigest()

async def verify_user(user_id, token):
    """Verify user with token"""
    expected_token = generate_verification_token(user_id)
    if token == expected_token:
        if user_id not in temp.VERIFIED_USERS:
            temp.VERIFIED_USERS.append(user_id)
        return True
    return False

def is_verification_required():
    """Check if verification is enabled"""
    return VERIFY
