"""
Advanced Scoring System for Trade Quality Assessment
Combines technical, sentiment, momentum, catalyst, and timing factors
"""

from typing import Dict, Tuple
import logging
from datetime import datetime

from .scoring_config import *
from .market_data import get_et_time_naive

logger = logging.getLogger(__name__)


def calculate_technical_score(technicals: Dict) -> Tuple[float, dict]:
    """
    Score technical setup (0-100).
    
    Evaluates:
    - RSI position (oversold is bullish)
    - Bollinger Band position
    - MACD histogram
    
    Returns:
        Tuple of (score, details_dict)
    """
    if not technicals or technicals.get('bb_status') == 'INSUFFICIENT_DATA':
        return 0.0, {'reason': 'insufficient_data'}
    
    score = 0.0
    details = {}
    
    # RSI Component (40 points max) - STRICT for long entries
    rsi = technicals.get('rsi')
    if rsi is not None:
        if rsi <= RSI_PERFECT_OVERSOLD:
            rsi_score = 40.0  # Perfect entry
        elif rsi <= RSI_GOOD_OVERSOLD:
            # Linear scale from perfect to good oversold
            rsi_score = 30.0 + (RSI_GOOD_OVERSOLD - rsi) / (RSI_GOOD_OVERSOLD - RSI_PERFECT_OVERSOLD) * 10.0
        elif rsi <= 35:
            # Slightly oversold - acceptable
            rsi_score = 20.0 + (35 - rsi) / (35 - RSI_GOOD_OVERSOLD) * 10.0
        elif rsi <= 40:
            # Borderline - very low score
            rsi_score = 10.0
        elif rsi <= 50:
            # Neutral - not a buy
            rsi_score = 5.0
        else:
            # Above 50 - terrible for longs
            rsi_score = 0.0
        
        score += rsi_score
        details['rsi_score'] = round(rsi_score, 1)
        details['rsi_value'] = round(rsi, 1)
    
    # Bollinger Band Component (35 points max)
    bb_status = technicals.get('bb_status', 'UNKNOWN')
    bb_score = BB_POSITION_WEIGHTS.get(bb_status, 0) * 0.35
    score += bb_score
    details['bb_score'] = round(bb_score, 1)
    
    # MACD Component (25 points max)
    macd_hist = technicals.get('macd_hist')
    if macd_hist is not None:
        if macd_hist >= MACD_STRONG_BULLISH:
            macd_score = 25.0
        elif macd_hist >= MACD_BULLISH_THRESHOLD:
            macd_score = 15.0 + (macd_hist / MACD_STRONG_BULLISH) * 10.0
        elif macd_hist >= 0:
            macd_score = 10.0
        else:
            # Negative MACD = bearish momentum
            macd_score = max(0, 10.0 + (macd_hist / 0.01) * 10.0)  # Scale down
        
        score += macd_score
        details['macd_score'] = round(macd_score, 1)
    
    return min(score, 100.0), details


def calculate_sentiment_score(sentiment: float, news_count: int) -> Tuple[float, dict]:
    """
    Score sentiment quality (0-100).
    
    Evaluates:
    - Sentiment score magnitude
    - Sentiment direction
    - News volume as confidence indicator
    
    Returns:
        Tuple of (score, details_dict)
    """
    score = 0.0
    details = {}
    
    # Base sentiment score (70 points max)
    if sentiment >= SENTIMENT_PERFECT_POSITIVE:
        sentiment_base = 70.0
    elif sentiment >= SENTIMENT_GOOD_POSITIVE:
        # Scale from good to perfect
        sentiment_base = 50.0 + ((sentiment - SENTIMENT_GOOD_POSITIVE) / 
                                 (SENTIMENT_PERFECT_POSITIVE - SENTIMENT_GOOD_POSITIVE)) * 20.0
    elif sentiment >= SENTIMENT_NEUTRAL:
        # Scale from neutral to good
        sentiment_base = 30.0 + (sentiment / SENTIMENT_GOOD_POSITIVE) * 20.0
    elif sentiment >= -SENTIMENT_GOOD_POSITIVE:
        # Slightly negative
        sentiment_base = 20.0 + ((sentiment - (-SENTIMENT_GOOD_POSITIVE)) / 
                                 SENTIMENT_GOOD_POSITIVE) * 10.0
    else:
        # Very negative - severe penalty
        sentiment_base = max(0, 20.0 + (sentiment / -SENTIMENT_GOOD_POSITIVE) * 20.0)
    
    # Apply negative sentiment penalty
    if sentiment < 0:
        sentiment_base *= (1.0 / SENTIMENT_PENALTY_NEGATIVE)
    
    score += sentiment_base
    details['sentiment_base'] = round(sentiment_base, 1)
    
    # News volume confidence (30 points max)
    if news_count >= OPTIMAL_NEWS_COUNT:
        news_volume_score = 30.0
    elif news_count >= MIN_NEWS_COUNT:
        # Scale from min to optimal
        news_volume_score = 15.0 + ((news_count - MIN_NEWS_COUNT) / 
                                    (OPTIMAL_NEWS_COUNT - MIN_NEWS_COUNT)) * 15.0
    elif news_count > 0:
        # Some news is better than none
        news_volume_score = (news_count / MIN_NEWS_COUNT) * 15.0
    else:
        # No news = low confidence
        news_volume_score = 0.0
    
    # Too much news can be noise
    if news_count > MAX_NEWS_COUNT:
        news_volume_score *= 0.8
    
    score += news_volume_score
    details['news_volume_score'] = round(news_volume_score, 1)
    
    return min(score, 100.0), details


def calculate_momentum_score(technicals: Dict) -> Tuple[float, dict]:
    """
    Score momentum and trend quality (0-100).
    
    Evaluates:
    - Trend direction
    - Volatility level
    - EMA alignment (if available)
    
    Returns:
        Tuple of (score, details_dict)
    """
    if not technicals:
        return 0.0, {'reason': 'no_data'}
    
    score = 0.0
    details = {}
    
    # Trend component (60 points max)
    trend = technicals.get('trend', 'UNKNOWN')
    trend_score = TREND_WEIGHTS.get(trend, 40) * 0.6
    score += trend_score
    details['trend_score'] = round(trend_score, 1)
    
    # Volatility component (40 points max)
    atr_pct = technicals.get('atr_pct')
    if atr_pct is not None:
        if atr_pct <= VOLATILITY_OPTIMAL:
            # Optimal volatility = max score
            vol_score = 40.0
        elif atr_pct <= VOLATILITY_MAX_GOOD:
            # Acceptable range
            vol_score = 30.0 + (VOLATILITY_MAX_GOOD - atr_pct) / \
                        (VOLATILITY_MAX_GOOD - VOLATILITY_OPTIMAL) * 10.0
        elif atr_pct <= VOLATILITY_TOO_HIGH:
            # Getting risky
            vol_score = 15.0 + (VOLATILITY_TOO_HIGH - atr_pct) / \
                        (VOLATILITY_TOO_HIGH - VOLATILITY_MAX_GOOD) * 15.0
        else:
            # Too volatile
            vol_score = max(0, 15.0 - (atr_pct - VOLATILITY_TOO_HIGH) * 2)
        
        score += vol_score
        details['volatility_score'] = round(vol_score, 1)
        details['atr_pct'] = round(atr_pct, 2)
    
    return min(score, 100.0), details


def calculate_catalyst_score(news_count: int, news_age_hours: float) -> Tuple[float, dict]:
    """
    Score news catalyst quality (0-100).
    
    Evaluates:
    - News recency
    - News volume
    
    Returns:
        Tuple of (score, details_dict)
    """
    score = 0.0
    details = {}
    
    # Recency score (60 points max)
    if news_age_hours <= NEWS_FRESH:
        recency_score = 60.0
    elif news_age_hours <= NEWS_RECENT:
        recency_score = 45.0 + (NEWS_RECENT - news_age_hours) / \
                        (NEWS_RECENT - NEWS_FRESH) * 15.0
    elif news_age_hours <= NEWS_STALE:
        recency_score = 20.0 + (NEWS_STALE - news_age_hours) / \
                        (NEWS_STALE - NEWS_RECENT) * 25.0
    else:
        # Stale news
        recency_score = max(0, 20.0 - (news_age_hours - NEWS_STALE) / 24.0 * 10.0)
    
    score += recency_score
    details['recency_score'] = round(recency_score, 1)
    details['news_age_hours'] = round(news_age_hours, 1)
    
    # Catalyst presence (40 points max)
    if news_count >= OPTIMAL_NEWS_COUNT:
        catalyst_score = 40.0
    elif news_count >= MIN_NEWS_COUNT:
        catalyst_score = 25.0 + ((news_count - MIN_NEWS_COUNT) / 
                                 (OPTIMAL_NEWS_COUNT - MIN_NEWS_COUNT)) * 15.0
    elif news_count > 0:
        catalyst_score = (news_count / MIN_NEWS_COUNT) * 25.0
    else:
        catalyst_score = 0.0
    
    score += catalyst_score
    details['catalyst_score'] = round(catalyst_score, 1)
    
    return min(score, 100.0), details


def calculate_timing_score() -> Tuple[float, dict]:
    """
    Score time of day quality (0-100).
    
    Evaluates:
    - Market session timing
    - Optimal trading windows
    
    Returns:
        Tuple of (score, details_dict)
    """
    now = get_et_time_naive()
    current_hour = now.hour + now.minute / 60.0
    
    details = {'current_hour_et': round(current_hour, 2)}
    
    # Check if weekend
    if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return 30.0, {**details, 'reason': 'weekend'}
    
    # Check if premarket (before 9:30 ET)
    if current_hour < TIMING_OPTIMAL_START:
        score = 50.0  # Premarket = moderate score
        details['session'] = 'premarket'
    # Optimal window (9:30-10:30 ET)
    elif TIMING_OPTIMAL_START <= current_hour <= TIMING_OPTIMAL_END:
        score = 100.0
        details['session'] = 'optimal'
    # Good window (10:30-15:00 ET)
    elif TIMING_GOOD_START <= current_hour <= TIMING_GOOD_END:
        score = 80.0
        details['session'] = 'good'
    # Power hour (15:30-16:00 ET)
    elif TIMING_AVOID_START <= current_hour <= TIMING_AVOID_END:
        score = 40.0
        details['session'] = 'power_hour'
    # After hours
    elif current_hour > TIMING_AVOID_END:
        score = 30.0
        details['session'] = 'afterhours'
    else:
        score = 60.0
        details['session'] = 'midday'
    
    return score, details


def apply_penalties_and_bonuses(base_score: float, technicals: Dict, sentiment: float, 
                                 news_age_hours: float, earnings_flag: str) -> Tuple[float, list]:
    """
    Apply penalties and bonuses based on risk factors and confluence.
    CRITICAL: Enforce entry requirements to prevent buying at bad prices.
    
    Returns:
        Tuple of (adjusted_score, list_of_adjustments)
    """
    score = base_score
    adjustments = []
    
    if not technicals:
        return score, adjustments
    
    rsi = technicals.get('rsi')
    trend = technicals.get('trend')
    bb_status = technicals.get('bb_status')
    macd_hist = technicals.get('macd_hist')
    atr_pct = technicals.get('atr_pct')
    
    # CRITICAL QUALITY GATES - Prevent buying at wrong levels
    from .scoring_config import (REQUIRE_OVERSOLD_FOR_BUY, MAX_RSI_FOR_BUY, 
                                 MAX_RSI_FOR_STRONG_BUY, MAX_RSI_FOR_ANY_LONG,
                                 ALLOWED_BB_FOR_BUY)
    
    # Gate 1: Never score high if RSI too high (buying expensive)
    if rsi and rsi > MAX_RSI_FOR_ANY_LONG:
        score = min(score, 40.0)  # Cap at AVOID level
        adjustments.append(f"NOT_OVERSOLD: RSI {rsi:.0f} > {MAX_RSI_FOR_ANY_LONG}")
    
    # Gate 2: Require oversold for BUY rating
    if REQUIRE_OVERSOLD_FOR_BUY and rsi:
        if score >= 75 and rsi > MAX_RSI_FOR_STRONG_BUY:
            score = min(score, 64.0)  # Downgrade from STRONG_BUY
            adjustments.append(f"MISSED_ENTRY: RSI {rsi:.0f} too high for STRONG_BUY")
        elif score >= 65 and rsi > MAX_RSI_FOR_BUY:
            score = min(score, 49.0)  # Downgrade to CAUTION
            adjustments.append(f"MISSED_ENTRY: RSI {rsi:.0f} too high for BUY")
    
    # Gate 3: BB position must be in lower area for BUY
    if bb_status and bb_status not in ALLOWED_BB_FOR_BUY and score >= 65:
        score = min(score, 49.0)  # Downgrade to CAUTION
        adjustments.append(f"WRONG_BB_POSITION: {bb_status} not in lower area")
    
    # Gate 4: Trend requirements for BUY signals
    from .scoring_config import (REQUIRE_UPTREND_FOR_STRONG_BUY, REQUIRE_TREND_FOR_BUY,
                                 ALLOWED_TRENDS_FOR_STRONG_BUY, ALLOWED_TRENDS_FOR_BUY,
                                 AVOID_TRENDS)
    
    if trend:
        # Strong Buy requires UPTREND
        if REQUIRE_UPTREND_FOR_STRONG_BUY and score >= 75:
            if trend not in ALLOWED_TRENDS_FOR_STRONG_BUY:
                score = min(score, 49.0)  # Downgrade to CAUTION
                adjustments.append(f"WRONG_TREND: {trend} - need UPTREND for STRONG_BUY")
        
        # Buy requires favorable trend
        if REQUIRE_TREND_FOR_BUY and score >= 65:
            if trend not in ALLOWED_TRENDS_FOR_BUY:
                score = min(score, 49.0)  # Downgrade to CAUTION
                adjustments.append(f"UNFAVORABLE_TREND: {trend} - waiting for uptrend")
        
        # Sideways/Downtrend penalty even for moderate scores
        if trend in AVOID_TRENDS and score >= 50:
            score = min(score, 45.0)  # Keep in AVOID range
            adjustments.append(f"AVOID_TREND_{trend}: Wait for direction")
    
    # PENALTIES
    
    # Falling knife detection
    if (rsi and rsi < 30 and 
        bb_status in ["BELOW_LOWER", "LOWER_HALF"] and
        trend == "DOWNTREND" and
        (macd_hist is None or macd_hist < 0)):
        score *= PENALTY_FALLING_KNIFE
        adjustments.append(f"FALLING_KNIFE: {int((PENALTY_FALLING_KNIFE - 1) * 100)}%")
    
    # Earnings risk
    if earnings_flag:
        score *= PENALTY_EARNINGS_SOON
        adjustments.append(f"EARNINGS_SOON: {int((PENALTY_EARNINGS_SOON - 1) * 100)}%")
    
    # Wide stops
    if atr_pct and atr_pct > VOLATILITY_TOO_HIGH:
        score *= PENALTY_WIDE_STOPS
        adjustments.append(f"WIDE_STOPS: {int((PENALTY_WIDE_STOPS - 1) * 100)}%")
    
    # News risk (negative news with technical buy signal)
    if (rsi and rsi < 30 and 
        bb_status in ["BELOW_LOWER", "LOWER_HALF"] and 
        sentiment < -0.5):
        score *= PENALTY_NEWS_RISK
        adjustments.append(f"NEWS_RISK: {int((PENALTY_NEWS_RISK - 1) * 100)}%")
    
    # Insufficient data
    if bb_status == 'INSUFFICIENT_DATA':
        score *= PENALTY_INSUFFICIENT_DATA
        adjustments.append(f"INSUFFICIENT_DATA: {int((PENALTY_INSUFFICIENT_DATA - 1) * 100)}%")
    
    # BONUSES
    
    # Strong confluence (oversold + below BB + positive sentiment + uptrend)
    if (rsi and rsi < 30 and 
        bb_status in ["BELOW_LOWER"] and 
        sentiment > 0.3 and
        trend == "UPTREND" and
        macd_hist and macd_hist > 0):
        score *= BONUS_STRONG_CONFLUENCE
        adjustments.append(f"STRONG_CONFLUENCE: +{int((BONUS_STRONG_CONFLUENCE - 1) * 100)}%")
    
    # Fresh catalyst
    if news_age_hours < NEWS_FRESH:
        score *= BONUS_FRESH_CATALYST
        adjustments.append(f"FRESH_CATALYST: +{int((BONUS_FRESH_CATALYST - 1) * 100)}%")
    
    # Oversold in uptrend (pullback buying opportunity)
    if (rsi and rsi < 35 and 
        trend == "UPTREND" and
        bb_status in ["BELOW_LOWER", "LOWER_HALF"]):
        score *= BONUS_OVERSOLD_UPTREND
        adjustments.append(f"OVERSOLD_UPTREND: +{int((BONUS_OVERSOLD_UPTREND - 1) * 100)}%")
    
    return min(score, 100.0), adjustments


def calculate_trade_score(technicals: Dict, sentiment: float, news_count: int, 
                          news_age_hours: float, earnings_flag: str) -> Dict:
    """
    Calculate comprehensive trade quality score (0-100).
    
    Args:
        technicals: Technical indicators dict
        sentiment: Sentiment score (-1 to 1)
        news_count: Number of news articles
        news_age_hours: Age of oldest news article
        earnings_flag: Earnings flag ("E" if earnings soon, "" otherwise)
    
    Returns:
        Dictionary with overall score and component breakdowns
    """
    # Calculate component scores
    tech_score, tech_details = calculate_technical_score(technicals)
    sent_score, sent_details = calculate_sentiment_score(sentiment, news_count)
    momentum_score, momentum_details = calculate_momentum_score(technicals)
    catalyst_score, catalyst_details = calculate_catalyst_score(news_count, news_age_hours)
    timing_score, timing_details = calculate_timing_score()
    
    # Calculate weighted base score
    base_score = (
        tech_score * WEIGHTS['technical'] +
        sent_score * WEIGHTS['sentiment'] +
        momentum_score * WEIGHTS['momentum'] +
        catalyst_score * WEIGHTS['catalyst'] +
        timing_score * WEIGHTS['timing']
    )
    
    # Apply penalties and bonuses
    final_score, adjustments = apply_penalties_and_bonuses(
        base_score, technicals, sentiment, news_age_hours, earnings_flag
    )
    
    # Quality gates
    quality_flags = []
    if technicals and technicals.get('atr_pct'):
        if technicals['atr_pct'] > MAX_ATR_PCT_ABSOLUTE:
            quality_flags.append("VOLATILITY_TOO_HIGH")
            final_score = min(final_score, MIN_DATA_QUALITY_SCORE)
    
    if news_count < MIN_NEWS_ARTICLES:
        quality_flags.append("INSUFFICIENT_NEWS")
    
    # Determine score category
    if final_score >= SCORE_STRONG_BUY:
        category = "STRONG_BUY"
        emoji = "🟢"
    elif final_score >= SCORE_BUY:
        category = "BUY"
        emoji = "🟢"
    elif final_score >= SCORE_CAUTION:
        category = "CAUTION"
        emoji = "🟡"
    elif final_score >= SCORE_AVOID:
        category = "AVOID"
        emoji = "🟠"
    else:
        category = "STRONG_AVOID"
        emoji = "🔴"
    
    # Add warning for non-oversold BUY signals
    if category in ["BUY", "STRONG_BUY"] and technicals:
        rsi = technicals.get('rsi')
        bb_status = technicals.get('bb_status')
        trend = technicals.get('trend')
        if rsi and rsi > 35:
            quality_flags.append(f"WARNING_NOT_OVERSOLD_RSI_{int(rsi)}")
        if bb_status and bb_status not in ['BELOW_LOWER', 'LOWER_HALF']:
            quality_flags.append(f"WARNING_NOT_IN_LOWER_BB_{bb_status}")
        if trend and trend not in ['UPTREND', 'UNKNOWN']:
            quality_flags.append(f"WARNING_TREND_{trend}_NOT_BULLISH")
    
    return {
        'final_score': round(final_score, 1),
        'base_score': round(base_score, 1),
        'category': category,
        'emoji': emoji,
        'components': {
            'technical': {'score': round(tech_score, 1), 'weight': WEIGHTS['technical'], 'details': tech_details},
            'sentiment': {'score': round(sent_score, 1), 'weight': WEIGHTS['sentiment'], 'details': sent_details},
            'momentum': {'score': round(momentum_score, 1), 'weight': WEIGHTS['momentum'], 'details': momentum_details},
            'catalyst': {'score': round(catalyst_score, 1), 'weight': WEIGHTS['catalyst'], 'details': catalyst_details},
            'timing': {'score': round(timing_score, 1), 'weight': WEIGHTS['timing'], 'details': timing_details}
        },
        'adjustments': adjustments,
        'quality_flags': quality_flags
    }


def get_score_interpretation(score: float) -> str:
    """Get human-readable interpretation of score."""
    if score >= SCORE_STRONG_BUY:
        return "Very high conviction - strong entry signal with multiple confirmations"
    elif score >= SCORE_BUY:
        return "High conviction - good setup with favorable risk/reward"
    elif score >= SCORE_CAUTION:
        return "Moderate conviction - mixed signals, proceed with caution"
    elif score >= SCORE_AVOID:
        return "Low conviction - weak setup, better to wait"
    else:
        return "Very low conviction - avoid trading this setup"
