"""
Enhanced Analysis with Advanced News Signal Extraction
Integrates market prediction from news articles
"""

from datetime import datetime
from typing import Dict
import logging

from .config import TICKERS
from .market_data import fetch_market_data, get_earnings_date, get_et_time_naive
from .technical_indicators import calculate_technicals
from .news_fetching import fetch_news_headlines
from .sentiment_analysis import analyze_sentiment_simple, analyze_sentiment_ai, get_sentiment_label
from .recommendation import generate_recommendation
from .scoring import calculate_trade_score, get_score_interpretation
from .news_signals import NewsSignalExtractor, format_signal_report
from .output import print_header, print_info

logger = logging.getLogger(__name__)


def analyze_ticker_with_prediction(ticker: str) -> Dict:
    """
    Perform complete analysis with news-based market prediction.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary with analysis results including prediction
    """
    print(f"📊 Analyzing {ticker}...")
    
    # Fetch market data
    df = fetch_market_data(ticker)
    
    # Calculate technicals
    technicals = calculate_technicals(df)
    
    # Fetch news
    articles, news_source, oldest_date, newest_date = fetch_news_headlines(ticker, hours=24)
    
    # Show sample headlines
    if articles:
        print(f"   📋 {len(articles)} articles found")
    
    # Traditional sentiment
    from .config import USE_AI_SENTIMENT
    sentiment = analyze_sentiment_ai(articles, ticker) if USE_AI_SENTIMENT else analyze_sentiment_simple(articles)
    
    # NEW: Advanced news signal extraction
    extractor = NewsSignalExtractor()
    news_analysis = extractor.analyze_multiple_articles(articles)
    prediction = extractor.predict_direction(news_analysis)
    
    # Show prediction
    print(f"   🎯 NEWS PREDICTION: {prediction['prediction']} ({prediction['strength']})")
    print(f"      Confidence: {prediction['confidence_score']:.0f}% | Expected: {prediction['expected_move']}")
    print(f"      Catalyst: {prediction['catalyst']}")
    
    # Traditional recommendation
    recommendation, color = generate_recommendation(technicals, sentiment, ticker)
    
    # Calculate score
    earnings_flag = ""
    earnings_date = get_earnings_date(ticker)
    if earnings_date:
        now_et = get_et_time_naive()
        days_until_earnings = (earnings_date - now_et).days
        if 0 <= days_until_earnings <= 7:
            earnings_flag = "E"
    
    news_age_hours = 0
    if articles and oldest_date:
        try:
            oldest_naive = oldest_date.replace(tzinfo=None) if hasattr(oldest_date, 'tzinfo') and oldest_date.tzinfo else oldest_date
            news_age_hours = (get_et_time_naive() - oldest_naive).total_seconds() / 3600
        except:
            pass
    
    score_result = calculate_trade_score(
        technicals=technicals,
        sentiment=sentiment,
        news_count=len(articles),
        news_age_hours=news_age_hours,
        earnings_flag=earnings_flag
    )
    
    print(f"   📊 SCORE: {score_result['final_score']:.0f}/100 ({score_result['category']})")
    
    # Combine technical score with prediction
    alignment = check_alignment(score_result, prediction, technicals)
    print(f"   {alignment['emoji']} ALIGNMENT: {alignment['status']}")
    if alignment['warning']:
        print(f"      ⚠️  {alignment['warning']}")
    
    return {
        'ticker': ticker,
        'price': technicals['price'] if technicals else 'N/A',
        'rsi': technicals['rsi'] if technicals else 'N/A',
        'bb_status': technicals['bb_status'] if technicals else 'N/A',
        'trend': technicals.get('trend', 'N/A') if technicals else 'N/A',
        'sentiment': round(sentiment, 2),
        'news_count': len(articles),
        'recommendation': recommendation,
        'score': score_result['final_score'],
        'score_category': score_result['category'],
        # News prediction fields
        'news_prediction': prediction['prediction'],
        'prediction_strength': prediction['strength'],
        'prediction_confidence': prediction['confidence_score'],
        'expected_move': prediction['expected_move'],
        'catalyst': prediction['catalyst'],
        'news_direction': news_analysis['aggregate_direction'],
        'signal_consistency': news_analysis['signal_consistency'],
        'recent_trend': news_analysis['recent_trend'],
        # Alignment
        'alignment': alignment['status'],
        'alignment_score': alignment['score'],
        'alignment_warning': alignment['warning']
    }


def check_alignment(score_result: Dict, prediction: Dict, technicals: Dict) -> Dict:
    """
    Check if technical setup aligns with news prediction.
    
    Returns:
        Alignment assessment
    """
    tech_score = score_result['final_score']
    tech_category = score_result['category']
    news_pred = prediction['prediction']
    pred_confidence = prediction['confidence_score']
    
    rsi = technicals.get('rsi') if technicals else None
    trend = technicals.get('trend', 'UNKNOWN') if technicals else 'UNKNOWN'
    
    # Check alignment
    tech_bullish = tech_score >= 65
    news_bullish = news_pred == 'BULLISH'
    
    if tech_bullish and news_bullish:
        # Perfect alignment - technical setup + bullish news
        if tech_score >= 75 and pred_confidence >= 70:
            return {
                'status': 'STRONG CONFLUENCE',
                'emoji': '🟢🟢',
                'score': 10,
                'warning': None
            }
        else:
            return {
                'status': 'BULLISH ALIGNMENT',
                'emoji': '🟢',
                'score': 8,
                'warning': None
            }
    
    elif not tech_bullish and news_pred == 'BEARISH':
        # Aligned - both bearish (avoid trade)
        return {
            'status': 'BEARISH ALIGNMENT',
            'emoji': '🔴',
            'score': 2,
            'warning': 'Both technicals and news are bearish - AVOID'
        }
    
    elif tech_bullish and news_pred == 'BEARISH':
        # Divergence - good technical setup but bad news
        return {
            'status': 'DIVERGENCE',
            'emoji': '⚠️',
            'score': 4,
            'warning': 'Technical buy signal BUT bearish news - HIGH RISK'
        }
    
    elif not tech_bullish and news_bullish:
        # Divergence - bullish news but bad technical setup
        if rsi and rsi > 50:
            return {
                'status': 'TOO EARLY',
                'emoji': '⏳',
                'score': 6,
                'warning': f'Bullish news BUT not oversold (RSI {rsi:.0f}) - WAIT for dip'
            }
        elif trend == 'DOWNTREND':
            return {
                'status': 'PREMATURE',
                'emoji': '⏳',
                'score': 5,
                'warning': 'Bullish news BUT downtrend - WAIT for reversal'
            }
        else:
            return {
                'status': 'WEAK SETUP',
                'emoji': '🟡',
                'score': 5,
                'warning': 'Bullish news but technical score too low'
            }
    
    else:
        # Neutral or unclear
        return {
            'status': 'NEUTRAL/UNCLEAR',
            'emoji': '⚪',
            'score': 5,
            'warning': 'Mixed signals - wait for clarity'
        }


def create_enhanced_output_table(results: list) -> str:
    """Create formatted table with predictions."""
    from tabulate import tabulate
    
    # Sort by alignment score then overall score
    sorted_results = sorted(
        results, 
        key=lambda x: (x.get('alignment_score', 0), x.get('score', 0)), 
        reverse=True
    )
    
    table_data = []
    for r in sorted_results:
        row = [
            r['ticker'],
            f"{r['score']:.0f}" if isinstance(r.get('score'), (int, float)) else "N/A",
            r.get('score_category', 'N/A')[:12],
            r.get('news_prediction', 'N/A'),
            f"{r.get('prediction_confidence', 0):.0f}%",
            r.get('alignment', 'N/A')[:15],
            f"{r['rsi']:.0f}" if isinstance(r['rsi'], (int, float)) else 'N/A',
            r.get('trend', 'N/A')[:4],
            f"${r['price']:.2f}" if isinstance(r['price'], (int, float)) else r['price']
        ]
        table_data.append(row)
    
    headers = ['Ticker', 'Score', 'Category', 'News→', 'Conf%', 'Alignment', 'RSI', 'Trend', 'Price']
    
    return tabulate(table_data, headers=headers, tablefmt='grid')


def print_enhanced_summary(results: list):
    """Print summary with prediction insights."""
    print("\n" + "="*80)
    print("📈 ENHANCED ANALYSIS SUMMARY")
    print("="*80)
    
    # Find strong opportunities (aligned bullish signals)
    strong_buys = [r for r in results if r.get('alignment_score', 0) >= 8]
    
    if strong_buys:
        print(f"\n🟢🟢 STRONG OPPORTUNITIES (Technical + News Aligned):")
        for r in strong_buys:
            print(f"\n   {r['ticker']}: Score {r['score']:.0f}/100")
            print(f"   ├─ Technical: {r['score_category']} (RSI {r['rsi']:.0f}, {r['trend']})")
            print(f"   ├─ News: {r['news_prediction']} ({r['prediction_confidence']:.0f}% confidence)")
            print(f"   ├─ Catalyst: {r['catalyst']}")
            print(f"   └─ Expected Move: {r['expected_move']}")
    else:
        print(f"\n⏸️  No strong opportunities with aligned signals")
    
    # Early signals (bullish news, waiting for dip)
    early = [r for r in results if r.get('news_prediction') == 'BULLISH' and r.get('score', 0) < 65]
    
    if early:
        print(f"\n⏳ WATCH LIST (Bullish news, waiting for entry):")
        for r in early:
            print(f"   {r['ticker']}: {r.get('alignment_warning', 'Bullish catalyst but not oversold yet')}")
    
    # Avoid (bearish alignment)
    avoid = [r for r in results if r.get('alignment_score', 0) <= 2]
    
    if avoid:
        print(f"\n🔴 AVOID (Bearish signals):")
        for r in avoid:
            print(f"   {r['ticker']}: {r.get('alignment_warning', 'Bearish news + weak technicals')}")


def main():
    """Main entry point for enhanced analysis."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )
    
    print_header()
    print("🎯 ENHANCED WITH NEWS PREDICTION")
    print("="*80)
    
    # Analyze all tickers
    results = []
    for ticker in TICKERS:
        try:
            result = analyze_ticker_with_prediction(ticker)
            results.append(result)
            print()  # Spacing
        except Exception as e:
            print(f"❌ Error analyzing {ticker}: {str(e)}\n")
            logger.error(f"Error: {e}")
    
    # Display results
    print("\n" + "="*80)
    print("📊 ENHANCED ANALYSIS RESULTS")
    print("="*80)
    table = create_enhanced_output_table(results)
    print(table)
    
    # Print summary
    print_enhanced_summary(results)
    
    print_info()
    
    print("\n✅ Enhanced analysis complete!\n")


if __name__ == "__main__":
    main()
