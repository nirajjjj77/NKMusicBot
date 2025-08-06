#!/usr/bin/env python3
"""
Railway Session Generator Starter
This file temporarily replaces your main bot to run session generation
"""

import os
import sys

def main():
    print("🚀 Starting Railway Session Generator...")
    print("📝 Check Railway logs to see the session generation process")
    print()
    
    # Check if we should run session generator or normal bot
    run_mode = os.getenv("RUN_MODE", "bot")
    
    if run_mode == "session":
        print("🔧 Running in SESSION GENERATION mode")
        # Import and run the session generator
        from generate_session import main as generate_session_main
        import asyncio
        asyncio.run(generate_session_main())
    else:
        print("🤖 Running in NORMAL BOT mode")
        # Import and run your normal bot
        from main import main as bot_main  # Replace 'main' with your actual main file
        bot_main()

if __name__ == "__main__":
    main()