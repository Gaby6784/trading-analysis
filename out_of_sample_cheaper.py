#!/usr/bin/env python3
"""
Out-of-sample test on cheaper stocks
Rank tickers on first year, test on second year
"""

import yfinance as yf
import pandas as pd
import numpy as np

# Main ticker universe (excluding weaker tickers)
TICKERS = ['TSLA', 'NVDA', 'MSFT', 'AAPL', 'AMZN', 'META', 'NFLX', 'INTC']
PERIOD = '2y'
INTERVAL = '1h'

# Safe settings
ACCOUNT_BALANCE = 200.0
RISK_PER_TRADE = 0.02
ROUND_STEP = 0.1
MAX_POSITION_PCT = 1.0  # 100% cap, no leverage

# Strategy parameters
RSI_LENGTH = 14
BB_LENGTH = 20
BB_MULT = 2.0
SL_PERCENT = 1.5
VOLUME_LENGTH = 20
RR_RATIO = 3.0
USE_TRAILING_SL = True

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


def run_backtest(data):
    balance = ACCOUNT_BALANCE
    trades = []
    position = None
    last_signal_time = None

    for i in range(len(data)):
        row = data.iloc[i]
        current_time = data.index[i]

        close_val = float(row['Close'])
        rsi_val = float(row['RSI'])
        bb_lower = float(row['BB_Lower'])
        bb_upper = float(row['BB_Upper'])
        volume_val = float(row['Volume'])
        volume_avg = float(row['Volume_Avg'])

        if position is not None:
            pos_type = position['type']
            entry = position['entry']
            sl = position['sl']
            tp = position['tp']
            shares = position['shares']
            risk_distance = position['risk_distance']

            if USE_TRAILING_SL:
                if pos_type == 'BUY':
                    current_profit = close_val - entry
                    profit_in_risk = current_profit / risk_distance

                    if profit_in_risk >= 1.0 and sl < entry:
                        sl = entry
                        position['sl'] = sl

                    if profit_in_risk > 1.0:
                        trail_level = close_val - (risk_distance * 0.5)
                        if trail_level > sl:
                            sl = trail_level
                            position['sl'] = sl

                    if close_val <= sl:
                        pnl = (close_val - entry) * shares
                        balance += pnl
                        trades.append(pnl)
                        position = None
                        continue
                else:
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
                        trades.append(pnl)
                        position = None
                        continue
            else:
                if pos_type == 'BUY':
                    if close_val <= sl:
                        pnl = (close_val - entry) * shares
                        balance += pnl
                        trades.append(pnl)
                        position = None
                        continue
                    if close_val >= tp:
                        pnl = (close_val - entry) * shares
                        balance += pnl
                        trades.append(pnl)
                        position = None
                        continue
                else:
                    if close_val >= sl:
                        pnl = (entry - close_val) * shares
                        balance += pnl
                        trades.append(pnl)
                        position = None
                        continue
                    if close_val <= tp:
                        pnl = (entry - close_val) * shares
                        balance += pnl
                        trades.append(pnl)
                        position = None
                        continue

        if position is None:
            if volume_val <= volume_avg:
                continue

            strong_buy = rsi_val < STRONG_BUY_THRESHOLD and close_val <= bb_lower
            moderate_buy = rsi_val < MODERATE_BUY_THRESHOLD and close_val <= bb_lower and not strong_buy
            buy_signal = strong_buy or moderate_buy

            strong_sell = rsi_val > STRONG_SELL_THRESHOLD and close_val >= bb_upper
            moderate_sell = rsi_val > MODERATE_SELL_THRESHOLD and close_val >= bb_upper and not strong_sell
            sell_signal = strong_sell or moderate_sell

            if last_signal_time is not None:
                time_diff = (current_time - last_signal_time).total_seconds() / 3600
                if time_diff < 5:
                    continue

            if buy_signal:
                sl_price = bb_lower * (1 - SL_PERCENT / 100)
                risk_distance = close_val - sl_price
                tp_price = close_val + (risk_distance * RR_RATIO)
                risk_amount = balance * RISK_PER_TRADE
                shares = max(ROUND_STEP, np.floor((risk_amount / risk_distance) / ROUND_STEP) * ROUND_STEP)

                if MAX_POSITION_PCT is not None:
                    max_shares = (balance * MAX_POSITION_PCT) / close_val
                    shares = min(shares, max_shares)
                    shares = max(ROUND_STEP, np.floor(shares / ROUND_STEP) * ROUND_STEP)

                if shares < ROUND_STEP:
                    continue

                position = {
                    'type': 'BUY',
                    'entry': close_val,
                    'sl': sl_price,
                    'tp': tp_price,
                    'shares': shares,
                    'risk_distance': risk_distance
                }
                last_signal_time = current_time

            elif sell_signal:
                sl_price = bb_upper * (1 + SL_PERCENT / 100)
                risk_distance = sl_price - close_val
                tp_price = close_val - (risk_distance * RR_RATIO)
                risk_amount = balance * RISK_PER_TRADE
                shares = max(ROUND_STEP, np.floor((risk_amount / risk_distance) / ROUND_STEP) * ROUND_STEP)

                if MAX_POSITION_PCT is not None:
                    max_shares = (balance * MAX_POSITION_PCT) / close_val
                    shares = min(shares, max_shares)
                    shares = max(ROUND_STEP, np.floor(shares / ROUND_STEP) * ROUND_STEP)

                if shares < ROUND_STEP:
                    continue

                position = {
                    'type': 'SELL',
                    'entry': close_val,
                    'sl': sl_price,
                    'tp': tp_price,
                    'shares': shares,
                    'risk_distance': risk_distance
                }
                last_signal_time = current_time

    if position is not None:
        final_close = float(data.iloc[-1]['Close'])
        if position['type'] == 'BUY':
            pnl = (final_close - position['entry']) * position['shares']
        else:
            pnl = (position['entry'] - final_close) * position['shares']
        balance += pnl
        trades.append(pnl)

    if not trades:
        return None

    total_return = ((balance - ACCOUNT_BALANCE) / ACCOUNT_BALANCE) * 100
    win_rate = (np.sum(np.array(trades) > 0) / len(trades)) * 100

    return {
        'return': total_return,
        'win_rate': win_rate,
        'trades': len(trades)
    }


def main():
    print("=" * 80)
    print("OUT-OF-SAMPLE TEST (CHEAPER STOCKS)")
    print("=" * 80)
    print(f"Tickers: {', '.join(TICKERS)}")
    print("Period: 2 years (1st year train, 2nd year test)")
    print("Safe settings: 2% risk, trailing SL, 100% cap")
    print()

    results = []

    for ticker in TICKERS:
        data = yf.download(ticker, period=PERIOD, interval=INTERVAL, progress=False)
        if data.empty or len(data) < 200:
            print(f"{ticker}: insufficient data")
            continue

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        data['RSI'] = calculate_rsi(data, RSI_LENGTH)
        data['BB_Upper'], data['BB_Middle'], data['BB_Lower'] = calculate_bb(data, BB_LENGTH, BB_MULT)
        data['Volume_Avg'] = data['Volume'].rolling(window=VOLUME_LENGTH).mean()
        data = data.dropna()

        if len(data) < 200:
            print(f"{ticker}: insufficient data after indicators")
            continue

        mid = len(data) // 2
        train_data = data.iloc[:mid]
        test_data = data.iloc[mid:]

        train_result = run_backtest(train_data)
        test_result = run_backtest(test_data)

        if train_result is None or test_result is None:
            print(f"{ticker}: no trades")
            continue

        results.append({
            'ticker': ticker,
            'train_return': train_result['return'],
            'train_win_rate': train_result['win_rate'],
            'test_return': test_result['return'],
            'test_win_rate': test_result['win_rate'],
            'test_trades': test_result['trades']
        })

        print(
            f"{ticker}: Train {train_result['return']:+6.2f}%, "
            f"Test {test_result['return']:+6.2f}% "
            f"({test_result['trades']} trades)"
        )

    if not results:
        print("No results to report")
        return

    # Rank by train and evaluate test
    ranked = sorted(results, key=lambda x: x['train_return'], reverse=True)

    print("\nTop 3 by train return:")
    for r in ranked[:3]:
        print(f"  {r['ticker']}: Train {r['train_return']:+.2f}%, Test {r['test_return']:+.2f}%")

    avg_test = np.mean([r['test_return'] for r in ranked[:3]])
    print(f"\nOut-of-sample average (Top 3): {avg_test:+.2f}%")

    all_test_avg = np.mean([r['test_return'] for r in results])
    print(f"All tickers average test return: {all_test_avg:+.2f}%")

    good = [r for r in results if r['test_return'] > 0]
    if good:
        good_sorted = sorted(good, key=lambda x: x['test_return'], reverse=True)
        good_avg = np.mean([r['test_return'] for r in good_sorted])
        print("\nGood tickers (positive test return):")
        print("  " + ", ".join([r['ticker'] for r in good_sorted]))
        print(f"Good tickers average test return: {good_avg:+.2f}%")
    else:
        print("\nGood tickers (positive test return): none")


if __name__ == "__main__":
    main()
