#!/usr/bin/env python3
"""
Backtest the Scoring System on Historical Trades
Analyzes how the scoring system would have performed on past trades.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from typing import Dict, List
import matplotlib.pyplot as plt
from tabulate import tabulate

from premarket_analysis.scoring import calculate_trade_score
from premarket_analysis.scoring_config import SCORE_STRONG_BUY, SCORE_BUY, SCORE_CAUTION


def load_historical_trades(filepath: str) -> pd.DataFrame:
    """Load historical trade data from CSV."""
    print(f"📂 Loading trades from: {filepath}")
    df = pd.read_csv(filepath)
    print(f"✅ Loaded {len(df)} trades")
    return df


def simulate_score_at_entry(row: pd.Series) -> Dict:
    """
    Simulate what the score would have been at trade entry.
    Uses the trade data to reconstruct entry conditions.
    """
    # Build technicals dict from trade data
    technicals = {
        'price': row.get('entry_price', 100),
        'rsi': row.get('rsi', 50),  # Default to neutral if missing
        'bb_status': row.get('bb_status', 'MIDDLE'),
        'trend': row.get('trend', 'UNKNOWN'),
        'macd_hist': row.get('macd_hist', 0),
        'atr_pct': row.get('atr_pct', 3.0),
        'volatility': 'NORMAL'
    }
    
    # Sentiment from trade data
    sentiment = row.get('sentiment', 0.0)
    
    # News data (use defaults if not in CSV)
    news_count = row.get('news_count', 5)
    news_age_hours = row.get('news_age_hours', 12)
    earnings_flag = row.get('earnings_flag', '')
    
    # Calculate score
    score_result = calculate_trade_score(
        technicals=technicals,
        sentiment=sentiment,
        news_count=news_count,
        news_age_hours=news_age_hours,
        earnings_flag=earnings_flag
    )
    
    return score_result


def analyze_by_score_bucket(df: pd.DataFrame) -> pd.DataFrame:
    """Group trades by score buckets and calculate statistics."""
    
    # Define score buckets
    df['score_bucket'] = pd.cut(
        df['score'],
        bins=[0, 50, 65, 75, 100],
        labels=['0-50 (AVOID)', '50-65 (CAUTION)', '65-75 (BUY)', '75+ (STRONG_BUY)']
    )
    
    # Calculate statistics by bucket
    grouped = df.groupby('score_bucket', observed=True).agg({
        'pnl': ['count', 'sum', 'mean', 'std'],
        'win': ['sum', 'mean']
    }).round(2)
    
    # Flatten column names
    grouped.columns = ['Trade_Count', 'Total_PnL', 'Avg_PnL', 'StdDev_PnL', 'Wins', 'Win_Rate']
    
    # Calculate additional metrics
    grouped['Win_Rate'] = (grouped['Win_Rate'] * 100).round(1)
    grouped['Profit_Factor'] = 0.0
    
    for bucket in grouped.index:
        bucket_trades = df[df['score_bucket'] == bucket]
        wins = bucket_trades[bucket_trades['pnl'] > 0]['pnl'].sum()
        losses = abs(bucket_trades[bucket_trades['pnl'] < 0]['pnl'].sum())
        
        if losses > 0:
            grouped.loc[bucket, 'Profit_Factor'] = round(wins / losses, 2)
        else:
            grouped.loc[bucket, 'Profit_Factor'] = wins if wins > 0 else 0
    
    return grouped


def calculate_filter_impact(df: pd.DataFrame, min_score: float) -> Dict:
    """Calculate impact of filtering trades by minimum score."""
    
    # Original performance (all trades)
    original_trades = len(df)
    original_wins = df['win'].sum()
    original_win_rate = (original_wins / original_trades * 100) if original_trades > 0 else 0
    original_pnl = df['pnl'].sum()
    
    # Filtered performance
    filtered = df[df['score'] >= min_score]
    filtered_trades = len(filtered)
    filtered_wins = filtered['win'].sum() if len(filtered) > 0 else 0
    filtered_win_rate = (filtered_wins / filtered_trades * 100) if filtered_trades > 0 else 0
    filtered_pnl = filtered['pnl'].sum() if len(filtered) > 0 else 0
    
    # Avoided trades (would have been filtered out)
    avoided = df[df['score'] < min_score]
    avoided_trades = len(avoided)
    avoided_pnl = avoided['pnl'].sum() if len(avoided) > 0 else 0
    
    return {
        'min_score': min_score,
        'original_trades': original_trades,
        'original_win_rate': round(original_win_rate, 1),
        'original_pnl': round(original_pnl, 2),
        'filtered_trades': filtered_trades,
        'filtered_win_rate': round(filtered_win_rate, 1),
        'filtered_pnl': round(filtered_pnl, 2),
        'avoided_trades': avoided_trades,
        'avoided_pnl': round(avoided_pnl, 2),
        'trade_reduction_pct': round((avoided_trades / original_trades * 100) if original_trades > 0 else 0, 1),
        'pnl_improvement': round(filtered_pnl - original_pnl, 2)
    }


def plot_score_vs_pnl(df: pd.DataFrame, output_file: str = 'score_vs_pnl.png'):
    """Create scatter plot of score vs P&L."""
    plt.figure(figsize=(12, 6))
    
    # Scatter plot
    plt.subplot(1, 2, 1)
    colors = ['red' if w == 0 else 'green' for w in df['win']]
    plt.scatter(df['score'], df['pnl'], c=colors, alpha=0.6)
    plt.axhline(y=0, color='black', linestyle='--', linewidth=0.5)
    plt.xlabel('Score')
    plt.ylabel('P&L ($)')
    plt.title('Score vs P&L (Green=Win, Red=Loss)')
    plt.grid(True, alpha=0.3)
    
    # Box plot by bucket
    plt.subplot(1, 2, 2)
    df.boxplot(column='pnl', by='score_bucket', ax=plt.gca())
    plt.xlabel('Score Bucket')
    plt.ylabel('P&L ($)')
    plt.title('P&L Distribution by Score Bucket')
    plt.suptitle('')  # Remove default title
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"📊 Chart saved to: {output_file}")


def print_report(df: pd.DataFrame):
    """Print comprehensive backtest report."""
    
    print("\n" + "="*80)
    print("📊 SCORING SYSTEM BACKTEST REPORT")
    print("="*80)
    
    # Overall statistics
    print(f"\n📈 Overall Performance:")
    print(f"   Total Trades: {len(df)}")
    print(f"   Wins: {df['win'].sum()} ({df['win'].mean()*100:.1f}%)")
    print(f"   Total P&L: ${df['pnl'].sum():.2f}")
    print(f"   Average P&L: ${df['pnl'].mean():.2f}")
    print(f"   Average Score: {df['score'].mean():.1f}/100")
    
    # Score distribution
    print(f"\n🎯 Score Distribution:")
    print(f"   STRONG_BUY (75+):   {len(df[df['score'] >= 75])} trades ({len(df[df['score'] >= 75])/len(df)*100:.1f}%)")
    print(f"   BUY (65-74):        {len(df[(df['score'] >= 65) & (df['score'] < 75)])} trades")
    print(f"   CAUTION (50-64):    {len(df[(df['score'] >= 50) & (df['score'] < 65)])} trades")
    print(f"   AVOID (0-49):       {len(df[df['score'] < 50])} trades")
    
    # Performance by bucket
    print(f"\n📊 Performance by Score Bucket:")
    bucket_stats = analyze_by_score_bucket(df)
    print(tabulate(bucket_stats, headers='keys', tablefmt='grid'))
    
    # Filter analysis
    print(f"\n🔍 Filter Impact Analysis:")
    filter_scenarios = [
        calculate_filter_impact(df, 50),
        calculate_filter_impact(df, 65),
        calculate_filter_impact(df, 75)
    ]
    
    filter_table = []
    for scenario in filter_scenarios:
        filter_table.append([
            f">= {scenario['min_score']}",
            f"{scenario['filtered_trades']}/{scenario['original_trades']}",
            f"{scenario['filtered_win_rate']}%",
            f"${scenario['filtered_pnl']:.2f}",
            f"{scenario['trade_reduction_pct']}%",
            f"${scenario['avoided_pnl']:.2f}",
            f"${scenario['pnl_improvement']:.2f}"
        ])
    
    headers = ['Min Score', 'Trades', 'Win Rate', 'P&L', 'Trades Cut', 'Avoided P&L', 'Improvement']
    print(tabulate(filter_table, headers=headers, tablefmt='grid'))
    
    # Best performing threshold
    best_threshold = max(filter_scenarios, key=lambda x: x['filtered_win_rate'])
    print(f"\n⭐ Optimal Threshold: {best_threshold['min_score']}+")
    print(f"   Would have improved win rate from {filter_scenarios[0]['original_win_rate']}% to {best_threshold['filtered_win_rate']}%")
    
    # Example trades
    print(f"\n🔴 Worst Scored Trades that Lost:")
    worst_losers = df[(df['win'] == 0) & (df['score'] < 50)].nsmallest(3, 'pnl')
    if len(worst_losers) > 0:
        for idx, row in worst_losers.iterrows():
            print(f"   {row['ticker']}: Score {row['score']:.0f} → Lost ${abs(row['pnl']):.2f}")
            if 'score_adjustments' in row and row['score_adjustments']:
                print(f"      Warnings: {row['score_adjustments']}")
    else:
        print("   (None - no low-scored losers)")
    
    print(f"\n🟢 Best Scored Trades that Won:")
    best_winners = df[(df['win'] == 1) & (df['score'] >= 65)].nlargest(3, 'pnl')
    if len(best_winners) > 0:
        for idx, row in best_winners.iterrows():
            print(f"   {row['ticker']}: Score {row['score']:.0f} → Won ${row['pnl']:.2f}")
    else:
        print("   (None - no high-scored winners)")
    
    # Correlations
    print(f"\n📈 Correlation Analysis:")
    score_pnl_corr = df['score'].corr(df['pnl'])
    score_win_corr = df['score'].corr(df['win'])
    print(f"   Score vs P&L: {score_pnl_corr:.3f}")
    print(f"   Score vs Win: {score_win_corr:.3f}")
    
    if score_win_corr > 0.3:
        print(f"   ✅ Strong positive correlation - scoring system is predictive!")
    elif score_win_corr > 0.1:
        print(f"   ✓ Moderate correlation - scoring system shows promise")
    else:
        print(f"   ⚠️  Weak correlation - may need tuning")


def main():
    """Main backtest execution."""
    
    # Check for input file
    if len(sys.argv) > 1:
        trade_file = sys.argv[1]
    else:
        # Try default file
        trade_file = 'AMZN_trades_FINAL_OPTIMIZED.csv'
    
    try:
        # Load trades
        df = load_historical_trades(trade_file)
        
        # Check required columns
        required_cols = ['pnl']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"❌ Error: Missing required columns: {missing_cols}")
            print(f"   Available columns: {df.columns.tolist()}")
            return 1
        
        # Add win column if not present
        if 'win' not in df.columns:
            df['win'] = (df['pnl'] > 0).astype(int)
        
        # Add default values for missing columns
        if 'ticker' not in df.columns:
            df['ticker'] = 'UNKNOWN'
        if 'rsi' not in df.columns:
            print("⚠️  Warning: No RSI data, using defaults (50)")
            df['rsi'] = 50
        if 'bb_status' not in df.columns:
            print("⚠️  Warning: No BB status, using defaults (MIDDLE)")
            df['bb_status'] = 'MIDDLE'
        if 'trend' not in df.columns:
            print("⚠️  Warning: No trend data, using defaults (UNKNOWN)")
            df['trend'] = 'UNKNOWN'
        if 'sentiment' not in df.columns:
            print("⚠️  Warning: No sentiment data, using defaults (0.0)")
            df['sentiment'] = 0.0
        if 'news_count' not in df.columns:
            df['news_count'] = 5
        if 'news_age_hours' not in df.columns:
            df['news_age_hours'] = 12
        if 'earnings_flag' not in df.columns:
            df['earnings_flag'] = ''
        
        print(f"\n⚙️  Calculating scores for {len(df)} trades...")
        
        # Calculate score for each trade
        scores = []
        categories = []
        adjustments_list = []
        
        for idx, row in df.iterrows():
            score_result = simulate_score_at_entry(row)
            scores.append(score_result['final_score'])
            categories.append(score_result['category'])
            adjustments_list.append(', '.join(score_result['adjustments'][:3]) if score_result['adjustments'] else '')
        
        df['score'] = scores
        df['score_category'] = categories
        df['score_adjustments'] = adjustments_list
        
        print(f"✅ Scoring complete!")
        
        # Generate report
        print_report(df)
        
        # Create visualizations
        try:
            plot_score_vs_pnl(df)
        except Exception as e:
            print(f"⚠️  Could not create chart: {e}")
        
        # Save detailed results
        output_file = 'backtest_results_detailed.csv'
        df.to_csv(output_file, index=False)
        print(f"\n💾 Detailed results saved to: {output_file}")
        
        print("\n✅ Backtest complete!\n")
        return 0
        
    except FileNotFoundError:
        print(f"❌ Error: File not found: {trade_file}")
        print(f"\nUsage: python3 backtest_scoring_system.py [trade_file.csv]")
        print(f"   Default file: AMZN_trades_FINAL_OPTIMIZED.csv")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
