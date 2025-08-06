"""
Configuration file for Telegram Music Bot
"""

import os
from typing import List

class Config:
    # Bot credentials
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    API_ID = int(os.getenv("API_ID", "0"))
    API_HASH = os.getenv("API_HASH", "")

    # User session string (for voice chat functionality)
    # Generate this using the generate_session.py script
    USER_SESSION_STRING = os.getenv("USER_SESSION_STRING", "")
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///musicbot.db")
    
    # Audio settings
    BITRATE = int(os.getenv("BITRATE", "512"))
    FPS = int(os.getenv("FPS", "20"))
    
    # Bot settings
    OWNER_ID = int(os.getenv("OWNER_ID", "0"))
    SUDO_USERS: List[int] = []
    
    # Load sudo users from environment
    sudo_users_str = os.getenv("SUDO_USERS", "")
    if sudo_users_str:
        SUDO_USERS = [int(x.strip()) for x in sudo_users_str.split(",") if x.strip().isdigit()]
    
    # Add owner to sudo users
    if OWNER_ID and OWNER_ID not in SUDO_USERS:
        SUDO_USERS.append(OWNER_ID)
    
    # Music settings
    MAX_QUEUE_SIZE = int(os.getenv("MAX_QUEUE_SIZE", "50"))
    MAX_SONG_DURATION = int(os.getenv("MAX_SONG_DURATION", "1800"))  # 30 minutes
    DEFAULT_VOLUME = int(os.getenv("DEFAULT_VOLUME", "100"))
    
    # YouTube settings
    YOUTUBE_COOKIES_PATH = os.getenv("YOUTUBE_COOKIES_PATH", "")
    
    # File paths
    DOWNLOADS_PATH = os.getenv("DOWNLOADS_PATH", "./downloads")
    LOGS_PATH = os.getenv("LOGS_PATH", "./logs")
    
    # Create directories if they don't exist
    os.makedirs(DOWNLOADS_PATH, exist_ok=True)
    os.makedirs(LOGS_PATH, exist_ok=True)
    
    # Rate limiting
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "10"))
    RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds
    
    # Features
    ENABLE_LYRICS = os.getenv("ENABLE_LYRICS", "true").lower() == "true"
    ENABLE_SPOTIFY = os.getenv("ENABLE_SPOTIFY", "false").lower() == "true"
    ENABLE_DEEZER = os.getenv("ENABLE_DEEZER", "false").lower() == "true"
    
    # Spotify credentials (if enabled)
    SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
    SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
    
    # Messages
    START_MESSAGE = """
🎵 **Welcome to Advanced Music Bot!**

I can play music in your voice chats with many advanced features:

**Basic Commands:**
• /play [song name/url] - Play music
• /pause - Pause current song
• /resume - Resume playback
• /skip - Skip current song
• /stop - Stop playback and clear queue
• /queue - Show current queue
• /np - Show now playing

**Advanced Features:**
• /shuffle - Shuffle queue
• /loop [off/song/queue] - Loop mode
• /volume [1-200] - Adjust volume
• /lyrics - Get song lyrics

Type /help for more commands!
"""
    
    HELP_MESSAGE = """
🎵 **Music Bot Commands**

**Music Control:**
• `/play` or `/p` - Play song from YouTube/Spotify/URL
• `/pause` - Pause current song
• `/resume` - Resume playback
• `/skip` - Skip to next song
• `/stop` - Stop music and clear queue

**Queue Management:**
• `/queue` or `/q` - Show current queue
• `/shuffle` - Shuffle current queue
• `/loop` [off/song/queue] - Set loop mode

**Information:**
• `/np` - Show currently playing song
• `/lyrics` - Get lyrics for current song
• `/volume` [1-200] - Adjust playback volume

**Admin Commands:**
• `/stats` - Show bot statistics
• `/ban` [user_id] - Ban user from bot
• `/unban` [user_id] - Unban user
• `/broadcast` [message] - Send message to all users

**Supported Sources:**
• YouTube (links and search)
• Spotify (if enabled)
• Direct audio file URLs

Join a voice chat and start playing music! 🎶
"""