"""
Market data fetching and time utilities
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import logging
from .config import *

logger = logging.getLogger(__name__)


def get_et_time() -> datetime:
    """Get current time in ET timezone."""
    return datetime.now(ET_TIMEZONE)


def get_et_time_naive() -> datetime:
    """Get current time in ET timezone, but timezone-naive for comparisons."""
    return datetime.now(ET_TIMEZONE).replace(tzinfo=None)


def is_market_hours(dt: datetime, session: str = 'regular') -> bool:
    """
    Check if datetime is within specified market session (ET).
    
    Args:
        dt: datetime object (should be ET timezone or timezone-naive ET)
        session: 'premarket', 'regular', 'extended', 'all_sessions', or 'all'
        
    Returns:
        True if within specified session
    """
    hour = dt.hour + dt.minute / 60.0
    weekday = dt.weekday()
    
    # 'all' means no filtering at all
    if session == 'all':
        return True
    
    # All other sessions should exclude weekends
    if weekday >= 5:
        return False
    
    if session == 'premarket':
        return PREMARKET_START <= hour < PREMARKET_END
    elif session == 'regular':
        return REGULAR_START <= hour < REGULAR_END
    elif session == 'extended':
        return REGULAR_START <= hour < EXTENDED_END
    elif session == 'all_sessions':
        # Pre-market + regular + after-hours (04:00-20:00 ET weekdays)
        return PREMARKET_START <= hour < EXTENDED_END
    else:
        return REGULAR_START <= hour < REGULAR_END


def fetch_market_data(ticker: str, period: str = "10d", interval: str = "1h") -> Optional[pd.DataFrame]:
    """
    Fetch market data from yfinance with session filtering.
    
    Args:
        ticker: Stock ticker symbol
        period: Time period (e.g., "10d", "1mo")
        interval: Data interval (e.g., "1h", "15m")
        
    Returns:
        DataFrame with OHLCV data or None on error
    """
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)
        
        if df is None or df.empty:
            logger.warning(f"   No data returned for {ticker}")
            return None
        
        # Filter by market session if not 'all'
        if MARKET_SESSION != 'all' and not df.empty:
            if df.index.tz is None:
                # Assume UTC, convert to ET
                df.index = pd.to_datetime(df.index).tz_localize('UTC').tz_convert(ET_TIMEZONE)
            else:
                df.index = df.index.tz_convert(ET_TIMEZONE)
            
            # Filter to specified session
            mask = df.index.to_series().apply(lambda x: is_market_hours(x, MARKET_SESSION))
            df = df[mask]
            
            if df.empty:
                logger.warning(f"   No data for {ticker} in {MARKET_SESSION} session")
                return None
        
        logger.debug(f"   Fetched {len(df)} candles for {ticker}")
        return df
        
    except Exception as e:
        logger.error(f"   Error fetching data for {ticker}: {str(e)}")
        return None


def get_earnings_date(ticker: str) -> Optional[datetime]:
    """
    Get next earnings date for a ticker with multiple fallback attempts.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Next earnings date (timezone-naive) or None
    """
    try:
        stock = yf.Ticker(ticker)
        
        # Method 1: Try calendar attribute
        try:
            calendar = stock.calendar
            if calendar is not None:
                # Handle different return types (dict, DataFrame, etc.)
                if isinstance(calendar, dict) and 'Earnings Date' in calendar:
                    earnings_dates = calendar['Earnings Date']
                    if isinstance(earnings_dates, list) and len(earnings_dates) > 0:
                        next_earnings = pd.to_datetime(earnings_dates[0])
                        # Return timezone-naive
                        return next_earnings.replace(tzinfo=None) if hasattr(next_earnings, 'tzinfo') and next_earnings.tzinfo else next_earnings
                elif isinstance(calendar, pd.DataFrame) and 'Earnings Date' in calendar.index:
                    next_earnings = pd.to_datetime(calendar.loc['Earnings Date'].iloc[0])
                    return next_earnings.replace(tzinfo=None) if hasattr(next_earnings, 'tzinfo') and next_earnings.tzinfo else next_earnings
        except:
            pass
        
        # Method 2: Try get_earnings_dates if available
        try:
            if hasattr(stock, 'get_earnings_dates'):
                earnings_df = stock.get_earnings_dates(limit=1)
                if earnings_df is not None and not earnings_df.empty:
                    next_earnings = earnings_df.index[0]
                    return next_earnings.replace(tzinfo=None) if hasattr(next_earnings, 'tzinfo') and next_earnings.tzinfo else next_earnings
        except:
            pass
        
        # Method 3: Try earnings_dates attribute
        try:
            if hasattr(stock, 'earnings_dates'):
                earnings_df = stock.earnings_dates
                if earnings_df is not None and not earnings_df.empty:
                    # Get future dates only
                    now = get_et_time_naive()
                    future_earnings = earnings_df[earnings_df.index > pd.Timestamp(now)]
                    if not future_earnings.empty:
                        next_earnings = future_earnings.index[0]
                        return next_earnings.replace(tzinfo=None) if hasattr(next_earnings, 'tzinfo') and next_earnings.tzinfo else next_earnings
        except:
            pass
            
    except Exception as e:
        logger.debug(f"   Could not fetch earnings for {ticker}: {str(e)}")
    
    return None
