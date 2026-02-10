"""
Trading recommendation generation
"""

from typing import Dict, Tuple
import logging
from .config import *

logger = logging.getLogger(__name__)


def generate_recommendation(technicals: Dict, sentiment: float, ticker: str) -> Tuple[str, str]:
    """
    Generate trading recommendation based on technicals and sentiment.
    
    Args:
        technicals: Dictionary of technical indicators
        sentiment: Sentiment score from -1 to 1
        ticker: Stock ticker symbol
        
    Returns:
        Tuple of (recommendation, color_code)
    """
    if technicals is None:
        return "NO DATA", "⚪"
    
    # Check for insufficient data
    if technicals.get('bb_status') == 'INSUFFICIENT_DATA':
        return "⚪ INSUFFICIENT DATA", "white"
    
    rsi = technicals.get('rsi')
    bb_status = technicals.get('bb_status')
    trend = technicals.get('trend', 'UNKNOWN')
    macd_hist = technicals.get('macd_hist', 0)
    volatility = technicals.get('volatility', 'UNKNOWN')
    atr_pct = technicals.get('atr_pct', 0)
    
    # Check if RSI is None (can happen with sparse data)
    if rsi is None:
        return "⚪ INSUFFICIENT DATA", "white"
    
    # WIDE STOPS WARNING - volatility too high for safe trading
    if atr_pct is not None and atr_pct > WIDE_STOPS_THRESHOLD:
        if rsi < RSI_OVERSOLD:
            return "⚠️  WIDE STOPS - CAUTION", "yellow"
        elif rsi > RSI_OVERBOUGHT:
            return "⚠️  WIDE STOPS - AVOID", "yellow"
    
    # FALLING KNIFE DETECTION - oversold but in strong downtrend
    if (rsi < RSI_OVERSOLD and 
        bb_status in ["BELOW_LOWER", "LOWER_HALF"] and
        trend == "DOWNTREND" and
        (macd_hist is None or macd_hist < 0)):
        return "⚠️  FALLING KNIFE - WAIT", "yellow"
    
    # STRONG BUY - oversold with trend confirmation and positive sentiment
    if (rsi < RSI_STRONG_OVERSOLD and 
        bb_status == "BELOW_LOWER" and 
        trend != "DOWNTREND" and
        sentiment > SENTIMENT_BULLISH):
        # Check for wide stops
        if atr_pct is not None and atr_pct > VOLATILITY_HIGH:
            return "🟢 BUY - WATCH STOPS", "green"
        return "🟢 STRONG BUY", "green"
    
    # STRONG SELL - overbought with trend confirmation and negative sentiment
    if (rsi > RSI_STRONG_OVERBOUGHT and 
        bb_status == "ABOVE_UPPER" and 
        trend != "UPTREND" and
        sentiment < SENTIMENT_BEARISH):
        return "🔴 STRONG SELL", "red"
    
    # AVOID - NEWS RISK (Technical buy signal but deeply negative sentiment)
    if (rsi < RSI_OVERSOLD and 
        bb_status in ["BELOW_LOWER", "LOWER_HALF"] and 
        sentiment < SENTIMENT_BEARISH):
        return "⚠️  AVOID - NEWS RISK", "yellow"
    
    # BUY - oversold with uptrend or neutral trend
    if rsi < RSI_OVERSOLD and trend in ["UPTREND", "SIDEWAYS", "UNKNOWN"] and sentiment >= 0:
        # Check for wide stops
        if atr_pct is not None and atr_pct > VOLATILITY_HIGH:
            return "🟢 BUY - WATCH STOPS", "green"
        return "🟢 BUY", "green"
    
    # SELL - overbought with downtrend confirmation
    if rsi > RSI_OVERBOUGHT and (trend == "DOWNTREND" or sentiment < 0):
        return "🔴 SELL", "red"
    
    # High volatility warning
    if volatility == "HIGH" and abs(rsi - 50) < 15:
        return "⚠️  HIGH VOLATILITY", "yellow"
    
    # CAUTION - Mixed signals
    if abs(rsi - 50) < 10 and abs(sentiment) > 0.5:
        if sentiment > 0:
            return "🟡 CAUTION - BULLISH SENTIMENT", "yellow"
        else:
            return "🟡 CAUTION - BEARISH SENTIMENT", "yellow"
    
    # HOLD - No strong signals
    return "⚪ HOLD", "white"
