"""
Admin Handler - Handles admin-only commands
"""

import logging
from typing import List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ChatAction
from config import Config
from utils.database import Database
from utils.decorators import admin_only

logger = logging.getLogger(__name__)

class AdminHandler:
    def __init__(self, db: Database):
        self.db = db
        
    @admin_only
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show bot statistics"""
        await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
        
        # Get bot stats
        bot_stats = await self.db.get_bot_stats()
        
        # Get top users and chats
        top_users = await self.db.get_top_users(5)
        top_chats = await self.db.get_top_chats(5)
        popular_songs = await self.db.get_popular_songs(5)
        
        message = f"""📊 **Bot Statistics**

👥 **Users:** {bot_stats['total_users']}
💬 **Active Chats:** {bot_stats['total_chats']}
🎵 **Total Songs Played:** {bot_stats['total_songs_played']}
🚀 **Bot Started:** {bot_stats['bot_start_time'][:19] if bot_stats['bot_start_time'] else 'Unknown'}

🏆 **Top Users:**
"""
        
        for i, user in enumerate(top_users, 1):
            name = user['first_name'] or user['username'] or f"User {user['user_id']}"
            message += f"{i}. {name} - {user['total_songs_played']} songs\n"
            
        message += "\n🏆 **Top Chats:**\n"
        for i, chat in enumerate(top_chats, 1):
            chat_name = chat['chat_title'] or f"Chat {chat['chat_id']}"
            message += f"{i}. {chat_name} - {chat['total_songs_played']} songs\n"
            
        message += "\n🎵 **Popular Songs:**\n"
        for i, song in enumerate(popular_songs, 1):
            title = song['title'][:30] + "..." if len(song['title']) > 30 else song['title']
            message += f"{i}. {title} - {song['play_count']} plays\n"
            
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_stats"),
             InlineKeyboardButton("📈 Detailed Stats", callback_data="detailed_stats")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    @admin_only
    async def ban_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ban a user from using the bot"""
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a user ID!\n"
                "Usage: `/ban <user_id>`",
                parse_mode='Markdown'
            )
            return
            
        try:
            user_id = int(context.args[0])
            
            # Don't allow banning admins
            if user_id in Config.SUDO_USERS:
                await update.message.reply_text("❌ Cannot ban admin users!")
                return
                
            await self.db.ban_user(user_id)
            await update.message.reply_text(
                f"✅ **User {user_id} has been banned!**",
                parse_mode='Markdown'
            )
            
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")
        except Exception as e:
            logger.error(f"Error banning user: {e}")
            await update.message.reply_text("❌ Error banning user!")
            
    @admin_only
    async def unban_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Unban a user"""
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a user ID!\n"
                "Usage: `/unban <user_id>`",
                parse_mode='Markdown'
            )
            return
            
        try:
            user_id = int(context.args[0])
            await self.db.unban_user(user_id)
            await update.message.reply_text(
                f"✅ **User {user_id} has been unbanned!**",
                parse_mode='Markdown'
            )
            
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")
        except Exception as e:
            logger.error(f"Error unbanning user: {e}")
            await update.message.reply_text("❌ Error unbanning user!")
            
    @admin_only
    async def broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Broadcast message to all users"""
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a message to broadcast!\n"
                "Usage: `/broadcast <message>`",
                parse_mode='Markdown'
            )
            return
            
        message = " ".join(context.args)
        
        # Confirmation
        keyboard = [
            [InlineKeyboardButton("✅ Confirm Broadcast", callback_data=f"confirm_broadcast"),
             InlineKeyboardButton("❌ Cancel", callback_data="cancel_broadcast")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Store broadcast message in context
        context.user_data['broadcast_message'] = message
        
        await update.message.reply_text(
            f"📢 **Broadcast Preview:**\n\n{message}\n\n"
            "Are you sure you want to send this message to all users?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    async def execute_broadcast(self, context: ContextTypes.DEFAULT_TYPE, message: str, chat_id: int):
        """Execute the broadcast"""
        try:
            user_ids = await self.db.get_all_users()
            successful = 0
            failed = 0
            
            await context.bot.send_message(
                chat_id,
                f"📢 **Broadcasting to {len(user_ids)} users...**",
                parse_mode='Markdown'
            )
            
            for user_id in user_ids:
                try:
                    await context.bot.send_message(
                        user_id,
                        f"📢 **Broadcast from Bot Admin:**\n\n{message}",
                        parse_mode='Markdown'
                    )
                    successful += 1
                except Exception as e:
                    failed += 1
                    logger.warning(f"Failed to send broadcast to {user_id}: {e}")
                    
            # Send results
            await context.bot.send_message(
                chat_id,
                f"✅ **Broadcast completed!**\n"
                f"**Successful:** {successful}\n"
                f"**Failed:** {failed}",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in broadcast: {e}")
            await context.bot.send_message(
                chat_id,
                "❌ Error executing broadcast!",
                parse_mode='Markdown'
            )
            
    @admin_only
    async def cleanup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Clean up old files and database entries"""
        await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
        
        try:
            # Clean up old song history (older than 30 days)
            await self.db.cleanup_old_history(30)
            
            # Clean up old downloaded files
            from utils.youtube_downloader import YouTubeDownloader
            youtube_dl = YouTubeDownloader()
            await youtube_dl.cleanup_old_files(24)  # 24 hours
            
            await update.message.reply_text(
                "✅ **Cleanup completed!**\n"
                "• Removed old song history (30+ days)\n"
                "• Cleaned up old audio files (24+ hours)",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in cleanup: {e}")
            await update.message.reply_text("❌ Error during cleanup!")
            
    @admin_only
    async def system_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show system information"""
        try:
            import psutil
            import platform
            from datetime import datetime, timedelta
            
            # System info
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            
            message = f"""🖥️ **System Information**

**OS:** {platform.system()} {platform.release()}
**Python:** {platform.python_version()}
**CPU Usage:** {cpu_percent}%
**Memory:** {memory.percent}% ({memory.used // 1024 // 1024} MB / {memory.total // 1024 // 1024} MB)
**Disk:** {disk.percent}% ({disk.used // 1024 // 1024 // 1024} GB / {disk.total // 1024 // 1024 // 1024} GB)
**Boot Time:** {boot_time.strftime('%Y-%m-%d %H:%M:%S')}
**Uptime:** {str(datetime.now() - boot_time).split('.')[0]}

**Bot Process:**
**PID:** {psutil.Process().pid}
**Memory Usage:** {psutil.Process().memory_info().rss // 1024 // 1024} MB
**CPU Time:** {psutil.Process().cpu_times().user + psutil.Process().cpu_times().system:.2f}s
"""
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except ImportError:
            await update.message.reply_text(
                "❌ psutil not installed. Install with: `pip install psutil`",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            await update.message.reply_text("❌ Error getting system information!")
            
    @admin_only
    async def backup_db(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Create database backup"""
        try:
            import shutil
            from datetime import datetime
            
            backup_name = f"musicbot_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            backup_path = f"./backups/{backup_name}"
            
            # Create backups directory
            import os
            os.makedirs('./backups', exist_ok=True)
            
            # Copy database
            shutil.copy2('./musicbot.db', backup_path)
            
            # Send backup file
            with open(backup_path, 'rb') as backup_file:
                await context.bot.send_document(
                    chat_id=update.effective_chat.id,
                    document=backup_file,
                    filename=backup_name,
                    caption=f"📦 **Database Backup**\nCreated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            await update.message.reply_text("❌ Error creating database backup!")
            
    @admin_only
    async def restart_bot(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Restart the bot"""
        keyboard = [
            [InlineKeyboardButton("✅ Confirm Restart", callback_data="confirm_restart"),
             InlineKeyboardButton("❌ Cancel", callback_data="cancel_restart")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🔄 **Are you sure you want to restart the bot?**\n"
            "This will stop all music playback and disconnect from voice chats.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    @admin_only
    async def get_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get bot logs"""
        try:
            log_file = "bot.log"
            if os.path.exists(log_file):
                # Get last 100 lines
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    last_lines = lines[-100:] if len(lines) > 100 else lines
                    
                log_content = ''.join(last_lines)
                
                # Send as file if too long
                if len(log_content) > 4000:
                    with open(log_file, 'rb') as f:
                        await context.bot.send_document(
                            chat_id=update.effective_chat.id,
                            document=f,
                            filename="bot_logs.txt",
                            caption="📋 **Bot Logs** (Last 100 lines)"
                        )
                else:
                    await update.message.reply_text(
                        f"📋 **Bot Logs (Last 100 lines):**\n\n```\n{log_content}\n```",
                        parse_mode='Markdown'
                    )
            else:
                await update.message.reply_text("❌ Log file not found!")
                
        except Exception as e:
            logger.error(f"Error getting logs: {e}")
            await update.message.reply_text("❌ Error retrieving logs!")