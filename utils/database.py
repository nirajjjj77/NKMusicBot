"""
Database Manager - Handles all database operations
"""

import asyncio
import logging
import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime
import aiosqlite
from config import Config

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.db_path = "musicbot.db"
        
    async def initialize(self):
        """Initialize database and create tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Users table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    is_banned BOOLEAN DEFAULT FALSE,
                    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_songs_played INTEGER DEFAULT 0
                )
            """)
            
            # Chats table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS chats (
                    chat_id INTEGER PRIMARY KEY,
                    chat_title TEXT,
                    chat_type TEXT DEFAULT 'group',
                    is_active BOOLEAN DEFAULT TRUE,
                    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_songs_played INTEGER DEFAULT 0
                )
            """)
            
            # Songs history table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS song_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    user_id INTEGER,
                    song_title TEXT,
                    song_url TEXT,
                    song_duration INTEGER,
                    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chat_id) REFERENCES chats (chat_id),
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # Playlists table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS playlists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    playlist_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_public BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # Playlist songs table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS playlist_songs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    playlist_id INTEGER,
                    song_title TEXT,
                    song_url TEXT,
                    song_duration INTEGER,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (playlist_id) REFERENCES playlists (id)
                )
            """)
            
            # Bot statistics table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS bot_stats (
                    id INTEGER PRIMARY KEY,
                    total_users INTEGER DEFAULT 0,
                    total_chats INTEGER DEFAULT 0,
                    total_songs_played INTEGER DEFAULT 0,
                    bot_start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert initial stats if not exists
            await db.execute("""
                INSERT OR IGNORE INTO bot_stats (id, bot_start_time) 
                VALUES (1, CURRENT_TIMESTAMP)
            """)
            
            await db.commit()
            
        logger.info("Database initialized successfully")
        
    async def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None):
        """Add or update user in database"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO users 
                (user_id, username, first_name, last_name, last_activity)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (user_id, username, first_name, last_name))
            await db.commit()
            
    async def add_chat(self, chat_id: int, chat_title: str = None, chat_type: str = "group"):
        """Add or update chat in database"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO chats 
                (chat_id, chat_title, chat_type, last_activity)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (chat_id, chat_title, chat_type))
            await db.commit()
            
    async def is_user_banned(self, user_id: int) -> bool:
        """Check if user is banned"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT is_banned FROM users WHERE user_id = ?", (user_id,)
            )
            result = await cursor.fetchone()
            return result and result[0]
            
    async def ban_user(self, user_id: int):
        """Ban a user"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET is_banned = TRUE WHERE user_id = ?", (user_id,)
            )
            await db.commit()
            
    async def unban_user(self, user_id: int):
        """Unban a user"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET is_banned = FALSE WHERE user_id = ?", (user_id,)
            )
            await db.commit()
            
    async def add_song_to_history(self, chat_id: int, user_id: int, song_title: str, song_url: str, duration: int):
        """Add song to play history"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO song_history 
                (chat_id, user_id, song_title, song_url, song_duration)
                VALUES (?, ?, ?, ?, ?)
            """, (chat_id, user_id, song_title, song_url, duration))
            
            # Update user stats
            await db.execute("""
                UPDATE users SET total_songs_played = total_songs_played + 1,
                last_activity = CURRENT_TIMESTAMP WHERE user_id = ?
            """, (user_id,))
            
            # Update chat stats
            await db.execute("""
                UPDATE chats SET total_songs_played = total_songs_played + 1,
                last_activity = CURRENT_TIMESTAMP WHERE chat_id = ?
            """, (chat_id,))
            
            # Update bot stats
            await db.execute("""
                UPDATE bot_stats SET total_songs_played = total_songs_played + 1,
                last_updated = CURRENT_TIMESTAMP WHERE id = 1
            """)
            
            await db.commit()
            
    async def get_user_stats(self, user_id: int) -> Optional[Dict]:
        """Get user statistics"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT username, first_name, total_songs_played, join_date, last_activity
                FROM users WHERE user_id = ?
            """, (user_id,))
            result = await cursor.fetchone()
            
            if result:
                return {
                    'username': result[0],
                    'first_name': result[1],
                    'total_songs_played': result[2],
                    'join_date': result[3],
                    'last_activity': result[4]
                }
            return None
            
    async def get_chat_stats(self, chat_id: int) -> Optional[Dict]:
        """Get chat statistics"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT chat_title, total_songs_played, join_date, last_activity
                FROM chats WHERE chat_id = ?
            """, (chat_id,))
            result = await cursor.fetchone()
            
            if result:
                return {
                    'chat_title': result[0],
                    'total_songs_played': result[1],
                    'join_date': result[2],
                    'last_activity': result[3]
                }
            return None
            
    async def get_bot_stats(self) -> Dict:
        """Get bot statistics"""
        async with aiosqlite.connect(self.db_path) as db:
            # Get bot stats
            cursor = await db.execute("""
                SELECT total_users, total_chats, total_songs_played, bot_start_time
                FROM bot_stats WHERE id = 1
            """)
            bot_stats = await cursor.fetchone()
            
            # Get actual counts
            cursor = await db.execute("SELECT COUNT(*) FROM users")
            total_users = (await cursor.fetchone())[0]
            
            cursor = await db.execute("SELECT COUNT(*) FROM chats WHERE is_active = TRUE")
            total_chats = (await cursor.fetchone())[0]
            
            cursor = await db.execute("SELECT COUNT(*) FROM song_history")
            total_songs = (await cursor.fetchone())[0]
            
            # Update bot stats
            await db.execute("""
                UPDATE bot_stats SET 
                total_users = ?, total_chats = ?, total_songs_played = ?,
                last_updated = CURRENT_TIMESTAMP WHERE id = 1
            """, (total_users, total_chats, total_songs))
            await db.commit()
            
            return {
                'total_users': total_users,
                'total_chats': total_chats,
                'total_songs_played': total_songs,
                'bot_start_time': bot_stats[3] if bot_stats else None
            }
            
    async def get_top_users(self, limit: int = 10) -> List[Dict]:
        """Get top users by songs played"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT user_id, username, first_name, total_songs_played
                FROM users ORDER BY total_songs_played DESC LIMIT ?
            """, (limit,))
            results = await cursor.fetchall()
            
            return [
                {
                    'user_id': result[0],
                    'username': result[1],
                    'first_name': result[2],
                    'total_songs_played': result[3]
                }
                for result in results
            ]
            
    async def get_top_chats(self, limit: int = 10) -> List[Dict]:
        """Get top chats by songs played"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT chat_id, chat_title, total_songs_played
                FROM chats WHERE is_active = TRUE 
                ORDER BY total_songs_played DESC LIMIT ?
            """, (limit,))
            results = await cursor.fetchall()
            
            return [
                {
                    'chat_id': result[0],
                    'chat_title': result[1],
                    'total_songs_played': result[2]
                }
                for result in results
            ]
            
    async def get_recent_songs(self, chat_id: int, limit: int = 10) -> List[Dict]:
        """Get recently played songs in a chat"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT s.song_title, s.song_url, s.played_at, u.username, u.first_name
                FROM song_history s
                JOIN users u ON s.user_id = u.user_id
                WHERE s.chat_id = ?
                ORDER BY s.played_at DESC LIMIT ?
            """, (chat_id, limit))
            results = await cursor.fetchall()
            
            return [
                {
                    'song_title': result[0],
                    'song_url': result[1],
                    'played_at': result[2],
                    'username': result[3],
                    'first_name': result[4]
                }
                for result in results
            ]
            
    async def create_playlist(self, user_id: int, playlist_name: str, is_public: bool = False) -> int:
        """Create a new playlist"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO playlists (user_id, playlist_name, is_public)
                VALUES (?, ?, ?)
            """, (user_id, playlist_name, is_public))
            await db.commit()
            return cursor.lastrowid
            
    async def add_song_to_playlist(self, playlist_id: int, song_title: str, song_url: str, duration: int):
        """Add song to playlist"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO playlist_songs (playlist_id, song_title, song_url, song_duration)
                VALUES (?, ?, ?, ?)
            """, (playlist_id, song_title, song_url, duration))
            await db.commit()
            
    async def get_user_playlists(self, user_id: int) -> List[Dict]:
        """Get user's playlists"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT id, playlist_name, created_at, is_public,
                       (SELECT COUNT(*) FROM playlist_songs WHERE playlist_id = p.id) as song_count
                FROM playlists p WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
            results = await cursor.fetchall()
            
            return [
                {
                    'id': result[0],
                    'name': result[1],
                    'created_at': result[2],
                    'is_public': result[3],
                    'song_count': result[4]
                }
                for result in results
            ]
            
    async def get_playlist_songs(self, playlist_id: int) -> List[Dict]:
        """Get songs in a playlist"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT song_title, song_url, song_duration, added_at
                FROM playlist_songs WHERE playlist_id = ?
                ORDER BY added_at ASC
            """, (playlist_id,))
            results = await cursor.fetchall()
            
            return [
                {
                    'title': result[0],
                    'url': result[1],
                    'duration': result[2],
                    'added_at': result[3]
                }
                for result in results
            ]
            
    async def delete_playlist(self, playlist_id: int, user_id: int) -> bool:
        """Delete a playlist"""
        async with aiosqlite.connect(self.db_path) as db:
            # Check if playlist belongs to user
            cursor = await db.execute(
                "SELECT user_id FROM playlists WHERE id = ?", (playlist_id,)
            )
            result = await cursor.fetchone()
            
            if not result or result[0] != user_id:
                return False
                
            # Delete playlist songs first
            await db.execute("DELETE FROM playlist_songs WHERE playlist_id = ?", (playlist_id,))
            # Delete playlist
            await db.execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))
            await db.commit()
            return True
            
    async def get_all_users(self) -> List[int]:
        """Get all user IDs for broadcasting"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT user_id FROM users WHERE is_banned = FALSE")
            results = await cursor.fetchall()
            return [result[0] for result in results]
            
    async def get_popular_songs(self, limit: int = 10) -> List[Dict]:
        """Get most played songs"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT song_title, song_url, COUNT(*) as play_count
                FROM song_history
                GROUP BY song_title, song_url
                ORDER BY play_count DESC
                LIMIT ?
            """, (limit,))
            results = await cursor.fetchall()
            
            return [
                {
                    'title': result[0],
                    'url': result[1],
                    'play_count': result[2]
                }
                for result in results
            ]
            
    async def search_songs_history(self, query: str, limit: int = 10) -> List[Dict]:
        """Search in song history"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT DISTINCT s.song_title, s.song_url, s.song_duration,
                       COUNT(*) as play_count
                FROM song_history s
                WHERE s.song_title LIKE ?
                GROUP BY s.song_title, s.song_url
                ORDER BY play_count DESC
                LIMIT ?
            """, (f"%{query}%", limit))
            results = await cursor.fetchall()
            
            return [
                {
                    'title': result[0],
                    'url': result[1],
                    'duration': result[2],
                    'play_count': result[3]
                }
                for result in results
            ]
            
    async def cleanup_old_history(self, days: int = 30):
        """Clean up old song history"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                DELETE FROM song_history 
                WHERE played_at < datetime('now', '-{} days')
            """.format(days))
            await db.commit()
            
    async def deactivate_chat(self, chat_id: int):
        """Mark chat as inactive"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE chats SET is_active = FALSE WHERE chat_id = ?", (chat_id,)
            )
            await db.commit()
            
    async def close(self):
        """Close database connection"""
        # SQLite connections are closed automatically with aiosqlite
        pass