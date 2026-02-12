#!/usr/bin/env python3
"""
Flask API for premarket analysis
Provides REST endpoints and web dashboard
"""

from flask import Flask, jsonify, render_template, send_from_directory, request
from flask_cors import CORS
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import json
from pathlib import Path

from premarket_analysis.main_with_predictions import analyze_ticker_with_prediction
from premarket_analysis.news_fetching import fetch_news_headlines
from database import Database, AnalysisResult

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Initialize database
db = Database()

# Default tickers to analyze
DEFAULT_TICKERS = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'NVDA', 'TSLA', 'META', 'NFLX']


@app.route('/')
def index():
    """Serve the dashboard"""
    return render_template('index.html')


@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': db.get_stats()
    })


@app.route('/api/analyze')
def analyze():
    """
    Run analysis on default tickers
    Returns latest analysis results
    """
    try:
        results = []
        
        for ticker in DEFAULT_TICKERS:
            try:
                analysis = analyze_ticker_with_prediction(ticker)
                
                # Save to database
                db_result = db.save_analysis(
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
                
                results.append({
                    'ticker': ticker,
                    'score': analysis['score'],
                    'category': analysis['score_category'],
                    'rsi': analysis.get('rsi'),
                    'trend': analysis.get('trend'),
                    'price': analysis.get('price'),
                    'news_direction': analysis['news_prediction'],
                    'news_confidence': analysis['prediction_confidence'],
                    'expected_move': analysis['expected_move'],
                    'alignment': analysis['alignment'],
                    'alignment_score': analysis['alignment_score'],
                    'timestamp': db_result.timestamp.isoformat()
                })
                
            except Exception as e:
                print(f"Error analyzing {ticker}: {e}")
                results.append({
                    'ticker': ticker,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/latest')
def get_latest():
    """Get latest analysis for all tickers"""
    try:
        results = db.get_latest_results()
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'results': [r.to_dict() for r in results]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/history/<ticker>')
def get_history(ticker):
    """Get historical analysis for a specific ticker"""
    try:
        days = int(request.args.get('days', 7))
        results = db.get_ticker_history(ticker, days=days)
        
        return jsonify({
            'success': True,
            'ticker': ticker,
            'days': days,
            'results': [r.to_dict() for r in results]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/alerts')
def get_alerts():
    """Get high-confidence signals (score >= 70 or news confidence >= 60%)"""
    try:
        results = db.get_high_confidence_signals()
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'alerts': [r.to_dict() for r in results]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stats')
def get_stats():
    """Get database statistics"""
    try:
        stats = db.get_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/news')
def get_news():
    """Get latest news across tickers with target symbols attached."""
    try:
        hours = int(request.args.get('hours', 24))
        limit = int(request.args.get('limit', 30))

        utc_tz = timezone.utc

        news_map = {}

        for ticker in DEFAULT_TICKERS:
            articles, source, _, _ = fetch_news_headlines(ticker, hours=hours)

            for headline, published_at in articles:
                key = headline.strip()
                entry = news_map.get(key)

                if entry is None:
                    # published_at is naive ET time from news_fetching
                    # Convert ET -> UTC for frontend
                    from zoneinfo import ZoneInfo
                    et_tz = ZoneInfo("America/New_York")
                    published_et = published_at.replace(tzinfo=et_tz)
                    published_utc = published_et.astimezone(utc_tz)

                    news_map[key] = {
                        'headline': key,
                        'published_at': published_utc.isoformat().replace('+00:00', 'Z'),
                        'sources': {source},
                        'tickers': {ticker}
                    }
                else:
                    entry['sources'].add(source)
                    entry['tickers'].add(ticker)

        news_items = list(news_map.values())

        # Sort by published_at (descending)
        news_items.sort(key=lambda x: x['published_at'], reverse=True)

        # Normalize sets to sorted lists
        for item in news_items:
            item['sources'] = sorted(list(item['sources']))
            item['tickers'] = sorted(list(item['tickers']))

        return jsonify({
            'success': True,
            'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'count': min(len(news_items), limit),
            'results': news_items[:limit]
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/debug/config')
def debug_config():
    """Debug endpoint to check Railway configuration"""
    import sys
    
    config = {
        'python_version': sys.version,
        'environment_variables': {
            'PORT': os.environ.get('PORT', 'NOT SET'),
            'NEWS_API_KEY': 'SET ✅' if os.environ.get('NEWS_API_KEY') else 'MISSING ❌',
            'TELEGRAM_BOT_TOKEN': 'SET' if os.environ.get('TELEGRAM_BOT_TOKEN') else 'NOT SET (optional)',
            'TELEGRAM_CHAT_ID': 'SET' if os.environ.get('TELEGRAM_CHAT_ID') else 'NOT SET (optional)',
        },
        'database_records': db.get_stats()['total_records'],
        'tickers_to_analyze': DEFAULT_TICKERS
    }
    
    # Test imports
    try:
        import yfinance
        import pandas
        import pandas_ta
        config['imports_status'] = 'All imports successful ✅'
    except Exception as e:
        config['imports_status'] = f'Import error: {str(e)} ❌'
    
    return jsonify(config)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"\n🚀 Starting Trading Analysis API on port {port}")
    print(f"📊 Dashboard: http://localhost:{port}")
    print(f"🔧 Debug mode: {debug}\n")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
