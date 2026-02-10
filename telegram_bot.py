#!/usr/bin/env python3
"""
Telegram Bot Integration
Sends alerts for high-confidence trading signals
"""

import os
import requests
from datetime import datetime
from typing import List, Optional
from database import AnalysisResult


class TelegramBot:
    """Telegram bot for sending trading alerts"""
    
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.bot_token = bot_token or os.environ.get('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.environ.get('TELEGRAM_CHAT_ID')
        
        if not self.bot_token:
            print("⚠️  Warning: TELEGRAM_BOT_TOKEN not set - notifications disabled")
        if not self.chat_id:
            print("⚠️  Warning: TELEGRAM_CHAT_ID not set - notifications disabled")
    
    def is_configured(self) -> bool:
        """Check if bot is properly configured"""
        return bool(self.bot_token and self.chat_id)
    
    def send_message(self, text: str, parse_mode: str = 'HTML') -> bool:
        """Send a message via Telegram"""
        if not self.is_configured():
            print("❌ Telegram not configured, skipping message")
            return False
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        payload = {
            'chat_id': self.chat_id,
            'text': text,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ Telegram message sent successfully")
                return True
            else:
                print(f"❌ Telegram API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending Telegram message: {e}")
            return False
    
    def format_signal_alert(self, result: AnalysisResult) -> str:
        """Format a trading signal as a Telegram message"""
        
        # Emoji based on category
        category_emoji = {
            'STRONG_BUY': '🚀',
            'BUY': '📈',
            'WATCH': '👀',
            'AVOID': '⛔',
            'NEUTRAL': '➖'
        }
        
        emoji = category_emoji.get(result.category, '📊')
        
        # Emoji for news direction
        news_emoji = {
            'BULLISH': '🟢',
            'BEARISH': '🔴',
            'NEUTRAL': '⚪'
        }
        
        news_icon = news_emoji.get(result.news_direction, '⚪')
        
        message = f"""
{emoji} <b>{result.ticker}</b> - {result.category}
━━━━━━━━━━━━━━━━━━━━

<b>📊 Score:</b> {result.score:.0f}/100

<b>💰 Price:</b> ${result.price:.2f if result.price else 'N/A'}
<b>📉 RSI:</b> {result.rsi:.1f if result.rsi else 'N/A'}
<b>📈 Trend:</b> {result.trend or 'N/A'}

<b>📰 News Prediction:</b>
{news_icon} {result.news_direction} ({result.news_confidence:.0f}% confidence)

<b>🎯 Alignment:</b> {result.alignment}
<b>⚖️  Alignment Score:</b> {result.alignment_score:.0f}/10

<b>🕐 Time:</b> {result.timestamp.strftime('%Y-%m-%d %H:%M:%S') if result.timestamp else 'N/A'}
"""
        
        return message.strip()
    
    def send_high_confidence_alert(self, result: AnalysisResult) -> bool:
        """Send alert for high-confidence signal"""
        
        if not self.is_configured():
            return False
        
        # Only send if score >= 70 or news confidence >= 60%
        if result.score < 70 and result.news_confidence < 60:
            return False
        
        message = self.format_signal_alert(result)
        return self.send_message(message)
    
    def send_daily_summary(self, results: List[AnalysisResult]) -> bool:
        """Send daily summary of all analyses"""
        
        if not self.is_configured():
            return False
        
        if not results:
            message = "📊 <b>Daily Summary</b>\n\nNo analysis results available."
            return self.send_message(message)
        
        # Count by category
        categories = {}
        for r in results:
            categories[r.category] = categories.get(r.category, 0) + 1
        
        # Find high-confidence signals
        high_conf = [r for r in results if r.score >= 70 or r.news_confidence >= 60]
        
        message = f"""
📊 <b>Daily Analysis Summary</b>
━━━━━━━━━━━━━━━━━━━━

<b>Total tickers analyzed:</b> {len(results)}

<b>Category Breakdown:</b>
"""
        
        for cat, count in sorted(categories.items()):
            message += f"  • {cat}: {count}\n"
        
        message += f"\n<b>🔔 High-Confidence Signals:</b> {len(high_conf)}\n"
        
        if high_conf:
            message += "\n<b>Top Opportunities:</b>\n"
            for r in sorted(high_conf, key=lambda x: x.score, reverse=True)[:3]:
                message += f"  • {r.ticker}: {r.score:.0f} ({r.category})\n"
        
        message += f"\n<b>🕐 Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return self.send_message(message.strip())
    
    def send_error_alert(self, error: str) -> bool:
        """Send error notification"""
        
        if not self.is_configured():
            return False
        
        message = f"""
⚠️ <b>System Error</b>
━━━━━━━━━━━━━━━━━━━━

{error}

<b>🕐 Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return self.send_message(message.strip())
    
    def test_connection(self) -> bool:
        """Test Telegram bot connection"""
        
        if not self.is_configured():
            print("❌ Telegram bot not configured")
            print("  Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
            return False
        
        message = "🤖 <b>Trading Analysis Bot - Connection Test</b>\n\nBot is connected and working! 🎉"
        
        return self.send_message(message)


def get_telegram_setup_instructions():
    """Get instructions for setting up Telegram bot"""
    
    instructions = """
📱 TELEGRAM BOT SETUP INSTRUCTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 1: Create a Telegram Bot
1. Open Telegram and search for @BotFather
2. Send /newbot command
3. Follow instructions to create your bot
4. Copy the Bot Token (looks like: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz)

STEP 2: Get Your Chat ID
1. Search for @userinfobot in Telegram
2. Start a chat with it
3. Copy your Chat ID (a number like: 123456789)

STEP 3: Set Environment Variables
Add these to your .env file or Railway environment:

TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

STEP 4: Test the Connection
Run: python3 telegram_bot.py

You should receive a test message from your bot!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔔 Your bot will send alerts when:
  • Score >= 70 (STRONG_BUY or BUY)
  • News confidence >= 60%
  • Daily summaries (3x per day)
"""
    
    return instructions


if __name__ == '__main__':
    print(get_telegram_setup_instructions())
    print("\n" + "="*50 + "\n")
    
    # Test connection
    bot = TelegramBot()
    
    if bot.is_configured():
        print("🧪 Testing Telegram connection...")
        success = bot.test_connection()
        
        if success:
            print("✅ Telegram bot is working!")
            
            # Send example alert
            print("\n📊 Sending example alert...")
            
            from database import AnalysisResult
            from datetime import datetime
            
            example = AnalysisResult(
                id=1,
                ticker='AAPL',
                timestamp=datetime.now(),
                score=78.5,
                category='BUY',
                rsi=28.5,
                trend='UPTREND',
                price=180.25,
                news_direction='BULLISH',
                news_confidence=65.0,
                alignment='STRONG CONFLUENCE',
                alignment_score=9.0
            )
            
            bot.send_high_confidence_alert(example)
        else:
            print("❌ Telegram connection test failed")
    else:
        print("❌ Telegram bot not configured")
        print("   Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
