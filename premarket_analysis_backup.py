"""
Pre-Market Stock Analysis Tool
Analyzes tickers using technical indicators, news sentiment, and AI-powered recommendations.
"""

import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from prettytable import PrettyTable
import requests
from typing import Dict, List, Tuple, Optional
import warnings
from dateutil import parser as date_parser
import json
import os
import hashlib
import logging
warnings.filterwarnings('ignore')

# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

# Set to DEBUG for verbose output, INFO for normal, WARNING for quiet
LOG_LEVEL = logging.INFO
logger.setLevel(LOG_LEVEL)

# ============================================================================
# CONFIGURATION
# ============================================================================

TICKERS = ['NVDA', 'META', 'MSFT', 'NFLX', 'AAPL', 'PUBM', 'AMZN']

# Timezone Configuration
ET_TIMEZONE = ZoneInfo("America/New_York")

# Market Session Configuration
# Options: 'premarket', 'regular', 'extended', 'all'
MARKET_SESSION = 'all'  # Change to 'regular' for 9:30-16:00 ET only

# Session Times (ET)
PREMARKET_START = 4   # 04:00 ET
PREMARKET_END = 9.5   # 09:30 ET
REGULAR_START = 9.5   # 09:30 ET
REGULAR_END = 16      # 16:00 ET
EXTENDED_END = 20     # 20:00 ET

# Technical Indicator Parameters
RSI_PERIOD = 14
BB_PERIOD = 20
BB_STD = 2.0
EMA_FAST = 20
EMA_SLOW = 50
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
ATR_PERIOD = 14

# Trading Logic Thresholds (More Practical)
RSI_OVERSOLD = 30          # Standard oversold
RSI_OVERBOUGHT = 70        # Standard overbought
RSI_STRONG_OVERSOLD = 20   # Extreme oversold
RSI_STRONG_OVERBOUGHT = 80 # Extreme overbought
SENTIMENT_BULLISH = 0.5
SENTIMENT_BEARISH = -0.5

# Volatility Thresholds (ATR as % of price)
VOLATILITY_LOW = 2.0       # ATR < 2% of price
VOLATILITY_HIGH = 5.0      # ATR > 5% of price

# Risk Management
ATR_STOP_MULTIPLIER = 1.5  # Suggested stop = 1.5 * ATR

# Earnings Detection
EARNINGS_RISK_DAYS = 7     # Flag if earnings within N days

# News Caching
ENABLE_NEWS_CACHE = True
CACHE_DURATION_MINUTES = 15
CACHE_DIR = os.path.join(os.path.dirname(__file__), '.news_cache')

# News API Configuration (Get free key from https://newsapi.org/)
NEWS_API_KEY = "YOUR_NEWS_API_KEY_HERE"  # Replace with your API key
NEWS_LOOKBACK_HOURS = 24

# News Source Priority (will try in order until successful)
# Options: 'yahoo_rss', 'finviz', 'newsapi', 'google_news'
NEWS_SOURCES = ['yahoo_rss', 'finviz', 'newsapi']  # Yahoo RSS is free and doesn't need API key

# AI API Configuration (Optional - for Gemini or OpenAI)
AI_API_KEY = "YOUR_AI_API_KEY_HERE"  # Replace with your AI API key
USE_AI_SENTIMENT = False  # Set to True when you have API keys configured

# ============================================================================
# MARKET DATA FUNCTIONS
# ============================================================================

def get_et_time() -> datetime:
    """Get current time in ET timezone."""
    return datetime.now(ET_TIMEZONE)

def is_market_hours(dt: datetime, session: str = 'regular') -> bool:
    """
    Check if datetime is within specified market session (ET).
    
    Args:
        dt: datetime object (should be ET timezone)
        session: 'premarket', 'regular', 'extended', or 'all'
    """
    hour = dt.hour + dt.minute / 60.0
    weekday = dt.weekday()
    
    # Skip weekends
    if weekday >= 5:
        return False
    
    if session == 'premarket':
        return PREMARKET_START <= hour < PREMARKET_END
    elif session == 'regular':
        return REGULAR_START <= hour < REGULAR_END
    elif session == 'extended':
        return PREMARKET_START <= hour < EXTENDED_END
    else:  # 'all'
        return True

def filter_by_session(df: pd.DataFrame, session: str = 'all') -> pd.DataFrame:
    """
    Filter DataFrame to include only data from specified market session.
    
    Args:
        df: DataFrame with datetime index
        session: 'premarket', 'regular', 'extended', or 'all'
    """
    if session == 'all' or df is None or df.empty:
        return df
    
    # Convert index to ET if not already
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC').tz_convert(ET_TIMEZONE)
    elif df.index.tz != ET_TIMEZONE:
        df.index = df.index.tz_convert(ET_TIMEZONE)
    
    # Filter by session
    mask = df.index.to_series().apply(lambda x: is_market_hours(x, session))
    return df[mask]

def fetch_market_data(ticker: str, days: int = 30) -> pd.DataFrame:
    """
    Fetch historical market data for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        days: Number of days to look back
        
    Returns:
        DataFrame with OHLCV data filtered by market session
    """
    try:
        end_date = get_et_time()
        start_date = end_date - timedelta(days=days)
        
        stock = yf.Ticker(ticker)
        df = stock.history(
            start=start_date,
            end=end_date,
            interval='1h'
        )
        
        if df.empty:
            logger.warning(f"No data available for {ticker}")
            return None
        
        # Filter by market session
        df = filter_by_session(df, MARKET_SESSION)
        
        if df.empty:
            logger.warning(f"No data in {MARKET_SESSION} session for {ticker}")
            return None
            
        return df
        
    except Exception as e:
        logger.error(f"Error fetching data for {ticker}: {str(e)}")
        return None

def get_earnings_date(ticker: str) -> Optional[datetime]:
    """
    Get next earnings date for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Next earnings date or None
    """
    try:
        stock = yf.Ticker(ticker)
        calendar = stock.calendar
        if calendar is not None and 'Earnings Date' in calendar:
            earnings_dates = calendar['Earnings Date']
            if isinstance(earnings_dates, list) and len(earnings_dates) > 0:
                next_earnings = pd.to_datetime(earnings_dates[0])
                return next_earnings
    except:
        pass
    return None

# ============================================================================
# TECHNICAL ANALYSIS FUNCTIONS
# ============================================================================

def get_last_valid_value(series: pd.Series, default=None):
    """
    Get last valid (non-NaN) value from series.
    """
    valid_values = series.dropna()
    return valid_values.iloc[-1] if len(valid_values) > 0 else default

def calculate_technicals(df: pd.DataFrame) -> Dict:
    """
    Calculate technical indicators: RSI, Bollinger Bands, EMAs, MACD, ATR.
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        Dictionary with technical indicator values
    """
    if df is None or df.empty:
        return None
    
    try:
        # Calculate RSI
        rsi_series = ta.rsi(df['Close'], length=RSI_PERIOD)
        df['RSI'] = rsi_series
        
        # Calculate Bollinger Bands - use returned dataframe directly
        bbands = ta.bbands(df['Close'], length=BB_PERIOD, std=BB_STD)
        
        if bbands is None or bbands.empty:
            logger.error("Bollinger Bands calculation failed")
            return None
        
        # Extract BB columns from the returned dataframe
        bb_cols = [col for col in bbands.columns if 'BB' in col]
        bb_lower_col = [col for col in bb_cols if 'BBL_' in col][0] if any('BBL_' in col for col in bb_cols) else None
        bb_upper_col = [col for col in bb_cols if 'BBU_' in col][0] if any('BBU_' in col for col in bb_cols) else None
        bb_mid_col = [col for col in bb_cols if 'BBM_' in col][0] if any('BBM_' in col for col in bb_cols) else None
        
        if not all([bb_lower_col, bb_upper_col, bb_mid_col]):
            logger.error(f"BB columns not found. Available: {bbands.columns.tolist()}")
            return None
        
        df = pd.concat([df, bbands], axis=1)
        
        # Calculate EMAs for trend
        df['EMA_Fast'] = ta.ema(df['Close'], length=EMA_FAST)
        df['EMA_Slow'] = ta.ema(df['Close'], length=EMA_SLOW)
        
        # Calculate MACD
        macd_result = ta.macd(df['Close'], fast=MACD_FAST, slow=MACD_SLOW, signal=MACD_SIGNAL)
        if macd_result is not None:
            df = pd.concat([df, macd_result], axis=1)
        
        # Calculate ATR for volatility
        atr_series = ta.atr(df['High'], df['Low'], df['Close'], length=ATR_PERIOD)
        df['ATR'] = atr_series
        
        # Get latest values with NaN handling
        latest = df.iloc[-1]
        
        price = get_last_valid_value(df['Close'])
        rsi = get_last_valid_value(df['RSI'])
        bb_lower = get_last_valid_value(df[bb_lower_col])
        bb_upper = get_last_valid_value(df[bb_upper_col])
        bb_mid = get_last_valid_value(df[bb_mid_col])
        ema_fast = get_last_valid_value(df['EMA_Fast'])
        ema_slow = get_last_valid_value(df['EMA_Slow'])
        atr = get_last_valid_value(df['ATR'])
        
        if any(v is None for v in [price, rsi, bb_lower, bb_upper, bb_mid]):
            logger.error("Required indicators returned NaN")
            return None
        
        # Calculate RSI delta (momentum)
        rsi_values = df['RSI'].dropna().tail(4)
        rsi_delta = rsi_values.iloc[-1] - rsi_values.iloc[0] if len(rsi_values) >= 4 else 0
        
        # Determine BB status
        if price < bb_lower:
            bb_status = "BELOW_LOWER"
        elif price > bb_upper:
            bb_status = "ABOVE_UPPER"
        elif price < bb_mid:
            bb_status = "LOWER_HALF"
        else:
            bb_status = "UPPER_HALF"
        
        # Price vs BB mid percentage
        bb_mid_pct = ((price - bb_mid) / bb_mid * 100) if bb_mid else 0
        
        # Trend determination
        if ema_fast and ema_slow:
            if ema_fast > ema_slow * 1.005:  # 0.5% buffer
                trend = "UPTREND"
            elif ema_fast < ema_slow * 0.995:
                trend = "DOWNTREND"
            else:
                trend = "SIDEWAYS"
        else:
            trend = "UNKNOWN"
        
        # Volatility assessment
        atr_pct = (atr / price * 100) if atr and price else 0
        if atr_pct < VOLATILITY_LOW:
            volatility = "LOW"
        elif atr_pct > VOLATILITY_HIGH:
            volatility = "HIGH"
        else:
            volatility = "MEDIUM"
        
        # Suggested stop distance
        suggested_stop = atr * ATR_STOP_MULTIPLIER if atr else None
        
        # MACD values
        macd_line = get_last_valid_value(df['MACD_12_26_9']) if 'MACD_12_26_9' in df.columns else None
        macd_signal = get_last_valid_value(df['MACDs_12_26_9']) if 'MACDs_12_26_9' in df.columns else None
        macd_hist = get_last_valid_value(df['MACDh_12_26_9']) if 'MACDh_12_26_9' in df.columns else None
        
        return {
            'price': round(price, 2),
            'rsi': round(rsi, 2),
            'rsi_delta': round(rsi_delta, 2),
            'bb_lower': round(bb_lower, 2),
            'bb_upper': round(bb_upper, 2),
            'bb_mid': round(bb_mid, 2),
            'bb_mid_pct': round(bb_mid_pct, 2),
            'bb_status': bb_status,
            'ema_fast': round(ema_fast, 2) if ema_fast else None,
            'ema_slow': round(ema_slow, 2) if ema_slow else None,
            'trend': trend,
            'atr': round(atr, 2) if atr else None,
            'atr_pct': round(atr_pct, 2),
            'volatility': volatility,
            'suggested_stop': round(suggested_stop, 2) if suggested_stop else None,
            'macd_line': round(macd_line, 2) if macd_line else None,
            'macd_signal': round(macd_signal, 2) if macd_signal else None,
            'macd_hist': round(macd_hist, 4) if macd_hist else None
        }
        
    except Exception as e:
        logger.error(f"Error calculating technicals: {str(e)}")
        return None

# ============================================================================
# NEWS FETCHING FUNCTIONS
# ============================================================================

def fetch_yahoo_rss_news(ticker: str) -> List[Tuple[str, datetime]]:
    """
    Fetch news from Yahoo Finance RSS feed (FREE - no API key needed).
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        List of tuples (headline, datetime)
    """
    try:
        import xml.etree.ElementTree as ET
        
        # Yahoo Finance RSS feed URL
        url = f"https://finance.yahoo.com/rss/headline?s={ticker}"
        
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            articles = []
            cutoff_time = datetime.now() - timedelta(hours=NEWS_LOOKBACK_HOURS)
            
            # Parse RSS feed with dates
            for item in root.findall('.//item'):
                title = item.find('title')
                pub_date = item.find('pubDate')
                
                if title is not None and title.text:
                    article_date = None
                    if pub_date is not None and pub_date.text:
                        try:
                            # Parse date and remove timezone info for comparison
                            article_date = date_parser.parse(pub_date.text).replace(tzinfo=None)
                        except:
                            article_date = datetime.now()
                    else:
                        article_date = datetime.now()
                    
                    # Only include articles from the last N hours
                    if article_date >= cutoff_time:
                        articles.append((title.text, article_date))
            
            return articles[:10]  # Return top 10 recent articles
        else:
            return []
            
    except Exception as e:
        print(f"⚠️  Yahoo RSS error for {ticker}: {str(e)}")
        return []

def fetch_finviz_news(ticker: str) -> List[Tuple[str, datetime]]:
    """
    Fetch news from Finviz (FREE - no API key needed).
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        List of tuples (headline, datetime)
    """
    try:
        from bs4 import BeautifulSoup
        
        url = f"https://finviz.com/quote.ashx?t={ticker}"
        
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            news_table = soup.find('table', {'class': 'fullview-news-outer'})
            
            articles = []
            cutoff_time = datetime.now() - timedelta(hours=NEWS_LOOKBACK_HOURS)
            
            if news_table:
                for row in news_table.find_all('tr'):
                    link = row.find('a')
                    date_cell = row.find('td')
                    
                    if link and link.text:
                        # Try to parse Finviz date format
                        article_date = datetime.now()  # Default to now
                        if date_cell and date_cell.text:
                            try:
                                date_text = date_cell.text.strip()
                                # Finviz uses format like "Jan-04-26" or "04:20PM"
                                if 'PM' in date_text or 'AM' in date_text:
                                    # Today's article
                                    article_date = datetime.now()
                                else:
                                    article_date = date_parser.parse(date_text)
                            except:
                                pass
                        
                        # Only include recent articles
                        if article_date >= cutoff_time:
                            articles.append((link.text.strip(), article_date))
            
            return articles[:10]  # Return top 10
        else:
            return []
            
    except Exception as e:
        print(f"⚠️  Finviz error for {ticker}: {str(e)}")
        return []

def fetch_google_news_rss(ticker: str) -> List[Tuple[str, datetime]]:
    """
    Fetch news from Google News RSS (FREE - no API key needed).
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        List of tuples (headline, datetime)
    """
    try:
        import xml.etree.ElementTree as ET
        
        # Get company name mapping for better results
        company_names = {
            'NVDA': 'NVIDIA',
            'META': 'Meta',
            'MSFT': 'Microsoft',
            'NFLX': 'Netflix',
            'AAPL': 'Apple',
            'PUBM': 'PubMatic',
            'AMZN': 'Amazon'
        }
        
        query = company_names.get(ticker, ticker)
        url = f"https://news.google.com/rss/search?q={query}+stock&hl=en-US&gl=US&ceid=US:en"
        
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            articles = []
            cutoff_time = datetime.now() - timedelta(hours=NEWS_LOOKBACK_HOURS)
            
            # Parse RSS feed with dates
            for item in root.findall('./channel/item'):
                title = item.find('title')
                pub_date = item.find('pubDate')
                
                if title is not None and title.text:
                    article_date = None
                    if pub_date is not None and pub_date.text:
                        try:
                            # Parse date and remove timezone info for comparison
                            article_date = date_parser.parse(pub_date.text).replace(tzinfo=None)
                        except:
                            article_date = datetime.now()
                    else:
                        article_date = datetime.now()
                    
                    # Only include articles from the last N hours
                    if article_date >= cutoff_time:
                        articles.append((title.text, article_date))
            
            return articles[:10]  # Return top 10
        else:
            return []
            
    except Exception as e:
        print(f"⚠️  Google News error for {ticker}: {str(e)}")
        return []

def fetch_news_headlines(ticker: str, hours: int = 24) -> Tuple[List[Tuple[str, datetime]], str, datetime, datetime]:
    """
    Fetch recent news headlines for a ticker using multiple sources.
    Will try sources in order until successful.
    
    Args:
        ticker: Stock ticker symbol
        hours: Hours to look back
        
    Returns:
        Tuple of (List of (headline, datetime) tuples, source name used, oldest date, newest date)
    """
    articles = []
    source_used = "none"
    
    # Try each news source in order
    for source in NEWS_SOURCES:
        try:
            if source == 'yahoo_rss':
                articles = fetch_yahoo_rss_news(ticker)
            elif source == 'finviz':
                articles = fetch_finviz_news(ticker)
            elif source == 'google_news':
                articles = fetch_google_news_rss(ticker)
            elif source == 'newsapi':
                articles = fetch_newsapi_headlines(ticker, hours)
            
            # If we got articles, return them with source name and date range
            if articles:
                source_used = source
                dates = [date for _, date in articles]
                oldest = min(dates) if dates else datetime.now()
                newest = max(dates) if dates else datetime.now()
                # Ensure timezone-naive for calculation
                oldest_naive = oldest.replace(tzinfo=None) if oldest.tzinfo else oldest
                hours_old = (datetime.now() - oldest_naive).total_seconds() / 3600
                print(f"   📰 Found {len(articles)} articles from {source} (last {hours_old:.1f}h)")
                return articles, source_used, oldest, newest
                
        except Exception as e:
            print(f"⚠️  Error with {source} for {ticker}: {str(e)}")
            continue
    
    # If all sources failed, return empty list
    return [], source_used, datetime.now(), datetime.now()

def fetch_newsapi_headlines(ticker: str, hours: int = 24) -> List[Tuple[str, datetime]]:
    """
    Fetch news from NewsAPI (requires API key).
    
    Args:
        ticker: Stock ticker symbol
        hours: Hours to look back
        
    Returns:
        List of tuples (headline, datetime)
    """
    if NEWS_API_KEY == "YOUR_NEWS_API_KEY_HERE":
        return []
    
    try:
        from_date = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d')
        
        # Get company name mapping
        company_names = {
            'NVDA': 'NVIDIA',
            'META': 'Meta OR Facebook',
            'MSFT': 'Microsoft',
            'NFLX': 'Netflix',
            'AAPL': 'Apple',
            'PUBM': 'PubMatic',
            'AMZN': 'Amazon'
        }
        
        query = company_names.get(ticker, ticker)
        
        url = 'https://newsapi.org/v2/everything'
        params = {
            'q': query,
            'from': from_date,
            'sortBy': 'publishedAt',
            'language': 'en',
            'apiKey': NEWS_API_KEY,
            'pageSize': 10
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            articles_data = response.json().get('articles', [])
            articles = []
            for article in articles_data:
                if article.get('title'):
                    # Parse date and remove timezone info for consistency
                    pub_date = date_parser.parse(article['publishedAt']).replace(tzinfo=None) if article.get('publishedAt') else datetime.now()
                    articles.append((article['title'], pub_date))
            return articles[:10]  # Return top 10
        else:
            return []
            
    except Exception as e:
        print(f"⚠️  NewsAPI error for {ticker}: {str(e)}")
        return []

# ============================================================================
# AI SENTIMENT ANALYSIS FUNCTIONS
# ============================================================================

def analyze_sentiment_simple(headlines: List[Tuple[str, datetime]]) -> float:
    """
    Simple keyword-based sentiment analysis (fallback method).
    
    Args:
        headlines: List of (headline, datetime) tuples
        
    Returns:
        Sentiment score from -1 to 1
    """
    if not headlines:
        return 0.0
    
    # Extract just the headline text
    headline_texts = [headline for headline, _ in headlines]
    
    # Define keyword lists
    positive_keywords = [
        'surge', 'rally', 'beat', 'exceeds', 'growth', 'bullish', 'buy',
        'upgrade', 'outperform', 'strong', 'record', 'profit', 'earnings beat',
        'innovation', 'breakthrough', 'partnership', 'acquisition', 'gain'
    ]
    
    negative_keywords = [
        'plunge', 'crash', 'decline', 'miss', 'bearish', 'sell', 'downgrade',
        'underperform', 'weak', 'loss', 'lawsuit', 'investigation', 'fine',
        'concern', 'risk', 'warning', 'layoff', 'cut', 'disappointing'
    ]
    
    sentiment_sum = 0
    
    for headline in headline_texts:
        headline_lower = headline.lower()
        
        # Count positive keywords
        positive_count = sum(1 for word in positive_keywords if word in headline_lower)
        
        # Count negative keywords
        negative_count = sum(1 for word in negative_keywords if word in headline_lower)
        
        # Calculate headline sentiment
        if positive_count + negative_count > 0:
            headline_sentiment = (positive_count - negative_count) / (positive_count + negative_count)
            sentiment_sum += headline_sentiment
    
    # Average sentiment across all headlines
    if len(headline_texts) > 0:
        avg_sentiment = sentiment_sum / len(headline_texts)
        # Normalize to -1 to 1 range
        return max(-1.0, min(1.0, avg_sentiment))
    
    return 0.0

def analyze_sentiment_ai(headlines: List[Tuple[str, datetime]], ticker: str) -> float:
    """
    AI-powered sentiment analysis using Gemini or OpenAI (placeholder).
    
    Args:
        headlines: List of (headline, datetime) tuples
        ticker: Stock ticker symbol
        
    Returns:
        Sentiment score from -1 to 1
    """
    # This is a placeholder for AI integration
    # Uncomment and implement based on your chosen AI provider
    
    if not USE_AI_SENTIMENT or AI_API_KEY == "YOUR_AI_API_KEY_HERE":
        return analyze_sentiment_simple(headlines)
    
    # Example OpenAI integration (commented out):
    """
    import openai
    openai.api_key = AI_API_KEY
    
    headlines_text = "\n".join(headlines)
    prompt = f'''
    Analyze the following news headlines for {ticker} stock and provide a sentiment score 
    from -1 (extremely bearish) to 1 (extremely bullish). 
    Consider market impact, company performance, and investor sentiment.
    
    Headlines:
    {headlines_text}
    
    Return only a single number between -1 and 1.
    '''
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    
    try:
        score = float(response.choices[0].message.content.strip())
        return max(-1.0, min(1.0, score))
    except:
        return analyze_sentiment_simple(headlines)
    """
    
    # Example Gemini integration (commented out):
    """
    import google.generativeai as genai
    genai.configure(api_key=AI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    
    headlines_text = "\n".join(headlines)
    prompt = f'''
    Analyze sentiment for {ticker}: Rate from -1 (bearish) to 1 (bullish).
    Headlines: {headlines_text}
    Return only a number.
    '''
    
    response = model.generate_content(prompt)
    try:
        score = float(response.text.strip())
        return max(-1.0, min(1.0, score))
    except:
        return analyze_sentiment_simple(headlines)
    """
    
    return analyze_sentiment_simple(headlines)

# ============================================================================
# TRADING LOGIC FUNCTIONS
# ============================================================================

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
    
    rsi = technicals['rsi']
    bb_status = technicals['bb_status']
    
    # STRONG BUY conditions
    if (rsi < RSI_OVERSOLD and 
        bb_status == "BELOW_LOWER" and 
        sentiment > SENTIMENT_BULLISH):
        return "🟢 STRONG BUY", "green"
    
    # STRONG SELL conditions
    if (rsi > RSI_OVERBOUGHT and 
        bb_status == "ABOVE_UPPER" and 
        sentiment < SENTIMENT_BEARISH):
        return "🔴 STRONG SELL", "red"
    
    # AVOID - NEWS RISK (Technical buy signal but negative sentiment)
    if (rsi < 30 and 
        bb_status in ["BELOW_LOWER", "LOWER_HALF"] and 
        sentiment < SENTIMENT_BEARISH):
        return "⚠️  AVOID - NEWS RISK", "yellow"
    
    # BUY - Technical oversold with neutral/positive sentiment
    if rsi < 30 and sentiment >= 0:
        return "🟢 BUY", "green"
    
    # SELL - Technical overbought with neutral/negative sentiment
    if rsi > 70 and sentiment <= 0:
        return "🔴 SELL", "red"
    
    # CAUTION - Mixed signals
    if abs(rsi - 50) < 10 and abs(sentiment) > 0.5:
        if sentiment > 0:
            return "🟡 CAUTION - BULLISH SENTIMENT", "yellow"
        else:
            return "🟡 CAUTION - BEARISH SENTIMENT", "yellow"
    
    # HOLD - No strong signals
    return "⚪ HOLD", "white"

# ============================================================================
# MAIN ANALYSIS FUNCTION
# ============================================================================

def analyze_ticker(ticker: str) -> Dict:
    """
    Perform complete analysis for a single ticker.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary with analysis results
    """
    print(f"📊 Analyzing {ticker}...")
    
    # Fetch market data
    df = fetch_market_data(ticker)
    
    # Calculate technicals
    technicals = calculate_technicals(df)
    
    # Fetch news
    articles, news_source, oldest_date, newest_date = fetch_news_headlines(ticker, hours=NEWS_LOOKBACK_HOURS)
    
    # Show sample headlines with dates
    if articles:
        print(f"   📋 Sample headlines (most recent):")
        for i, (headline, pub_date) in enumerate(articles[:3], 1):
            # Ensure timezone-naive for calculation
            pub_date_naive = pub_date.replace(tzinfo=None) if pub_date.tzinfo else pub_date
            hours_ago = (datetime.now() - pub_date_naive).total_seconds() / 3600
            time_str = f"{int(hours_ago)}h ago" if hours_ago < 24 else f"{int(hours_ago/24)}d ago"
            print(f"      {i}. [{time_str}] {headline[:70]}{'...' if len(headline) > 70 else ''}")
    
    # Analyze sentiment
    sentiment = analyze_sentiment_ai(articles, ticker) if USE_AI_SENTIMENT else analyze_sentiment_simple(articles)
    
    # Generate recommendation
    recommendation, color = generate_recommendation(technicals, sentiment, ticker)
    
    return {
        'ticker': ticker,
        'price': technicals['price'] if technicals else 'N/A',
        'rsi': technicals['rsi'] if technicals else 'N/A',
        'bb_status': technicals['bb_status'] if technicals else 'N/A',
        'sentiment': round(sentiment, 2),
        'sentiment_label': get_sentiment_label(sentiment),
        'news_count': len(articles),
        'news_source': news_source,
        'news_age_hours': (datetime.now() - (oldest_date.replace(tzinfo=None) if oldest_date.tzinfo else oldest_date)).total_seconds() / 3600 if articles else 0,
        'recommendation': recommendation,
        'color': color
    }

def get_sentiment_label(sentiment: float) -> str:
    """Convert sentiment score to label."""
    if sentiment > 0.7:
        return "Very Bullish"
    elif sentiment > 0.3:
        return "Bullish"
    elif sentiment > -0.3:
        return "Neutral"
    elif sentiment > -0.7:
        return "Bearish"
    else:
        return "Very Bearish"

# ============================================================================
# OUTPUT FUNCTIONS
# ============================================================================

def create_output_table(results: List[Dict]) -> PrettyTable:
    """
    Create a formatted table of analysis results.
    
    Args:
        results: List of analysis result dictionaries
        
    Returns:
        PrettyTable object
    """
    table = PrettyTable()
    table.field_names = [
        "Ticker",
        "Price",
        "RSI",
        "BB Status",
        "Sentiment",
        "Articles",
        "Source",
        "Recommendation"
    ]
    
    # Set alignment
    table.align["Ticker"] = "l"
    table.align["Price"] = "r"
    table.align["RSI"] = "r"
    table.align["BB Status"] = "l"
    table.align["Sentiment"] = "l"
    table.align["Articles"] = "r"
    table.align["Source"] = "l"
    table.align["Recommendation"] = "l"
    
    # Add rows
    for result in results:
        table.add_row([
            result['ticker'],
            f"${result['price']}" if result['price'] != 'N/A' else 'N/A',
            result['rsi'] if result['rsi'] != 'N/A' else 'N/A',
            result['bb_status'].replace('_', ' ') if result['bb_status'] != 'N/A' else 'N/A',
            f"{result['sentiment_label']} ({result['sentiment']})",
            result['news_count'],
            result['news_source'],
            result['recommendation']
        ])
    
    return table

def print_summary(results: List[Dict]):
    """Print summary statistics."""
    buy_signals = sum(1 for r in results if 'BUY' in r['recommendation'])
    sell_signals = sum(1 for r in results if 'SELL' in r['recommendation'])
    hold_signals = sum(1 for r in results if 'HOLD' in r['recommendation'])
    avoid_signals = sum(1 for r in results if 'AVOID' in r['recommendation'])
    total_articles = sum(r['news_count'] for r in results)
    
    # Count sources used
    source_counts = {}
    for r in results:
        source = r.get('news_source', 'unknown')
        source_counts[source] = source_counts.get(source, 0) + 1
    
    print("\n" + "="*80)
    print("📈 ANALYSIS SUMMARY")
    print("="*80)
    print(f"Total Tickers Analyzed: {len(results)}")
    print(f"Buy Signals: {buy_signals}")
    print(f"Sell Signals: {sell_signals}")
    print(f"Hold Signals: {hold_signals}")
    print(f"Avoid Signals: {avoid_signals}")
    print("-" * 80)
    print(f"📰 Total News Articles Consulted: {total_articles}")
    print(f"   Articles per ticker (average): {total_articles / len(results):.1f}")    
    # Show average news age
    avg_age = sum(r['news_age_hours'] for r in results if r['news_age_hours'] > 0) / len([r for r in results if r['news_age_hours'] > 0]) if any(r['news_age_hours'] > 0 for r in results) else 0
    if avg_age < 24:
        print(f"   Average article age: {avg_age:.1f} hours (FRESH - Good for prediction!)")
    else:
        print(f"   Average article age: {avg_age/24:.1f} days")
    
    print(f"   News lookback window: {NEWS_LOOKBACK_HOURS} hours")
    print(f"   News sources used:")
    for source, count in source_counts.items():
        print(f"      • {source}: {count} ticker(s)")
    print("="*80 + "\n")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function."""
    print("\n" + "="*80)
    print("🚀 PRE-MARKET STOCK ANALYSIS")
    print("="*80)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Analyzing: {', '.join(TICKERS)}")
    print("="*80 + "\n")
    
    # Analyze all tickers
    results = []
    for ticker in TICKERS:
        try:
            result = analyze_ticker(ticker)
            results.append(result)
        except Exception as e:
            print(f"❌ Error analyzing {ticker}: {str(e)}")
            results.append({
                'ticker': ticker,
                'price': 'N/A',
                'rsi': 'N/A',
                'bb_status': 'N/A',
                'sentiment': 0.0,
                'sentiment_label': 'N/A',
                'news_count': 0,
                'news_source': 'error',
                'news_age_hours': 0,
                'recommendation': 'ERROR',
                'color': 'white'
            })
    
    # Display results
    print("\n" + "="*80)
    print("📊 ANALYSIS RESULTS")
    print("="*80)
    table = create_output_table(results)
    print(table)
    
    # Print summary
    print_summary(results)
    
    # Print configuration info
    print("ℹ️  NEWS SOURCES: " + " → ".join(NEWS_SOURCES))
    if 'yahoo_rss' in NEWS_SOURCES or 'finviz' in NEWS_SOURCES or 'google_news' in NEWS_SOURCES:
        print("   Using FREE news sources (no API key required) ✅\n")
    
    if not USE_AI_SENTIMENT:
        print("ℹ️  SENTIMENT: Using keyword-based analysis")
        print("   For AI-powered sentiment, set USE_AI_SENTIMENT=True\n")
    
    print("✅ Analysis complete!\n")

if __name__ == "__main__":
    main()
