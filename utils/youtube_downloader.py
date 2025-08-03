"""
YouTube Downloader - Handles music search and download
"""

import asyncio
import logging
import os
import yt_dlp
from typing import Optional, Dict, List
from youtubesearchpython import VideosSearch
from config import Config

logger = logging.getLogger(__name__)

class YouTubeDownloader:
    def __init__(self):
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'extractaudio': True,
            'audioformat': 'mp3',
            'outtmpl': f'{Config.DOWNLOADS_PATH}/%(title)s.%(ext)s',
            'restrictfilenames': True,
            'no_warnings': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_color': True,
            'extractflat': False,
            'writethumbnail': False,
            'writeinfojson': False,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        
        # Add cookies if available
        if Config.YOUTUBE_COOKIES_PATH and os.path.exists(Config.YOUTUBE_COOKIES_PATH):
            self.ydl_opts['cookiefile'] = Config.YOUTUBE_COOKIES_PATH
            
    async def search_youtube(self, query: str, limit: int = 1) -> List[Dict]:
        """Search YouTube for videos"""
        try:
            search = VideosSearch(query, limit=limit)
            results = await asyncio.get_event_loop().run_in_executor(
                None, search.result
            )
            
            videos = []
            for video in results['result']:
                duration_str = video.get('duration', '0:00')
                duration_parts = duration_str.split(':')
                
                # Convert duration to seconds
                if len(duration_parts) == 2:
                    duration_seconds = int(duration_parts[0]) * 60 + int(duration_parts[1])
                elif len(duration_parts) == 3:
                    duration_seconds = int(duration_parts[0]) * 3600 + int(duration_parts[1]) * 60 + int(duration_parts[2])
                else:
                    duration_seconds = 0
                    
                # Check duration limit
                if duration_seconds > Config.MAX_SONG_DURATION:
                    continue
                    
                videos.append({
                    'id': video['id'],
                    'title': video['title'],
                    'duration': duration_str,
                    'duration_seconds': duration_seconds,
                    'url': video['link'],
                    'thumbnail': video['thumbnails'][0]['url'] if video['thumbnails'] else None,
                    'channel': video['channel']['name'],
                    'views': video['viewCount']['text'] if video['viewCount'] else 'Unknown'
                })
                
            return videos
            
        except Exception as e:
            logger.error(f"Error searching YouTube: {e}")
            return []
            
    async def download_audio(self, url: str) -> Optional[Dict]:
        """Download audio from YouTube URL"""
        try:
            loop = asyncio.get_event_loop()
            
            # Extract info first
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = await loop.run_in_executor(None, ydl.extract_info, url, False)
                
            if not info:
                return None
                
            # Check duration
            duration_seconds = info.get('duration', 0)
            if duration_seconds > Config.MAX_SONG_DURATION:
                raise Exception(f"Song too long! Maximum duration is {Config.MAX_SONG_DURATION // 60} minutes.")
                
            # Download audio
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                await loop.run_in_executor(None, ydl.download, [url])
                
            # Format duration
            minutes, seconds = divmod(duration_seconds, 60)
            hours, minutes = divmod(minutes, 60)
            
            if hours:
                duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                duration_str = f"{minutes:02d}:{seconds:02d}"
                
            # Find downloaded file
            safe_title = self._sanitize_filename(info['title'])
            possible_extensions = ['mp3', 'webm', 'm4a', 'ogg']
            file_path = None
            
            for ext in possible_extensions:
                potential_path = os.path.join(Config.DOWNLOADS_PATH, f"{safe_title}.{ext}")
                if os.path.exists(potential_path):
                    file_path = potential_path
                    break
                    
            if not file_path:
                # Try with original filename
                for ext in possible_extensions:
                    potential_path = os.path.join(Config.DOWNLOADS_PATH, f"{info['title']}.{ext}")
                    if os.path.exists(potential_path):
                        file_path = potential_path
                        break
                        
            if not file_path:
                raise Exception("Downloaded file not found")
                
            return {
                'id': info['id'],
                'title': info['title'],
                'duration': duration_str,
                'duration_seconds': duration_seconds,
                'url': url,
                'file_path': file_path,
                'thumbnail': info.get('thumbnail'),
                'channel': info.get('uploader', 'Unknown'),
                'views': info.get('view_count', 0)
            }
            
        except Exception as e:
            logger.error(f"Error downloading audio: {e}")
            raise
            
    async def search_and_download(self, query: str) -> Optional[Dict]:
        """Search and download music"""
        try:
            # Check if query is a URL
            if query.startswith(('http://', 'https://')):
                if 'youtube.com' in query or 'youtu.be' in query:
                    return await self.download_audio(query)
                else:
                    raise Exception("Only YouTube URLs are supported")
                    
            # Search YouTube
            search_results = await self.search_youtube(query)
            if not search_results:
                return None
                
            # Download first result
            best_result = search_results[0]
            return await self.download_audio(best_result['url'])
            
        except Exception as e:
            logger.error(f"Error in search_and_download: {e}")
            raise
            
    async def get_lyrics(self, song_title: str) -> Optional[str]:
        """Get lyrics for a song"""
        if not Config.ENABLE_LYRICS:
            return None
            
        try:
            import lyricsgenius
            genius = lyricsgenius.Genius(os.getenv("GENIUS_API_TOKEN", ""))
            genius.verbose = False
            genius.remove_section_headers = True
            
            loop = asyncio.get_event_loop()
            song = await loop.run_in_executor(None, genius.search_song, song_title)
            
            if song:
                return song.lyrics
            return None
            
        except Exception as e:
            logger.error(f"Error getting lyrics: {e}")
            return None
            
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage"""
        import re
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filename = re.sub(r'\s+', ' ', filename).strip()
        return filename[:100]  # Limit length
        
    async def cleanup_old_files(self, max_age_hours: int = 24):
        """Clean up old downloaded files"""
        try:
            import time
            current_time = time.time()
            
            for filename in os.listdir(Config.DOWNLOADS_PATH):
                file_path = os.path.join(Config.DOWNLOADS_PATH, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > (max_age_hours * 3600):
                        os.remove(file_path)
                        logger.info(f"Cleaned up old file: {filename}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up files: {e}")
            
    async def get_video_info(self, url: str) -> Optional[Dict]:
        """Get video information without downloading"""
        try:
            loop = asyncio.get_event_loop()
            
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = await loop.run_in_executor(None, ydl.extract_info, url, False)
                
            if not info:
                return None
                
            duration_seconds = info.get('duration', 0)
            minutes, seconds = divmod(duration_seconds, 60)
            hours, minutes = divmod(minutes, 60)
            
            if hours:
                duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                duration_str = f"{minutes:02d}:{seconds:02d}"
                
            return {
                'id': info['id'],
                'title': info['title'],
                'duration': duration_str,
                'duration_seconds': duration_seconds,
                'thumbnail': info.get('thumbnail'),
                'channel': info.get('uploader', 'Unknown'),
                'views': info.get('view_count', 0),
                'description': info.get('description', '')[:200] + '...' if info.get('description') else ''
            }
            
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            return None