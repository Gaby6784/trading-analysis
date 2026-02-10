"""
Output formatting and display
"""

from prettytable import PrettyTable
from typing import List, Dict
from datetime import datetime
from .config import TICKERS, NEWS_SOURCES, USE_AI_SENTIMENT, NEWS_LOOKBACK_HOURS, TRADING_CAPITAL


def create_output_table(results: List[Dict]) -> PrettyTable:
    """
    Create a formatted table of analysis results with enhanced metrics.
    
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
        "Trend",
        "Vol",
        "Stop",
        "BB%",
        "Sentiment",
        "News",
        "Src",
        "Earn",
        "Shares",
        "Recommendation"
    ]
    
    # Set alignment
    table.align["Ticker"] = "l"
    table.align["Price"] = "r"
    table.align["RSI"] = "r"
    table.align["Trend"] = "c"
    table.align["Vol"] = "c"
    table.align["Stop"] = "r"
    table.align["BB%"] = "r"
    table.align["Sentiment"] = "l"
    table.align["News"] = "r"
    table.align["Src"] = "c"
    table.align["Earn"] = "c"
    table.align["Shares"] = "r"
    table.align["Recommendation"] = "l"
    
    # Add rows
    for result in results:
        # Format trend
        trend = result.get('trend', 'N/A')
        if trend == 'UPTREND':
            trend_symbol = '↑'
        elif trend == 'DOWNTREND':
            trend_symbol = '↓'
        elif trend == 'SIDEWAYS':
            trend_symbol = '→'
        elif trend == 'INSUFFICIENT_DATA':
            trend_symbol = '?'
        else:
            trend_symbol = '-'
        
        # Format volatility
        vol = result.get('volatility', 'N/A')
        if vol == 'HIGH':
            vol_symbol = '🔥'
        elif vol == 'MED':
            vol_symbol = '~'
        elif vol == 'LOW':
            vol_symbol = '.'
        else:
            vol_symbol = '-'
        
        # Format suggested stop
        stop = result.get('suggested_stop', 'N/A')
        stop_str = f"${stop:.2f}" if isinstance(stop, (int, float)) else 'N/A'
        
        # Format BB% (distance from middle band)
        bb_pct = result.get('bb_mid_pct', 'N/A')
        bb_str = f"{bb_pct:+.1f}%" if isinstance(bb_pct, (int, float)) else 'N/A'
        
        # Format source
        source = result.get('news_source', 'N/A')
        source_abbr = {
            'yahoo_rss': 'Y',
            'reuters': 'R',
            'finviz': 'F',
            'google_news': 'G',
            'newsapi': 'N',
            'cache': 'C',
            'error': 'X',
            'none': '-'
        }.get(source, source[0].upper() if source != 'N/A' else '-')
        
        # Format earnings flag
        earnings_flag = result.get('earnings_flag', '')
        
        # Format price properly
        price = result['price']
        price_str = f"${price:.2f}" if isinstance(price, (int, float)) else 'N/A'
        
        # Calculate position size for BUY signals
        shares_str = '-'
        recommendation = result['recommendation']
        if '🟢' in recommendation and isinstance(price, (int, float)) and price > 0:
            # Calculate max shares we can afford
            max_shares = TRADING_CAPITAL / price
            shares_str = f"{max_shares:.3f}"
        
        table.add_row([
            result['ticker'],
            price_str,
            result['rsi'] if result['rsi'] != 'N/A' else 'N/A',
            trend_symbol,
            vol_symbol,
            stop_str,
            bb_str,
            f"{result['sentiment_label'][:4]} ({result['sentiment']})",
            f"{result['news_count']}",
            source_abbr,
            earnings_flag,
            shares_str,
            result['recommendation']
        ])
    
    return table


def print_summary(results: List[Dict]):
    """Print summary statistics."""
    total = len(results)
    buy_signals = sum(1 for r in results if '🟢' in r['recommendation'])
    sell_signals = sum(1 for r in results if '🔴' in r['recommendation'])
    hold_signals = sum(1 for r in results if '⚪' in r['recommendation'])
    avoid_signals = sum(1 for r in results if '⚠️' in r['recommendation'])
    
    print("\n" + "="*80)
    print("📈 ANALYSIS SUMMARY")
    print("="*80)
    print(f"Total Tickers Analyzed: {total}")
    print(f"Buy Signals: {buy_signals}")
    print(f"Sell Signals: {sell_signals}")
    print(f"Hold Signals: {hold_signals}")
    print(f"Avoid Signals: {avoid_signals}")
    print("-" * 80)
    
    # Trading Plan - show BUY recommendations
    buy_results = [r for r in results if '🟢' in r['recommendation']]
    if buy_results:
        print(f"\n💰 TRADING PLAN (Capital: ${TRADING_CAPITAL:.2f})")
        print("-" * 80)
        for r in buy_results:
            ticker = r['ticker']
            price = r['price']
            stop = r['suggested_stop']
            shares = TRADING_CAPITAL / price
            cost = shares * price
            risk_per_share = price - stop if stop != 'N/A' else 0
            total_risk = shares * risk_per_share if stop != 'N/A' else 0
            risk_pct = (total_risk / TRADING_CAPITAL * 100) if total_risk > 0 else 0
            
            print(f"{ticker}:")
            print(f"  • BUY {shares:.3f} shares @ ${price:.2f} = ${cost:.2f}")
            if stop != 'N/A':
                print(f"  • Stop-Loss: ${stop:.2f} (risk ${risk_per_share:.2f}/share)")
                print(f"  • Total Risk: ${total_risk:.2f} ({risk_pct:.1f}% of capital)")
            print(f"  • Reason: {r['recommendation']}")
            print()
        print("-" * 80)
    
    # News statistics
    total_news = sum(r['news_count'] for r in results)
    avg_news = total_news / total if total > 0 else 0
    
    # Calculate average news age
    valid_ages = [r['news_age_hours'] for r in results if r['news_age_hours'] > 0]
    avg_age = sum(valid_ages) / len(valid_ages) if valid_ages else 0
    
    freshness = "FRESH - Good for prediction!" if avg_age < 12 else \
                "MODERATE - Somewhat current" if avg_age < 24 else \
                "STALE - Use caution"
    
    print(f"📰 Total News Articles Consulted: {total_news}")
    print(f"   Articles per ticker (average): {avg_news:.1f}")
    print(f"   Average article age: {avg_age:.1f} hours ({freshness})")
    print(f"   News lookback window: {NEWS_LOOKBACK_HOURS} hours")
    
    # Group by source
    source_counts = {}
    for r in results:
        source = r['news_source']
        source_counts[source] = source_counts.get(source, 0) + 1
    
    print("   News sources used:")
    for source, count in sorted(source_counts.items(), key=lambda x: -x[1]):
        source_name = {
            'yahoo_rss': 'Yahoo RSS',
            'reuters': 'Reuters',
            'finviz': 'Finviz',
            'google_news': 'Google News',
            'newsapi': 'NewsAPI',
            'cache': 'Cache',
            'error': 'error',
            'none': 'none'
        }.get(source, source)
        print(f"      • {source_name}: {count} ticker(s)")
    
    print("="*80)


def print_info():
    """Print configuration info."""
    print(f"\nℹ️  NEWS SOURCES: {' → '.join(NEWS_SOURCES)}")
    if any(s == 'newsapi' for s in NEWS_SOURCES):
        print("   Note: NewsAPI requires API key (free tier: 100 requests/day)")
    else:
        print("   Using FREE news sources (no API key required) ✅")
    
    print(f"\nℹ️  SENTIMENT: Using {'AI-powered' if USE_AI_SENTIMENT else 'keyword-based'} analysis")
    if not USE_AI_SENTIMENT:
        print("   For AI-powered sentiment, set USE_AI_SENTIMENT=True")


def print_header():
    """Print analysis header."""
    print("\n" + "="*80)
    print("🚀 PRE-MARKET STOCK ANALYSIS")
    print("="*80)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Analyzing: {', '.join(TICKERS)}")
    print("="*80 + "\n")
