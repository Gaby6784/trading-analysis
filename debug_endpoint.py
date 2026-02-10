#!/usr/bin/env python3
"""
Debug endpoint to check Railway configuration
Add this to app.py temporarily
"""

from flask import Flask, jsonify
import os
import sys

app = Flask(__name__)

@app.route('/debug/config')
def debug_config():
    """Check environment configuration"""
    
    config = {
        'python_version': sys.version,
        'environment_variables': {
            'PORT': os.environ.get('PORT', 'NOT SET'),
            'NEWS_API_KEY': 'SET' if os.environ.get('NEWS_API_KEY') else 'MISSING ❌',
            'TELEGRAM_BOT_TOKEN': 'SET' if os.environ.get('TELEGRAM_BOT_TOKEN') else 'NOT SET (optional)',
            'TELEGRAM_CHAT_ID': 'SET' if os.environ.get('TELEGRAM_CHAT_ID') else 'NOT SET (optional)',
            'FLASK_ENV': os.environ.get('FLASK_ENV', 'NOT SET'),
        },
        'imports_working': True
    }
    
    # Test imports
    try:
        import yfinance
        import pandas
        import pandas_ta
        from premarket_analysis.main_with_predictions import analyze_ticker_with_prediction
        config['imports_status'] = 'All imports successful ✅'
    except Exception as e:
        config['imports_status'] = f'Import error: {str(e)} ❌'
        config['imports_working'] = False
    
    # Test database
    try:
        from database import Database
        db = Database()
        stats = db.get_stats()
        config['database_status'] = f'Connected ✅ ({stats["total_records"]} records)'
    except Exception as e:
        config['database_status'] = f'Database error: {str(e)} ❌'
    
    # Test news API
    try:
        if os.environ.get('NEWS_API_KEY'):
            from newsapi import NewsApiClient
            newsapi = NewsApiClient(api_key=os.environ.get('NEWS_API_KEY'))
            # Quick test
            config['newsapi_status'] = 'API key configured ✅'
        else:
            config['newsapi_status'] = 'API key missing ❌'
    except Exception as e:
        config['newsapi_status'] = f'NewsAPI error: {str(e)} ❌'
    
    return jsonify(config)


if __name__ == '__main__':
    print("Add /debug/config route to your app.py")
