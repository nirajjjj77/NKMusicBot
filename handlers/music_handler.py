"""
Music Handler - Handles all music-related commands
"""

import asyncio
import logging
import random
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ChatAction
from config import Config
from utils.database import Database
from utils.audio_manager import AudioManager
from utils.youtube_downloader import YouTubeDownloader
from utils.decorators import rate_limit, is_user_banned

logger = logging.getLogger(__name__)

class MusicHandler:
    def __init__(self, db: Database, audio_manager: AudioManager):
        self.db = db
        self.audio_manager = audio_manager
        self.youtube_dl = YouTubeDownloader()
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command handler"""
        user = update.effective_user
        chat = update.effective_chat
        
        # Add user to database
        await self.db.add_user(user.id, user.username, user.first_name)
        await self.db.add_chat(chat.id, chat.title if chat.title else f"Private_{user.id}")
        
        keyboard = [
            [InlineKeyboardButton("🎵 Join Voice Chat", callback_data="join_vc")],
            [InlineKeyboardButton("📋 Help", callback_data="help"),
             InlineKeyboardButton("📊 Stats", callback_data="stats")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            Config.START_MESSAGE,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help command handler"""
        await update.message.reply_text(
            Config.HELP_MESSAGE,
            parse_mode='Markdown'
        )
        
    @rate_limit
    @is_user_banned
    async def play(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Play command handler"""
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a song name or URL!\n"
                "Usage: `/play <song name>` or `/play <YouTube URL>`",
                parse_mode='Markdown'
            )
            return
            
        query = " ".join(context.args)
        
        # Send typing action
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        
        # Check if bot is in voice chat
        if not await self.audio_manager.is_in_voice_chat(chat_id):
            try:
                await self.audio_manager.join_voice_chat(chat_id)
            except Exception as e:
                await update.message.reply_text(
                    f"❌ Couldn't join voice chat: {str(e)}\n"
                    "Make sure there's an active voice chat and I have proper permissions!"
                )
                return
        
        # Show processing message
        processing_msg = await update.message.reply_text("🔍 Searching for music...")
        
        try:
            # Search and download
            track_info = await self.youtube_dl.search_and_download(query)
            
            if not track_info:
                await processing_msg.edit_text("❌ No results found for your query!")
                return
                
            # Add to queue
            queue_position = await self.audio_manager.add_to_queue(
                chat_id, track_info, user_id
            )
            
            if queue_position == 1:
                # Start playing immediately
                await self.audio_manager.play_next(chat_id)
                
                keyboard = [
                    [InlineKeyboardButton("⏸️ Pause", callback_data=f"pause_{chat_id}"),
                     InlineKeyboardButton("⏭️ Skip", callback_data=f"skip_{chat_id}")],
                    [InlineKeyboardButton("🔀 Shuffle", callback_data=f"shuffle_{chat_id}"),
                     InlineKeyboardButton("📋 Queue", callback_data=f"queue_{chat_id}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await processing_msg.edit_text(
                    f"🎵 **Now Playing:**\n"
                    f"**Title:** {track_info['title']}\n"
                    f"**Duration:** {track_info['duration']}\n"
                    f"**Requested by:** {update.effective_user.mention_html()}",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            else:
                await processing_msg.edit_text(
                    f"✅ **Added to Queue (Position #{queue_position}):**\n"
                    f"**Title:** {track_info['title']}\n"
                    f"**Duration:** {track_info['duration']}\n"
                    f"**Requested by:** {update.effective_user.mention_html()}",
                    parse_mode='HTML'
                )
                
        except Exception as e:
            logger.error(f"Error in play command: {e}")
            await processing_msg.edit_text(
                f"❌ An error occurred while processing your request:\n`{str(e)}`",
                parse_mode='Markdown'
            )
            
    @is_user_banned
    async def pause(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Pause current playback"""
        chat_id = update.effective_chat.id
        
        if await self.audio_manager.pause(chat_id):
            await update.message.reply_text("⏸️ **Playback paused**", parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Nothing is playing!")
            
    @is_user_banned
    async def resume(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Resume playback"""
        chat_id = update.effective_chat.id
        
        if await self.audio_manager.resume(chat_id):
            await update.message.reply_text("▶️ **Playback resumed**", parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Nothing is paused!")
            
    @is_user_banned
    async def skip(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Skip current song"""
        chat_id = update.effective_chat.id
        
        current_track = await self.audio_manager.get_current_track(chat_id)
        if not current_track:
            await update.message.reply_text("❌ Nothing is playing!")
            return
            
        await self.audio_manager.skip(chat_id)
        await update.message.reply_text(
            f"⏭️ **Skipped:** {current_track['title']}",
            parse_mode='Markdown'
        )
        
    @is_user_banned
    async def stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Stop playback and clear queue"""
        chat_id = update.effective_chat.id
        
        await self.audio_manager.stop(chat_id)
        await update.message.reply_text("⏹️ **Playback stopped and queue cleared**", parse_mode='Markdown')
        
    @is_user_banned
    async def show_queue(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show current queue"""
        chat_id = update.effective_chat.id
        
        queue = await self.audio_manager.get_queue(chat_id)
        current_track = await self.audio_manager.get_current_track(chat_id)
        
        if not current_track and not queue:
            await update.message.reply_text("📋 **Queue is empty!**", parse_mode='Markdown')
            return
            
        message = "📋 **Current Queue:**\n\n"
        
        if current_track:
            message += f"🎵 **Now Playing:**\n{current_track['title']}\n\n"
            
        if queue:
            message += "**Up Next:**\n"
            for i, track in enumerate(queue[:10], 1):
                message += f"{i}. {track['title']}\n"
                
            if len(queue) > 10:
                message += f"\n... and {len(queue) - 10} more tracks"
        else:
            message += "**Queue is empty**"
            
        keyboard = [
            [InlineKeyboardButton("🔀 Shuffle", callback_data=f"shuffle_{chat_id}"),
             InlineKeyboardButton("🗑️ Clear", callback_data=f"clear_queue_{chat_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    @is_user_banned
    async def now_playing(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show currently playing track"""
        chat_id = update.effective_chat.id
        
        current_track = await self.audio_manager.get_current_track(chat_id)
        if not current_track:
            await update.message.reply_text("❌ Nothing is playing!")
            return
            
        # Get playback info
        progress = await self.audio_manager.get_progress(chat_id)
        volume = await self.audio_manager.get_volume(chat_id)
        
        keyboard = [
            [InlineKeyboardButton("⏸️ Pause", callback_data=f"pause_{chat_id}"),
             InlineKeyboardButton("⏭️ Skip", callback_data=f"skip_{chat_id}")],
            [InlineKeyboardButton("🔄 Loop", callback_data=f"loop_{chat_id}"),
             InlineKeyboardButton("📝 Lyrics", callback_data=f"lyrics_{chat_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"🎵 **Now Playing:**\n"
            f"**Title:** {current_track['title']}\n"
            f"**Duration:** {current_track['duration']}\n"
            f"**Progress:** {progress}\n"
            f"**Volume:** {volume}%\n"
            f"**Requested by:** <a href='tg://user?id={current_track['requested_by']}'>{current_track['requester_name']}</a>",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
    @is_user_banned
    async def shuffle_queue(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Shuffle the current queue"""
        chat_id = update.effective_chat.id
        
        if await self.audio_manager.shuffle_queue(chat_id):
            await update.message.reply_text("🔀 **Queue shuffled!**", parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Queue is empty!")
            
    @is_user_banned
    async def loop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set loop mode"""
        chat_id = update.effective_chat.id
        
        if not context.args:
            # Show current loop mode
            loop_mode = await self.audio_manager.get_loop_mode(chat_id)
            await update.message.reply_text(
                f"🔄 **Current loop mode:** {loop_mode}\n"
                "**Available modes:** off, song, queue",
                parse_mode='Markdown'
            )
            return
            
        mode = context.args[0].lower()
        if mode not in ['off', 'song', 'queue']:
            await update.message.reply_text("❌ Invalid loop mode! Use: off, song, or queue")
            return
            
        await self.audio_manager.set_loop_mode(chat_id, mode)
        await update.message.reply_text(
            f"🔄 **Loop mode set to:** {mode}",
            parse_mode='Markdown'
        )
        
    @is_user_banned
    async def volume(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Adjust volume"""
        chat_id = update.effective_chat.id
        
        if not context.args:
            current_volume = await self.audio_manager.get_volume(chat_id)
            await update.message.reply_text(
                f"🔊 **Current volume:** {current_volume}%\n"
                "Usage: `/volume <1-200>`",
                parse_mode='Markdown'
            )
            return
            
        try:
            volume_level = int(context.args[0])
            if not 1 <= volume_level <= 200:
                raise ValueError
        except ValueError:
            await update.message.reply_text("❌ Volume must be between 1 and 200!")
            return
            
        await self.audio_manager.set_volume(chat_id, volume_level)
        await update.message.reply_text(
            f"🔊 **Volume set to:** {volume_level}%",
            parse_mode='Markdown'
        )
        
    @is_user_banned
    async def lyrics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get lyrics for current song"""
        if not Config.ENABLE_LYRICS:
            await update.message.reply_text("❌ Lyrics feature is disabled!")
            return
            
        chat_id = update.effective_chat.id
        current_track = await self.audio_manager.get_current_track(chat_id)
        
        if not current_track:
            await update.message.reply_text("❌ Nothing is playing!")
            return
            
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        
        try:
            lyrics = await self.youtube_dl.get_lyrics(current_track['title'])
            if lyrics:
                # Split lyrics if too long
                if len(lyrics) > 4000:
                    lyrics = lyrics[:4000] + "...\n\n[Lyrics truncated]"
                    
                await update.message.reply_text(
                    f"📝 **Lyrics for:** {current_track['title']}\n\n{lyrics}",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text("❌ Lyrics not found!")
        except Exception as e:
            logger.error(f"Error getting lyrics: {e}")
            await update.message.reply_text("❌ Error getting lyrics!")
            
    async def voice_chat_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle voice chat updates"""
        chat_id = update.effective_chat.id
        
        if update.message.voice_chat_started:
            await self.audio_manager.voice_chat_started(chat_id)
        elif update.message.voice_chat_ended:
            await self.audio_manager.voice_chat_ended(chat_id)
            await update.message.reply_text("🔇 Voice chat ended. Music stopped.")
        elif update.message.voice_chat_participants_invited:
            # Bot was invited to voice chat
            pass