#!/bin/bash

# Telegram Music Bot Startup Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Banner
print_header "
🎵 ================================ 🎵
   TELEGRAM MUSIC BOT LAUNCHER
🎵 ================================ 🎵
"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_warning "Running as root is not recommended!"
   read -p "Continue anyway? (y/N): " -n 1 -r
   echo
   if [[ ! $REPLY =~ ^[Yy]$ ]]; then
       exit 1
   fi
fi

# Check Python version
print_status "Checking Python version..."
if ! python3 -c 'import sys; assert sys.version_info >= (3,8)' 2>/dev/null; then
    print_error "Python 3.8+ is required!"
    exit 1
fi
print_status "Python version check passed ✅"

# Check if .env exists
if [[ ! -f .env ]]; then
    print_error ".env file not found!"
    print_status "Creating .env template..."
    python3 setup.py
    print_warning "Please edit .env with your credentials before running again!"
    exit 1
fi

# Load environment variables
set -a
source .env
set +a

# Validate required environment variables
required_vars=("BOT_TOKEN" "API_ID" "API_HASH" "OWNER_ID")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [[ -z "${!var}" ]] || [[ "${!var}" == *"your_"* ]]; then
        missing_vars+=("$var")
    fi
done

if [[ ${#missing_vars[@]} -gt 0 ]]; then
    print_error "Missing required environment variables:"
    printf '%s\n' "${missing_vars[@]}"
    print_warning "Please configure these in your .env file!"
    exit 1
fi

# Check FFmpeg
print_status "Checking FFmpeg installation..."
if ! command -v ffmpeg &> /dev/null; then
    print_error "FFmpeg is not installed!"
    print_status "Please install FFmpeg:"
    echo "  Ubuntu/Debian: sudo apt install ffmpeg"
    echo "  CentOS/RHEL:   sudo yum install ffmpeg"
    echo "  macOS:         brew install ffmpeg"
    exit 1
fi
print_status "FFmpeg check passed ✅"

# Create directories
print_status "Creating directories..."
mkdir -p downloads logs backups
print_status "Directories created ✅"

# Check if virtual environment exists
if [[ ! -d "venv" ]]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
print_status "Installing dependencies..."
pip install --upgrade pip > /dev/null 2>&1
if [[ -f requirements.txt ]]; then
    pip install -r requirements.txt > /dev/null 2>&1
else
    print_error "requirements.txt not found!"
    exit 1
fi
print_status "Dependencies installed ✅"

# Function to handle cleanup on exit
cleanup() {
    print_status "Cleaning up..."
    # Kill any background processes
    jobs -p | xargs -r kill
    print_status "Goodbye! 👋"
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

# Check maintenance mode
if [[ "${MAINTENANCE_MODE:-false}" == "true" ]]; then
    print_warning "Bot is in maintenance mode!"
    print_status "Only admin users will be able to use the bot."
fi

# Start the bot
print_status "Starting Telegram Music Bot..."
print_header "
🎵 Bot is starting up...
🔊 Ready to play music in voice chats!
⚡ Press Ctrl+C to stop
"

# Run with auto-restart on crash
while true; do
    if python3 main.py; then
        print_status "Bot exited normally."
        break
    else
        exit_code=$?
        print_error "Bot crashed with exit code $exit_code"
        
        # Don't restart on certain exit codes
        if [[ $exit_code -eq 130 ]]; then  # Ctrl+C
            break
        fi
        
        print_warning "Restarting in 5 seconds..."
        sleep 5
        print_status "Restarting bot..."
    fi
done

print_status "Bot stopped."