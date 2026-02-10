#!/usr/bin/env python3
"""
Demo: Show detailed news signal analysis for a ticker
"""

import sys
from premarket_analysis.news_fetching import fetch_news_headlines
from premarket_analysis.news_signals import NewsSignalExtractor, format_signal_report

def main():
    ticker = sys.argv[1] if len(sys.argv) > 1 else 'AMZN'
    
    print(f"\n🔍 DETAILED NEWS SIGNAL ANALYSIS FOR {ticker}")
    print("="*80)
    
    # Fetch news
    articles, news_source, oldest_date, newest_date = fetch_news_headlines(ticker, hours=48)
    
    if not articles:
        print(f"❌ No news found for {ticker}")
        return
    
    print(f"\n📰 Found {len(articles)} articles from {news_source}")
    print(f"   Time range: {oldest_date.strftime('%Y-%m-%d %H:%M')} to {newest_date.strftime('%Y-%m-%d %H:%M')}")
    
    # Extract signals
    extractor = NewsSignalExtractor()
    
    print(f"\n📋 ANALYZING EACH ARTICLE:")
    print("-" * 80)
    
    for i, (headline, pub_date) in enumerate(articles[:10], 1):  # Show first 10
        signal = extractor.extract_signals(headline)
        
        emoji = "🟢" if signal['direction'] == 'BULLISH' else "🔴" if signal['direction'] == 'BEARISH' else "⚪"
        
        print(f"\n{i}. {emoji} [{pub_date.strftime('%Y-%m-%d %H:%M')}]")
        print(f"   \"{headline[:70]}{'...' if len(headline) > 70 else ''}\"")
        print(f"   Direction: {signal['direction']} (Confidence: {signal['confidence']*100:.0f}%)")
        print(f"   Impact Score: {signal['impact_score']:.0f}/100 | Catalyst: {signal['catalyst']}")
        
        if signal['bullish_signals']:
            print(f"   ✅ Bullish: {', '.join(list(signal['bullish_signals'].values())[0][:2])}")
        
        if signal['bearish_signals']:
            print(f"   ❌ Bearish: {', '.join(list(signal['bearish_signals'].values())[0][:2])}")
        
        if signal['magnitude'] > 1.2:
            print(f"   📈 High magnitude: {signal['magnitude']:.1f}x")
        
        if signal['urgency'] > 1.2:
            print(f"   ⚡ High urgency: {signal['urgency']:.1f}x")
    
    # Aggregate analysis
    print(f"\n\n{'='*80}")
    print("📊 AGGREGATE ANALYSIS & PREDICTION")
    print("="*80)
    
    agg = extractor.analyze_multiple_articles(articles)
    pred = extractor.predict_direction(agg)
    
    print(f"\n📰 Article Breakdown:")
    print(f"   Total: {agg['article_breakdown']['total']}")
    print(f"   Bullish: {agg['article_breakdown']['bullish']} ({agg['article_breakdown']['bullish']/agg['article_breakdown']['total']*100:.0f}%)")
    print(f"   Bearish: {agg['article_breakdown']['bearish']} ({agg['article_breakdown']['bearish']/agg['article_breakdown']['total']*100:.0f}%)")
    print(f"   Neutral: {agg['article_breakdown']['neutral']} ({agg['article_breakdown']['neutral']/agg['article_breakdown']['total']*100:.0f}%)")
    
    print(f"\n📊 Aggregate Metrics:")
    print(f"   Direction: {agg['aggregate_direction']} ({agg['aggregate_confidence']*100:.0f}% confidence)")
    print(f"   Impact Score: {agg['aggregate_impact']:.0f}/100")
    print(f"   Dominant Catalyst: {agg['dominant_catalyst']}")
    print(f"   Signal Consistency: {agg['signal_consistency']*100:.0f}%")
    print(f"   Recent Trend (last 3): {agg['recent_trend']}")
    
    print(f"\n🎯 MARKET PREDICTION:")
    print(f"   Predicted Direction: {pred['prediction']} ({pred['strength']})")
    print(f"   Confidence: {pred['confidence_score']:.0f}%")
    print(f"   Expected Move: {pred['expected_move']}")
    print(f"   Key Catalyst: {pred['catalyst']}")
    print(f"   {pred['confidence_level']}")
    
    print(f"\n💡 Reasoning:")
    for reason in pred['reasoning']:
        print(f"   • {reason}")
    
    print(f"\n{'='*80}")
    print("✅ Analysis complete!")
    print(f"\n💡 TIP: Run this during major news events to see high-impact signals\n")


if __name__ == "__main__":
    main()
