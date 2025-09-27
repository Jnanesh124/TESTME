# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import logging, asyncio, os, re, random, pytz, aiohttp, requests, string, json, http.client
from info import *
from imdb import Cinemagoer
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import enums
from pyrogram.errors import *
from typing import Union
from Script import script
from datetime import datetime, date
from typing import List
from database.users_chats_db import db
from database.join_reqs import JoinReqs
from bs4 import BeautifulSoup
from shortzy import Shortzy

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
join_db = JoinReqs
BTN_URL_REGEX = re.compile(r"(\[([^\[]+?)\]\((buttonurl|buttonalert):(?:/{0,2})(.+?)(:same)?\))")

imdb = Cinemagoer()
TOKENS = {}
VERIFIED = {}
BANNED = {}
SECOND_SHORTENER = {}
SMART_OPEN = '“'
SMART_CLOSE = '”'
START_CHAR = ('\'', '"', SMART_OPEN)

# temp db for banned
class temp(object):
    BANNED_USERS = []
    BANNED_CHATS = []
    ME = None
    CURRENT=int(os.environ.get("SKIP", 2))
    CANCEL = False
    MELCOW = {}
    U_NAME = None
    B_NAME = None
    GETALL = {}
    SHORT = {}
    SETTINGS = {}
    IMDB_CAP = {}
    VERIFIED_USERS = []


async def pub_is_subscribed(bot, query, channel):
    btn = []
    for id in channel:
        chat = await bot.get_chat(int(id))
        try:
            await bot.get_chat_member(id, query.from_user.id)
        except UserNotParticipant:
            btn.append(
                [InlineKeyboardButton(f'Join {chat.title}', url=chat.invite_link)]
            )
        except Exception as e:
            pass
    return btn

async def is_subscribed(bot, query, channel_id=None):
    """
    Check if user is subscribed to a channel or AUTH_CHANNEL
    """
    if channel_id is None:
        channel_id = AUTH_CHANNEL

    if not channel_id:
        logger.info(f"No channel_id provided for user {query.from_user.id}")
        return True

    try:
        user = await bot.get_chat_member(channel_id, query.from_user.id)
        logger.info(f"User {query.from_user.id} status in channel {channel_id}: {user.status}")
    except UserNotParticipant:
        logger.info(f"User {query.from_user.id} is not a participant in channel {channel_id}")
        return False
    except Exception as e:
        logger.error(f"Error checking subscription for user {query.from_user.id} in channel {channel_id}: {e}")
        return False
    else:
        if user.status != enums.ChatMemberStatus.BANNED:
            logger.info(f"User {query.from_user.id} is subscribed to channel {channel_id}")
            return True
        else:
            logger.info(f"User {query.from_user.id} is banned in channel {channel_id}")
    return False

async def get_poster(query, bulk=False, id=False, file=None):
    try:
        if not id:
            query = (query.strip()).lower()
            title = query
            year = re.findall(r'[1-2]\d{3}$', query, re.IGNORECASE)
            if year:
                year = list_to_str(year[:1])
                title = (query.replace(year, "")).strip()
            elif file is not None:
                year = re.findall(r'[1-2]\d{3}', file, re.IGNORECASE)
                if year:
                    year = list_to_str(year[:1])
            else:
                year = None
            movieid = imdb.search_movie(title.lower(), results=10)
            if not movieid:
                logger.warning(f"No IMDb results found for: {title}")
                return None
            if year:
                filtered=list(filter(lambda k: str(k.get('year')) == str(year), movieid))
                if not filtered:
                    filtered = movieid
            else:
                filtered = movieid
            movieid=list(filter(lambda k: k.get('kind') in ['movie', 'tv series'], filtered))
            if not movieid:
                movieid = filtered
            if bulk:
                return movieid
            movieid = movieid[0].movieID
        else:
            movieid = query
        movie = imdb.get_movie(movieid)
        if not movie:
            logger.warning(f"No movie data found for IMDb ID: {movieid}")
            return None
    except Exception as e:
        logger.error(f"IMDb API error: {e}")
        # Return None to gracefully handle IMDb failures
        return None
    if movie.get("original air date"):
        date = movie["original air date"]
    elif movie.get("year"):
        date = movie.get("year")
    else:
        date = "N/A"
    plot = ""
    if not LONG_IMDB_DESCRIPTION:
        plot = movie.get('plot')
        if plot and len(plot) > 0:
            plot = plot[0]
    else:
        plot = movie.get('plot outline')
    if plot and len(plot) > 800:
        plot = plot[0:800] + "..."

    return {
        'title': movie.get('title'),
        'votes': movie.get('votes'),
        "aka": list_to_str(movie.get("akas")),
        "seasons": movie.get("number of seasons"),
        "box_office": movie.get('box office'),
        'localized_title': movie.get('localized title'),
        'kind': movie.get("kind"),
        "imdb_id": f"tt{movie.get('imdbID')}",
        "cast": list_to_str(movie.get("cast")),
        "runtime": list_to_str(movie.get("runtimes")),
        "countries": list_to_str(movie.get("countries")),
        "certificates": list_to_str(movie.get("certificates")),
        "languages": list_to_str(movie.get("languages")),
        "director": list_to_str(movie.get("director")),
        "writer":list_to_str(movie.get("writer")),
        "producer":list_to_str(movie.get("producer")),
        "composer":list_to_str(movie.get("composer")) ,
        "cinematographer":list_to_str(movie.get("cinematographer")),
        "music_team": list_to_str(movie.get("music department")),
        "distributors": list_to_str(movie.get("distributors")),
        'release_date': date,
        'year': movie.get('year'),
        'genres': list_to_str(movie.get("genres")),
        'poster': movie.get('full-size cover url'),
        'plot': plot,
        'rating': str(movie.get("rating")),
        'url':f'https://www.imdb.com/title/tt{movieid}'
    }

async def broadcast_messages(user_id, message):
    try:
        await message.copy(chat_id=user_id)
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return await broadcast_messages(user_id, message)
    except InputUserDeactivated:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id}-Removed from Database, since deleted account.")
        return False, "Deleted"
    except UserIsBlocked:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id} -Blocked the bot.")
        return False, "Blocked"
    except PeerIdInvalid:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id} - PeerIdInvalid")
        return False, "Error"
    except Exception as e:
        return False, "Error"

async def broadcast_messages_group(chat_id, message):
    try:
        kd = await message.copy(chat_id=chat_id)
        try:
            await kd.pin()
        except:
            pass
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return await broadcast_messages_group(chat_id, message)
    except Exception as e:
        return False, "Error"

async def remove_bad_words_from_filename(filename):
    """Remove bad words from filename with enhanced tokenization"""
    original_filename = filename
    removed_words = []

    # Get bad words from database
    from database.bad_words_mdb import get_all_bad_words
    try:
        bad_words = await get_all_bad_words()
        if not bad_words:
            # Fallback to info.py if database is empty
            from info import BAD_WORDS
            bad_words = BAD_WORDS
    except:
        # Fallback to info.py if database error
        from info import BAD_WORDS
        bad_words = BAD_WORDS

    # First split the filename into tokens using various delimiters
    # Split by common separators like spaces, dots, dashes, underscores
    import re
    tokens = re.split(r'[\s\.\-_]+', filename)

    # Remove empty tokens
    tokens = [token for token in tokens if token.strip()]

    # Remove all bad words from tokens
    cleaned_tokens = []
    for token in tokens:
        token_removed = False

        # Check exact match against each bad word (case-insensitive)
        for bad_word in bad_words:
            if token.lower() == bad_word.lower():
                removed_words.append(token)
                logger.info(f"Removed exact word match: '{token}' (matched bad word: '{bad_word}')")
                token_removed = True
                break

            # Check if the token contains the bad word as a substring
            elif bad_word.lower() in token.lower() and len(bad_word) > 2:  # Only for longer bad words
                removed_words.append(token)
                logger.info(f"Removed token containing bad word: '{token}' (contains: '{bad_word}')")
                token_removed = True
                break

            # Check if the token is contained within the bad word
            elif token.lower() in bad_word.lower() and len(token) > 2:  # Only for longer tokens
                removed_words.append(token)
                logger.info(f"Removed token found in bad word pattern: '{token}' (found in: '{bad_word}')")
                token_removed = True
                break

        if not token_removed:
            cleaned_tokens.append(token)

    # Rejoin the cleaned tokens with spaces
    cleaned_filename = ' '.join(cleaned_tokens)

    # Clean up extra spaces
    cleaned_filename = ' '.join(cleaned_filename.split())

    # Log the cleaning result
    if removed_words:
        logger.info(f"BAD WORDS REMOVAL: Original: '{original_filename}' -> Cleaned: '{cleaned_filename}' | Removed words: {removed_words}")
    else:
        logger.info(f"BAD WORDS REMOVAL: No bad words found in '{original_filename}'")

    return cleaned_filename

async def remove_ignore_words_from_filename(filename):
    """Remove IGNORE_WORDS from filename with enhanced tokenization"""
    import re

    original_filename = filename
    removed_words = []

    # Split the filename into tokens using various delimiters
    tokens = re.split(r'[\s\.\-_~]+', filename)
    tokens = [token for token in tokens if token.strip()]

    # Convert IGNORE_WORDS to lowercase set for faster lookup
    ignore_words_lower = {word.lower() for word in IGNORE_WORDS}

    # Remove all ignore words
    cleaned_tokens = []
    for token in tokens:
        # Clean token by removing special characters but keep original for comparison
        token_cleaned = re.sub(r'[@#~\-_()]+', '', token)
        token_lower = token_cleaned.lower()

        # Skip empty tokens after cleaning
        if not token_cleaned:
            continue

        token_removed = False

        # Check exact match against IGNORE_WORDS (case-insensitive)
        if token_lower in ignore_words_lower:
            removed_words.append(token)
            logger.info(f"Removed IGNORE_WORD exact match: '{token}' -> '{token_lower}'")
            token_removed = True
        else:
            # Check if token contains any ignore word as substring (for longer words)
            for ignore_word in IGNORE_WORDS:
                if len(ignore_word) > 3:  # Only check longer ignore words for substring match
                    if ignore_word.lower() in token_lower:
                        removed_words.append(token)
                        logger.info(f"Removed token containing IGNORE_WORD: '{token}' (contains: '{ignore_word}')")
                        token_removed = True
                        break

        if not token_removed:
            cleaned_tokens.append(token_cleaned)  # Use cleaned version

    # Rejoin the cleaned tokens with spaces
    clean_filename_result = ' '.join(cleaned_tokens)
    clean_filename_result = ' '.join(clean_filename_result.split())  # Clean up extra spaces

    if removed_words:
        logger.info(f"IGNORE WORDS REMOVAL: Original: '{original_filename}' -> Cleaned: '{clean_filename_result}' | Removed words: {removed_words}")
    else:
        logger.info(f"IGNORE WORDS REMOVAL: No ignore words found in '{original_filename}'")

    return clean_filename_result

def clean_filename(file_name):
    original_filename = file_name
    removed_words = []
    import re

    logger.info(f"🔧 Starting filename cleaning with priority order for: {original_filename}")

    # STEP 0: Replace ! with | (character replacement)
    file_name = file_name.replace('!', '|')
    logger.info(f"🔄 After replacing ! with |: {file_name}")

    # STEP 1: Remove BAD_WORDS first (HIGHEST PRIORITY)
    file_name = remove_bad_words_from_filename(file_name)
    logger.info(f"❌ After removing BAD_WORDS (Priority 1): {file_name}")

    # STEP 2: Remove IGNORE_WORDS second priority  
    file_name = remove_ignore_words_from_filename(file_name)
    logger.info(f"🚫 After removing IGNORE_WORDS (Priority 2): {file_name}")

    # STEP 3: Remove special characters @ ~ # last (lowest priority)
    file_name = re.sub(r'[@~#]+', ' ', file_name)
    logger.info(f"🧹 After removing special chars (@~#) (Priority 3): {file_name}")

    # Clean up extra spaces
    file_name = ' '.join(file_name.split())

    # Log the cleaning result
    logger.info(f"✅ FILENAME CLEANING COMPLETE: '{original_filename}' -> '{file_name}'")

    return file_name

async def search_gagala(text):
    usr_agent = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/61.0.3163.100 Safari/537.36'
        }
    text = text.replace(" ", '+')
    url = f'https://www.google.com/search?q={text}'
    response = requests.get(url, headers=usr_agent)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    titles = soup.find_all( 'h3' )
    return [title.getText() for title in titles]

async def get_settings(group_id):
    settings = await db.get_settings(group_id)
    return settings

async def save_group_settings(group_id, key, value):
    current = await get_settings(group_id)
    current.update({key: value})
    await db.update_settings(group_id, current)

def get_size(size):
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])

def split_list(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]

def get_file_id(msg: Message):
    if msg.media:
        for message_type in (
            "photo",
            "animation",
            "audio",
            "document",
            "video",
            "video_note",
            "voice",
            "sticker"
        ):
            obj = getattr(msg, message_type)
            if obj:
                setattr(obj, "message_type", message_type)
                return obj

def extract_user(message: Message) -> Union[int, str]:
    user_id = None
    user_first_name = None
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        user_first_name = message.reply_to_message.from_user.first_name

    elif len(message.command) > 1:
        if (
            len(message.entities) > 1 and
            message.entities[1].type == enums.MessageEntityType.TEXT_MENTION
        ):

            required_entity = message.entities[1]
            user_id = required_entity.user.id
            user_first_name = required_entity.user.first_name
        else:
            user_id = message.command[1]
            # don't want to make a request -_-
            user_first_name = user_id
        try:
            user_id = int(user_id)
        except ValueError:
            pass
    else:
        user_id = message.from_user.id
        user_first_name = message.from_user.first_name
    return (user_id, user_first_name)

def list_to_str(k):
    if not k:
        return "N/A"
    elif len(k) == 1:
        return str(k[0])
    elif MAX_LIST_ELM:
        k = k[:int(MAX_LIST_ELM)]
        return ' '.join(f'{elem}, ' for elem in k)
    else:
        return ' '.join(f'{elem}, ' for elem in k)

def last_online(from_user):
    time = ""
    if from_user.is_bot:
        time += "🤖 Bot :("
    elif from_user.status == enums.UserStatus.RECENTLY:
        time += "Recently"
    elif from_user.status == enums.UserStatus.LAST_WEEK:
        time += "Within the last week"
    elif from_user.status == enums.UserStatus.LAST_MONTH:
        time += "Within the last month"
    elif from_user.status == enums.UserStatus.LONG_AGO:
        time += "A long time ago :("
    elif from_user.status == enums.UserStatus.ONLINE:
        time += "Currently Online"
    elif from_user.status == enums.UserStatus.OFFLINE:
        time += from_user.last_online_date.strftime("%a, %d %b %Y, %H:%M:%S")
    return time

def split_quotes(text: str) -> List:
    if not any(text.startswith(char) for char in START_CHAR):
        return text.split(None, 1)
    counter = 1  # ignore first char -> is some kind of quote
    while counter < len(text):
        if text[counter] == "\\":
            counter += 1
        elif text[counter] == text[0] or (text[0] == SMART_OPEN and text[counter] == SMART_CLOSE):
            break
        counter += 1
    else:
        return text.split(None, 1)

    # 1 to avoid starting quote, and counter is exclusive so avoids ending
    key = remove_escapes(text[1:counter].strip())
    # index will be in range, or `else` would have been executed and returned
    rest = text[counter + 1:].strip()
    if not key:
        key = text[0] + text[0]
    return list(filter(None, [key, rest]))

def gfilterparser(text, keyword):
    if "buttonalert" in text:
        text = (text.replace("\n", "\\n").replace("\t", "\\t"))
    buttons = []
    note_data = ""
    prev = 0
    i = 0
    alerts = []
    for match in BTN_URL_REGEX.finditer(text):
        # Check if btnurl is escaped
        n_escapes = 0
        to_check = match.start(1) - 1
        while to_check > 0 and text[to_check] == "\\":
            n_escapes += 1
            to_check -= 1

        # if even, not escaped -> create button
        if n_escapes % 2 == 0:
            note_data += text[prev:match.start(1)]
            prev = match.end(1)
            if match.group(3) == "buttonalert":
                # create a thruple with button label, url, and newline status
                if bool(match.group(5)) and buttons:
                    buttons[-1].append(InlineKeyboardButton(
                        text=match.group(2),
                        callback_data=f"gfilteralert:{i}:{keyword}"
                    ))
                else:
                    buttons.append([InlineKeyboardButton(
                        text=match.group(2),
                        callback_data=f"gfilteralert:{i}:{keyword}"
                    )])
                i += 1
                alerts.append(match.group(4))
            elif bool(match.group(5)) and buttons:
                buttons[-1].append(InlineKeyboardButton(
                    text=match.group(2),
                    url=match.group(4).replace(" ", "")
                ))
            else:
                buttons.append([InlineKeyboardButton(
                    text=match.group(2),
                    url=match.group(4).replace(" ", "")
                )])

        else:
            note_data += text[prev:to_check]
            prev = match.start(1) - 1
    else:
        note_data += text[prev:]

    try:
        return note_data, buttons, alerts
    except:
        return note_data, buttons, None

def parser(text, keyword):
    if "buttonalert" in text:
        text = (text.replace("\n", "\\n").replace("\t", "\\t"))
    buttons = []
    note_data = ""
    prev = 0
    i = 0
    alerts = []
    for match in BTN_URL_REGEX.finditer(text):
        # Check if btnurl is escaped
        n_escapes = 0
        to_check = match.start(1) - 1
        while to_check > 0 and text[to_check] == "\\":
            n_escapes += 1
            to_check -= 1

        # if even, not escaped -> create button
        if n_escapes % 2 == 0:
            note_data += text[prev:match.start(1)]
            prev = match.end(1)
            if match.group(3) == "buttonalert":
                # create a thruple with button label, url, and newline status
                if bool(match.group(5)) and buttons:
                    buttons[-1].append(InlineKeyboardButton(
                        text=match.group(2),
                        callback_data=f"alertmessage:{i}:{keyword}"
                    ))
                else:
                    buttons.append([InlineKeyboardButton(
                        text=match.group(2),
                        callback_data=f"alertmessage:{i}:{keyword}"
                    )])
                i += 1
                alerts.append(match.group(4))
            elif bool(match.group(5)) and buttons:
                buttons[-1].append(InlineKeyboardButton(
                    text=match.group(2),
                    url=match.group(4).replace(" ", "")
                ))
            else:
                buttons.append([InlineKeyboardButton(
                    text=match.group(2),
                    url=match.group(4).replace(" ", "")
                )])

        else:
            note_data += text[prev:to_check]
            prev = match.start(1) - 1
    else:
        note_data += text[prev:]

    try:
        return note_data, buttons, alerts
    except:
        return note_data, buttons, None

def remove_escapes(text: str) -> str:
    res = ""
    is_escaped = False
    for counter in range(len(text)):
        if is_escaped:
            res += text[counter]
            is_escaped = False
        elif text[counter] == "\\":
            is_escaped = True
        else:
            res += text[counter]
    return res

def humanbytes(size):
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'



async def get_clone_shortlink(link, url, api):
    shortzy = Shortzy(api_key=api, base_site=url)
    link = await shortzy.convert(link)
    return link

async def get_shortlink(chat_id, link):
    settings = await get_settings(chat_id) #fetching settings for group
    if 'shortlink' in settings.keys():
        URL = settings['shortlink']
        API = settings['shortlink_api']
    else:
        URL = SHORTLINK_URL
        API = SHORTLINK_API
    if URL.startswith("shorturllink") or URL.startswith("terabox.in") or URL.startswith("urlshorten.in"):
        URL = SHORTLINK_URL
        API = SHORTLINK_API
    if URL == "api.shareus.io":
        url = f'https://{URL}/easy_api'
        params = {
            "key": API,
            "link": link,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, raise_for_status=True, ssl=False) as response:
                    data = await response.text()
                    return data
        except Exception as e:
            logger.error(e)
            return link
    else:
        shortzy = Shortzy(api_key=API, base_site=URL)
        link = await shortzy.convert(link)
        return link

async def get_tutorial(chat_id):
    settings = await get_settings(chat_id) #fetching settings for group
    return settings['tutorial']

async def get_verify_shorted_link(link, url, api):
    API = api
    URL = url
    if URL == "api.shareus.io":
        url = f'https://{URL}/easy_api'
        params = {
            "key": API,
            "link": link,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, raise_for_status=True, ssl=False) as response:
                    data = await response.text()
                    return data
        except Exception as e:
            logger.error(e)
            return link
    else:
        shortzy = Shortzy(api_key=API, base_site=URL)
        link = await shortzy.convert(link)
        return link

async def check_token(bot, userid, token):
    try:
        user = await bot.get_users(userid)
        if not await db.is_user_exist(user.id):
            await db.add_user(user.id, user.first_name)
            try:
                await bot.send_message(LOG_CHANNEL, script.LOG_TEXT_P.format(user.id, user.mention))
            except Exception as e:
                logger.error(f"Failed to send log message: {e}")

        if user.id in TOKENS.keys():
            TKN = TOKENS[user.id]
            if token in TKN.keys():
                is_used = TKN[token]
                if is_used == True:
                    return False
                else:
                    # Mark token as used
                    TOKENS[user.id][token] = True
                    return True
        else:
            return False
    except Exception as e:
        logger.error(f"Error in check_token: {e}")
        return False

async def get_token(bot, userid, link):
    try:
        user = await bot.get_users(userid)
        if not await db.is_user_exist(user.id):
            await db.add_user(user.id, user.first_name)
            try:
                await bot.send_message(LOG_CHANNEL, script.LOG_TEXT_P.format(user.id, user.mention))
            except Exception as e:
                logger.error(f"Failed to send log message: {e}")

        token = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        TOKENS[user.id] = {token: False}
        link = f"{link}verify-{user.id}-{token}"

        try:
            shortened_verify_url = await get_verify_shorted_link(link, VERIFY_SHORTLINK_URL, VERIFY_SHORTLINK_API)
            if VERIFY_SECOND_SHORTNER == True:
                snd_link = await get_verify_shorted_link(shortened_verify_url, VERIFY_SND_SHORTLINK_URL, VERIFY_SND_SHORTLINK_API)
                return str(snd_link)
            else:
                return str(shortened_verify_url)
        except Exception as e:
            logger.error(f"Error shortening verification link: {e}")
            return link
    except Exception as e:
        logger.error(f"Error in get_token: {e}")
        return link

async def verify_user(bot, userid, token):
    try:
        from bot.verification import verification_manager
        return await verification_manager.verify_user(userid, token, bot)
    except Exception as e:
        logger.error(f"Error in verify_user: {e}")
        return False

async def check_verification(bot, userid):
    try:
        from verification_storage import verification_storage
        # Use JSON storage for faster checking
        return verification_storage.is_user_verified(userid)
    except Exception as e:
        logger.error(f"Error in check_verification: {e}")
        return False

async def send_all(bot, userid, files, ident, chat_id, user_name, query):
    settings = await get_settings(chat_id)
    if 'is_shortlink' in settings.keys():
        ENABLE_SHORTLINK = settings['is_shortlink']
    else:
        await save_group_settings(message.chat.id, 'is_shortlink', False)
        ENABLE_SHORTLINK = False
    try:
        if ENABLE_SHORTLINK:
            for file in files:
                title = file["file_name"]
                size = get_size(file["file_size"])
                if not await db.has_premium_access(userid) and SHORTLINK_MODE == True:
                    await bot.send_message(chat_id=userid, text=f"<b>Hᴇʏ ᴛʜᴇʀᴇ {user_name} 👋🏽 \n\n✅ Sᴇᴄᴜʀᴇ ʟɪɴᴋ ᴛᴏ ʏᴏᴜʀ ғɪʟᴇ ʜᴀs sᴜᴄᴄᴇssғᴜʟʟʏ ʙᴇᴇɴ ɢᴇɴᴇʀᴀᴛᴇᴅ ᴘʟᴇᴀsᴇ ᴄʟɪᴄᴋ ᴅᴏᴡɴʟᴏᴀᴅ ʙᴜᴛᴛᴏɴ\n\n🗃️ Fɪʟᴇ Nᴀᴍᴇ : {title}\n🔖 Fɪʟᴇ Sɪᴢᴇ : {size}</b>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📤 Dᴏᴡɴʟᴏᴀᴅ 📥", url=await get_shortlink(chat_id, f"https://telegram.me/{temp.U_NAME}?start=files_{file['file_id']}"))]]))
        else:
            for file in files:
                f_caption = file["caption"]
                title = file["file_name"]
                size = get_size(file["file_size"])
                if CUSTOM_FILE_CAPTION:
                    try:
                        f_caption = CUSTOM_FILE_CAPTION.format(
                            file_name='' if title is None else title,
                            file_size='' if size is None else size,
                            file_caption='' if f_caption is None else f_caption
                        )
                    except Exception as e:
                        print(e)
                        f_caption = f_caption
                if f_caption is None:
                    f_caption = f"{title}"
                await bot.send_cached_media(
                    chat_id=userid,
                    file_id=file["file_id"],
                    caption=f_caption,
                    protect_content=True if ident == "filep" else False,
                    reply_markup=InlineKeyboardMarkup(
                        [[
                            InlineKeyboardButton('Sᴜᴘᴘᴏʀᴛ Gʀᴏᴜᴘ', url=GRP_LNK),
                            InlineKeyboardButton('Uᴘᴅᴀᴛᴇs Cʜᴀɴɴᴇʟ', url=CHNL_LNK)
                        ],[
                            InlineKeyboardButton("Bᴏᴛ Oᴡɴᴇʀ", url=OWNER_LNK)
                        ]]
                    )
                )
    except UserIsBlocked:
        await query.answer('Uɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ ᴍᴀʜɴ !', show_alert=True)
    except PeerIdInvalid:
        await query.answer('Hᴇʏ, Sᴛᴀʀᴛ Bᴏᴛ Fɪʀsᴛ Aɴᴅ Cʟɪᴄᴋ Sᴇɴᴅ Aʟʟ', show_alert=True)
    except Exception as e:
        await query.answer('Hᴇʏ, Sᴛᴀʀᴛ Bᴏᴛ Fɪʀsᴛ Aɴᴅ Cʟɪᴄᴋ Sᴇɴᴅ Aʟʟ', show_alert=True)

async def get_cap(settings, remaining_seconds, files, query, total_results, search):
    if settings["imdb"]:
        IMDB_CAP = temp.IMDB_CAP.get(query.from_user.id)
        if IMDB_CAP:
            cap = IMDB_CAP
            cap+="<b>\n\n<u>🍿 Your Movie Files 👇</u></b>\n\n"
            for file in files:
                 cap += f"<b>\n{idx}. <a href='https://telegram.me/{temp.U_NAME}?start=file_{message.chat.id}_{file.file_id}'>[{get_size(file.file_size)}] {clean_filename(file.file_name)}\n</a></b>"
        else:
            imdb = await get_poster(search, file=(files[0])["file_name"]) if settings["imdb"] else None
            if imdb:
                TEMPLATE = script.IMDB_TEMPLATE_TXT
                cap = TEMPLATE.format(
                    qurey=search,
                    title=imdb['title'],
                    votes=imdb['votes'],
                    aka=imdb["aka"],
                    seasons=imdb["seasons"],
                    box_office=imdb['box_office'],
                    localized_title=imdb['localized_title'],
                    kind=imdb['kind'],
                    imdb_id=imdb["imdb_id"],
                    cast=imdb["cast"],
                    runtime=imdb["runtime"],
                    countries=imdb["countries"],
                    certificates=imdb["certificates"],
                    languages=imdb["languages"],
                    director=imdb["director"],
                    writer=imdb["writer"],
                    producer=imdb["producer"],
                    composer=imdb["composer"],
                    cinematographer=imdb["cinematographer"],
                    music_team=imdb["music_department"],
                    distributors=imdb["distributors"],
                    release_date=imdb['release_date'],
                    year=imdb['year'],
                    genres=imdb['genres'],
                    poster=imdb['poster'],
                    plot=imdb['plot'],
                    rating=imdb['rating'],
                    url=imdb['url'],
                    **locals()
                )
                cap+="<b>\n\n<u>🍿 Your Movie Files 👇</u></b>\n\n"
                for file in files:
                     cap += f"<b>\n{idx}. <a href='https://telegram.me/{temp.U_NAME}?start=file_{message.chat.id}_{file.file_id}'>[{get_size(file.file_size)}] {clean_filename(file.file_name)}\n</a></b>"
            else:
                cap = f"<b>Tʜᴇ Rᴇꜱᴜʟᴛꜱ Fᴏʀ ☞ {search}\n\nRᴇǫᴜᴇsᴛᴇᴅ Bʏ ☞ {query.from_user.mention}\n\nʀᴇsᴜʟᴛ sʜᴏᴡ ɪɴ ☞ {remaining_seconds} sᴇᴄᴏɴᴅs\n\nᴘᴏᴡᴇʀᴇᴅ ʙʏ ☞ : {query.message.chat.title}\n\n⚠️ ᴀꜰᴛᴇʀ 5 ᴍɪɴᴜᴛᴇꜱ ᴛʜɪꜱ ᴍᴇꜱꜱᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴅᴇʟᴇᴛᴇᴅ 🗑️\n\n</b>"
                cap+="<b><u>🍿 Your Movie Files 👇</u></b>\n\n"
                for file in files:
                     cap += f"<b>\n{idx}. <a href='https://telegram.me/{temp.U_NAME}?start=file_{message.chat.id}_{file.file_id}'>[{get_size(file.file_size)}] {clean_filename(file.file_name)}\n</a></b>"
    else:
        cap = f"<b>Tʜᴇ Rᴇꜱᴜʟᴛꜱ Fᴏʀ ☞ {search}\n\nRᴇǫᴜᴇsᴛᴇᴅ Bʏ ☞ {query.from_user.mention}\n\nʀᴇsᴜʟᴛ sʜᴏᴡ ɪɴ ☞ {remaining_seconds} sᴇᴄᴏɴᴅs\n\nᴘᴏᴡᴇʀᴇᴅ ʙʏ ☞ : {query.message.chat.title} \n\n⚠️ ᴀꜰᴛᴇʀ 5 ᴍɪɴᴜᴛᴇꜱ ᴛʜɪꜱ ᴍᴇꜱꜱᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴅᴇʟᴇᴛᴇᴅ 🗑️\n\n</b>"
        cap+="<b><u>🍿 Your Movie Files 👇</u></b>\n\n"
        for file in files:
             cap += f"<b>\n{idx}. <a href='https://telegram.me/{temp.U_NAME}?start=file_{message.chat.id}_{file.file_id}'>[{get_size(file.file_size)}] {clean_filename(file.file_name)}\n</a></b>"
    return cap


async def get_seconds(time_string):
    def extract_value_and_unit(ts):
        value = ""
        unit = ""
        index = 0
        while index < len(ts) and ts[index].isdigit():
            value += ts[index]
            index += 1
        unit = ts[index:]
        if value:
            value = int(value)
        return value, unit
    value, unit = extract_value_and_unit(time_string)
    if unit == 's':
        return value
    elif unit == 'min':
        return value * 60
    elif unit == 'hour':
        return value * 3600
    elif unit == 'day':
        return value * 86400
    elif unit == 'month':
        return value * 86400 * 30
    elif unit == 'year':
        return value * 86400 * 365
    else:
        return 0

def format_file_button(file):
    """Format file button with enhanced info extraction - Format: {file_size} | {movie_name} {year} {language} {quality}"""
    filename = file['file_name']
    file_size = get_size(file['file_size'])

    # Replace ! with | in filename if present
    filename = filename.replace('!', '|')

    # Extract enhanced info using improved methods
    movie_info = extract_enhanced_movie_info(filename, file.get('caption', ''))

    # Build button text: {file_size} | {movie_name} {year} {language} {quality}
    button_parts = [file_size, "|"]

    if movie_info['name']:
        # Also replace ! with | in movie name
        movie_name = movie_info['name'].replace('!', '|')
        button_parts.append(movie_name)

    details = []
    if movie_info['year']:
        details.append(movie_info['year'])
    if movie_info['language']:
        details.append(movie_info['language'])
    if movie_info['quality']:
        details.append(movie_info['quality'])

    if details:
        button_parts.append(" ".join(details))

    return " ".join(button_parts)

def extract_enhanced_movie_info(filename, caption_text=None):
    """Extract movie name, year, language, and quality from filename and caption"""
    import re

    logger.info(f"🔍 Starting enhanced extraction for: {filename}")

    # Remove file extension
    name_without_ext = re.sub(r'\.[^.]+$', '', filename)

    # Step 1: Extract Year
    year = extract_year_from_filename(name_without_ext)

    # Step 2: Extract Quality using token-based method
    quality = extract_quality_from_tokens(name_without_ext)

    # Step 3: Extract Language from both filename and caption, prioritize caption
    language = extract_language_comprehensive(name_without_ext, caption_text)

    # Step 4: Extract clean movie name (remove bad words first)
    movie_name = extract_clean_movie_name_enhanced(name_without_ext, year, quality, language)

    return {
        'name': movie_name,
        'year': year,
        'language': language,
        'quality': quality
    }

def extract_year_from_filename(filename):
    """Extract year from filename using the method from example code"""
    import re

    # Look for 4-digit year patterns
    year_pattern = re.compile(r"(?<![A-Za-z0-9])(?:19|20)\d{2}(?![A-Za-z0-9])")
    year_match = year_pattern.search(filename)

    if year_match:
        year = year_match.group(0)
        logger.info(f"📅 Found year: {year}")
        return year

    logger.info(f"📅 No year found")
    return None

def extract_quality_from_tokens(filename):
    """Extract quality using token-based method from example code"""
    import re

    logger.info(f"🎯 Extracting quality from: {filename}")

    # Split into tokens using multiple delimiters
    tokens = re.split(r'[\s\-_\.]+', filename)
    quality_tokens = []

    # Quality indicators to look for (comprehensive list from example)
    quality_patterns = {
        'hdcam': 'HDCAM', 'hdtc': 'HDTC', 'camrip': 'CAMRip', 'cam': 'CAM',
        'ts': 'TS', 'tc': 'TC', 'telesync': 'TeleSync',
        'dvdscr': 'DVDScr', 'dvdrip': 'DVDRip', 'predvd': 'PreDVD',
        'webrip': 'WEBRip', 'web-dl': 'WEB-DL', 'webdl': 'WEBRip', 'web': 'WEB',
        'tvrip': 'TVRip', 'hdtv': 'HDTV', 'bluray': 'BluRay', 'brrip': 'BRRip',
        'bdrip': 'BDRip', 'hevc': 'HEVC', 'hdrip': 'HDRip',
        '360p': '360p', '480p': '480p', '720p': '720p', '1080p': '1080p',
        '2160p': '2160p', '4k': '4K', '1440p': '1440p', '540p': '540p',
        '240p': '240p', '140p': '140p', 'uhd': 'UHD', 'fhd': 'FHD', 'hd': 'HD'
    }

    for token in tokens:
        # Clean token but preserve original case for display
        token_clean = re.sub(r'[@#~\-_()]+', '', token).lower()
        if token_clean in quality_patterns:
            quality_tokens.append(quality_patterns[token_clean])
            logger.info(f"✅ Found quality token: {token_clean} -> {quality_patterns[token_clean]}")

    # Also check for resolution patterns that might be written differently
    resolution_pattern = re.search(r'\b(\d{3,4})p?\b', filename, re.IGNORECASE)
    if resolution_pattern:
        res_value = resolution_pattern.group(1)
        if res_value in ['360', '480', '720', '1080', '2160']:
            res_quality = f"{res_value}p"
            if res_quality not in quality_tokens:
                quality_tokens.append(res_quality)
                logger.info(f"✅ Found resolution pattern: {res_quality}")

    # Remove duplicates while preserving order and limit to 2 most important
    unique_qualities = []
    for quality in quality_tokens:
        if quality not in unique_qualities:
            unique_qualities.append(quality)

    result = " ".join(unique_qualities[:2]) if unique_qualities else None
    logger.info(f"🎯 Final quality: {result}")
    return result

def extract_language_comprehensive(filename, caption_text=None):
    """Extract language from both filename and caption, prioritizing caption hashtags"""
    import re

    logger.info(f"🌍 Extracting language from filename: {filename}")
    if caption_text:
        logger.info(f"📝 Caption available for language extraction")

    all_languages = []

    # Step 1: Extract from caption first (hashtags and text patterns)
    if caption_text:
        caption_languages = extract_language_from_caption(caption_text)
        if caption_languages and caption_languages != "N/A":
            all_languages.extend(caption_languages.split(", "))
            logger.info(f"✅ Found caption languages: {caption_languages}")

    # Step 2: Extract from filename tokens
    filename_languages = extract_language_from_tokens(filename)
    if filename_languages and filename_languages != "N/A":
        filename_langs = filename_languages.split(", ")
        for lang in filename_langs:
            if lang not in all_languages:
                all_languages.append(lang)
        logger.info(f"✅ Found filename languages: {filename_languages}")

    # Step 3: Check for bracket format like [Tam + Tel + Hin]
    bracket_languages = extract_bracket_languages(filename)
    if bracket_languages:
        for lang in bracket_languages:
            if lang not in all_languages:
                all_languages.append(lang)
        logger.info(f"✅ Found bracket languages: {', '.join(bracket_languages)}")

    # Remove duplicates and limit to 3 languages
    unique_languages = []
    for lang in all_languages:
        if lang not in unique_languages:
            unique_languages.append(lang)

    result = "+".join(unique_languages[:3]) if unique_languages else None
    logger.info(f"🌍 Final comprehensive language: {result}")
    return result

def extract_language_from_caption(caption_text):
    """Extract language from message caption (hashtags and plain text patterns)"""
    import re

    if not caption_text:
        return "N/A"

    logger.info(f"🌍 Extracting language from caption: {caption_text[:100]}...")

    # Clean caption text by removing special characters @ ~ # etc.
    caption_cleaned = re.sub(r'[@~#\-_()]+', ' ', caption_text)
    caption_cleaned = re.sub(r'\s+', ' ', caption_cleaned).strip()
    logger.info(f"🧹 Cleaned caption: {caption_cleaned[:100]}...")

    language_tokens = []

    # Enhanced language mapping including abbreviations and full names
    lang_mapping = {
        'hindi': 'Hindi', 'hin': 'Hindi', 'english': 'English', 'eng': 'English',
        'tamil': 'Tamil', 'tam': 'Tamil', 'telugu': 'Telugu', 'tel': 'Telugu',
        'malayalam': 'Malayalam', 'mal': 'Malayalam', 'kannada': 'Kannada', 'kan': 'Kannada',
        'bengali': 'Bengali', 'ben': 'Bengali', 'marathi': 'Marathi', 'mar': 'Marathi',
        'gujarati': 'Gujarati', 'guj': 'Gujarati', 'punjabi': 'Punjabi', 'pun': 'Punjabi',
        'urdu': 'Urdu', 'urd': 'Urdu', 'korean': 'Korean', 'kor': 'Korean',
        'japanese': 'Japanese', 'jpn': 'Japanese', 'chinese': 'Chinese', 'mandarin': 'Chinese'
    }

    # Method 1: Look for hashtag patterns like #Hindi, #Tamil etc.
    hashtag_pattern = re.findall(r'#(\w+)', caption_text)
    for hashtag in hashtag_pattern:
        hashtag_lower = hashtag.lower()
        if hashtag_lower in lang_mapping:
            language_name = lang_mapping[hashtag_lower]
            if language_name not in language_tokens:
                language_tokens.append(language_name)
                logger.info(f"✅ Found caption hashtag language: #{hashtag} -> {language_name}")

    # Method 2: Check for plain text language mentions (word boundaries)
    for lang_key, lang_name in lang_mapping.items():
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(lang_key) + r'\b'
        if re.search(pattern, caption_cleaned, re.IGNORECASE) and lang_name not in language_tokens:
            language_tokens.append(lang_name)
            logger.info(f"✅ Found caption plain text language: {lang_key} -> {lang_name}")

    # Method 3: Check for bracketed language format like [Tamil + Telugu]
    bracket_pattern = re.search(r'\[([^\]]+)\]', caption_text)
    if bracket_pattern:
        bracket_content = bracket_pattern.group(1)
        # Split by + and check each language
        bracket_langs = re.split(r'\s*\+\s*', bracket_content)
        for lang in bracket_langs:
            lang_clean = re.sub(r'[@#~\-_()]+', '', lang).strip().lower()
            if lang_clean in lang_mapping:
                language_name = lang_mapping[lang_clean]
                if language_name not in language_tokens:
                    language_tokens.append(language_name)
                    logger.info(f"✅ Found bracket language: {lang_clean} -> {language_name}")

    # Method 4: Check for common patterns like "Tamil Movie", "Hindi Film" etc.
    context_patterns = [
        r'\b(Tamil|Hindi|English|Telugu|Malayalam|Kannada|Bengali|Marathi|Gujarati|Punjabi|Urdu)\s+(Movie|Film|Cinema)\b',
        r'\b(Movie|Film|Cinema)\s+in\s+(Tamil|Hindi|English|Telugu|Malayalam|Kannada|Bengali|Marathi|Gujarati|Punjabi|Urdu)\b'
    ]

    for pattern in context_patterns:
        matches = re.findall(pattern, caption_text, re.IGNORECASE)
        for match in matches:
            for lang in match:
                if lang.lower() in ['movie', 'film', 'cinema', 'in']:
                    continue
                lang_name = lang.capitalize()
                if lang_name not in language_tokens:
                    language_tokens.append(lang_name)
                    logger.info(f"✅ Found context language: {lang} -> {lang_name}")

    result = ", ".join(language_tokens) if language_tokens else "N/A"
    logger.info(f"🌍 Final caption language: {result}")
    return result

def extract_language_from_tokens(filename):
    """Extract language using token-based method"""
    import re

    # Token-based method - split filename into tokens
    tokens = re.split(r'[\s\-_\.]+', filename)
    language_tokens = []

    # Extended language patterns including exact matches
    extended_languages = {
        # Direct language names
        'hindi': 'Hindi', 'english': 'English', 'tamil': 'Tamil', 
        'telugu': 'Telugu', 'malayalam': 'Malayalam', 'kannada': 'Kannada',
        'bengali': 'Bengali', 'marathi': 'Marathi', 'gujarati': 'Gujarati',
        'punjabi': 'Punjabi', 'urdu': 'Urdu', 'korean': 'Korean', 'japanese': 'Japanese',
        # Abbreviations
        'hin': 'Hindi', 'eng': 'English', 'tam': 'Tamil', 'tel': 'Telugu',
        'mal': 'Malayalam', 'kan': 'Kannada', 'ben': 'Bengali', 'mar': 'Marathi',
        'guj': 'Gujarati', 'pun': 'Punjabi', 'urd': 'Urdu', 'kor': 'Korean', 'jpn': 'Japanese',
        # Additional patterns
        'dual': 'Dual', 'multi': 'Multi', 'dubbed': 'Dubbed',
        'org': 'Original', 'original': 'Original'
    }

    for token in tokens:
        # Clean token but preserve original case for checking
        original_token = token.lower()
        token_clean = re.sub(r'[@#~\-_()]+', '', original_token)

        # Check both cleaned and original token
        for check_token in [token_clean, original_token]:
            if check_token in extended_languages:
                language_name = extended_languages[check_token]
                if language_name not in language_tokens:
                    language_tokens.append(language_name)
                    logger.info(f"✅ Found filename language token: {check_token} -> {language_name}")

    result = ", ".join(language_tokens) if language_tokens else "N/A"
    return result

def extract_bracket_languages(filename):
    """Extract languages from bracket format like [Tam + Tel + Hin]"""
    import re

    bracket_pattern = re.search(r'\[([^\]]+)\]', filename)
    if bracket_pattern:
        bracket_content = bracket_pattern.group(1)
        logger.info(f"🔍 Found bracket content: {bracket_content}")

        # Split by + and clean each language
        bracket_langs = re.split(r'\s*\+\s*', bracket_content)
        language_tokens = []

        for lang in bracket_langs:
            lang_clean = lang.strip().lower()
            # Map common abbreviations to full names
            lang_mapping = {
                'tam': 'Tamil', 'tel': 'Telugu', 'hin': 'Hindi',
                'mal': 'Malayalam', 'kan': 'Kannada', 'eng': 'English',
                'ben': 'Bengali', 'mar': 'Marathi', 'guj': 'Gujarati',
                'pun': 'Punjabi', 'urd': 'Urdu', 'kor': 'Korean', 'jpn': 'Japanese'
            }

            if lang_clean in lang_mapping:
                language_tokens.append(lang_mapping[lang_clean])
                logger.info(f"✅ Found bracket language: {lang_clean} -> {lang_mapping[lang_clean]}")

        return language_tokens

    return []

def extract_clean_movie_name_enhanced(filename, year=None, quality=None, language=None):
    """Extract clean movie name following exact priority: BAD_WORDS (highest) -> IGNORE_WORDS -> special characters"""
    import re

    logger.info(f"🔍 Starting enhanced movie name extraction for: {filename}")

    # Step 1: Remove file extension first
    name_without_ext = re.sub(r'\.[^.]+$', '', filename)
    logger.info(f"📝 After removing extension: {name_without_ext}")

    # Step 2: NEW METHOD - Remove everything after year if year is found (HIGHEST PRIORITY)
    if year:
        # Find year position and keep only text before year
        year_pattern = rf'\b{re.escape(year)}\b'
        year_match = re.search(year_pattern, name_without_ext)
        if year_match:
            # Keep only text before the year
            name_before_year = name_without_ext[:year_match.start()].strip()
            logger.info(f"🎯 YEAR-BACKWARD METHOD: Found year '{year}' at position {year_match.start()}")
            logger.info(f"🎯 Text before year: '{name_before_year}'")
            logger.info(f"🎯 Ignored text after year: '{name_without_ext[year_match.start():].strip()}'")
            name_without_ext = name_before_year
        else:
            logger.info(f"🎯 YEAR-BACKWARD METHOD: Year '{year}' not found in filename, proceeding normally")

    # Step 3: Remove BAD_WORDS 
    clean_name = remove_bad_words_from_filename(name_without_ext)
    logger.info(f"❌ After removing BAD_WORDS (Priority 2): {clean_name}")

    # Step 4: Remove IGNORE_WORDS
    clean_name = remove_ignore_words_from_filename(clean_name)
    logger.info(f"🚫 After removing IGNORE_WORDS (Priority 3): {clean_name}")

    # Step 5: Remove special characters @ ~ # 
    clean_name = re.sub(r'[@~#]+', ' ', clean_name)
    logger.info(f"🧹 After removing special chars (@~#) (Priority 4): {clean_name}")

    # Step 6: Year already removed in step 2, so skip this step

    # Step 7: Remove quality and codec indicators (be more aggressive) - Only if year method didn't handle it
    quality_remove_patterns = [
        r'\b(4K|2160p|1080p|720p|480p|360p|240p|140p|540p|1440p)\b',
        r'\b(HDRip|WEBRip|BluRay|DVDRip|CAMRip|HDCAM|PreDVD|WEB-DL|HDTV|BRRip|BDRip|HDTC|TS|TC)\b',
        r'\b(HEVC|x264|x265|AAC|AC3|DTS|AAC2\.0)\b',
        r'\b(10bit|8bit|ESub|MSub)\b',
        r'\b(HQ|Clean|Proper|REPACK|EXTENDED)\b'
    ]

    for pattern in quality_remove_patterns:
        before = clean_name
        clean_name = re.sub(pattern, '', clean_name, flags=re.IGNORECASE)
        if before != clean_name:
            logger.info(f"🎯 Removed quality pattern: {pattern}")

    # Step 8: Remove language indicators more aggressively - Only if year method didn't handle it  
    language_remove_patterns = [
        r'\b(Hindi|Hin|Tamil|Tam|Telugu|Tel|Malayalam|Mal|Kannada|Kan)\b',
        r'\b(English|Eng|Bengali|Ben|Marathi|Mar|Gujarati|Guj|Punjabi|Pun)\b',
        r'\b(Urdu|Urd|Korean|Kor|Japanese|Jpn|Chinese|Mandarin)\b',
        r'\b(Dual\s*Audio|Multi\s*Audio|Dubbed|Original|Audio)\b',
        r'\[([^\]]*)\]',  # Remove bracket content like [Tam + Tel + Hin]
        r'\(([^\)]*)\)'   # Remove parenthesis content
    ]

    for pattern in language_remove_patterns:
        before = clean_name
        clean_name = re.sub(pattern, '', clean_name, flags=re.IGNORECASE)
        if before != clean_name:
            logger.info(f"🌍 Removed language pattern: {pattern}")

    # Step 9: Remove other unwanted patterns - Only if year method didn't handle it
    unwanted_patterns = [
        r'\b(Season|Series|Episode|EP|Part|Vol|Volume)\b',  # Series indicators
        r'\b\d+(\.\d+)?(GB|MB|KB|TB)\b',  # File sizes
        r'\b(Sample|Trailer|Teaser)\b',  # Sample files
        r'[-_~\.]{2,}',  # Multiple separators
        r'\{[^}]*\}',  # Content in curly braces
    ]

    for pattern in unwanted_patterns:
        before = clean_name
        clean_name = re.sub(pattern, '', clean_name, flags=re.IGNORECASE)
        if before != clean_name:
            logger.info(f"🗑️ Removed unwanted pattern: {pattern}")

    # Step 10: Clean up separators and normalize spaces
    clean_name = re.sub(r'[-_~\.]+', ' ', clean_name)
    clean_name = re.sub(r'\s+', ' ', clean_name)
    clean_name = clean_name.strip()
    logger.info(f"✨ After cleanup: {clean_name}")

    # Step 11: Split into tokens and final filtering
    tokens = clean_name.split()
    clean_tokens = []
    ignore_words_lower = {word.lower() for word in IGNORE_WORDS}

    for i, token in enumerate(tokens):
        logger.info(f"🔍 Processing final token {i+1}: '{token}'")

        # Skip very short tokens (unless they're meaningful like "V" in "Gen V")
        if len(token) < 2 and not (len(token) == 1 and token.isalpha()):
            logger.info(f"❌ Token too short, skipping: '{token}'")
            continue

        # Skip tokens that are just numbers 
        if token.isdigit():
            logger.info(f"❌ Token is just a number, skipping: '{token}'")
            continue

        # Skip tokens that don't contain letters
        if not any(c.isalpha() for c in token):
            logger.info(f"❌ Token has no letters, skipping: '{token}'")
            continue

        # Final check against IGNORE_WORDS
        if token.lower() in ignore_words_lower:
            logger.info(f"❌ Token found in IGNORE_WORDS, skipping: '{token}'")
            continue

        clean_tokens.append(token)
        logger.info(f"✅ Token accepted: '{token}'")

    # Step 12: Rebuild name
    if clean_tokens:
        movie_name = ' '.join(clean_tokens)
        # Proper case the name
        movie_name = ' '.join(word.capitalize() for word in movie_name.split())
        if year:
            logger.info(f"🎬 Final movie name (using year-backward method): '{movie_name}'")
        else:
            logger.info(f"🎬 Final movie name (standard method): '{movie_name}'")
        return movie_name[:50]  # Limit length for button
    else:
        logger.warning(f"⚠️ No valid tokens found, returning 'Unknown Movie'")
        return "Unknown Movie"

def remove_bad_words_from_filename(filename):
    """Remove bad words from filename with enhanced tokenization"""
    original_filename = filename
    removed_words = []

    # First split the filename into tokens using various delimiters
    # Split by common separators like spaces, dots, dashes, underscores
    import re
    tokens = re.split(r'[\s\.\-_]+', filename)

    # Remove empty tokens
    tokens = [token for token in tokens if token.strip()]

    # Remove all bad words from tokens
    cleaned_tokens = []
    for token in tokens:
        token_removed = False

        # Check exact match against each bad word (case-insensitive)
        for bad_word in BAD_WORDS:
            if token.lower() == bad_word.lower():
                removed_words.append(token)
                logger.info(f"Removed exact word match: '{token}' (matched bad word: '{bad_word}')")
                token_removed = True
                break

            # Check if the token contains the bad word as a substring
            elif bad_word.lower() in token.lower() and len(bad_word) > 2:  # Only for longer bad words
                removed_words.append(token)
                logger.info(f"Removed token containing bad word: '{token}' (contains: '{bad_word}')")
                token_removed = True
                break

            # Check if the token is contained within the bad word
            elif token.lower() in bad_word.lower() and len(token) > 2:  # Only for longer tokens
                removed_words.append(token)
                logger.info(f"Removed token found in bad word pattern: '{token}' (found in: '{bad_word}')")
                token_removed = True
                break

        if not token_removed:
            cleaned_tokens.append(token)

    # Rejoin the cleaned tokens with spaces
    cleaned_filename = ' '.join(cleaned_tokens)

    # Clean up extra spaces
    cleaned_filename = ' '.join(cleaned_filename.split())

    # Log the cleaning result
    if removed_words:
        logger.info(f"BAD WORDS REMOVAL: Original: '{original_filename}' -> Cleaned: '{cleaned_filename}' | Removed words: {removed_words}")
    else:
        logger.info(f"BAD WORDS REMOVAL: No bad words found in '{original_filename}'")

    return cleaned_filename

def remove_ignore_words_from_filename(filename):
    """Remove IGNORE_WORDS from filename with enhanced tokenization"""
    import re

    original_filename = filename
    removed_words = []

    # Split the filename into tokens using various delimiters
    tokens = re.split(r'[\s\.\-_~]+', filename)
    tokens = [token for token in tokens if token.strip()]

    # Convert IGNORE_WORDS to lowercase set for faster lookup
    ignore_words_lower = {word.lower() for word in IGNORE_WORDS}

    # Remove all ignore words
    cleaned_tokens = []
    for token in tokens:
        # Clean token by removing special characters but keep original for comparison
        token_cleaned = re.sub(r'[@#~\-_()]+', '', token)
        token_lower = token_cleaned.lower()

        # Skip empty tokens after cleaning
        if not token_cleaned:
            continue

        token_removed = False

        # Check exact match against IGNORE_WORDS (case-insensitive)
        if token_lower in ignore_words_lower:
            removed_words.append(token)
            logger.info(f"Removed IGNORE_WORD exact match: '{token}' -> '{token_lower}'")
            token_removed = True
        else:
            # Check if token contains any ignore word as substring (for longer words)
            for ignore_word in IGNORE_WORDS:
                if len(ignore_word) > 3:  # Only check longer ignore words for substring match
                    if ignore_word.lower() in token_lower:
                        removed_words.append(token)
                        logger.info(f"Removed token containing IGNORE_WORD: '{token}' (contains: '{ignore_word}')")
                        token_removed = True
                        break

        if not token_removed:
            cleaned_tokens.append(token_cleaned)  # Use cleaned version

    # Rejoin the cleaned tokens with spaces
    clean_filename_result = ' '.join(cleaned_tokens)
    clean_filename_result = ' '.join(clean_filename_result.split())  # Clean up extra spaces

    if removed_words:
        logger.info(f"IGNORE WORDS REMOVAL: Original: '{original_filename}' -> Cleaned: '{clean_filename_result}' | Removed words: {removed_words}")
    else:
        logger.info(f"IGNORE WORDS REMOVAL: No ignore words found in '{original_filename}'")

    return clean_filename_result

def start_scheduler():
    """Initialize any scheduled tasks or background processes"""
    # Placeholder function for scheduler initialization
    # Add any scheduled task setup here if needed
    pass