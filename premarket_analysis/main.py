"""
Main analysis orchestration
"""

from datetime import datetime
from typing import Dict
import logging
import traceback

from .config import *
from .market_data import fetch_market_data, get_earnings_date, get_et_time_naive
from .technical_indicators import calculate_technicals
from .news_fetching import fetch_news_headlines
from .sentiment_analysis import analyze_sentiment_simple, analyze_sentiment_ai, get_sentiment_label
from .recommendation import generate_recommendation
from .output import create_output_table, print_summary, print_info, print_header

logger = logging.getLogger(__name__)


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
    
    # Show sample headlines with dates (using ET time consistently)
    if articles:
        print(f"   📋 Sample headlines (most recent):")
        now_et = get_et_time_naive()
        
        for i, (headline, pub_date) in enumerate(articles[:3], 1):
            # Calculate hours ago (all in ET naive)
            try:
                pub_date_naive = pub_date.replace(tzinfo=None) if hasattr(pub_date, 'tzinfo') and pub_date.tzinfo else pub_date
                hours_ago = (now_et - pub_date_naive).total_seconds() / 3600
                # Use absolute value to handle timezone edge cases
                hours_ago = abs(hours_ago)
                time_str = f"{int(hours_ago)}h ago" if hours_ago < 24 else f"{int(hours_ago/24)}d ago"
            except:
                time_str = "?"
            
            print(f"      {i}. [{time_str}] {headline[:70]}{'...' if len(headline) > 70 else ''}")
    
    # Analyze sentiment
    sentiment = analyze_sentiment_ai(articles, ticker) if USE_AI_SENTIMENT else analyze_sentiment_simple(articles)
    
    # Generate recommendation
    recommendation, color = generate_recommendation(technicals, sentiment, ticker)
    
    # Check for upcoming earnings
    earnings_flag = ""
    earnings_date = get_earnings_date(ticker)
    if earnings_date:
        now_et = get_et_time_naive()
        # Both are now timezone-naive
        days_until_earnings = (earnings_date - now_et).days
        if 0 <= days_until_earnings <= EARNINGS_RISK_DAYS:
            earnings_flag = "E"
            recommendation = f"{recommendation} ⚠️  EARNINGS IN {days_until_earnings}d"
            logger.info(f"   ⚠️  {ticker} has earnings in {days_until_earnings} days ({earnings_date.strftime('%Y-%m-%d')})")
    
    # Calculate news age (using ET time consistently)
    news_age_hours = 0
    if articles and oldest_date:
        try:
            oldest_naive = oldest_date.replace(tzinfo=None) if hasattr(oldest_date, 'tzinfo') and oldest_date.tzinfo else oldest_date
            news_age_hours = (get_et_time_naive() - oldest_naive).total_seconds() / 3600
        except:
            pass
    
    return {
        'ticker': ticker,
        'price': technicals['price'] if technicals else 'N/A',
        'rsi': technicals['rsi'] if technicals else 'N/A',
        'bb_status': technicals['bb_status'] if technicals else 'N/A',
        'sentiment': round(sentiment, 2),
        'sentiment_label': get_sentiment_label(sentiment),
        'news_count': len(articles),
        'news_source': news_source,
        'news_age_hours': news_age_hours,
        'recommendation': recommendation,
        'color': color,
        'earnings_flag': earnings_flag,
        # Additional risk/trend metrics
        'trend': technicals.get('trend', 'N/A') if technicals else 'N/A',
        'volatility': technicals.get('volatility', 'N/A') if technicals else 'N/A',
        'suggested_stop': technicals.get('suggested_stop', 'N/A') if technicals else 'N/A',
        'bb_mid_pct': technicals.get('bb_mid_pct', 'N/A') if technicals else 'N/A'
    }


def main():
    """Main entry point for analysis."""
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format='%(message)s'
    )
    
    print_header()
    
    # Analyze all tickers
    results = []
    for ticker in TICKERS:
        try:
            result = analyze_ticker(ticker)
            results.append(result)
        except Exception as e:
            print(f"❌ Error analyzing {ticker}: {str(e)}")
            logger.error(f"Full traceback for {ticker}:\n{traceback.format_exc()}")
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
                'color': 'white',
                'earnings_flag': '',
                'trend': 'N/A',
                'volatility': 'N/A',
                'suggested_stop': 'N/A',
                'bb_mid_pct': 'N/A'
            })
    
    # Display results
    print("\n" + "="*80)
    print("📊 ANALYSIS RESULTS")
    print("="*80)
    table = create_output_table(results)
    print(table)
    
    # Print summary
    print_summary(results)
    
    # Print info
    print_info()
    
    print("\n✅ Analysis complete!\n")


if __name__ == "__main__":
    main()
