#!/usr/bin/env python3
"""
Generate a user session string for the music bot - Railway Version
This version is safe to push to GitHub as it uses environment variables only
"""

import asyncio
import sys
import os
from pyrogram import Client

async def main():
    print("=" * 60)
    print("🎵 MUSIC BOT - USER SESSION GENERATOR (RAILWAY)")
    print("=" * 60)
    print()
    print("📱 This will generate a session string for your personal Telegram account")
    print("⚠️  IMPORTANT: This account will be used to join voice chats")
    print("   Make sure this account is added to groups where you want music!")
    print()
    
    # Load from environment variables (Railway sets these)
    try:
        API_ID = int(os.getenv("API_ID", "0"))
        API_HASH = os.getenv("API_HASH", "")
        
        if not API_ID or not API_HASH:
            print("❌ ERROR: API_ID and API_HASH environment variables not set!")
            print("📝 Please set these in Railway dashboard:")
            print("   - Go to your Railway project")
            print("   - Click on 'Variables' tab")
            print("   - Add: API_ID=your_api_id")
            print("   - Add: API_HASH=your_api_hash")
            return
            
        print("✅ Loaded API credentials from environment variables")
        print(f"🔑 Using API_ID: {API_ID}")
        print(f"🔑 Using API_HASH: {API_HASH[:8]}...")
        print()
        
    except Exception as e:
        print(f"❌ ERROR loading environment variables: {e}")
        return
    
    try:
        print("🚀 Starting session generation...")
        print("📞 You'll be asked for:")
        print("   1. Your phone number (with country code, e.g., +1234567890)")
        print("   2. Verification code sent to your Telegram")
        print("   3. 2FA password if you have one enabled")
        print()
        
        # Create client for user account
        client = Client(
            "music_bot_session",
            api_id=API_ID,
            api_hash=API_HASH,
            workdir="/tmp"  # Use tmp directory on Railway
        )
        
        async with client:
            session_string = await client.export_session_string()
            
            print()
            print("=" * 60)
            print("✅ SESSION STRING GENERATED SUCCESSFULLY!")
            print("=" * 60)
            print()
            print("📋 COPY THIS ENTIRE LINE:")
            print()
            print(f"USER_SESSION_STRING={session_string}")
            print()
            print("=" * 60)
            print("📝 NEXT STEPS FOR RAILWAY:")
            print("1. Copy the USER_SESSION_STRING line above")
            print("2. Go to Railway dashboard > Your project > Variables tab")
            print("3. Add new variable: USER_SESSION_STRING=<the long string>")
            print("4. Update your audio_manager.py with user account version")
            print("5. Deploy the updated code")
            print("6. Make sure the Telegram account is added to your music groups")
            print()
            print("⚠️  SECURITY WARNING:")
            print("   - Keep this session string SECRET!")
            print("   - Add it only to Railway environment variables")
            print("   - Don't commit it to GitHub")
            print("=" * 60)
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print()
        print("🔧 Common issues:")
        print("1. Wrong API_ID or API_HASH in Railway variables")
        print("2. Invalid phone number format")
        print("3. Wrong verification code")
        print("4. Network connection issues")
        print()
        print("💡 Make sure you:")
        print("- Set correct API credentials in Railway dashboard")
        print("- Enter phone number with country code (+1234567890)")
        print("- Enter the 5-digit code sent to your Telegram")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    finally:
        # Clean up session file
        try:
            if os.path.exists("/tmp/music_bot_session.session"):
                os.remove("/tmp/music_bot_session.session")
                print("🧹 Cleaned up temporary session file")
        except:
            pass
        
        # Keep the Railway deployment running so you can see the output
        print("\n⏳ Keeping process alive for 5 minutes so you can copy the session string...")
        print("   Copy the USER_SESSION_STRING line and add it to Railway variables")
        import time
        time.sleep(300)  # 5 minutes