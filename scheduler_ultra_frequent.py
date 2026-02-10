#!/usr/bin/env python3
"""
Ultra-frequent scheduler - Every 15 minutes during market hours
28 analyses per trading day
"""

# Replace the schedule_jobs method in scheduler.py with this:

def schedule_jobs_ultra_frequent(self):
    """Schedule analysis jobs - every 15 min during market hours (ET)"""
    
    # Generate times every 15 minutes from 9:30 AM to 4:00 PM
    times = []
    hour = 9
    minute = 30
    
    while hour < 16 or (hour == 16 and minute == 0):
        times.append(f"{hour:02d}:{minute:02d}")
        minute += 15
        if minute >= 60:
            minute = 0
            hour += 1
    
    for time_str in times:
        schedule.every().day.at(time_str).do(self.run_analysis)
    
    print(f"\n⏰ ULTRA-FREQUENT SCHEDULE (ET):")
    print(f"  🔥 Every 15 minutes during market hours")
    print(f"  📊 Total: {len(times)} analyses per trading day")
    print(f"  🚀 Times: {', '.join(times[:8])}...")
    print(f"\n🤖 Bot running 24/7... Press Ctrl+C to stop\n")

# This would run at:
# 9:30, 9:45, 10:00, 10:15, 10:30, 10:45...
# 15:30, 15:45, 16:00
# Total: 28 times per day!
