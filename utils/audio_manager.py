"""
Audio Manager - Handles all audio playback and queue management
"""

import asyncio
import logging
import random
from typing import Dict, List, Optional, Any
from pytgcalls import PyTgCalls
from pytgcalls.media_devices import StreamType
from pytgcalls.types.input_stream import AudioPiped
from pytgcalls.types.input_stream.quality import HighQualityAudio
from pyrogram import Client
from config import Config

logger = logging.getLogger(__name__)

class AudioManager:
    def __init__(self):
        self.pyrogram_client = Client(
            "musicbot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN
        )
        self.pytgcalls = PyTgCalls(self.pyrogram_client)
        
        # Chat states
        self.queues: Dict[int, List[Dict]] = {}
        self.current_tracks: Dict[int, Optional[Dict]] = {}
        self.loop_modes: Dict[int, str] = {}  # off, song, queue
        self.volumes: Dict[int, int] = {}
        self.paused_chats: set = set()
        
        # Initialize PyTgCalls
        self.pytgcalls.on_stream_end()(self._on_stream_end)
        
    async def initialize(self):
        """Initialize the audio manager"""
        await self.pyrogram_client.start()
        await self.pytgcalls.start()
        logger.info("Audio manager initialized")
        
    async def cleanup(self):
        """Cleanup resources"""
        await self.pytgcalls.stop()
        await self.pyrogram_client.stop()
        
    async def is_in_voice_chat(self, chat_id: int) -> bool:
        """Check if bot is in voice chat"""
        try:
            call = await self.pytgcalls.get_call(chat_id)
            return call is not None
        except:
            return False
            
    async def join_voice_chat(self, chat_id: int):
        """Join voice chat"""
        try:
            # Initialize chat state
            if chat_id not in self.queues:
                self.queues[chat_id] = []
                self.current_tracks[chat_id] = None
                self.loop_modes[chat_id] = "off"
                self.volumes[chat_id] = Config.DEFAULT_VOLUME
                
            # Try to join the voice chat with silent audio initially
            await self.pytgcalls.join_group_call(
                chat_id,
                AudioPiped(
                    "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav",
                    HighQualityAudio()
                ),
                stream_type=StreamType().local_stream
            )
            logger.info(f"Joined voice chat in {chat_id}")
            
        except Exception as e:
            logger.error(f"Failed to join voice chat {chat_id}: {e}")
            raise
            
    async def leave_voice_chat(self, chat_id: int):
        """Leave voice chat"""
        try:
            await self.pytgcalls.leave_group_call(chat_id)
            # Clean up chat state
            self.queues.pop(chat_id, None)
            self.current_tracks.pop(chat_id, None)
            self.loop_modes.pop(chat_id, None)
            self.volumes.pop(chat_id, None)
            self.paused_chats.discard(chat_id)
            logger.info(f"Left voice chat in {chat_id}")
        except Exception as e:
            logger.error(f"Error leaving voice chat {chat_id}: {e}")
            
    async def add_to_queue(self, chat_id: int, track_info: Dict, user_id: int) -> int:
        """Add track to queue and return position"""
        if chat_id not in self.queues:
            self.queues[chat_id] = []
            
        # Check queue size limit
        if len(self.queues[chat_id]) >= Config.MAX_QUEUE_SIZE:
            raise Exception(f"Queue is full! Maximum {Config.MAX_QUEUE_SIZE} tracks allowed.")
            
        track_info['requested_by'] = user_id
        track_info['requester_name'] = "Unknown"  # Will be updated by caller
        
        self.queues[chat_id].append(track_info)
        return len(self.queues[chat_id])
        
    async def play_next(self, chat_id: int) -> bool:
        """Play next track in queue"""
        if chat_id not in self.queues or not self.queues[chat_id]:
            return False
            
        next_track = self.queues[chat_id].pop(0)
        self.current_tracks[chat_id] = next_track
        
        try:
            # Change stream to new track
            await self.pytgcalls.change_stream(
                chat_id,
                AudioPiped(
                    next_track['file_path'],
                    HighQualityAudio()
                )
            )
            
            # Set volume
            volume = self.volumes.get(chat_id, Config.DEFAULT_VOLUME)
            await self.pytgcalls.change_volume_call(chat_id, volume)
            
            logger.info(f"Playing {next_track['title']} in chat {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error playing track in {chat_id}: {e}")
            return False
            
    async def pause(self, chat_id: int) -> bool:
        """Pause playback"""
        try:
            if await self.is_in_voice_chat(chat_id) and chat_id not in self.paused_chats:
                await self.pytgcalls.pause_stream(chat_id)
                self.paused_chats.add(chat_id)
                return True
        except Exception as e:
            logger.error(f"Error pausing in {chat_id}: {e}")
        return False
        
    async def resume(self, chat_id: int) -> bool:
        """Resume playback"""
        try:
            if chat_id in self.paused_chats:
                await self.pytgcalls.resume_stream(chat_id)
                self.paused_chats.remove(chat_id)
                return True
        except Exception as e:
            logger.error(f"Error resuming in {chat_id}: {e}")
        return False
        
    async def skip(self, chat_id: int) -> bool:
        """Skip current track"""
        if chat_id in self.current_tracks:
            return await self.play_next(chat_id)
        return False
        
    async def stop(self, chat_id: int):
        """Stop playback and clear queue"""
        try:
            if await self.is_in_voice_chat(chat_id):
                await self.leave_voice_chat(chat_id)
        except Exception as e:
            logger.error(f"Error stopping playback in {chat_id}: {e}")
            
    async def get_queue(self, chat_id: int) -> List[Dict]:
        """Get current queue"""
        return self.queues.get(chat_id, [])
        
    async def get_current_track(self, chat_id: int) -> Optional[Dict]:
        """Get currently playing track"""
        return self.current_tracks.get(chat_id)
        
    async def shuffle_queue(self, chat_id: int) -> bool:
        """Shuffle the queue"""
        if chat_id in self.queues and self.queues[chat_id]:
            random.shuffle(self.queues[chat_id])
            return True
        return False
        
    async def clear_queue(self, chat_id: int):
        """Clear the queue"""
        if chat_id in self.queues:
            self.queues[chat_id].clear()
            
    async def get_loop_mode(self, chat_id: int) -> str:
        """Get loop mode"""
        return self.loop_modes.get(chat_id, "off")
        
    async def set_loop_mode(self, chat_id: int, mode: str):
        """Set loop mode"""
        self.loop_modes[chat_id] = mode
        
    async def get_volume(self, chat_id: int) -> int:
        """Get volume"""
        return self.volumes.get(chat_id, Config.DEFAULT_VOLUME)
        
    async def set_volume(self, chat_id: int, volume: int):
        """Set volume"""
        self.volumes[chat_id] = volume
        try:
            if await self.is_in_voice_chat(chat_id):
                await self.pytgcalls.change_volume_call(chat_id, volume)
        except Exception as e:
            logger.error(f"Error setting volume in {chat_id}: {e}")
            
    async def get_progress(self, chat_id: int) -> str:
        """Get playback progress"""
        # This is a placeholder - actual implementation would depend on PyTgCalls capabilities
        return "00:00 / 00:00"
        
    async def voice_chat_started(self, chat_id: int):
        """Handle voice chat start"""
        logger.info(f"Voice chat started in {chat_id}")
        
    async def voice_chat_ended(self, chat_id: int):
        """Handle voice chat end"""
        logger.info(f"Voice chat ended in {chat_id}")
        await self.stop(chat_id)
        
    async def _on_stream_end(self, client, update):
        """Handle stream end event"""
        chat_id = update.chat_id
        logger.info(f"Stream ended in chat {chat_id}")
        
        # Handle loop modes
        loop_mode = self.loop_modes.get(chat_id, "off")
        current_track = self.current_tracks.get(chat_id)
        
        if loop_mode == "song" and current_track:
            # Repeat current song
            try:
                await self.pytgcalls.change_stream(
                    chat_id,
                    AudioPiped(
                        current_track['file_path'],
                        HighQualityAudio()
                    )
                )
            except Exception as e:
                logger.error(f"Error repeating song in {chat_id}: {e}")
                
        elif loop_mode == "queue" and current_track:
            # Add current song back to end of queue
            self.queues[chat_id].append(current_track)
            await self.play_next(chat_id)
            
        else:
            # Play next song
            if not await self.play_next(chat_id):
                # No more songs, leave voice chat
                await self.leave_voice_chat(chat_id)