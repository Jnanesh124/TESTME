
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

async def add_ignored_word(word):
    """Add a word to the ignored words list"""
    mycol = mydb['ignored_words']
    
    # Check if word already exists
    existing = mycol.find_one({'word': word.lower()})
    if existing:
        return False
    
    data = {
        'word': word.lower()
    }
    
    try:
        mycol.insert_one(data)
        return True
    except Exception as e:
        logger.exception('Error adding ignored word!', exc_info=True)
        return False

async def remove_ignored_word(word):
    """Remove a word from the ignored words list"""
    mycol = mydb['ignored_words']
    
    try:
        result = mycol.delete_one({'word': word.lower()})
        return result.deleted_count > 0
    except Exception as e:
        logger.exception('Error removing ignored word!', exc_info=True)
        return False

async def get_ignored_words():
    """Get all ignored words"""
    mycol = mydb['ignored_words']
    
    try:
        words = []
        cursor = mycol.find({})
        async for doc in cursor:
            words.append(doc['word'])
        return words
    except Exception as e:
        logger.exception('Error getting ignored words!', exc_info=True)
        return []

async def is_ignored_word(word):
    """Check if a word is in the ignored list"""
    mycol = mydb['ignored_words']
    
    try:
        result = mycol.find_one({'word': word.lower()})
        return result is not None
    except Exception as e:
        logger.exception('Error checking ignored word!', exc_info=True)
        return False
