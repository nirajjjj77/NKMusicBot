#!/usr/bin/env python3
"""
Advanced Telegram Music Bot - Main Entry Point
"""

import asyncio
import logging
import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from config import Config
from handlers.music_handler import MusicHandler
from handlers.admin_handler import AdminHandler
from handlers.callback_handler import CallbackHandler
from utils.database import Database
from utils.audio_manager import AudioManager

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MusicBot:
    def __init__(self):
        self.app = Application.builder().token(Config.BOT_TOKEN).build()
        self.db = Database()
        self.audio_manager = AudioManager()
        self.music_handler = MusicHandler(self.db, self.audio_manager)
        self.admin_handler = AdminHandler(self.db)
        self.callback_handler = CallbackHandler(self.db, self.audio_manager)
        
    def setup_handlers(self):
        """Setup all command and message handlers"""
        # Command handlers
        self.app.add_handler(CommandHandler("start", self.music_handler.start))
        self.app.add_handler(CommandHandler("help", self.music_handler.help_command))
        self.app.add_handler(CommandHandler("play", self.music_handler.play))
        self.app.add_handler(CommandHandler("p", self.music_handler.play))
        self.app.add_handler(CommandHandler("pause", self.music_handler.pause))
        self.app.add_handler(CommandHandler("resume", self.music_handler.resume))
        self.app.add_handler(CommandHandler("skip", self.music_handler.skip))
        self.app.add_handler(CommandHandler("stop", self.music_handler.stop))
        self.app.add_handler(CommandHandler("queue", self.music_handler.show_queue))
        self.app.add_handler(CommandHandler("q", self.music_handler.show_queue))
        self.app.add_handler(CommandHandler("np", self.music_handler.now_playing))
        self.app.add_handler(CommandHandler("shuffle", self.music_handler.shuffle_queue))
        self.app.add_handler(CommandHandler("loop", self.music_handler.loop))
        self.app.add_handler(CommandHandler("volume", self.music_handler.volume))
        self.app.add_handler(CommandHandler("lyrics", self.music_handler.lyrics))
        
        # Admin handlers
        self.app.add_handler(CommandHandler("stats", self.admin_handler.stats))
        self.app.add_handler(CommandHandler("ban", self.admin_handler.ban_user))
        self.app.add_handler(CommandHandler("unban", self.admin_handler.unban_user))
        self.app.add_handler(CommandHandler("broadcast", self.admin_handler.broadcast))
        
        # Callback query handler
        self.app.add_handler(CallbackQueryHandler(self.callback_handler.handle_callback))
        
        # Message handler for voice chat updates
        self.app.add_handler(MessageHandler(
            filters.StatusUpdate.VIDEO_CHAT_STARTED |
            filters.StatusUpdate.VIDEO_CHAT_ENDED |
            filters.StatusUpdate.VIDEO_CHAT_PARTICIPANTS_INVITED,
            self.music_handler.voice_chat_update
        ))
        
        # Error handler
        self.app.add_error_handler(self.error_handler)
        
    async def error_handler(self, update, context):
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}")
        
    async def initialize(self):
        """Initialize bot components"""
        await self.db.initialize()
        await self.audio_manager.initialize()  # <-- ADD THIS
        logger.info("Bot initialized successfully")
        
    async def start_bot(self):
        """Start the bot"""
        await self.initialize()
        self.setup_handlers()
        
        logger.info("Starting bot...")
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
        
        try:
            # Keep the bot running
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        finally:
            await self.app.stop()
            await self.db.close()

async def main():
    """Main function"""
    bot = MusicBot()
    await bot.start_bot()

if __name__ == "__main__":
    # Check if required environment variables are set
    required_vars = ['BOT_TOKEN', 'API_ID', 'API_HASH']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        exit(1)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped")