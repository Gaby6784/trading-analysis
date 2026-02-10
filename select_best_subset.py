#!/usr/bin/env python3
"""
Select best 5-6 main tickers (excluding GOOGL/TSLA/AMD) and add best cheap ticker.
Out-of-sample: train year 1, test year 2.
"""

import yfinance as yf
import pandas as pd
import numpy as np

# Main tickers and exclusions
MAIN_TICKERS = ['TSLA', 'NVDA', 'MSFT', 'AAPL', 'GOOGL', 'AMZN', 'META', 'AMD', 'NFLX', 'INTC']
EXCLUDE_MAIN = {'GOOGL', 'TSLA', 'AMD'}
CHEAP_TICKERS = ['BE', 'PLUG', 'PUBM', 'BBAI']

PERIOD = '2y'
INTERVAL = '1h'

ACCOUNT_BALANCE = 200.0
RISK_PER_TRADE = 0.02
ROUND_STEP = 0.1
MAX_POSITION_PCT = 1.0

RSI_LENGTH = 14
BB_LENGTH = 20
BB_MULT = 2.0
SL_PERCENT = 1.5
VOLUME_LENGTH = 20
RR_RATIO = 3.0
USE_TRAILING_SL = False

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
                if risk_distance <= 0:
                    continue
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
                if risk_distance <= 0:
                    continue
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
        pnl = (final_close - position['entry']) * position['shares'] if position['type'] == 'BUY' else (position['entry'] - final_close) * position['shares']
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


def prepare_data(ticker):
    data = yf.download(ticker, period=PERIOD, interval=INTERVAL, progress=False)
    if data.empty or len(data) < 200:
        return None
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data['RSI'] = calculate_rsi(data, RSI_LENGTH)
    data['BB_Upper'], data['BB_Middle'], data['BB_Lower'] = calculate_bb(data, BB_LENGTH, BB_MULT)
    data['Volume_Avg'] = data['Volume'].rolling(window=VOLUME_LENGTH).mean()
    data = data.dropna()

    if len(data) < 200:
        return None

    return data


def run_for_ticker(ticker):
    data = prepare_data(ticker)
    if data is None:
        return None

    mid = len(data) // 2
    train_data = data.iloc[:mid]
    test_data = data.iloc[mid:]

    train_result = run_backtest(train_data)
    test_result = run_backtest(test_data)

    if train_result is None or test_result is None:
        return None

    return {
        'ticker': ticker,
        'train_return': train_result['return'],
        'test_return': test_result['return'],
        'test_trades': test_result['trades']
    }


def main():
    print("=" * 80)
    print("SELECT BEST MAIN TICKERS + BEST CHEAP TICKER")
    print("=" * 80)
    print("Safe settings: 2% risk, fixed SL/TP, 100% cap")
    print()

    main_candidates = [t for t in MAIN_TICKERS if t not in EXCLUDE_MAIN]

    main_results = []
    cheap_results = []

    for ticker in main_candidates:
        res = run_for_ticker(ticker)
        if res:
            main_results.append(res)
            print(f"{ticker}: Train {res['train_return']:+6.2f}%, Test {res['test_return']:+6.2f}%")
        else:
            print(f"{ticker}: insufficient data")

    print()
    for ticker in CHEAP_TICKERS:
        res = run_for_ticker(ticker)
        if res:
            cheap_results.append(res)
            print(f"{ticker}: Train {res['train_return']:+6.2f}%, Test {res['test_return']:+6.2f}%")
        else:
            print(f"{ticker}: insufficient data")

    if not main_results:
        print("No main results")
        return

    if not cheap_results:
        print("No cheap results")
        return

    # Selection by test return
    main_sorted_test = sorted(main_results, key=lambda x: x['test_return'], reverse=True)
    top6_test = main_sorted_test[:6]
    best_cheap_test = max(cheap_results, key=lambda x: x['test_return'])

    selected_test = top6_test + [best_cheap_test]
    avg_selected_test = np.mean([r['test_return'] for r in selected_test])

    positive_test = [r for r in main_sorted_test if r['test_return'] > 0]
    top5_pos_test = positive_test[:5]
    selected_test_pos = top5_pos_test + [best_cheap_test]
    avg_selected_test_pos = np.mean([r['test_return'] for r in selected_test_pos]) if selected_test_pos else None

    print("\nSelected main tickers (top 6 by test return):")
    for r in top6_test:
        print(f"  {r['ticker']}: Test {r['test_return']:+.2f}%")

    print(f"\nSelected cheap ticker (by test): {best_cheap_test['ticker']} ({best_cheap_test['test_return']:+.2f}%)")
    print(f"Average test return (selected 7): {avg_selected_test:+.2f}%")
    print(f"Estimated $ profit on $200: ${ACCOUNT_BALANCE * avg_selected_test / 100:.2f}")

    if top5_pos_test:
        print("\nSelected main tickers (top 5 positive by test return):")
        for r in top5_pos_test:
            print(f"  {r['ticker']}: Test {r['test_return']:+.2f}%")
        print(f"\nSelected cheap ticker (by test): {best_cheap_test['ticker']} ({best_cheap_test['test_return']:+.2f}%)")
        print(f"Average test return (selected 6): {avg_selected_test_pos:+.2f}%")
        print(f"Estimated $ profit on $200: ${ACCOUNT_BALANCE * avg_selected_test_pos / 100:.2f}")

    # Selection by train return
    main_sorted_train = sorted(main_results, key=lambda x: x['train_return'], reverse=True)
    top6_train = main_sorted_train[:6]
    best_cheap_train = max(cheap_results, key=lambda x: x['train_return'])

    selected_train = top6_train + [best_cheap_train]
    avg_selected_train = np.mean([r['test_return'] for r in selected_train])

    positive_train = [r for r in main_sorted_train if r['test_return'] > 0]
    top5_pos_train = positive_train[:5]
    selected_train_pos = top5_pos_train + [best_cheap_train]
    avg_selected_train_pos = np.mean([r['test_return'] for r in selected_train_pos]) if selected_train_pos else None

    print("\nSelected main tickers (top 6 by train return):")
    for r in top6_train:
        print(f"  {r['ticker']}: Train {r['train_return']:+.2f}%, Test {r['test_return']:+.2f}%")

    print(f"\nSelected cheap ticker (by train): {best_cheap_train['ticker']} (Train {best_cheap_train['train_return']:+.2f}%, Test {best_cheap_train['test_return']:+.2f}%)")
    print(f"Average test return (selected 7): {avg_selected_train:+.2f}%")
    print(f"Estimated $ profit on $200: ${ACCOUNT_BALANCE * avg_selected_train / 100:.2f}")

    if top5_pos_train:
        print("\nSelected main tickers (top 5 positive by test return, train-ranked):")
        for r in top5_pos_train:
            print(f"  {r['ticker']}: Train {r['train_return']:+.2f}%, Test {r['test_return']:+.2f}%")
        print(f"\nSelected cheap ticker (by train): {best_cheap_train['ticker']} (Train {best_cheap_train['train_return']:+.2f}%, Test {best_cheap_train['test_return']:+.2f}%)")
        print(f"Average test return (selected 6): {avg_selected_train_pos:+.2f}%")
        print(f"Estimated $ profit on $200: ${ACCOUNT_BALANCE * avg_selected_train_pos / 100:.2f}")


if __name__ == "__main__":
    main()
