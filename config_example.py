"""
Configuration file for Pre-Market Analysis Tool
Copy this to config.py and customize your settings
"""

# ============================================================================
# API KEYS
# ============================================================================

# NewsAPI - Get free key from https://newsapi.org/
NEWS_API_KEY = "YOUR_NEWS_API_KEY_HERE"

# OpenAI API Key (optional)
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY_HERE"

# Google Gemini API Key (optional)
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"

# Enable AI sentiment analysis (requires API key above)
USE_AI_SENTIMENT = False
AI_PROVIDER = "openai"  # Options: "openai" or "gemini"

# ============================================================================
# STOCK UNIVERSE
# ============================================================================

# Tickers to analyze
TICKERS = [
    'NVDA',  # NVIDIA
    'META',  # Meta/Facebook
    'MSFT',  # Microsoft
    'NFLX',  # Netflix
    'AAPL',  # Apple
    'PUBM',  # PubMatic
    'AMZN'   # Amazon
]

# Add more sectors:
# TECH_TICKERS = ['GOOGL', 'TSLA', 'AMD', 'INTC']
# FINANCE_TICKERS = ['JPM', 'BAC', 'GS', 'MS']
# ENERGY_TICKERS = ['XOM', 'CVX', 'COP', 'SLB']

# ============================================================================
# DATA PARAMETERS
# ============================================================================

# Historical data lookback period (days)
DATA_LOOKBACK_DAYS = 30

# Data interval (yfinance supported: 1m, 5m, 15m, 30m, 1h, 1d)
DATA_INTERVAL = '1h'

# News lookback period (hours)
NEWS_LOOKBACK_HOURS = 24

# ============================================================================
# TECHNICAL INDICATOR PARAMETERS
# ============================================================================

# RSI (Relative Strength Index)
RSI_PERIOD = 14

# Bollinger Bands
BB_PERIOD = 20
BB_STD_DEV = 2.0

# Additional indicators (future expansion)
# MACD_FAST = 12
# MACD_SLOW = 26
# MACD_SIGNAL = 9
# EMA_FAST = 20
# EMA_SLOW = 50

# ============================================================================
# TRADING LOGIC THRESHOLDS
# ============================================================================

# RSI Levels
RSI_OVERSOLD = 20      # Below this = oversold (buy signal)
RSI_OVERBOUGHT = 80    # Above this = overbought (sell signal)
RSI_MODERATE_LOW = 30  # Moderate oversold
RSI_MODERATE_HIGH = 70 # Moderate overbought

# Sentiment Thresholds
SENTIMENT_VERY_BULLISH = 0.7
SENTIMENT_BULLISH = 0.5
SENTIMENT_NEUTRAL_HIGH = 0.3
SENTIMENT_NEUTRAL_LOW = -0.3
SENTIMENT_BEARISH = -0.5
SENTIMENT_VERY_BEARISH = -0.7

# Confidence thresholds for signals
MIN_NEWS_COUNT = 2  # Minimum news articles required for sentiment

# ============================================================================
# SIGNAL WEIGHTS (for future scoring system)
# ============================================================================

WEIGHT_TECHNICAL = 0.6   # 60% weight to technical indicators
WEIGHT_SENTIMENT = 0.4   # 40% weight to sentiment

# ============================================================================
# OUTPUT SETTINGS
# ============================================================================

# Display options
SHOW_DETAILED_ANALYSIS = True
SAVE_TO_CSV = False
CSV_OUTPUT_PATH = 'premarket_analysis_results.csv'

# Alert settings
ALERT_ON_STRONG_SIGNALS = True
EMAIL_ALERTS = False  # Future feature
EMAIL_ADDRESS = "your_email@example.com"

# ============================================================================
# ADVANCED SETTINGS
# ============================================================================

# Risk management
MAX_POSITION_RISK_PCT = 1.0  # Future feature: position sizing

# Backtesting
ENABLE_BACKTESTING = False   # Future feature

# Logging
LOG_LEVEL = "INFO"  # Options: DEBUG, INFO, WARNING, ERROR
LOG_TO_FILE = False
LOG_FILE_PATH = "premarket_analysis.log"

# Performance
MAX_CONCURRENT_REQUESTS = 5  # For parallel data fetching
REQUEST_TIMEOUT_SECONDS = 10

# ============================================================================
# CUSTOM FILTERS
# ============================================================================

# Price filters
MIN_PRICE = 0    # Ignore stocks below this price
MAX_PRICE = 9999 # Ignore stocks above this price

# Volume filters
MIN_AVG_VOLUME = 0  # Minimum average volume (future feature)

# Market cap filters (future feature)
MIN_MARKET_CAP = 0
MAX_MARKET_CAP = float('inf')
