#!/usr/bin/env python3
"""
Flask API for premarket analysis
Provides REST endpoints and web dashboard
"""

from flask import Flask, jsonify, render_template, send_from_directory, request
from flask_cors import CORS
import os
from datetime import datetime
import json
from pathlib import Path

from premarket_analysis.main_with_predictions import analyze_ticker_with_prediction
from database import Database, AnalysisResult

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Initialize database
db = Database()

# Default tickers to analyze
DEFAULT_TICKERS = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'NVDA', 'TSLA', 'META']


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
                    category=analysis['category'],
                    rsi=analysis['technical'].get('rsi'),
                    trend=analysis['technical'].get('trend'),
                    price=analysis['technical'].get('price'),
                    news_direction=analysis['prediction']['prediction'],
                    news_confidence=analysis['prediction']['confidence_score'],
                    alignment=analysis['alignment']['status'],
                    alignment_score=analysis['alignment']['score']
                )
                
                results.append({
                    'ticker': ticker,
                    'score': analysis['score'],
                    'category': analysis['category'],
                    'rsi': analysis['technical'].get('rsi'),
                    'trend': analysis['technical'].get('trend'),
                    'price': analysis['technical'].get('price'),
                    'news_direction': analysis['prediction']['prediction'],
                    'news_confidence': analysis['prediction']['confidence_score'],
                    'expected_move': analysis['prediction']['expected_move'],
                    'alignment': analysis['alignment']['status'],
                    'alignment_score': analysis['alignment']['score'],
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


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"\n🚀 Starting Trading Analysis API on port {port}")
    print(f"📊 Dashboard: http://localhost:{port}")
    print(f"🔧 Debug mode: {debug}\n")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
