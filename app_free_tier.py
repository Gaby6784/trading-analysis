#!/usr/bin/env python3
"""
Optimized scheduler for Railway FREE tier
Uses external cron services to wake up sleeping app
"""

from flask import Flask, jsonify
import os
from datetime import datetime

from premarket_analysis.main_with_predictions import analyze_ticker_with_prediction
from database import Database
from telegram_bot import TelegramBot

app = Flask(__name__)

# Initialize
db = Database()
telegram = TelegramBot()
DEFAULT_TICKERS = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'NVDA', 'TSLA', 'META']


@app.route('/cron/analyze')
def cron_analyze():
    """
    Endpoint to be called by external cron service
    Works even when Railway app is sleeping
    """
    
    print(f"\n🔄 Cron triggered analysis at {datetime.now()}")
    
    results = []
    high_confidence_signals = []
    
    for ticker in DEFAULT_TICKERS:
        try:
            analysis = analyze_ticker_with_prediction(ticker)
            
            result = db.save_analysis(
                ticker=ticker,
                score=analysis['score'],
                category=analysis['category'],
                rsi=analysis['technical'].get('rsi'),
                trend=analysis['technical'].get('trend'),
                price=analysis['technical'].get('price'),
                news_direction=analysis['prediction']['prediction'],
                news_confidence=analysis['prediction']['confidence_score'],
                alignment=analysis['alignment']['status'],
                alignment_score=analysis['alignment']['score']
            )
            
            results.append(result.to_dict())
            
            if result.score >= 70 or result.news_confidence >= 60:
                high_confidence_signals.append(result)
                telegram.send_high_confidence_alert(result)
            
        except Exception as e:
            print(f"Error analyzing {ticker}: {e}")
    
    return jsonify({
        'success': True,
        'timestamp': datetime.now().isoformat(),
        'analyzed': len(results),
        'alerts': len(high_confidence_signals),
        'results': results
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
