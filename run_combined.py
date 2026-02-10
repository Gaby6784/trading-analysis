#!/usr/bin/env python3
"""
Combined Flask + Scheduler for Railway deployment
Runs both web server and scheduled analysis in one process
"""

import os
import threading
from datetime import datetime

# Import Flask app
from app import app

# Import scheduler
from scheduler import AnalysisScheduler


def run_scheduler():
    """Run scheduler in background thread"""
    print("⏰ Starting scheduler thread...")
    
    scheduler = AnalysisScheduler()
    
    try:
        # Run immediately on startup
        print("🚀 Running initial analysis...")
        scheduler.run_analysis()
        
        # Schedule future runs
        scheduler.schedule_jobs()
        
        # Keep running
        scheduler.run_forever()
        
    except Exception as e:
        print(f"❌ Scheduler error: {e}")


def main():
    """Main entry point"""
    
    print("\n" + "="*60)
    print("🚀 Starting Trading Analysis Platform")
    print("="*60)
    
    # Check if scheduler should run
    scheduler_enabled = os.environ.get('SCHEDULER_ENABLED', 'true').lower() == 'true'
    
    if scheduler_enabled:
        print("✅ Scheduler: ENABLED")
        # Start scheduler in background thread
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
    else:
        print("⚠️  Scheduler: DISABLED (set SCHEDULER_ENABLED=true to enable)")
    
    # Start Flask app
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Starting Flask API on port {port}")
    print("="*60 + "\n")
    
    # Run Flask (this blocks)
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)


if __name__ == '__main__':
    main()
