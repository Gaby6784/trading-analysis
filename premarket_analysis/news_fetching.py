"""
News fetching from multiple sources with caching
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from dateutil import parser as date_parser
import json
import os
import hashlib
import logging
from .config import *
from .market_data import get_et_time_naive

logger = logging.getLogger(__name__)

# Cache directory setup
CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', '.news_cache')
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)


def cleanup_old_cache():
    """Remove cache files older than CACHE_CLEANUP_HOURS."""
    try:
        now = datetime.now()
        cutoff = now - timedelta(hours=CACHE_CLEANUP_HOURS)
        
        if not os.path.exists(CACHE_DIR):
            return
        
        removed = 0
        for filename in os.listdir(CACHE_DIR):
            filepath = os.path.join(CACHE_DIR, filename)
            if os.path.isfile(filepath):
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                if file_time < cutoff:
                    os.remove(filepath)
                    removed += 1
        
        if removed > 0:
            logger.debug(f"   Cleaned up {removed} old cache files")
    except Exception as e:
        logger.warning(f"   Cache cleanup error: {e}")


def get_cache_key(ticker: str) -> str:
    """Generate cache key for news articles."""
    current_hour = get_et_time_naive().strftime("%Y%m%d%H")
    cache_str = f"{ticker}_{current_hour}"
    return hashlib.md5(cache_str.encode()).hexdigest()


def get_cached_news(ticker: str) -> Optional[List[Tuple[str, datetime]]]:
    """Retrieve cached news articles if available and not expired."""
    cache_key = get_cache_key(ticker)
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Check if cache is still valid
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            if (datetime.now() - cache_time).total_seconds() < CACHE_DURATION_MINUTES * 60:
                logger.info(f"   ✓ Using cached news for {ticker}")
                # Reconstruct datetime objects (ensure timezone-naive)
                articles = [(article['headline'], datetime.fromisoformat(article['date']).replace(tzinfo=None)) 
                           for article in cache_data['articles']]
                return articles
        except Exception as e:
            logger.warning(f"   Cache read error for {ticker}: {e}")
    
    return None


def cache_news(ticker: str, articles: List[Tuple[str, datetime]]) -> None:
    """Cache news articles to disk."""
    cache_key = get_cache_key(ticker)
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    
    try:
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'ticker': ticker,
            'articles': [
                {'headline': headline, 'date': date.isoformat()}
                for headline, date in articles
            ]
        }
        
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f)
        
        logger.debug(f"   ✓ Cached {len(articles)} articles for {ticker}")
    except Exception as e:
        logger.warning(f"   Cache write error for {ticker}: {e}")


def deduplicate_articles(articles: List[Tuple[str, datetime]]) -> List[Tuple[str, datetime]]:
    """Remove duplicate or near-duplicate articles based on headline similarity."""
    if not articles:
        return articles
    
    from difflib import SequenceMatcher
    
    def similarity(a: str, b: str) -> float:
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    
    unique_articles = []
    for headline, date in articles:
        is_duplicate = False
        for existing_headline, _ in unique_articles:
            if similarity(headline, existing_headline) > 0.85:
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique_articles.append((headline, date))
    
    removed_count = len(articles) - len(unique_articles)
    if removed_count > 0:
        logger.debug(f"   Removed {removed_count} duplicate articles")
    
    return unique_articles


def fetch_yahoo_rss_news(ticker: str) -> List[Tuple[str, datetime]]:
    """Fetch news from Yahoo Finance RSS feed (FREE - no API key needed)."""
    try:
        url = f"https://finance.yahoo.com/rss/headline?s={ticker}"
        
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            articles = []
            cutoff_time = get_et_time_naive() - timedelta(hours=NEWS_LOOKBACK_HOURS)
            
            for item in root.findall('.//item'):
                title = item.find('title')
                pub_date = item.find('pubDate')
                
                if title is not None and title.text:
                    # Parse date - skip if parsing fails (don't use fallback datetime.now())
                    if pub_date is not None and pub_date.text:
                        try:
                            article_date = date_parser.parse(pub_date.text).replace(tzinfo=None)
                            # Only include if within lookback window
                            if article_date >= cutoff_time:
                                articles.append((title.text, article_date))
                        except:
                            # Skip articles with unparseable dates
                            pass
            
            return articles[:10]
        else:
            return []
            
    except Exception as e:
        logger.debug(f"   Yahoo RSS error for {ticker}: {str(e)}")
        return []


def fetch_finviz_news(ticker: str) -> List[Tuple[str, datetime]]:
    """
    Fetch news from Finviz (FREE - no API key needed).
    Improved date parsing for mixed date/time format.
    """
    try:
        from bs4 import BeautifulSoup
        
        url = f"https://finviz.com/quote.ashx?t={ticker}"
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            news_table = soup.find('table', {'id': 'news-table'})
            
            if news_table:
                articles = []
                cutoff_time = get_et_time_naive() - timedelta(hours=NEWS_LOOKBACK_HOURS)
                current_date = None  # Track current date for time-only rows
                
                for row in news_table.find_all('tr'):
                    cells = row.find_all('td')
                    if len(cells) < 2:
                        continue
                    
                    date_cell = cells[0].text.strip()
                    headline_cell = cells[1].find('a')
                    
                    if headline_cell:
                        headline = headline_cell.text.strip()
                        
                        # Parse date/time
                        try:
                            # Check if date_cell contains a date (e.g., "Feb-09-26 08:12AM")
                            if any(char.isalpha() for char in date_cell[:7]):
                                # Full date + time
                                parsed = date_parser.parse(date_cell)
                                current_date = parsed.date()
                                article_date = parsed.replace(tzinfo=None)
                            else:
                                # Time only (e.g., "08:04AM") - use current_date
                                if current_date:
                                    time_obj = date_parser.parse(date_cell).time()
                                    article_date = datetime.combine(current_date, time_obj)
                                else:
                                    # No previous date to reference, skip
                                    continue
                            
                            # Only include if within lookback window
                            if article_date >= cutoff_time:
                                articles.append((headline, article_date))
                        except:
                            # Skip articles with unparseable dates
                            pass
                
                return articles[:10]
        
        return []
            
    except Exception as e:
        logger.debug(f"   Finviz error for {ticker}: {str(e)}")
        return []


def fetch_reuters_rss(ticker: str) -> List[Tuple[str, datetime]]:
    """Fetch news from Reuters RSS feed (FREE - no API key needed)."""
    try:
        # Try Reuters business news general feed
        url = "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best"
        
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            articles = []
            cutoff_time = get_et_time_naive() - timedelta(hours=NEWS_LOOKBACK_HOURS)
            
            # Filter for ticker-relevant articles
            company_names = {
                'NVDA': ['NVIDIA', 'Nvidia', 'nvda'],
                'META': ['Meta', 'Facebook', 'meta'],
                'MSFT': ['Microsoft', 'MSFT', 'msft'],
                'NFLX': ['Netflix', 'NFLX', 'nflx'],
                'AAPL': ['Apple', 'AAPL', 'aapl', 'iPhone', 'iPad'],
                'PUBM': ['PubMatic', 'PUBM', 'pubm'],
                'AMZN': ['Amazon', 'AMZN', 'amzn', 'AWS']
            }
            
            keywords = company_names.get(ticker, [ticker])
            
            for item in root.findall('.//item'):
                title = item.find('title')
                pub_date = item.find('pubDate')
                
                if title is not None and title.text:
                    # Check if any keyword matches
                    if any(keyword.lower() in title.text.lower() for keyword in keywords):
                        if pub_date is not None and pub_date.text:
                            try:
                                article_date = date_parser.parse(pub_date.text).replace(tzinfo=None)
                                if article_date >= cutoff_time:
                                    articles.append((title.text, article_date))
                            except:
                                pass
            
            return articles[:10] if articles else []
        else:
            return []
            
    except Exception as e:
        logger.debug(f"   Reuters RSS error for {ticker}: {str(e)}")
        return []


def fetch_google_news_rss(ticker: str) -> List[Tuple[str, datetime]]:
    """Fetch news from Google News RSS (FREE - no API key needed)."""
    try:
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
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            articles = []
            cutoff_time = get_et_time_naive() - timedelta(hours=NEWS_LOOKBACK_HOURS)
            
            for item in root.findall('.//item'):
                title = item.find('title')
                pub_date = item.find('pubDate')
                
                if title is not None and title.text:
                    if pub_date is not None and pub_date.text:
                        try:
                            article_date = date_parser.parse(pub_date.text).replace(tzinfo=None)
                            if article_date >= cutoff_time:
                                articles.append((title.text, article_date))
                        except:
                            pass
            
            return articles[:10]
        else:
            return []
            
    except Exception as e:
        logger.debug(f"   Google News error for {ticker}: {str(e)}")
        return []


def fetch_newsapi_headlines(ticker: str, hours: int = 24) -> List[Tuple[str, datetime]]:
    """Fetch news from NewsAPI (requires API key)."""
    if NEWS_API_KEY == "YOUR_NEWS_API_KEY_HERE":
        return []
    
    try:
        from_date = (get_et_time_naive() - timedelta(hours=hours)).strftime('%Y-%m-%d')
        
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
            data = response.json()
            articles = []
            articles_data = data.get('articles', [])
            
            for article in articles_data:
                if article.get('title'):
                    try:
                        pub_date = date_parser.parse(article['publishedAt']).replace(tzinfo=None)
                        articles.append((article['title'], pub_date))
                    except:
                        pass
            
            return articles[:10]
        else:
            return []
            
    except Exception as e:
        logger.debug(f"   NewsAPI error for {ticker}: {str(e)}")
        return []


def fetch_news_headlines(ticker: str, hours: int = 24) -> Tuple[List[Tuple[str, datetime]], str, datetime, datetime]:
    """
    Fetch recent news headlines for a ticker using multiple sources.
    
    Returns:
        Tuple of (List of (headline, datetime) tuples, source name used, oldest date, newest date)
    """
    # Clean up old cache first
    cleanup_old_cache()
    
    # Try cache first
    cached_articles = get_cached_news(ticker)
    if cached_articles:
        dates = [date for _, date in cached_articles]
        oldest = min(dates) if dates else get_et_time_naive()
        newest = max(dates) if dates else get_et_time_naive()
        return cached_articles, 'cache', oldest, newest
    
    articles = []
    source_used = "none"
    
    # Try each news source in order
    for source in NEWS_SOURCES:
        try:
            if source == 'yahoo_rss':
                articles = fetch_yahoo_rss_news(ticker)
            elif source == 'reuters':
                articles = fetch_reuters_rss(ticker)
            elif source == 'finviz':
                articles = fetch_finviz_news(ticker)
            elif source == 'google_news':
                articles = fetch_google_news_rss(ticker)
            elif source == 'newsapi':
                articles = fetch_newsapi_headlines(ticker, hours)
            
            if articles:
                # Deduplicate articles
                articles = deduplicate_articles(articles)
                
                source_used = source
                dates = [date for _, date in articles]
                oldest = min(dates) if dates else get_et_time_naive()
                newest = max(dates) if dates else get_et_time_naive()
                hours_old = (get_et_time_naive() - oldest).total_seconds() / 3600
                print(f"   📰 Found {len(articles)} unique articles from {source} (last {hours_old:.1f}h)")
                
                # Cache the articles
                cache_news(ticker, articles)
                
                return articles, source_used, oldest, newest
                
        except Exception as e:
            print(f"⚠️  Error with {source} for {ticker}: {str(e)}")
            continue
    
    # If all sources failed, return empty list
    return [], source_used, get_et_time_naive(), get_et_time_naive()
