#!/usr/bin/env python3
"""
Full Trading Simulation: All 10 Tickers, 1 Year
Simulates what would happen if you started trading today with the optimized strategy
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configuration - YOUR TICKERS
TICKERS = ['TSLA', 'NVDA', 'MSFT', 'AAPL', 'GOOGL', 'AMZN', 'META', 'AMD', 'NFLX', 'INTC', 'BE', 'PLUG', 'PUBM', 'BBAI']
PERIOD = '1y'
INTERVAL = '1h'

# YOUR TRADING PARAMETERS
ACCOUNT_BALANCE = 200.0
RISK_PER_TRADE = 0.02  # 2% risk per trade
ROUND_STEP = 0.1
MAX_POSITION_PCT = 1.0  # Max 100% of balance per position (no leverage)

# OPTIMIZED STRATEGY PARAMETERS
RSI_LENGTH = 14
BB_LENGTH = 20
BB_MULT = 2.0
SL_PERCENT = 1.5
VOLUME_LENGTH = 20
RR_RATIO = 3.0  # Optimized from 2.0 to 3.0
USE_TRAILING_SL = True  # Trailing SL enabled

# Signal Thresholds (Moderate + Strong)
STRONG_BUY_THRESHOLD = 20
MODERATE_BUY_THRESHOLD = 25
STRONG_SELL_THRESHOLD = 80
MODERATE_SELL_THRESHOLD = 75

def calculate_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_bb(data, period=20, num_std=2.0):
    middle = data['Close'].rolling(window=period).mean()
    std = data['Close'].rolling(window=period).std()
    upper = middle + (std * num_std)
    lower = middle - (std * num_std)
    return upper, middle, lower

def backtest_ticker(ticker):
    """Run backtest on single ticker with optimized strategy"""
    try:
        data = yf.download(ticker, period=PERIOD, interval=INTERVAL, progress=False)
        if data.empty or len(data) < 50:
            return None
        
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        
        # Calculate indicators
        data['RSI'] = calculate_rsi(data, RSI_LENGTH)
        data['BB_Upper'], data['BB_Middle'], data['BB_Lower'] = calculate_bb(data, BB_LENGTH, BB_MULT)
        data['Volume_Avg'] = data['Volume'].rolling(window=VOLUME_LENGTH).mean()
        data = data.dropna()
        
        if len(data) < 50:
            return None
        
        balance = ACCOUNT_BALANCE
        trades = []
        position = None
        last_signal_time = None
        balance_history = [(data.index[0], balance)]
        
        for i in range(len(data)):
            row = data.iloc[i]
            current_time = data.index[i]
            
            close_val = float(row['Close'])
            rsi_val = float(row['RSI'])
            bb_lower = float(row['BB_Lower'])
            bb_upper = float(row['BB_Upper'])
            volume_val = float(row['Volume'])
            volume_avg = float(row['Volume_Avg'])
            
            # Position management
            if position is not None:
                pos_type = position['type']
                entry = position['entry']
                sl = position['sl']
                shares = position['shares']
                risk_distance = position['risk_distance']
                
                if USE_TRAILING_SL:
                    # Trailing Stop Loss Logic
                    if pos_type == 'BUY':
                        current_profit = close_val - entry
                        profit_in_risk = current_profit / risk_distance
                        
                        # Move to breakeven at 1x risk
                        if profit_in_risk >= 1.0 and sl < entry:
                            sl = entry
                            position['sl'] = sl
                        
                        # Trail at 0.5x risk distance behind price
                        if profit_in_risk > 1.0:
                            trail_level = close_val - (risk_distance * 0.5)
                            if trail_level > sl:
                                sl = trail_level
                                position['sl'] = sl
                        
                        if close_val <= sl:
                            pnl = (close_val - entry) * shares
                            balance += pnl
                            exit_type = 'TRAILING_SL' if sl > entry else 'INITIAL_SL'
                            trades.append({
                                'ticker': ticker,
                                'date': current_time,
                                'type': pos_type,
                                'entry': entry,
                                'exit': close_val,
                                'shares': shares,
                                'pnl': pnl,
                                'pnl_pct': (pnl / (entry * shares)) * 100,
                                'balance': balance,
                                'exit_reason': exit_type,
                                'bars_held': position.get('bars_held', 0)
                            })
                            balance_history.append((current_time, balance))
                            position = None
                            continue
                        else:
                            position['bars_held'] = position.get('bars_held', 0) + 1
                    
                    else:  # SELL position
                        current_profit = entry - close_val
                        profit_in_risk = current_profit / risk_distance
                        
                        if profit_in_risk >= 1.0 and sl > entry:
                            sl = entry
                            position['sl'] = sl
                        
                        if profit_in_risk > 1.0:
                            trail_level = close_val + (risk_distance * 0.5)
                            if trail_level < sl:
                                sl = trail_level
                                position['sl'] = sl
                        
                        if close_val >= sl:
                            pnl = (entry - close_val) * shares
                            balance += pnl
                            exit_type = 'TRAILING_SL' if sl < entry else 'INITIAL_SL'
                            trades.append({
                                'ticker': ticker,
                                'date': current_time,
                                'type': pos_type,
                                'entry': entry,
                                'exit': close_val,
                                'shares': shares,
                                'pnl': pnl,
                                'pnl_pct': (pnl / (entry * shares)) * 100,
                                'balance': balance,
                                'exit_reason': exit_type,
                                'bars_held': position.get('bars_held', 0)
                            })
                            balance_history.append((current_time, balance))
                            position = None
                            continue
                        else:
                            position['bars_held'] = position.get('bars_held', 0) + 1
            
            # Look for new signals
            if position is None:
                volume_confirmed = volume_val > volume_avg
                if not volume_confirmed:
                    continue
                
                strong_buy = rsi_val < STRONG_BUY_THRESHOLD and close_val <= bb_lower
                moderate_buy = rsi_val < MODERATE_BUY_THRESHOLD and close_val <= bb_lower and not strong_buy
                buy_signal = strong_buy or moderate_buy
                
                strong_sell = rsi_val > STRONG_SELL_THRESHOLD and close_val >= bb_upper
                moderate_sell = rsi_val > MODERATE_SELL_THRESHOLD and close_val >= bb_upper and not strong_sell
                sell_signal = strong_sell or moderate_sell
                
                # Deduplication: only one signal per 5 bars
                if last_signal_time is not None:
                    time_diff = (current_time - last_signal_time).total_seconds() / 3600
                    if time_diff < 5:
                        continue
                
                if buy_signal:
                    sl_price = bb_lower * (1 - SL_PERCENT / 100)
                    risk_distance = close_val - sl_price
                    risk_amount = balance * RISK_PER_TRADE
                    shares = max(ROUND_STEP, np.floor((risk_amount / risk_distance) / ROUND_STEP) * ROUND_STEP)
                    
                    # Apply affordability constraint (optional)
                    if MAX_POSITION_PCT is not None:
                        max_shares = (balance * MAX_POSITION_PCT) / close_val
                        shares = min(shares, max_shares)
                        shares = max(ROUND_STEP, np.floor(shares / ROUND_STEP) * ROUND_STEP)
                    
                    if shares < ROUND_STEP:
                        continue
                    
                    tp_price = close_val + (risk_distance * RR_RATIO)
                    signal_type = 'STRONG' if strong_buy else 'MODERATE'
                    
                    position = {
                        'type': 'BUY',
                        'entry': close_val,
                        'sl': sl_price,
                        'tp': tp_price,
                        'shares': shares,
                        'risk_distance': risk_distance,
                        'signal_type': signal_type,
                        'bars_held': 0
                    }
                    last_signal_time = current_time
                
                elif sell_signal:
                    sl_price = bb_upper * (1 + SL_PERCENT / 100)
                    risk_distance = sl_price - close_val
                    risk_amount = balance * RISK_PER_TRADE
                    shares = max(ROUND_STEP, np.floor((risk_amount / risk_distance) / ROUND_STEP) * ROUND_STEP)
                    
                    # Apply affordability constraint (optional)
                    if MAX_POSITION_PCT is not None:
                        max_shares = (balance * MAX_POSITION_PCT) / close_val
                        shares = min(shares, max_shares)
                        shares = max(ROUND_STEP, np.floor(shares / ROUND_STEP) * ROUND_STEP)
                    
                    if shares < ROUND_STEP:
                        continue
                    
                    tp_price = close_val - (risk_distance * RR_RATIO)
                    signal_type = 'STRONG' if strong_sell else 'MODERATE'
                    
                    position = {
                        'type': 'SELL',
                        'entry': close_val,
                        'sl': sl_price,
                        'tp': tp_price,
                        'shares': shares,
                        'risk_distance': risk_distance,
                        'signal_type': signal_type,
                        'bars_held': 0
                    }
                    last_signal_time = current_time
        
        # Close any open position at end
        if position is not None:
            final_close = float(data.iloc[-1]['Close'])
            if position['type'] == 'BUY':
                pnl = (final_close - position['entry']) * position['shares']
            else:
                pnl = (position['entry'] - final_close) * position['shares']
            balance += pnl
            trades.append({
                'ticker': ticker,
                'date': data.index[-1],
                'type': position['type'],
                'entry': position['entry'],
                'exit': final_close,
                'shares': position['shares'],
                'pnl': pnl,
                'pnl_pct': (pnl / (position['entry'] * position['shares'])) * 100,
                'balance': balance,
                'exit_reason': 'EOD',
                'bars_held': position.get('bars_held', 0)
            })
            balance_history.append((data.index[-1], balance))
        
        if not trades:
            return None
        
        trades_df = pd.DataFrame(trades)
        balance_df = pd.DataFrame(balance_history, columns=['date', 'balance'])
        
        # Calculate statistics
        winning_trades = trades_df[trades_df['pnl'] > 0]
        losing_trades = trades_df[trades_df['pnl'] <= 0]
        
        total_return = ((balance - ACCOUNT_BALANCE) / ACCOUNT_BALANCE) * 100
        win_rate = len(winning_trades) / len(trades_df) * 100 if len(trades_df) > 0 else 0
        
        profit_factor = abs(winning_trades['pnl'].sum() / losing_trades['pnl'].sum()) if len(losing_trades) > 0 and losing_trades['pnl'].sum() != 0 else 999
        
        avg_win = winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0
        avg_loss = losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0
        
        # Calculate max drawdown
        balance_df['peak'] = balance_df['balance'].cummax()
        balance_df['drawdown'] = (balance_df['balance'] - balance_df['peak']) / balance_df['peak'] * 100
        max_drawdown = balance_df['drawdown'].min()
        
        # Avg bars held
        avg_bars_held = trades_df['bars_held'].mean() if 'bars_held' in trades_df.columns else 0
        avg_hours_held = avg_bars_held
        
        # Exit reasons breakdown
        trailing_sl_hits = len(trades_df[trades_df['exit_reason'] == 'TRAILING_SL'])
        initial_sl_hits = len(trades_df[trades_df['exit_reason'] == 'INITIAL_SL'])
        
        return {
            'ticker': ticker,
            'total_trades': len(trades_df),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'total_return': total_return,
            'final_balance': balance,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'max_drawdown': max_drawdown,
            'avg_hours_held': avg_hours_held,
            'trailing_sl_hits': trailing_sl_hits,
            'initial_sl_hits': initial_sl_hits,
            'trades_df': trades_df,
            'balance_df': balance_df
        }
    
    except Exception as e:
        print(f"Error processing {ticker}: {str(e)}")
        return None

def main():
    print("=" * 80)
    print("FULL TRADING SIMULATION: Selected Tickers, 1 Year")
    print("=" * 80)
    print(f"Period: {PERIOD} ({INTERVAL} bars)")
    print(f"Starting Balance: ${ACCOUNT_BALANCE:.2f}")
    print(f"Risk Per Trade: {RISK_PER_TRADE*100:.1f}%")
    print(f"Max Position Cap: {MAX_POSITION_PCT * 100:.0f}%" if MAX_POSITION_PCT is not None else "Max Position Cap: None")
    print()
    print("Strategy: Moderate + Volume + 3.0x R:R + Trailing SL")
    print(f"Tickers: {', '.join(TICKERS)}")
    print("=" * 80)
    print()
    
    results = []
    all_trades = []
    
    for ticker in TICKERS:
        print(f"Simulating {ticker}...", end=' ')
        result = backtest_ticker(ticker)
        
        if result:
            results.append(result)
            all_trades.extend(result['trades_df'].to_dict('records'))
            print(f"✓ ${result['final_balance']:.2f} ({result['total_return']:>+7.2f}%) | {result['total_trades']} trades | WR: {result['win_rate']:.1f}%")
        else:
            print("✗ Insufficient data")
    
    if not results:
        print("\nNo results to analyze")
        return
    
    # Detailed Results Table
    print(f"\n{'=' * 80}")
    print("DETAILED RESULTS BY TICKER")
    print(f"{'=' * 80}\n")
    
    print(f"{'Ticker':<8} {'Balance':>10} {'Return':>10} {'Trades':>8} {'Win%':>8} {'PF':>8} {'MaxDD':>8}")
    print("-" * 80)
    
    for r in results:
        print(f"{r['ticker']:<8} ${r['final_balance']:>8.2f} {r['total_return']:>+9.2f}% "
              f"{r['total_trades']:>8} {r['win_rate']:>7.1f}% {r['profit_factor']:>7.2f} "
              f"{r['max_drawdown']:>7.2f}%")
    
    # Portfolio Statistics
    print(f"\n{'=' * 80}")
    print("PORTFOLIO STATISTICS")
    print(f"{'=' * 80}\n")
    
    positive_tickers = [r for r in results if r['total_return'] > 0]
    negative_tickers = [r for r in results if r['total_return'] <= 0]
    
    avg_return = np.mean([r['total_return'] for r in results])
    median_return = np.median([r['total_return'] for r in results])
    std_return = np.std([r['total_return'] for r in results])
    
    total_trades = sum([r['total_trades'] for r in results])
    total_winning = sum([r['winning_trades'] for r in results])
    total_losing = sum([r['losing_trades'] for r in results])
    
    avg_win_rate = np.mean([r['win_rate'] for r in results])
    avg_profit_factor = np.mean([r['profit_factor'] for r in results if r['profit_factor'] < 100])
    avg_max_drawdown = np.mean([r['max_drawdown'] for r in results])
    avg_hours_held = np.mean([r['avg_hours_held'] for r in results])
    
    total_trailing_hits = sum([r['trailing_sl_hits'] for r in results])
    total_initial_hits = sum([r['initial_sl_hits'] for r in results])
    
    print(f"Positive Tickers: {len(positive_tickers)}/{len(results)} ({len(positive_tickers)/len(results)*100:.1f}%)")
    print(f"Negative Tickers: {len(negative_tickers)}/{len(results)} ({len(negative_tickers)/len(results)*100:.1f}%)")
    print()
    print(f"Average Return per Ticker: {avg_return:+.2f}%")
    print(f"Median Return per Ticker: {median_return:+.2f}%")
    print(f"Std Dev of Returns: {std_return:.2f}%")
    print()
    print(f"Total Trades Across All Tickers: {total_trades}")
    print(f"  Winning Trades: {total_winning} ({total_winning/total_trades*100:.1f}%)")
    print(f"  Losing Trades: {total_losing} ({total_losing/total_trades*100:.1f}%)")
    print()
    print(f"Average Win Rate: {avg_win_rate:.2f}%")
    print(f"Average Profit Factor: {avg_profit_factor:.2f}")
    print(f"Average Max Drawdown: {avg_max_drawdown:.2f}%")
    print(f"Average Trade Duration: {avg_hours_held:.1f} hours")
    print()
    print(f"Trailing SL Protection: {total_trailing_hits}/{total_trailing_hits+total_initial_hits} trades ({total_trailing_hits/(total_trailing_hits+total_initial_hits)*100:.1f}%)")
    
    # Best and Worst Performers
    print(f"\n{'=' * 80}")
    print("BEST & WORST PERFORMERS")
    print(f"{'=' * 80}\n")
    
    best = max(results, key=lambda x: x['total_return'])
    worst = min(results, key=lambda x: x['total_return'])
    
    print(f"🏆 Best: {best['ticker']} → ${best['final_balance']:.2f} ({best['total_return']:+.2f}%)")
    print(f"   Win Rate: {best['win_rate']:.1f}%, Trades: {best['total_trades']}, PF: {best['profit_factor']:.2f}")
    print()
    print(f"❌ Worst: {worst['ticker']} → ${worst['final_balance']:.2f} ({worst['total_return']:+.2f}%)")
    print(f"   Win Rate: {worst['win_rate']:.1f}%, Trades: {worst['total_trades']}, PF: {worst['profit_factor']:.2f}")
    
    # If you traded all 10 simultaneously
    print(f"\n{'=' * 80}")
    print(f"WHAT IF YOU TRADED ALL {len(TICKERS)} TICKERS?")
    print(f"{'=' * 80}\n")
    
    # Assuming you split your balance across all tickers
    per_ticker_balance = ACCOUNT_BALANCE / len(TICKERS)
    total_final_balance = sum([per_ticker_balance * (1 + r['total_return'] / 100) for r in results])
    portfolio_return = ((total_final_balance - ACCOUNT_BALANCE) / ACCOUNT_BALANCE) * 100
    
    print(f"Starting: ${ACCOUNT_BALANCE:.2f} → ${per_ticker_balance:.2f} per ticker")
    print(f"Ending: ${total_final_balance:.2f}")
    print(f"Total Return: {portfolio_return:+.2f}%")
    print()
    print(f"This would be {total_trades} total trades over 1 year")
    print(f"Average ~{total_trades/52:.1f} trades per week")
    
    # Expected Forward Performance
    print(f"\n{'=' * 80}")
    print("FORWARD EXPECTATIONS (If you start trading now)")
    print(f"{'=' * 80}\n")
    
    print("Based on these backtests, here's what you can expect:")
    print()
    print(f"✓ Average Return per Ticker: {avg_return:+.2f}%")
    print(f"✓ Win Rate: ~{avg_win_rate:.0f}%")
    print(f"✓ Profit Factor: ~{avg_profit_factor:.1f}x")
    print(f"✓ Max Drawdown: ~{avg_max_drawdown:.1f}%")
    print()
    print(f"Conservative Estimate (25th percentile): {np.percentile([r['total_return'] for r in results], 25):+.2f}%")
    print(f"Median Estimate: {median_return:+.2f}%")
    print(f"Optimistic Estimate (75th percentile): {np.percentile([r['total_return'] for r in results], 75):+.2f}%")
    print()
    print("⚠️ Important Notes:")
    print("   - These are BACKTEST results, not guarantees")
    print("   - Market conditions change")
    print("   - Stick to 2% risk per trade maximum")
    print("   - Use stop losses religiously")
    print("   - Don't overtrade - wait for quality signals")
    
    # Monthly breakdown
    print(f"\n{'=' * 80}")
    print("EXPECTED MONTHLY PERFORMANCE")
    print(f"{'=' * 80}\n")
    
    monthly_return = avg_return / 12
    print(f"Expected Return per Month: {monthly_return:+.2f}%")
    print(f"On ${ACCOUNT_BALANCE:.2f} account: ${ACCOUNT_BALANCE * monthly_return / 100:+.2f} per month")
    print()
    print("Projection over 12 months:")
    balance = ACCOUNT_BALANCE
    for month in range(1, 13):
        balance += balance * (monthly_return / 100)
        print(f"  Month {month:2d}: ${balance:>7.2f} ({((balance-ACCOUNT_BALANCE)/ACCOUNT_BALANCE*100):>+6.2f}%)")

if __name__ == "__main__":
    main()
