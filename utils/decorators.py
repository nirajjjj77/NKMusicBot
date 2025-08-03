"""
Decorators for bot functionality
"""

import asyncio
import logging
from functools import wraps
from typing import Dict, List
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from config import Config

logger = logging.getLogger(__name__)

# Rate limiting storage
rate_limit_storage: Dict[int, List[datetime]] = {}

def rate_limit(func):
    """Rate limiting decorator"""
    @wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        current_time = datetime.now()
        
        # Initialize user's request history
        if user_id not in rate_limit_storage:
            rate_limit_storage[user_id] = []
            
        # Clean old requests
        rate_limit_storage[user_id] = [
            request_time for request_time in rate_limit_storage[user_id]
            if current_time - request_time < timedelta(seconds=Config.RATE_LIMIT_WINDOW)
        ]
        
        # Check rate limit
        if len(rate_limit_storage[user_id]) >= Config.RATE_LIMIT_REQUESTS:
            await update.message.reply_text(
                f"🚫 **Rate limit exceeded!**\n"
                f"Please wait {Config.RATE_LIMIT_WINDOW} seconds before making another request.",
                parse_mode='Markdown'
            )
            return
            
        # Add current request
        rate_limit_storage[user_id].append(current_time)
        
        # Execute function
        return await func(self, update, context, *args, **kwargs)
    return wrapper

def admin_only(func):
    """Admin only decorator"""
    @wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        if user_id not in Config.SUDO_USERS:
            await update.message.reply_text(
                "🚫 **Access Denied!**\n"
                "This command is only available to bot administrators.",
                parse_mode='Markdown'
            )
            return
            
        return await func(self, update, context, *args, **kwargs)
    return wrapper

def is_user_banned(func):
    """Check if user is banned decorator"""
    @wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        # Check if user is banned
        if hasattr(self, 'db') and await self.db.is_user_banned(user_id):
            await update.message.reply_text(
                "🚫 **You are banned from using this bot!**\n"
                "Contact bot administrator if you think this is an error.",
                parse_mode='Markdown'
            )
            return
            
        return await func(self, update, context, *args, **kwargs)
    return wrapper

def log_command(func):
    """Log command usage decorator"""
    @wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        chat = update.effective_chat
        command = update.message.text.split()[0] if update.message and update.message.text else "unknown"
        
        logger.info(
            f"Command used: {command} by {user.first_name} ({user.id}) "
            f"in {chat.title or 'Private'} ({chat.id})"
        )
        
        return await func(self, update, context, *args, **kwargs)
    return wrapper

def voice_chat_only(func):
    """Voice chat only decorator"""
    @wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        chat_id = update.effective_chat.id
        
        # Check if it's a group/supergroup
        if update.effective_chat.type not in ['group', 'supergroup']:
            await update.message.reply_text(
                "❌ This command can only be used in groups with voice chats!",
                parse_mode='Markdown'
            )
            return
            
        return await func(self, update, context, *args, **kwargs)
    return wrapper

def error_handler(func):
    """Error handling decorator"""
    @wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        try:
            return await func(self, update, context, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            try:
                await update.message.reply_text(
                    "❌ **An error occurred while processing your request.**\n"
                    "Please try again later or contact the administrator.",
                    parse_mode='Markdown'
                )
            except Exception as reply_error:
                logger.error(f"Failed to send error message: {reply_error}")
    return wrapper

def typing_action(func):
    """Send typing action decorator"""
    @wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        chat_id = update.effective_chat.id
        
        # Send typing action
        typing_task = asyncio.create_task(
            context.bot.send_chat_action(chat_id, "typing")
        )
        
        try:
            # Execute function
            result = await func(self, update, context, *args, **kwargs)
            return result
        finally:
            # Cancel typing action
            typing_task.cancel()
            try:
                await typing_task
            except asyncio.CancelledError:
                pass
                
    return wrapper

def channel_log(func):
    """Log to channel decorator"""
    @wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        # Execute function first
        result = await func(self, update, context, *args, **kwargs)
        
        # Log to channel if configured
        log_channel = os.getenv('LOG_CHANNEL_ID')
        if log_channel:
            try:
                user = update.effective_user
                chat = update.effective_chat
                command = update.message.text.split()[0] if update.message and update.message.text else "unknown"
                
                log_message = (
                    f"📊 **Command Log**\n"
                    f"**Command:** {command}\n"
                    f"**User:** {user.first_name} (`{user.id}`)\n"
                    f"**Chat:** {chat.title or 'Private'} (`{chat.id}`)\n"
                    f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                
                await context.bot.send_message(
                    chat_id=int(log_channel),
                    text=log_message,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.warning(f"Failed to log to channel: {e}")
                
        return result
    return wrapper

def premium_only(func):
    """Premium users only decorator (placeholder for future premium features)"""
    @wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        # For now, treat admins as premium users
        if user_id not in Config.SUDO_USERS:
            await update.message.reply_text(
                "💎 **Premium Feature**\n"
                "This feature is only available to premium users.\n"
                "Contact bot administrator for more information.",
                parse_mode='Markdown'
            )
            return
            
        return await func(self, update, context, *args, **kwargs)
    return wrapper

def maintenance_mode(func):
    """Maintenance mode decorator"""
    @wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        maintenance = os.getenv('MAINTENANCE_MODE', 'false').lower() == 'true'
        user_id = update.effective_user.id
        
        if maintenance and user_id not in Config.SUDO_USERS:
            await update.message.reply_text(
                "🔧 **Bot is under maintenance**\n"
                "Please try again later. We'll be back soon!",
                parse_mode='Markdown'
            )
            return
            
        return await func(self, update, context, *args, **kwargs)
    return wrapper