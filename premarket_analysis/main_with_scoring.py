"""
Enhanced main analysis with scoring system integration.
This is a new entry point that adds scoring on top of existing analysis.
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
from .output import print_info, print_header
from .scoring import calculate_trade_score, get_score_interpretation

logger = logging.getLogger(__name__)


def analyze_ticker_with_scoring(ticker: str) -> Dict:
    """
    Perform complete analysis with enhanced scoring for a single ticker.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary with analysis results including score
    """
    print(f"📊 Analyzing {ticker}...")
    
    # Fetch market data
    df = fetch_market_data(ticker)
    
    # Calculate technicals
    technicals = calculate_technicals(df)
    
    # Fetch news
    articles, news_source, oldest_date, newest_date = fetch_news_headlines(ticker, hours=NEWS_LOOKBACK_HOURS)
    
    # Show sample headlines
    if articles:
        print(f"   📋 Sample headlines (most recent):")
        now_et = get_et_time_naive()
        
        for i, (headline, pub_date) in enumerate(articles[:3], 1):
            try:
                pub_date_naive = pub_date.replace(tzinfo=None) if hasattr(pub_date, 'tzinfo') and pub_date.tzinfo else pub_date
                hours_ago = (now_et - pub_date_naive).total_seconds() / 3600
                hours_ago = abs(hours_ago)
                time_str = f"{int(hours_ago)}h ago" if hours_ago < 24 else f"{int(hours_ago/24)}d ago"
            except:
                time_str = "?"
            
            print(f"      {i}. [{time_str}] {headline[:70]}{'...' if len(headline) > 70 else ''}")
    
    # Analyze sentiment
    sentiment = analyze_sentiment_ai(articles, ticker) if USE_AI_SENTIMENT else analyze_sentiment_simple(articles)
    
    # Generate traditional recommendation
    recommendation, color = generate_recommendation(technicals, sentiment, ticker)
    
    # Check for upcoming earnings
    earnings_flag = ""
    earnings_date = get_earnings_date(ticker)
    if earnings_date:
        now_et = get_et_time_naive()
        days_until_earnings = (earnings_date - now_et).days
        if 0 <= days_until_earnings <= EARNINGS_RISK_DAYS:
            earnings_flag = "E"
            logger.info(f"   ⚠️  {ticker} has earnings in {days_until_earnings} days ({earnings_date.strftime('%Y-%m-%d')})")
    
    # Calculate news age
    news_age_hours = 0
    if articles and oldest_date:
        try:
            oldest_naive = oldest_date.replace(tzinfo=None) if hasattr(oldest_date, 'tzinfo') and oldest_date.tzinfo else oldest_date
            news_age_hours = (get_et_time_naive() - oldest_naive).total_seconds() / 3600
        except:
            pass
    
    # *** NEW: Calculate comprehensive trade score ***
    score_result = calculate_trade_score(
        technicals=technicals,
        sentiment=sentiment,
        news_count=len(articles),
        news_age_hours=news_age_hours,
        earnings_flag=earnings_flag
    )
    
    # Print score summary
    print(f"   {score_result['emoji']} SCORE: {score_result['final_score']}/100 ({score_result['category']})")
    
    # Show component breakdown if logger is at DEBUG level
    if logger.isEnabledFor(logging.DEBUG):
        print(f"   └─ Components: Tech={score_result['components']['technical']['score']:.0f}, "
              f"Sent={score_result['components']['sentiment']['score']:.0f}, "
              f"Mom={score_result['components']['momentum']['score']:.0f}, "
              f"Cat={score_result['components']['catalyst']['score']:.0f}, "
              f"Time={score_result['components']['timing']['score']:.0f}")
        if score_result['adjustments']:
            print(f"   └─ Adjustments: {', '.join(score_result['adjustments'])}")
    
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
        'trend': technicals.get('trend', 'N/A') if technicals else 'N/A',
        'volatility': technicals.get('volatility', 'N/A') if technicals else 'N/A',
        'suggested_stop': technicals.get('suggested_stop', 'N/A') if technicals else 'N/A',
        'bb_mid_pct': technicals.get('bb_mid_pct', 'N/A') if technicals else 'N/A',
        # New scoring fields
        'score': score_result['final_score'],
        'score_category': score_result['category'],
        'score_emoji': score_result['emoji'],
        'score_components': score_result['components'],
        'score_adjustments': score_result['adjustments'],
        'score_quality_flags': score_result['quality_flags']
    }


def create_scored_output_table(results: list) -> str:
    """
    Create formatted table with scores.
    
    Args:
        results: List of analysis result dictionaries
        
    Returns:
        Formatted table string
    """
    from tabulate import tabulate
    
    # Sort by score (highest first)
    sorted_results = sorted(results, key=lambda x: x.get('score', 0), reverse=True)
    
    table_data = []
    for r in sorted_results:
        row = [
            r['ticker'],
            f"{r['score']:.0f}" if isinstance(r.get('score'), (int, float)) else "N/A",
            r.get('score_category', 'N/A'),
            f"${r['price']:.2f}" if isinstance(r['price'], (int, float)) else r['price'],
            f"{r['rsi']:.0f}" if isinstance(r['rsi'], (int, float)) else r['rsi'],
            r['bb_status'][:12] if isinstance(r['bb_status'], str) else 'N/A',
            f"{r['sentiment']:+.2f}" if isinstance(r['sentiment'], (int, float)) else r['sentiment'],
            r['news_count'],
            r['recommendation'][:25] if isinstance(r['recommendation'], str) else 'N/A'
        ]
        table_data.append(row)
    
    headers = ['Ticker', 'Score', 'Category', 'Price', 'RSI', 'BB Status', 'Sent', 'News', 'Recommendation']
    
    return tabulate(table_data, headers=headers, tablefmt='grid')


def print_scored_summary(results: list):
    """
    Print summary with score statistics.
    
    Args:
        results: List of analysis result dictionaries
    """
    print("\n" + "="*80)
    print("📈 TRADE QUALITY SUMMARY")
    print("="*80)
    
    # Count by category
    categories = {}
    for r in results:
        cat = r.get('score_category', 'UNKNOWN')
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"\n🎯 Score Distribution:")
    for cat in ['STRONG_BUY', 'BUY', 'CAUTION', 'AVOID', 'STRONG_AVOID']:
        count = categories.get(cat, 0)
        if count > 0:
            print(f"   {cat}: {count}")
    
    # Top picks
    top_scored = sorted(results, key=lambda x: x.get('score', 0), reverse=True)[:3]
    valid_top = [r for r in top_scored if isinstance(r.get('score'), (int, float)) and r['score'] > 50]
    
    if valid_top:
        print(f"\n⭐ Top Scored Setups:")
        for i, r in enumerate(valid_top, 1):
            interpretation = get_score_interpretation(r['score'])
            print(f"   {i}. {r['ticker']} - {r['score']:.0f}/100 ({r['score_category']})")
            print(f"      {interpretation}")
            if r.get('score_adjustments'):
                print(f"      Factors: {', '.join(r['score_adjustments'][:3])}")
    else:
        print(f"\n⚠️  No high-quality setups found (all scores < 50)")
    
    # Average scores
    valid_scores = [r['score'] for r in results if isinstance(r.get('score'), (int, float))]
    if valid_scores:
        avg_score = sum(valid_scores) / len(valid_scores)
        print(f"\n📊 Average Score: {avg_score:.1f}/100")


def main():
    """Main entry point for analysis with scoring."""
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format='%(message)s'
    )
    
    print_header()
    print("🎯 ENHANCED WITH SCORING SYSTEM")
    print("="*80)
    
    # Analyze all tickers
    results = []
    for ticker in TICKERS:
        try:
            result = analyze_ticker_with_scoring(ticker)
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
                'bb_mid_pct': 'N/A',
                'score': 0,
                'score_category': 'ERROR',
                'score_emoji': '❌',
                'score_components': {},
                'score_adjustments': [],
                'score_quality_flags': ['ERROR']
            })
    
    # Display results
    print("\n" + "="*80)
    print("📊 SCORED ANALYSIS RESULTS")
    print("="*80)
    table = create_scored_output_table(results)
    print(table)
    
    # Print summary
    print_scored_summary(results)
    
    # Print info
    print_info()
    
    print("\n✅ Scored analysis complete!\n")


if __name__ == "__main__":
    main()
