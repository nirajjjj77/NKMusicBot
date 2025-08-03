# 🎵 Advanced Telegram Music Bot

A fully-featured Telegram music bot with advanced features for playing music in voice chats.

## ✨ Features

### 🎵 Music Playback
- Play music from YouTube (search or direct links)
- High-quality audio streaming
- Queue management with shuffle and loop modes
- Pause, resume, skip controls
- Volume control (1-200%)
- Now playing information

### 📋 Queue Management
- Add multiple songs to queue
- View current queue
- Shuffle queue
- Clear queue
- Loop modes (off/song/queue)

### 🎯 Advanced Features
- Song lyrics fetching
- Play history tracking
- User statistics
- Admin controls and broadcasting
- Rate limiting and spam protection
- Database-driven user management

### 👑 Admin Features
- Ban/unban users
- Broadcast messages to all users
- Bot statistics and analytics
- System information monitoring
- Database backup functionality
- Log management

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- FFmpeg
- Telegram Bot Token
- Telegram API ID and Hash

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/telegram-music-bot.git
cd telegram-music-bot
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. **Required Environment Variables**
```bash
BOT_TOKEN=your_bot_token_from_botfather
API_ID=your_api_id_from_my.telegram.org
API_HASH=your_api_hash_from_my.telegram.org
OWNER_ID=your_telegram_user_id
```

5. **Run the bot**
```bash
python main.py
```

## 🐳 Docker Installation

1. **Build and run with Docker**
```bash
docker build -t music-bot .
docker run -d --name music-bot --env-file .env music-bot
```

2. **Using Docker Compose**
```bash
docker-compose up -d
```

## 📁 Project Structure

```
telegram-music-bot/
├── main.py                 # Main bot entry point
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables
├── Dockerfile            # Docker configuration
├── handlers/             # Command handlers
│   ├── music_handler.py  # Music commands
│   ├── admin_handler.py  # Admin commands
│   └── callback_handler.py # Inline button handlers
├── utils/               # Utility modules
│   ├── database.py      # Database operations
│   ├── audio_manager.py # Audio playback management
│   ├── youtube_downloader.py # YouTube integration
│   └── decorators.py    # Function decorators
├── downloads/           # Downloaded audio files
├── logs/               # Bot logs
└── backups/            # Database backups
```

## 🎛️ Commands

### User Commands
- `/start` - Start the bot and show welcome message
- `/help` - Show help message with all commands
- `/play <song>` - Play a song (YouTube search or URL)
- `/p <song>` - Shortcut for play command
- `/pause` - Pause current playback
- `/resume` - Resume paused playback
- `/skip` - Skip current song
- `/stop` - Stop playback and clear queue
- `/queue` or `/q` - Show current queue
- `/np` - Show now playing information
- `/shuffle` - Shuffle the current queue
- `/loop [mode]` - Set loop mode (off/song/queue)
- `/volume <1-200>` - Adjust playback volume
- `/lyrics` - Get lyrics for current song

### Admin Commands
- `/stats` - Show bot statistics
- `/ban <user_id>` - Ban a user from using the bot
- `/unban <user_id>` - Unban a user
- `/broadcast <message>` - Broadcast message to all users
- `/cleanup` - Clean up old files and database entries
- `/backup` - Create database backup
- `/logs` - Get bot logs
- `/restart` - Restart the bot

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BOT_TOKEN` | Telegram bot token | Required |
| `API_ID` | Telegram API ID | Required |
| `API_HASH` | Telegram API hash | Required |
| `OWNER_ID` | Bot owner user ID | Required |
| `SUDO_USERS` | Comma-separated admin user IDs | Empty |
| `MAX_QUEUE_SIZE` | Maximum songs in queue | 50 |
| `MAX_SONG_DURATION` | Maximum song duration (seconds) | 1800 |
| `DEFAULT_VOLUME` | Default playback volume | 100 |
| `ENABLE_LYRICS` | Enable lyrics feature | true |
| `RATE_LIMIT_REQUESTS` | Rate limit requests per window | 10 |
| `RATE_LIMIT_WINDOW` | Rate limit window (seconds) | 60 |

### Optional Features

#### Spotify Integration
```bash
ENABLE_SPOTIFY=true
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
```

#### Lyrics Support
```bash
ENABLE_LYRICS=true
GENIUS_API_TOKEN=your_genius_api_token
```

#### YouTube Cookies (for age-restricted content)
```bash
YOUTUBE_COOKIES_PATH=./cookies.txt
```

## 🛠️ Getting Credentials

### 1. Telegram Bot Token
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Create a new bot with `/newbot`
3. Copy the provided token

### 2. Telegram API Credentials
1. Go to [my.telegram.org](https://my.telegram.org)
2. Log in with your phone number
3. Go to "API Development Tools"
4. Create a new application
5. Copy API ID and API Hash

### 3. Your User ID
1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. Copy your user ID

### 4. Optional: Genius API (for lyrics)
1. Go to [genius.com/api-clients](https://genius.com/api-clients)
2. Create a new API client
3. Copy the access token

## 🔧 Troubleshooting

### Common Issues

1. **Bot doesn't respond**
   - Check if bot token is correct
   - Ensure bot is added to the group
   - Verify bot has proper permissions

2. **Can't join voice chat**
   - Make sure there's an active voice chat
   - Bot needs admin permissions in the group
   - Check if pytgcalls is properly installed

3. **Audio quality issues**
   - Adjust BITRATE in environment variables
   - Ensure stable internet connection
   - Check FFmpeg installation

4. **Permission errors**
   - Run with proper file permissions
   - Check directory write permissions
   - Ensure downloads folder exists

### Logs

Check logs for detailed error information:
```bash
tail -f bot.log
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

- Create an issue on GitHub
- Join our [Telegram Support Group](https://t.me/your_support_group)
- Read the documentation

## 🙏 Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [pytgcalls](https://github.com/pytgcalls/pytgcalls)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [pyrogram](https://github.com/pyrogram/pyrogram)

## ⭐ Star History

If you found this project helpful, please consider giving it a star!

---

**Made with ❤️ for the Telegram community**