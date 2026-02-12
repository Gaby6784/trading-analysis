#!/usr/bin/env python3
"""
Timezone-aware scheduler for automated analysis
Runs every 30 min during market hours (9:30 AM - 4:00 PM ET)
Works correctly regardless of server timezone
"""

import time
from datetime import datetime, timedelta
import pytz
from typing import Optional

from premarket_analysis.main_with_predictions import analyze_ticker_with_prediction
from database import Database
from telegram_bot import TelegramBot


class AnalysisScheduler:
    """Timezone-aware scheduler for running automated analysis"""
    
    def __init__(self, tickers: list = None):
        self.tickers = tickers or ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'NVDA', 'TSLA', 'META', 'NFLX']
        self.db = Database()
        self.telegram = TelegramBot()
        self.eastern = pytz.timezone('US/Eastern')
        self.last_run_minute = None
        
        # Market hours schedule in ET: every 30 min from 9:30 AM to 4:00 PM
        self.schedule_times = [
            (9, 30), (10, 0), (10, 30), (11, 0), (11, 30),
            (12, 0), (12, 30), (13, 0), (13, 30), (14, 0),
            (14, 30), (15, 0), (15, 30), (16, 0)
        ]
    
    def get_current_et_time(self):
        """Get current time in Eastern Time"""
        return datetime.now(self.eastern)
    
    def should_run_now(self):
        """Check if we should run analysis now based on ET time"""
        et_now = self.get_current_et_time()
        
        # Only run on weekdays
        if et_now.weekday() >= 5:  # Saturday=5, Sunday=6
            return False
        
        current_hour = et_now.hour
        current_minute = et_now.minute
        
        # Check if current time matches any scheduled time
        for hour, minute in self.schedule_times:
            if current_hour == hour and current_minute == minute:
                # Avoid running multiple times in the same minute
                current_key = f"{et_now.year}-{et_now.month}-{et_now.day}-{hour}-{minute}"
                if self.last_run_minute != current_key:
                    self.last_run_minute = current_key
                    return True
        
        return False
    
    def run_analysis(self, send_alerts: bool = True):
        """Run analysis on all tickers"""
        
        et_now = self.get_current_et_time()
        utc_now = datetime.now(pytz.UTC)
        
        print(f"\n{'='*60}")
        print(f"🔄 Running scheduled analysis")
        print(f"   📅 Date: {et_now.strftime('%Y-%m-%d')}")
        print(f"   🕐 Market Time (ET): {et_now.strftime('%I:%M %p')}")
        print(f"   🌍 Server Time (UTC): {utc_now.strftime('%H:%M:%S')}")
        print(f"{'='*60}\n")
        
        results = []
        high_confidence_signals = []
        
        for ticker in self.tickers:
            try:
                print(f"📊 Analyzing {ticker}...")
                
                analysis = analyze_ticker_with_prediction(ticker)
                
                # Save to database
                result = self.db.save_analysis(
                    ticker=ticker,
                    score=analysis['score'],
                    category=analysis['score_category'],
                    rsi=analysis.get('rsi'),
                    trend=analysis.get('trend'),
                    price=analysis.get('price'),
                    news_direction=analysis['news_prediction'],
                    news_confidence=analysis['prediction_confidence'],
                    alignment=analysis['alignment'],
                    alignment_score=analysis['alignment_score']
                )
                
                results.append(result)
                
                print(f"  ✅ {ticker}: Score {result.score:.0f} ({result.category})")
                
                # Check if high-confidence signal
                if result.score >= 70 or result.news_confidence >= 60:
                    high_confidence_signals.append(result)
                    print(f"     🔔 HIGH CONFIDENCE SIGNAL!")
                
            except Exception as e:
                print(f"  ❌ Error analyzing {ticker}: {e}")
        
        print(f"\n{'='*60}")
        print(f"✅ Analysis complete: {len(results)} tickers analyzed")
        print(f"🔔 High-confidence signals: {len(high_confidence_signals)}")
        print(f"{'='*60}\n")
        
        # Send alerts via Telegram
        if send_alerts and self.telegram.is_configured():
            print("📱 Sending Telegram alerts...")
            
            # Send individual alerts for high-confidence signals
            for signal in high_confidence_signals:
                self.telegram.send_high_confidence_alert(signal)
        
        return results
    
    def run_forever(self):
        """Run scheduler loop - checks every minute for scheduled times"""
        
        print("\n" + "="*60)
        print("⏰ TIMEZONE-AWARE SCHEDULER STARTED")
        print("="*60)
        print(f"📊 Tickers: {', '.join(self.tickers)}")
        print(f"🕐 Schedule: Every 30 min during market hours (ET)")
        print(f"📅 Days: Monday - Friday")
        print(f"⏰ Times (ET): 9:30 AM - 4:00 PM (14 analyses/day)")
        print(f"\n🌍 Server timezone: {time.tzname[0]}")
        
        et_now = self.get_current_et_time()
        print(f"🕐 Current ET time: {et_now.strftime('%Y-%m-%d %I:%M %p %Z')}")
        print(f"📍 Day: {et_now.strftime('%A')}")
        print("="*60)
        
        # Run immediately on startup if during market hours
        if self.should_run_now():
            print("\n🚀 Starting initial analysis (within scheduled time)...")
            try:
                self.run_analysis()
            except Exception as e:
                print(f"❌ Initial analysis error: {e}")
        else:
            print(f"\n⏸️  Outside market hours - waiting for next scheduled time...")
        
        print("\n🤖 Scheduler running... checking every minute\n")
        
        # Main loop: check every minute
        while True:
            try:
                if self.should_run_now():
                    self.run_analysis()
                
                # Sleep for 60 seconds
                time.sleep(60)
                
            except KeyboardInterrupt:
                print("\n\n👋 Scheduler stopped by user")
                break
            except Exception as e:
                print(f"❌ Error in scheduler loop: {e}")
                time.sleep(60)


def run_manual():
    """Run analysis manually (for testing)"""
    scheduler = AnalysisScheduler()
    scheduler.run_analysis()


def run_continuous():
    """Run continuous scheduled analysis"""
    scheduler = AnalysisScheduler()
    
    try:
        scheduler.run_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Scheduler stopped by user")
        print("📊 Final stats:")
        stats = scheduler.db.get_stats()
        for key, value in stats.items():
            print(f"  • {key}: {value}")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--manual':
        # Run once manually
        run_manual()
    else:
        # Run continuous scheduler
        print("""
╔════════════════════════════════════════════════════════════╗
║       📊 TRADING ANALYSIS SCHEDULER                        ║
║       Timezone-aware: Runs at correct ET times             ║
╚════════════════════════════════════════════════════════════╝
""")
        run_continuous()
