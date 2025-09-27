
# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import pymongo
from info import DATABASE_URI, DATABASE_NAME
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

myclient = pymongo.MongoClient(DATABASE_URI)
mydb = myclient[DATABASE_NAME]

async def add_bad_word(word):
    """Add a word to the bad words list"""
    mycol = mydb['bad_words']
    
    # Check if word already exists
    existing = mycol.find_one({'word': word})
    if existing:
        return False
    
    data = {
        'word': word
    }
    
    try:
        mycol.insert_one(data)
        return True
    except Exception as e:
        logger.exception('Error adding bad word!', exc_info=True)
        return False

async def remove_bad_word(word):
    """Remove a word from the bad words list"""
    mycol = mydb['bad_words']
    
    try:
        result = mycol.delete_one({'word': word})
        return result.deleted_count > 0
    except Exception as e:
        logger.exception('Error removing bad word!', exc_info=True)
        return False

async def get_all_bad_words():
    """Get all bad words from database"""
    mycol = mydb['bad_words']
    
    try:
        cursor = mycol.find({})
        words = [doc['word'] for doc in cursor]
        return words
    except Exception as e:
        logger.exception('Error getting bad words!', exc_info=True)
        return []

async def initialize_bad_words_from_info():
    """Initialize database with bad words from info.py"""
    from info import BAD_WORDS
    mycol = mydb['bad_words']
    
    try:
        # Clear existing collection
        mycol.delete_many({})
        
        # Add all words from info.py
        for word in BAD_WORDS:
            await add_bad_word(word)
        
        logger.info(f"Initialized {len(BAD_WORDS)} bad words in database")
        return True
    except Exception as e:
        logger.exception('Error initializing bad words!', exc_info=True)
        return False
