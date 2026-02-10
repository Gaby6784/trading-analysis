"""
Technical indicator calculations
"""

import pandas as pd
import pandas_ta as ta
from typing import Dict, Optional
import logging
from .config import *

logger = logging.getLogger(__name__)


def get_last_valid_value(series: pd.Series, default=None):
    """Get last valid (non-NaN) value from series."""
    valid_values = series.dropna()
    return valid_values.iloc[-1] if len(valid_values) > 0 else default


def calculate_technicals(df: pd.DataFrame) -> Optional[Dict]:
    """
    Calculate technical indicators: RSI, Bollinger Bands, EMAs, MACD, ATR.
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        Dictionary with technical indicator values or None if insufficient data
    """
    if df is None or df.empty:
        return None
    
    # Data quality gate: ensure enough candles for reliable indicators
    min_required = max(RSI_PERIOD, BB_PERIOD, EMA_SLOW, ATR_PERIOD, MACD_SLOW + MACD_SIGNAL) + MIN_CANDLES_BUFFER
    
    if len(df) < min_required:
        logger.warning(f"   Insufficient data: {len(df)} candles, need {min_required} minimum")
        return {
            'price': df['Close'].iloc[-1] if not df.empty else None,
            'rsi': None,
            'bb_status': 'INSUFFICIENT_DATA',
            'trend': 'INSUFFICIENT_DATA',
            'volatility': 'INSUFFICIENT_DATA',
            'atr_pct': None,
            'suggested_stop': None,
            'bb_mid_pct': None,
            'macd_hist': None
        }
    
    try:
        # Calculate RSI
        rsi_series = ta.rsi(df['Close'], length=RSI_PERIOD)
        df['RSI'] = rsi_series
        
        # Calculate Bollinger Bands
        bb_result = ta.bbands(df['Close'], length=BB_PERIOD, std=BB_STD)
        if bb_result is not None:
            # Find the actual column names (they vary!)
            bb_cols = bb_result.columns.tolist()
            lower_col = [c for c in bb_cols if 'BBL_' in c][0] if any('BBL_' in c for c in bb_cols) else None
            mid_col = [c for c in bb_cols if 'BBM_' in c][0] if any('BBM_' in c for c in bb_cols) else None
            upper_col = [c for c in bb_cols if 'BBU_' in c][0] if any('BBU_' in c for c in bb_cols) else None
            
            if lower_col and mid_col and upper_col:
                df['BB_Lower'] = bb_result[lower_col]
                df['BB_Mid'] = bb_result[mid_col]
                df['BB_Upper'] = bb_result[upper_col]
        
        # Calculate EMAs
        df['EMA_Fast'] = ta.ema(df['Close'], length=EMA_FAST)
        df['EMA_Slow'] = ta.ema(df['Close'], length=EMA_SLOW)
        
        # Calculate MACD
        macd_result = ta.macd(df['Close'], fast=MACD_FAST, slow=MACD_SLOW, signal=MACD_SIGNAL)
        if macd_result is not None:
            macd_cols = macd_result.columns.tolist()
            hist_col = [c for c in macd_cols if 'MACDh_' in c][0] if any('MACDh_' in c for c in macd_cols) else None
            if hist_col:
                df['MACD_Hist'] = macd_result[hist_col]
        
        # Calculate ATR
        atr_series = ta.atr(df['High'], df['Low'], df['Close'], length=ATR_PERIOD)
        df['ATR'] = atr_series
        
        # Get current values (use last valid value to handle NaN)
        price = get_last_valid_value(df['Close'], default=df['Close'].iloc[-1])
        rsi = get_last_valid_value(df['RSI'])
        bb_lower = get_last_valid_value(df['BB_Lower']) if 'BB_Lower' in df else None
        bb_mid = get_last_valid_value(df['BB_Mid']) if 'BB_Mid' in df else None
        bb_upper = get_last_valid_value(df['BB_Upper']) if 'BB_Upper' in df else None
        ema_fast = get_last_valid_value(df['EMA_Fast']) if 'EMA_Fast' in df else None
        ema_slow = get_last_valid_value(df['EMA_Slow']) if 'EMA_Slow' in df else None
        macd_hist = get_last_valid_value(df['MACD_Hist']) if 'MACD_Hist' in df else None
        atr = get_last_valid_value(df['ATR'])
        
        # Determine BB status
        bb_status = "UNKNOWN"
        bb_mid_pct = None
        if bb_lower is not None and bb_upper is not None and bb_mid is not None:
            if price < bb_lower:
                bb_status = "BELOW_LOWER"
            elif price > bb_upper:
                bb_status = "ABOVE_UPPER"
            elif price < bb_mid:
                bb_status = "LOWER_HALF"
            else:
                bb_status = "UPPER_HALF"
            
            # Calculate % distance from middle band
            if bb_mid > 0:
                bb_mid_pct = ((price - bb_mid) / bb_mid) * 100
        
        # Determine trend
        trend = "UNKNOWN"
        if ema_fast is not None and ema_slow is not None:
            if ema_fast > ema_slow * 1.005:  # 0.5% buffer
                trend = "UPTREND"
            elif ema_fast < ema_slow * 0.995:
                trend = "DOWNTREND"
            else:
                trend = "SIDEWAYS"
        
        # Calculate volatility level
        volatility = "UNKNOWN"
        atr_pct = None
        if atr is not None and price > 0:
            atr_pct = (atr / price) * 100
            if atr_pct < VOLATILITY_LOW:
                volatility = "LOW"
            elif atr_pct > VOLATILITY_HIGH:
                volatility = "HIGH"
            else:
                volatility = "MED"
        
        # Calculate suggested stop loss
        suggested_stop = None
        if atr is not None:
            suggested_stop = price - (atr * ATR_STOP_MULTIPLIER)
        
        return {
            'price': round(price, 2) if price else None,
            'rsi': round(rsi, 2) if rsi else None,
            'bb_status': bb_status,
            'bb_mid_pct': round(bb_mid_pct, 2) if bb_mid_pct is not None else None,
            'trend': trend,
            'volatility': volatility,
            'atr_pct': round(atr_pct, 2) if atr_pct is not None else None,
            'suggested_stop': round(suggested_stop, 2) if suggested_stop else None,
            'macd_hist': round(macd_hist, 6) if macd_hist is not None else None
        }
        
    except Exception as e:
        logger.error(f"   Error calculating technicals: {str(e)}")
        return None
