#!/usr/bin/env python3
"""
Telegram Menu Setup Script
Sets up the persistent menu system for the Telegram bot
"""

import asyncio
import aiohttp
import os
from pathlib import Path
from dotenv import load_dotenv

class TelegramMenuSetup:
    def __init__(self, base_url: str = "https://crypto-analyzer-gpt.onrender.com"):
        # Load environment variables
        env_path = Path(__file__).parent.parent / '.env'
        load_dotenv(env_path)
        
        self.base_url = base_url
        self.api_key = os.getenv('API_KEY')
        
        if not self.api_key:
            print("❌ API_KEY not found in .env file")
            exit(1)
        
        # Set up headers with API key
        self.headers = {
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json'
        }
        
    async def setup_menu(self):
        """Setup the Telegram bot menu system"""
        print("🤖 Setting up Telegram Bot Menu System...")
        print("="*50)
        
        url = f"{self.base_url}/telegram/setup-menu"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self.headers, timeout=30) as response:
                    status = response.status
                    response_data = await response.json()
                    
                    if status == 200:
                        print("✅ Menu setup request sent successfully!")
                        print(f"📊 Status: {response_data}")
                        
                        if response_data.get('success'):
                            print("\n🎉 Menu system configured successfully!")
                            print("\n📱 What was set up:")
                            print("• ✅ Commands menu (when typing /)")
                            print("• ✅ Menu button (next to text input)")
                            
                            print("\n📋 Available commands:")
                            commands = [
                                "/start - Bot starten und Hauptmenü",
                                "/menu - Hauptmenü anzeigen", 
                                "/alerts - Alert Übersicht",
                                "/new - Neuen Alert erstellen",
                                "/status - System Status",
                                "/streams - Live Streams",
                                "/portfolio - Portfolio Watch", 
                                "/monitor - Trading Monitor",
                                "/performance - Performance Stats",
                                "/settings - Einstellungen",
                                "/help - Hilfe anzeigen"
                            ]
                            
                            for cmd in commands:
                                print(f"  • {cmd}")
                            
                            print(f"\n💡 Chat ID: {response_data.get('chat_id', 'N/A')}")
                            
                        else:
                            print("❌ Menu setup failed!")
                            
                    else:
                        print(f"❌ Menu setup failed: {status}")
                        print(f"Response: {response_data}")
                        
        except Exception as e:
            print(f"❌ Error setting up menu: {e}")
            
    async def test_webhook_status(self):
        """Test webhook status"""
        print("\n📡 Checking webhook status...")
        
        url = f"{self.base_url}/telegram/webhook-info"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, timeout=15) as response:
                    status = response.status
                    response_data = await response.json()
                    
                    if status == 200:
                        print("✅ Webhook info retrieved:")
                        print(f"  • URL: {response_data.get('webhook_url', 'Not set')}")
                        print(f"  • Pending updates: {response_data.get('pending_update_count', 0)}")
                        print(f"  • Max connections: {response_data.get('max_connections', 0)}")
                        
                        if response_data.get('last_error_message'):
                            print(f"  • Last error: {response_data.get('last_error_message')}")
                        else:
                            print("  • Status: ✅ No errors")
                            
                    else:
                        print(f"❌ Failed to get webhook info: {status}")
                        
        except Exception as e:
            print(f"❌ Error checking webhook: {e}")
            
    async def send_test_message(self):
        """Send a test message to verify the bot is working"""
        print("\n💬 Sending test message...")
        
        url = f"{self.base_url}/telegram/send"
        
        test_data = {
            "message": "🧪 **Menu Setup Test**\n\nDas Telegram Menu wurde erfolgreich eingerichtet!\n\n📱 Verwende das Menu-Symbol neben der Texteingabe oder tippe `/menu` für das Hauptmenü.",
            "analysis_type": "general"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=test_data, headers=self.headers, timeout=15) as response:
                    status = response.status
                    response_data = await response.json()
                    
                    if status == 200:
                        print("✅ Test message sent successfully!")
                        print("📱 Check your Telegram chat to see the menu!")
                    else:
                        print(f"❌ Test message failed: {status}")
                        print(f"Response: {response_data}")
                        
        except Exception as e:
            print(f"❌ Error sending test message: {e}")

async def main():
    """Main setup execution"""
    setup = TelegramMenuSetup()
    
    print("🚀 Starting Telegram Menu Setup")
    print(f"📊 Base URL: {setup.base_url}")
    print("="*50)
    
    # Setup menu system
    await setup.setup_menu()
    
    # Check webhook status  
    await setup.test_webhook_status()
    
    # Send test message
    await setup.send_test_message()
    
    print("\n🎉 Setup completed!")
    print("\n📱 Go to your Telegram chat and:")
    print("1. Look for the menu button next to the text input")
    print("2. Try typing / to see the commands menu")
    print("3. Send /menu or /start to test the bot")

if __name__ == "__main__":
    asyncio.run(main())
