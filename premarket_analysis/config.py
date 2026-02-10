"""
Configuration settings for Pre-Market Stock Analysis Tool
"""

from zoneinfo import ZoneInfo

# ============================================================================
# TICKERS
# ============================================================================
TICKERS = ['NVDA', 'META', 'MSFT', 'NFLX', 'AAPL', 'PUBM', 'AMZN']

# ============================================================================
# TRADING CAPITAL
# ============================================================================
TRADING_CAPITAL = 200.0  # Initial capital in dollars

# ============================================================================
# TIMEZONE CONFIGURATION
# ============================================================================
ET_TIMEZONE = ZoneInfo("America/New_York")

# ============================================================================
# MARKET SESSION CONFIGURATION
# ============================================================================
# Options: 'premarket', 'regular', 'extended', 'all_sessions', 'all'
# 'all_sessions': 04:00-20:00 ET weekdays (pre + regular + after hours)
# 'all': no time filtering at all (24/7)
MARKET_SESSION = 'all'  # Use 'all' for max data, 'regular' for market hours only

# Session Times (ET hours as float)
PREMARKET_START = 4.0      # 04:00 ET
PREMARKET_END = 9.5        # 09:30 ET
REGULAR_START = 9.5        # 09:30 ET
REGULAR_END = 16.0         # 16:00 ET
EXTENDED_END = 20.0        # 20:00 ET

# ============================================================================
# TECHNICAL INDICATOR PARAMETERS
# ============================================================================
RSI_PERIOD = 14
BB_PERIOD = 20
BB_STD = 2.0
EMA_FAST = 20
EMA_SLOW = 50
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
ATR_PERIOD = 14

# ============================================================================
# TRADING LOGIC THRESHOLDS
# ============================================================================
RSI_OVERSOLD = 30          # Standard oversold
RSI_OVERBOUGHT = 70        # Standard overbought
RSI_STRONG_OVERSOLD = 20   # Extreme oversold
RSI_STRONG_OVERBOUGHT = 80 # Extreme overbought
SENTIMENT_BULLISH = 0.5
SENTIMENT_BEARISH = -0.5

# Volatility Thresholds (ATR as % of price)
VOLATILITY_LOW = 2.0       # ATR < 2% of price
VOLATILITY_HIGH = 5.0      # ATR > 5% of price
WIDE_STOPS_THRESHOLD = 8.0 # Warn if ATR > 8% of price

# ============================================================================
# RISK MANAGEMENT
# ============================================================================
ATR_STOP_MULTIPLIER = 1.5  # Suggested stop = 1.5 * ATR
EARNINGS_RISK_DAYS = 7     # Flag if earnings within N days

# ============================================================================
# DATA QUALITY
# ============================================================================
# Minimum candles needed for reliable indicators
MIN_CANDLES_BUFFER = 5

# ============================================================================
# NEWS CACHING
# ============================================================================
ENABLE_NEWS_CACHE = True
CACHE_DURATION_MINUTES = 15
CACHE_CLEANUP_HOURS = 24   # Clean up cache files older than this

# News API Configuration
NEWS_API_KEY = "55bd26f16e745c98bfb74132ffb6c95"
NEWS_LOOKBACK_HOURS = 24

# News Source Priority (will try in order until successful)
NEWS_SOURCES = ['reuters', 'yahoo_rss', 'finviz', 'newsapi']

# ============================================================================
# AI CONFIGURATION
# ============================================================================
AI_API_KEY = "AIzaSyD1nVwqC3Xs1K_ca2w9EBwZ8Q15fz-IEKE"
USE_AI_SENTIMENT = False  # Set to True to enable Gemini-powered sentiment analysis

# ============================================================================
# LOGGING
# ============================================================================
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
