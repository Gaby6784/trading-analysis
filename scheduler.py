#!/usr/bin/env python3
"""
Scheduler for automated analysis runs
Runs analysis 3x daily during market hours (9:30 AM, 12 PM, 3:30 PM ET)
"""

import schedule
import time
from datetime import datetime
import pytz
from typing import Optional

from premarket_analysis.main_with_predictions import analyze_ticker_with_prediction
from database import Database
from telegram_bot import TelegramBot


class AnalysisScheduler:
    """Scheduler for running automated analysis"""
    
    def __init__(self, tickers: list = None):
        self.tickers = tickers or ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'NVDA', 'TSLA', 'META']
        self.db = Database()
        self.telegram = TelegramBot()
        self.eastern = pytz.timezone('US/Eastern')
    
    def run_analysis(self, send_alerts: bool = True):
        """Run analysis on all tickers"""
        
        print(f"\n{'='*60}")
        print(f"🔄 Running scheduled analysis at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
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
            
            # Send summary
            # self.telegram.send_daily_summary(results)  # Uncomment if you want summaries
        
        return results
    
    def schedule_jobs(self):
        """Schedule analysis jobs for market hours (ET)"""
        
        # Market open: 9:30 AM ET
        schedule.every().day.at("09:30").do(self.run_analysis)
        
        # Midday: 12:00 PM ET
        schedule.every().day.at("12:00").do(self.run_analysis)
        
        # Before close: 3:30 PM ET
        schedule.every().day.at("15:30").do(self.run_analysis)
        
        print(f"\n⏰ Scheduled analysis times (ET):")
        print(f"  • 09:30 AM - Market open")
        print(f"  • 12:00 PM - Midday check")
        print(f"  • 03:30 PM - Pre-close check")
        print(f"\n🤖 Bot is running... Press Ctrl+C to stop\n")
    
    def run_forever(self):
        """Run scheduler loop"""
        
        # Run once immediately
        print("🚀 Running initial analysis...")
        self.run_analysis()
        
        # Schedule future runs
        self.schedule_jobs()
        
        # Run scheduler loop
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute


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
║       Running automated analysis 3x daily                  ║
╚════════════════════════════════════════════════════════════╝
""")
        run_continuous()
