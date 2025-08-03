#!/usr/bin/env python3
"""
Setup script for Telegram Music Bot
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required!")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]} detected")

def check_ffmpeg():
    """Check if FFmpeg is installed"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ FFmpeg is installed")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ FFmpeg not found!")
    print("Please install FFmpeg:")
    
    system = platform.system().lower()
    if system == "linux":
        print("  Ubuntu/Debian: sudo apt update && sudo apt install ffmpeg")
        print("  CentOS/RHEL: sudo yum install ffmpeg")
        print("  Arch: sudo pacman -S ffmpeg")
    elif system == "darwin":
        print("  macOS: brew install ffmpeg")
    elif system == "windows":
        print("  Windows: Download from https://ffmpeg.org/download.html")
    
    return False

def install_requirements():
    """Install Python requirements"""
    print("📦 Installing Python dependencies...")
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    directories = ['downloads', 'logs', 'backups']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

def create_env_file():
    """Create .env file from template"""
    env_template = """# Telegram Bot Configuration
BOT_TOKEN=your_bot_token_here
API_ID=your_api_id_here
API_HASH=your_api_hash_here

# Bot Administration
OWNER_ID=your_user_id_here
SUDO_USERS=

# Database Configuration
DATABASE_URL=sqlite:///musicbot.db

# Audio Settings
BITRATE=512
FPS=20
DEFAULT_VOLUME=100

# Bot Settings
MAX_QUEUE_SIZE=50
MAX_SONG_DURATION=1800
RATE_LIMIT_REQUESTS=10
RATE_LIMIT_WINDOW=60

# File Paths
DOWNLOADS_PATH=./downloads
LOGS_PATH=./logs

# Features
ENABLE_LYRICS=true
ENABLE_SPOTIFY=false
ENABLE_DEEZER=false

# External APIs (Optional)
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
GENIUS_API_TOKEN=

# YouTube Settings (Optional)
YOUTUBE_COOKIES_PATH=

# Logging (Optional)
LOG_CHANNEL_ID=

# Maintenance Mode
MAINTENANCE_MODE=false
"""
    
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(env_template)
        print("✅ Created .env file")
        print("⚠️  Please edit .env file with your credentials!")
    else:
        print("✅ .env file already exists")

def create_systemd_service():
    """Create systemd service file (Linux only)"""
    if platform.system().lower() != 'linux':
        return
        
    current_dir = os.getcwd()
    python_path = sys.executable
    
    service_content = f"""[Unit]
Description=Telegram Music Bot
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'musicbot')}
WorkingDirectory={current_dir}
ExecStart={python_path} main.py
Restart=always
RestartSec=10
Environment=PYTHONPATH={current_dir}

[Install]
WantedBy=multi-user.target
"""
    
    service_file = 'musicbot.service'
    with open(service_file, 'w') as f:
        f.write(service_content)
    
    print(f"✅ Created systemd service file: {service_file}")
    print("To install the service:")
    print(f"  sudo cp {service_file} /etc/systemd/system/")
    print("  sudo systemctl daemon-reload")
    print("  sudo systemctl enable musicbot")
    print("  sudo systemctl start musicbot")

def validate_env_file():
    """Validate .env file has required variables"""
    if not os.path.exists('.env'):
        return False
        
    required_vars = ['BOT_TOKEN', 'API_ID', 'API_HASH', 'OWNER_ID']
    missing_vars = []
    
    with open('.env', 'r') as f:
        content = f.read()
        
    for var in required_vars:
        if f"{var}=your_" in content or f"{var}=" in content and f"{var}=\n" in content:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Please configure these variables in .env: {', '.join(missing_vars)}")
        return False
    
    return True

def show_getting_started():
    """Show getting started instructions"""
    print("\n" + "="*50)
    print("🎉 Setup completed successfully!")
    print("="*50)
    print("\n📋 Next steps:")
    print("1. Edit .env file with your bot credentials")
    print("2. Get your bot token from @BotFather")
    print("3. Get API credentials from https://my.telegram.org")
    print("4. Run the bot: python main.py")
    print("\n📖 For detailed instructions, see README.md")
    print("\n🆘 Need help? Check the troubleshooting section in README.md")

def main():
    """Main setup function"""
    print("🚀 Setting up Telegram Music Bot...")
    print("="*40)
    
    # Check requirements
    check_python_version()
    ffmpeg_ok = check_ffmpeg()
    
    if not ffmpeg_ok:
        print("\n❌ Setup cannot continue without FFmpeg")
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Install dependencies
    if not install_requirements():
        sys.exit(1)
    
    # Create configuration files
    create_env_file()
    create_systemd_service()
    
    # Final instructions
    show_getting_started()
    
    print("\n🔧 Quick test:")
    print("python -c \"from main import MusicBot; print('✅ Bot imports successfully')\"")

if __name__ == "__main__":
    main()