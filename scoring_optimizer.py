#!/usr/bin/env python3
"""
Scoring Weight Optimizer
Uses historical trade data to optimize scoring system weights.

This script analyzes past trades to find optimal weights that would have
maximized win rate and profit factor.

Usage:
    python3 scoring_optimizer.py --input AMZN_trades_FINAL_OPTIMIZED.csv
    python3 scoring_optimizer.py --input trades.csv --output optimized_weights.json
"""

import argparse
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from scipy.optimize import minimize
from datetime import datetime
import sys
import os

# Add parent dir to path to import from premarket_analysis
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from premarket_analysis.scoring_config import WEIGHTS


def load_trade_history(filepath: str) -> pd.DataFrame:
    """
    Load historical trade data from CSV.
    
    Expected columns:
    - ticker: Stock symbol
    - entry_price: Entry price
    - exit_price: Exit price  
    - pnl: Profit/loss
    - rsi: RSI at entry (optional)
    - bb_status: Bollinger band status (optional)
    - sentiment: Sentiment score (optional)
    - trend: Trend at entry (optional)
    
    Returns:
        DataFrame with trade history
    """
    df = pd.read_csv(filepath)
    
    # Add win/loss column if not present
    if 'win' not in df.columns and 'pnl' in df.columns:
        df['win'] = (df['pnl'] > 0).astype(int)
    
    return df


def calculate_component_scores(row: pd.Series) -> Dict[str, float]:
    """
    Calculate individual component scores for a trade based on entry conditions.
    This is a simplified version - in practice, you'd integrate with scoring.py
    
    Returns:
        Dictionary with component scores (0-100)
    """
    scores = {}
    
    # Technical score (based on RSI and BB position)
    if 'rsi' in row and pd.notna(row['rsi']):
        rsi = row['rsi']
        if rsi <= 20:
            tech_score = 90
        elif rsi <= 30:
            tech_score = 75
        elif rsi <= 40:
            tech_score = 50
        else:
            tech_score = 30
        scores['technical'] = tech_score
    else:
        scores['technical'] = 50  # neutral if missing
    
    # Sentiment score
    if 'sentiment' in row and pd.notna(row['sentiment']):
        # Convert -1 to 1 range to 0-100 score
        sentiment = row['sentiment']
        scores['sentiment'] = max(0, min(100, (sentiment + 1) * 50))
    else:
        scores['sentiment'] = 50
    
    # Momentum score (based on trend)
    if 'trend' in row and pd.notna(row['trend']):
        trend = str(row['trend']).upper()
        if trend == 'UPTREND':
            scores['momentum'] = 85
        elif trend == 'SIDEWAYS':
            scores['momentum'] = 60
        elif trend == 'DOWNTREND':
            scores['momentum'] = 30
        else:
            scores['momentum'] = 50
    else:
        scores['momentum'] = 50
    
    # Catalyst score (placeholder - would need news data)
    scores['catalyst'] = 60  # default moderate score
    
    # Timing score (placeholder - would need time of day)
    scores['timing'] = 70  # default good score
    
    return scores


def calculate_trade_score_with_weights(component_scores: Dict[str, float], 
                                       weights: Dict[str, float]) -> float:
    """
    Calculate weighted trade score given component scores and weights.
    
    Returns:
        Score from 0-100
    """
    score = (
        component_scores['technical'] * weights['technical'] +
        component_scores['sentiment'] * weights['sentiment'] +
        component_scores['momentum'] * weights['momentum'] +
        component_scores['catalyst'] * weights['catalyst'] +
        component_scores['timing'] * weights['timing']
    )
    return score


def evaluate_weights(weights_array: np.ndarray, df: pd.DataFrame, 
                    component_scores_list: List[Dict]) -> float:
    """
    Objective function to minimize: negative profit factor.
    
    We want to maximize:
    - Win rate on high-scored trades
    - Average profit on winning high-scored trades
    - Avoid losses on low-scored trades
    
    Returns:
        Negative profit factor (for minimization)
    """
    # Convert array to weights dict
    weights = {
        'technical': weights_array[0],
        'sentiment': weights_array[1],
        'momentum': weights_array[2],
        'catalyst': weights_array[3],
        'timing': weights_array[4]
    }
    
    # Calculate scores for all trades
    scores = []
    for comp_scores in component_scores_list:
        score = calculate_trade_score_with_weights(comp_scores, weights)
        scores.append(score)
    
    df['score'] = scores
    
    # Filter to high-conviction trades (score > 65)
    high_conviction = df[df['score'] >= 65]
    
    if len(high_conviction) < 3:  # Not enough trades
        return 1000.0  # Bad score
    
    # Calculate metrics
    win_rate = high_conviction['win'].mean()
    
    if 'pnl' in high_conviction.columns:
        gross_profit = high_conviction[high_conviction['pnl'] > 0]['pnl'].sum()
        gross_loss = abs(high_conviction[high_conviction['pnl'] < 0]['pnl'].sum())
        
        if gross_loss == 0:
            profit_factor = gross_profit if gross_profit > 0 else 0.1
        else:
            profit_factor = gross_profit / gross_loss
    else:
        # If no P&L data, use win rate as proxy
        profit_factor = win_rate * 2
    
    # We want to maximize profit factor and win rate
    # Also penalize if we filter out too many trades
    trade_retention = len(high_conviction) / len(df)
    
    # Combined objective (higher is better, so negate for minimization)
    objective = -(profit_factor * win_rate * (trade_retention ** 0.5))
    
    return objective


def optimize_weights(df: pd.DataFrame) -> Tuple[Dict[str, float], Dict]:
    """
    Find optimal weights using scipy.optimize.
    
    Returns:
        Tuple of (optimal_weights, optimization_results)
    """
    print("🔍 Calculating component scores for historical trades...")
    
    # Calculate component scores for each trade
    component_scores_list = []
    for idx, row in df.iterrows():
        comp_scores = calculate_component_scores(row)
        component_scores_list.append(comp_scores)
    
    print(f"✅ Processed {len(component_scores_list)} trades")
    print("\n⚙️  Optimizing weights...")
    
    # Initial weights (current settings)
    initial_weights = np.array([
        WEIGHTS['technical'],
        WEIGHTS['sentiment'],
        WEIGHTS['momentum'],
        WEIGHTS['catalyst'],
        WEIGHTS['timing']
    ])
    
    # Constraints: weights must sum to 1.0
    constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}
    
    # Bounds: each weight between 0.05 and 0.6
    bounds = [(0.05, 0.6)] * 5
    
    # Optimize
    result = minimize(
        evaluate_weights,
        initial_weights,
        args=(df, component_scores_list),
        method='SLSQP',
        bounds=bounds,
        constraints=constraints,
        options={'maxiter': 100, 'disp': True}
    )
    
    # Extract optimal weights
    optimal_weights = {
        'technical': float(result.x[0]),
        'sentiment': float(result.x[1]),
        'momentum': float(result.x[2]),
        'catalyst': float(result.x[3]),
        'timing': float(result.x[4])
    }
    
    # Calculate metrics with original vs optimal
    print("\n" + "="*80)
    print("📊 OPTIMIZATION RESULTS")
    print("="*80)
    
    # Evaluate original weights
    original_objective = evaluate_weights(initial_weights, df, component_scores_list)
    optimal_objective = result.fun
    
    improvement = ((original_objective - optimal_objective) / abs(original_objective)) * 100
    
    results = {
        'original_weights': {k: float(v) for k, v in WEIGHTS.items()},
        'optimal_weights': optimal_weights,
        'original_objective': float(original_objective),
        'optimal_objective': float(optimal_objective),
        'improvement_pct': float(improvement),
        'optimization_success': result.success,
        'iterations': result.nit
    }
    
    return optimal_weights, results


def print_comparison(results: Dict):
    """Print comparison of original vs optimal weights."""
    print("\n📊 Weight Comparison:")
    print("-" * 60)
    print(f"{'Component':<15} {'Original':<12} {'Optimal':<12} {'Change':<12}")
    print("-" * 60)
    
    for component in ['technical', 'sentiment', 'momentum', 'catalyst', 'timing']:
        original = results['original_weights'][component]
        optimal = results['optimal_weights'][component]
        change = optimal - original
        change_str = f"{change:+.3f}"
        
        print(f"{component:<15} {original:<12.3f} {optimal:<12.3f} {change_str:<12}")
    
    print("-" * 60)
    print(f"\n💡 Improvement: {results['improvement_pct']:.1f}%")
    print(f"✅ Success: {results['optimization_success']}")


def save_results(results: Dict, optimal_weights: Dict[str, float], output_file: str):
    """Save optimization results to JSON."""
    output = {
        'optimization_date': datetime.now().isoformat(),
        'results': results,
        'recommended_weights': optimal_weights
    }
    
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")


def generate_config_code(optimal_weights: Dict[str, float]) -> str:
    """Generate Python code to update scoring_config.py."""
    code = """
# OPTIMIZED WEIGHTS (generated by scoring_optimizer.py)
WEIGHTS = {
"""
    for component, weight in optimal_weights.items():
        code += f"    '{component}': {weight:.4f},\n"
    code += "}\n"
    
    return code


def main():
    parser = argparse.ArgumentParser(description='Optimize scoring system weights from trade history')
    parser.add_argument('--input', '-i', required=True, help='Input CSV file with trade history')
    parser.add_argument('--output', '-o', default='optimized_weights.json', 
                       help='Output JSON file for results (default: optimized_weights.json)')
    parser.add_argument('--min-trades', type=int, default=10,
                       help='Minimum number of trades required (default: 10)')
    
    args = parser.parse_args()
    
    # Load trade data
    print(f"📂 Loading trade history from: {args.input}")
    try:
        df = load_trade_history(args.input)
        print(f"✅ Loaded {len(df)} trades")
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return 1
    
    # Check minimum trades
    if len(df) < args.min_trades:
        print(f"⚠️  Warning: Only {len(df)} trades found. Need at least {args.min_trades} for reliable optimization.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return 1
    
    # Optimize
    try:
        optimal_weights, results = optimize_weights(df)
    except Exception as e:
        print(f"❌ Optimization error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Print results
    print_comparison(results)
    
    # Save results
    save_results(results, optimal_weights, args.output)
    
    # Generate config code
    print("\n" + "="*80)
    print("📝 TO APPLY THESE WEIGHTS:")
    print("="*80)
    print("\nAdd this to your scoring_config.py:")
    print(generate_config_code(optimal_weights))
    
    print("\n✅ Optimization complete!")
    return 0


if __name__ == "__main__":
    exit(main())
