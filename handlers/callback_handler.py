"""
Callback Handler - Handles inline keyboard callbacks
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import Config
from utils.database import Database
from utils.audio_manager import AudioManager

logger = logging.getLogger(__name__)

class CallbackHandler:
    def __init__(self, db: Database, audio_manager: AudioManager):
        self.db = db
        self.audio_manager = audio_manager
        
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all callback queries"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        
        try:
            if data == "help":
                await self._handle_help(query)
            elif data == "stats":
                await self._handle_stats(query)
            elif data == "join_vc":
                await self._handle_join_vc(query, context)
            elif data.startswith("pause_"):
                await self._handle_pause(query, context)
            elif data.startswith("resume_"):
                await self._handle_resume(query, context)
            elif data.startswith("skip_"):
                await self._handle_skip(query, context)
            elif data.startswith("stop_"):
                await self._handle_stop(query, context)
            elif data.startswith("shuffle_"):
                await self._handle_shuffle(query)
            elif data.startswith("queue_"):
                await self._handle_queue(query)
            elif data.startswith("clear_queue_"):
                await self._handle_clear_queue(query)
            elif data.startswith("loop_"):
                await self._handle_loop(query)
            elif data.startswith("lyrics_"):
                await self._handle_lyrics(query, context)
            elif data == "refresh_stats":
                await self._handle_refresh_stats(query)
            elif data == "detailed_stats":
                await self._handle_detailed_stats(query)
            elif data == "confirm_broadcast":
                await self._handle_confirm_broadcast(query, context)
            elif data == "cancel_broadcast":
                await self._handle_cancel_broadcast(query)
            elif data == "confirm_restart":
                await self._handle_confirm_restart(query, context)
            elif data == "cancel_restart":
                await self._handle_cancel_restart(query)
            else:
                await query.edit_message_text("❌ Unknown callback data!")
                
        except Exception as e:
            logger.error(f"Error handling callback {data}: {e}")
            try:
                await query.edit_message_text("❌ An error occurred!")
            except:
                pass
                
    async def _handle_help(self, query):
        """Handle help callback"""
        await query.edit_message_text(
            Config.HELP_MESSAGE,
            parse_mode='Markdown'
        )
        
    async def _handle_stats(self, query):
        """Handle stats callback"""
        bot_stats = await self.db.get_bot_stats()
        
        message = f"""📊 **Quick Stats**

👥 **Users:** {bot_stats['total_users']}
💬 **Active Chats:** {bot_stats['total_chats']}
🎵 **Songs Played:** {bot_stats['total_songs_played']}
"""
        
        keyboard = [
            [InlineKeyboardButton("📈 Detailed Stats", callback_data="detailed_stats"),
             InlineKeyboardButton("🔄 Refresh", callback_data="refresh_stats")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    async def _handle_join_vc(self, query, context):
        """Handle join voice chat callback"""
        chat_id = query.message.chat_id
        
        try:
            if await self.audio_manager.is_in_voice_chat(chat_id):
                await query.edit_message_text("✅ **Already connected to voice chat!**", parse_mode='Markdown')
            else:
                await self.audio_manager.join_voice_chat(chat_id)
                await query.edit_message_text("✅ **Joined voice chat successfully!**", parse_mode='Markdown')
        except Exception as e:
            await query.edit_message_text(
                f"❌ **Failed to join voice chat:**\n`{str(e)}`",
                parse_mode='Markdown'
            )
            
    async def _handle_pause(self, query, context):
        """Handle pause callback"""
        chat_id = int(query.data.split("_")[1])
        
        if await self.audio_manager.pause(chat_id):
            # Update button to resume
            keyboard = [
                [InlineKeyboardButton("▶️ Resume", callback_data=f"resume_{chat_id}"),
                 InlineKeyboardButton("⏭️ Skip", callback_data=f"skip_{chat_id}")],
                [InlineKeyboardButton("🔀 Shuffle", callback_data=f"shuffle_{chat_id}"),
                 InlineKeyboardButton("📋 Queue", callback_data=f"queue_{chat_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_reply_markup(reply_markup=reply_markup)
            await context.bot.send_message(chat_id, "⏸️ **Playback paused**", parse_mode='Markdown')
        else:
            await context.bot.send_message(chat_id, "❌ Nothing is playing!")
            
    async def _handle_resume(self, query, context):
        """Handle resume callback"""
        chat_id = int(query.data.split("_")[1])
        
        if await self.audio_manager.resume(chat_id):
            # Update button to pause
            keyboard = [
                [InlineKeyboardButton("⏸️ Pause", callback_data=f"pause_{chat_id}"),
                 InlineKeyboardButton("⏭️ Skip", callback_data=f"skip_{chat_id}")],
                [InlineKeyboardButton("🔀 Shuffle", callback_data=f"shuffle_{chat_id}"),
                 InlineKeyboardButton("📋 Queue", callback_data=f"queue_{chat_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_reply_markup(reply_markup=reply_markup)
            await context.bot.send_message(chat_id, "▶️ **Playback resumed**", parse_mode='Markdown')
        else:
            await context.bot.send_message(chat_id, "❌ Nothing is paused!")
            
    async def _handle_skip(self, query, context):
        """Handle skip callback"""
        chat_id = int(query.data.split("_")[1])
        
        current_track = await self.audio_manager.get_current_track(chat_id)
        if current_track:
            await self.audio_manager.skip(chat_id)
            await context.bot.send_message(
                chat_id, 
                f"⏭️ **Skipped:** {current_track['title']}", 
                parse_mode='Markdown'
            )
        else:
            await context.bot.send_message(chat_id, "❌ Nothing is playing!")
            
    async def _handle_stop(self, query, context):
        """Handle stop callback"""
        chat_id = int(query.data.split("_")[1])
        
        await self.audio_manager.stop(chat_id)
        await context.bot.send_message(
            chat_id, 
            "⏹️ **Playback stopped and queue cleared**", 
            parse_mode='Markdown'
        )
        
    async def _handle_shuffle(self, query):
        """Handle shuffle callback"""
        chat_id = int(query.data.split("_")[1])
        
        if await self.audio_manager.shuffle_queue(chat_id):
            await query.edit_message_text("🔀 **Queue shuffled!**", parse_mode='Markdown')
        else:
            await query.edit_message_text("❌ Queue is empty!")
            
    async def _handle_queue(self, query):
        """Handle queue callback"""
        chat_id = int(query.data.split("_")[1])
        
        queue = await self.audio_manager.get_queue(chat_id)
        current_track = await self.audio_manager.get_current_track(chat_id)
        
        if not current_track and not queue:
            await query.edit_message_text("📋 **Queue is empty!**", parse_mode='Markdown')
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
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    async def _handle_clear_queue(self, query):
        """Handle clear queue callback"""
        chat_id = int(query.data.split("_")[2])
        
        await self.audio_manager.clear_queue(chat_id)
        await query.edit_message_text("🗑️ **Queue cleared!**", parse_mode='Markdown')
        
    async def _handle_loop(self, query):
        """Handle loop callback"""
        chat_id = int(query.data.split("_")[1])
        
        current_mode = await self.audio_manager.get_loop_mode(chat_id)
        
        # Cycle through loop modes
        if current_mode == "off":
            new_mode = "song"
        elif current_mode == "song":
            new_mode = "queue"
        else:
            new_mode = "off"
            
        await self.audio_manager.set_loop_mode(chat_id, new_mode)
        
        mode_emojis = {"off": "➡️", "song": "🔂", "queue": "🔁"}
        await query.edit_message_text(
            f"{mode_emojis[new_mode]} **Loop mode: {new_mode}**",
            parse_mode='Markdown'
        )
        
    async def _handle_lyrics(self, query, context):
        """Handle lyrics callback"""
        chat_id = int(query.data.split("_")[1])
        
        if not Config.ENABLE_LYRICS:
            await query.edit_message_text("❌ Lyrics feature is disabled!")
            return
            
        current_track = await self.audio_manager.get_current_track(chat_id)
        if not current_track:
            await query.edit_message_text("❌ Nothing is playing!")
            return
            
        await query.edit_message_text("🔍 **Searching for lyrics...**", parse_mode='Markdown')
        
        try:
            from utils.youtube_downloader import YouTubeDownloader
            youtube_dl = YouTubeDownloader()
            lyrics = await youtube_dl.get_lyrics(current_track['title'])
            
            if lyrics:
                # Split lyrics if too long
                if len(lyrics) > 4000:
                    lyrics = lyrics[:4000] + "...\n\n[Lyrics truncated]"
                    
                await query.edit_message_text(
                    f"📝 **Lyrics for:** {current_track['title']}\n\n{lyrics}",
                    parse_mode='Markdown'
                )
            else:
                await query.edit_message_text("❌ Lyrics not found!")
        except Exception as e:
            logger.error(f"Error getting lyrics: {e}")
            await query.edit_message_text("❌ Error getting lyrics!")
            
    async def _handle_refresh_stats(self, query):
        """Handle refresh stats callback"""
        await self._handle_stats(query)
        
    async def _handle_detailed_stats(self, query):
        """Handle detailed stats callback"""
        bot_stats = await self.db.get_bot_stats()
        top_users = await self.db.get_top_users(10)
        top_chats = await self.db.get_top_chats(10)
        popular_songs = await self.db.get_popular_songs(10)
        
        message = f"""📊 **Detailed Statistics**

📈 **Bot Stats:**
👥 Users: {bot_stats['total_users']}
💬 Active Chats: {bot_stats['total_chats']}
🎵 Total Songs: {bot_stats['total_songs_played']}
🚀 Started: {bot_stats['bot_start_time'][:19] if bot_stats['bot_start_time'] else 'Unknown'}

🏆 **Top Users:**
"""
        
        for i, user in enumerate(top_users[:5], 1):
            name = user['first_name'] or user['username'] or f"User {user['user_id']}"
            message += f"{i}. {name} - {user['total_songs_played']} songs\n"
            
        message += "\n🏆 **Top Chats:**\n"
        for i, chat in enumerate(top_chats[:5], 1):
            chat_name = chat['chat_title'] or f"Chat {chat['chat_id']}"
            message += f"{i}. {chat_name} - {chat['total_songs_played']} songs\n"
            
        keyboard = [
            [InlineKeyboardButton("🔙 Back", callback_data="stats")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    async def _handle_confirm_broadcast(self, query, context):
        """Handle confirm broadcast callback"""
        user_id = query.from_user.id
        
        # Check if user is admin
        if user_id not in Config.SUDO_USERS:
            await query.edit_message_text("🚫 **Access Denied!**", parse_mode='Markdown')
            return
            
        broadcast_message = context.user_data.get('broadcast_message')
        if not broadcast_message:
            await query.edit_message_text("❌ No broadcast message found!")
            return
            
        await query.edit_message_text("📢 **Starting broadcast...**", parse_mode='Markdown')
        
        # Execute broadcast
        from handlers.admin_handler import AdminHandler
        admin_handler = AdminHandler(self.db)
        await admin_handler.execute_broadcast(context, broadcast_message, query.message.chat_id)
        
    async def _handle_cancel_broadcast(self, query):
        """Handle cancel broadcast callback"""
        await query.edit_message_text("❌ **Broadcast cancelled**", parse_mode='Markdown')
        
    async def _handle_confirm_restart(self, query, context):
        """Handle confirm restart callback"""
        user_id = query.from_user.id
        
        # Check if user is admin
        if user_id not in Config.SUDO_USERS:
            await query.edit_message_text("🚫 **Access Denied!**", parse_mode='Markdown')
            return
            
        await query.edit_message_text("🔄 **Restarting bot...**", parse_mode='Markdown')
        
        # Cleanup and restart
        import os
        import sys
        
        try:
            # Stop all music playback
            for chat_id in list(self.audio_manager.current_tracks.keys()):
                await self.audio_manager.stop(chat_id)
                
            # Close database connections
            await self.db.close()
            
            # Restart process
            os.execv(sys.executable, ['python'] + sys.argv)
        except Exception as e:
            logger.error(f"Error restarting: {e}")
            await context.bot.send_message(
                query.message.chat_id,
                "❌ Error restarting bot!"
            )
            
    async def _handle_cancel_restart(self, query):
        """Handle cancel restart callback"""
        await query.edit_message_text("❌ **Restart cancelled**", parse_mode='Markdown')