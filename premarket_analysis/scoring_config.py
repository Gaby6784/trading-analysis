"""
Scoring System Configuration
Tune these weights and thresholds to optimize your trading strategy
"""

# ============================================================================
# COMPONENT WEIGHTS (must sum to 1.0)
# ============================================================================
# These determine how much each factor influences the final score
WEIGHTS = {
    'technical': 0.30,      # RSI, BB position, MACD
    'sentiment': 0.25,      # News sentiment score
    'momentum': 0.20,       # Trend, volatility, volume
    'catalyst': 0.15,       # News quality and recency
    'timing': 0.10          # Time of day, market regime
}

# ============================================================================
# SCORE THRESHOLDS
# ============================================================================
SCORE_STRONG_BUY = 75       # Very high conviction trade
SCORE_BUY = 65              # High conviction
SCORE_CAUTION = 50          # Mixed signals - proceed carefully
SCORE_AVOID = 35            # Weak setup
SCORE_STRONG_AVOID = 25     # Stay away

# ============================================================================
# TECHNICAL SCORE PARAMETERS
# ============================================================================
# RSI scoring curves
RSI_PERFECT_OVERSOLD = 15   # Maximum score for oversold
RSI_GOOD_OVERSOLD = 25      # Good oversold score
RSI_PERFECT_OVERBOUGHT = 85 # Maximum score for overbought
RSI_GOOD_OVERBOUGHT = 75    # Good overbought score
RSI_NEUTRAL = 50            # Neutral zone gets lower score

# Bollinger Band position scoring
BB_POSITION_WEIGHTS = {
    'BELOW_LOWER': 100,     # Outside lower band = max score
    'LOWER_HALF': 70,       # In lower half
    'MIDDLE': 40,           # Near middle
    'UPPER_HALF': 30,       # In upper half
    'ABOVE_UPPER': 20       # Outside upper band = low score (for longs)
}

# MACD scoring
MACD_BULLISH_THRESHOLD = 0.001  # Positive histogram
MACD_STRONG_BULLISH = 0.01      # Strong positive momentum

# ============================================================================
# MOMENTUM SCORE PARAMETERS
# ============================================================================
TREND_WEIGHTS = {
    'UPTREND': 100,         # Strong uptrend = max score
    'SIDEWAYS': 60,         # Sideways = neutral
    'DOWNTREND': 20,        # Downtrend = low score
    'UNKNOWN': 40,          # Unknown = below neutral
    'INSUFFICIENT_DATA': 0  # No data = no score
}

# Volatility scoring (ATR as % of price)
VOLATILITY_OPTIMAL = 3.0     # Sweet spot volatility
VOLATILITY_MAX_GOOD = 5.0    # Still acceptable
VOLATILITY_TOO_HIGH = 8.0    # Too risky

# ============================================================================
# SENTIMENT SCORE PARAMETERS
# ============================================================================
SENTIMENT_PERFECT_POSITIVE = 0.8   # Maximum positive sentiment
SENTIMENT_GOOD_POSITIVE = 0.5      # Good positive sentiment
SENTIMENT_NEUTRAL = 0.0            # Neutral
SENTIMENT_PENALTY_NEGATIVE = 2.0   # Multiply penalty for negative news

# ============================================================================
# CATALYST SCORE PARAMETERS
# ============================================================================
# News recency scoring (hours)
NEWS_FRESH = 6              # Very recent news = max score
NEWS_RECENT = 12            # Recent news = good score
NEWS_STALE = 24             # Old news = reduced score

# News volume scoring
MIN_NEWS_COUNT = 3          # Minimum news for good score
OPTIMAL_NEWS_COUNT = 8      # Optimal number of articles
MAX_NEWS_COUNT = 20         # Too many = noise

# ============================================================================
# TIMING SCORE PARAMETERS
# ============================================================================
# Time of day scoring (ET hours as float)
TIMING_OPTIMAL_START = 9.5   # Market open
TIMING_OPTIMAL_END = 10.5    # First hour
TIMING_GOOD_START = 10.5
TIMING_GOOD_END = 15.0
TIMING_AVOID_START = 15.5    # Power hour - too volatile
TIMING_AVOID_END = 16.0

# ============================================================================
# PENALTY MULTIPLIERS
# ============================================================================
PENALTY_FALLING_KNIFE = 0.5     # Cut score in half for falling knives
PENALTY_EARNINGS_SOON = 0.8     # 20% reduction if earnings within days
PENALTY_WIDE_STOPS = 0.85       # 15% reduction for wide stops
PENALTY_INSUFFICIENT_DATA = 0.3 # Major penalty for low data quality
PENALTY_NEWS_RISK = 0.6         # Bad news + good technicals = risky

# ============================================================================
# BONUS MULTIPLIERS
# ============================================================================
BONUS_STRONG_CONFLUENCE = 1.15  # 15% bonus when all signals align
BONUS_FRESH_CATALYST = 1.10     # 10% bonus for very recent news
BONUS_OVERSOLD_UPTREND = 1.12   # 12% bonus for pullback in uptrend

# ============================================================================
# QUALITY GATES (CRITICAL - PREVENT BAD ENTRIES)
# ============================================================================
MIN_DATA_QUALITY_SCORE = 20     # Minimum score needed to be tradeable
MIN_NEWS_ARTICLES = 1           # Must have at least 1 news article
MAX_ATR_PCT_ABSOLUTE = 12.0     # Never trade if ATR > 12% of price

# ENTRY REQUIREMENTS (for scores > 65)
REQUIRE_OVERSOLD_FOR_BUY = True  # Must be RSI < 35 for BUY rating
MAX_RSI_FOR_STRONG_BUY = 30      # Strong buy only if RSI < 30
MAX_RSI_FOR_BUY = 35             # Buy only if RSI < 35
MAX_RSI_FOR_ANY_LONG = 50        # Never long above RSI 50

# BB Position requirements
ALLOWED_BB_FOR_BUY = ['BELOW_LOWER', 'LOWER_HALF']  # Must be in lower area

# TREND Requirements
REQUIRE_UPTREND_FOR_STRONG_BUY = True  # Strong buy only in uptrend
REQUIRE_TREND_FOR_BUY = True           # Buy requires uptrend or unknown (not sideways/down)
ALLOWED_TRENDS_FOR_STRONG_BUY = ['UPTREND']  # Only uptrend for strong buy
ALLOWED_TRENDS_FOR_BUY = ['UPTREND', 'UNKNOWN']  # Uptrend or insufficient data
AVOID_TRENDS = ['SIDEWAYS', 'DOWNTREND']  # Never buy these
