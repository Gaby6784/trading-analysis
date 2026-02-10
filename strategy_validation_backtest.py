#!/usr/bin/env python3
"""
Strategy Validation Backtest - Test converted strategy performance
Validates the Pine Strategy conversion maintains good performance
Tests with optimized settings: 2.5x R:R, fixed SL/TP, 6-ticker subset
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_bollinger_bands(prices, period=20, std_dev=2):
    """Calculate Bollinger Bands"""
    sma = prices.rolling(window=period).mean()
    rolling_std = prices.rolling(window=period).std()
    upper_band = sma + (rolling_std * std_dev)
    lower_band = sma - (rolling_std * std_dev)
    return upper_band, sma, lower_band

def get_signal_strength(rsi, bb_upper, bb_lower, close):
    """Determine signal strength based on RSI and BB position"""
    # Convert to scalar values if they are Series
    if hasattr(rsi, 'iloc'):
        rsi = rsi.iloc[0] if len(rsi) > 0 else rsi
    if hasattr(bb_upper, 'iloc'):
        bb_upper = bb_upper.iloc[0] if len(bb_upper) > 0 else bb_upper
    if hasattr(bb_lower, 'iloc'):
        bb_lower = bb_lower.iloc[0] if len(bb_lower) > 0 else bb_lower
    if hasattr(close, 'iloc'):
        close = close.iloc[0] if len(close) > 0 else close
    
    # Check for NaN values
    if pd.isna(rsi) or pd.isna(bb_upper) or pd.isna(bb_lower) or pd.isna(close):
        return 'NO_SIGNAL'
    
    bb_position = (close - bb_lower) / (bb_upper - bb_lower) * 100
    
    # Buy signals
    if rsi <= 20 and bb_position <= 5:  # Strong oversold
        return 'STRONG_BUY'
    elif rsi <= 30 and bb_position <= 20:  # Moderate oversold
        return 'MODERATE_BUY'
    
    # Sell signals  
    elif rsi >= 80 and bb_position >= 95:  # Strong overbought
        return 'STRONG_SELL'
    elif rsi >= 70 and bb_position >= 80:  # Moderate overbought
        return 'MODERATE_SELL'
    
    return 'NO_SIGNAL'

def calculate_position_size(account_balance, risk_per_trade, stop_loss_distance, price):
    """Calculate position size based on risk management"""
    risk_amount = account_balance * (risk_per_trade / 100)
    if stop_loss_distance > 0:
        units = risk_amount / stop_loss_distance
        return min(units, account_balance / price)  # Don't exceed account balance
    return 0

def backtest_strategy(symbol, start_date, end_date, initial_balance=200):
    """Backtest strategy on single symbol with optimized settings"""
    print(f"\n📊 Testing {symbol}...")
    
    # Download data
    try:
        data = yf.download(symbol, start=start_date, end=end_date, progress=False)
        if data.empty:
            return None
    except:
        print(f"❌ Failed to download data for {symbol}")
        return None
    
    # Calculate indicators
    data['RSI'] = calculate_rsi(data['Close'])
    data['BB_Upper'], data['BB_Middle'], data['BB_Lower'] = calculate_bollinger_bands(data['Close'])
    
    # Calculate signals (handle NaN values)
    signals = []
    for i in range(len(data)):
        rsi_val = data['RSI'].iloc[i]
        bb_upper = data['BB_Upper'].iloc[i]
        bb_lower = data['BB_Lower'].iloc[i]
        close_val = data['Close'].iloc[i]
        
        if pd.isna(rsi_val) or pd.isna(bb_upper) or pd.isna(bb_lower):
            signals.append('NO_SIGNAL')
        else:
            signals.append(get_signal_strength(rsi_val, bb_upper, bb_lower, close_val))
    
    data['Signal'] = signals
    
    # Strategy parameters (optimized from previous tests)
    account_balance = initial_balance
    risk_per_trade = 2.0  # 2% risk per trade
    risk_reward_ratio = 2.5  # 2.5:1 R:R ratio
    use_trailing_sl = False  # Fixed SL/TP performs better
    
    # Track trades and performance
    trades = []
    position = None
    equity_curve = [account_balance]
    
    for i in range(1, len(data)):
        current_price = data.iloc[i]['Close']
        current_signal = data.iloc[i]['Signal']  # Get scalar value from Series
        
        # Exit existing position first
        if position:
            # Check for exit conditions
            exit_trade = False
            exit_reason = ""
            exit_price = current_price
            
            if position['side'] == 'LONG':
                if current_price <= position['stop_loss']:
                    exit_trade = True
                    exit_reason = "Stop Loss"
                    exit_price = position['stop_loss']
                elif current_price >= position['take_profit']:
                    exit_trade = True
                    exit_reason = "Take Profit" 
                    exit_price = position['take_profit']
            else:  # SHORT
                if current_price >= position['stop_loss']:
                    exit_trade = True
                    exit_reason = "Stop Loss"
                    exit_price = position['stop_loss']
                elif current_price <= position['take_profit']:
                    exit_trade = True
                    exit_reason = "Take Profit"
                    exit_price = position['take_profit']
            
            if exit_trade:
                # Calculate P&L
                if position['side'] == 'LONG':
                    pnl = (exit_price - position['entry_price']) * position['units']
                else:
                    pnl = (position['entry_price'] - exit_price) * position['units']
                
                account_balance += pnl
                
                trades.append({
                    'Symbol': symbol,
                    'Entry_Date': position['entry_date'],
                    'Exit_Date': data.index[i],
                    'Side': position['side'],
                    'Entry_Price': position['entry_price'],
                    'Exit_Price': exit_price,
                    'Units': position['units'],
                    'PnL': pnl,
                    'Return_%': (pnl / (position['entry_price'] * position['units'])) * 100,
                    'Exit_Reason': exit_reason
                })
                
                position = None
        
        # Look for new entry signals (only if no position)
        if not position and current_signal in ['STRONG_BUY', 'MODERATE_BUY', 'STRONG_SELL', 'MODERATE_SELL']:
            
            if current_signal in ['STRONG_BUY', 'MODERATE_BUY']:
                # Long position
                stop_loss = current_price * 0.975  # 2.5% stop loss
                stop_distance = current_price - stop_loss
                take_profit = current_price + (stop_distance * risk_reward_ratio)
                
                units = calculate_position_size(account_balance, risk_per_trade, stop_distance, current_price)
                
                if units > 0:
                    position = {
                        'side': 'LONG',
                        'entry_date': data.index[i],
                        'entry_price': current_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'units': units
                    }
            
            elif current_signal in ['STRONG_SELL', 'MODERATE_SELL']:
                # Short position  
                stop_loss = current_price * 1.025  # 2.5% stop loss
                stop_distance = stop_loss - current_price
                take_profit = current_price - (stop_distance * risk_reward_ratio)
                
                units = calculate_position_size(account_balance, risk_per_trade, stop_distance, current_price)
                
                if units > 0:
                    position = {
                        'side': 'SHORT',
                        'entry_date': data.index[i], 
                        'entry_price': current_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'units': units
                    }
        
        equity_curve.append(account_balance)
    
    # Calculate performance metrics
    total_return = ((account_balance - initial_balance) / initial_balance) * 100
    
    if trades:
        trades_df = pd.DataFrame(trades)
        winning_trades = trades_df[trades_df['PnL'] > 0]
        losing_trades = trades_df[trades_df['PnL'] < 0]
        
        win_rate = len(winning_trades) / len(trades_df) * 100
        avg_win = winning_trades['Return_%'].mean() if len(winning_trades) > 0 else 0
        avg_loss = losing_trades['Return_%'].mean() if len(losing_trades) > 0 else 0
        
        results = {
            'Symbol': symbol,
            'Total_Return_%': total_return,
            'Final_Balance': account_balance,
            'Total_Trades': len(trades_df),
            'Win_Rate_%': win_rate,
            'Avg_Win_%': avg_win,
            'Avg_Loss_%': avg_loss,
            'Winning_Trades': len(winning_trades),
            'Losing_Trades': len(losing_trades)
        }
        
        print(f"✅ {symbol}: {total_return:.2f}% return, {len(trades_df)} trades, {win_rate:.1f}% win rate")
        return results
    else:
        print(f"⚠️  {symbol}: No trades generated")
        return {
            'Symbol': symbol,
            'Total_Return_%': 0,
            'Final_Balance': initial_balance,
            'Total_Trades': 0,
            'Win_Rate_%': 0,
            'Avg_Win_%': 0,
            'Avg_Loss_%': 0,
            'Winning_Trades': 0,
            'Losing_Trades': 0
        }

def main():
    print("🚀 STRATEGY VALIDATION BACKTEST")
    print("=" * 50)
    print("Testing converted Pine Strategy performance")
    print("Settings: 2.5x R:R, Fixed SL/TP, 2% risk per trade")
    
    # Optimized 6-ticker subset from previous tests
    tickers = ['NVDA', 'META', 'MSFT', 'NFLX', 'AAPL', 'PUBM']
    
    # Test period: 2 years (1 year train, 1 year test)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)  # 2 years
    split_date = end_date - timedelta(days=365)  # 1 year ago
    
    print(f"📅 Training Period: {start_date.strftime('%Y-%m-%d')} to {split_date.strftime('%Y-%m-%d')}")
    print(f"📅 Testing Period: {split_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # Test on training period
    print(f"\n🔬 TRAINING PERIOD RESULTS")
    print("-" * 30)
    train_results = []
    for symbol in tickers:
        result = backtest_strategy(symbol, start_date, split_date)
        if result:
            train_results.append(result)
    
    # Test on out-of-sample period
    print(f"\n📊 OUT-OF-SAMPLE TEST RESULTS")
    print("-" * 30)
    test_results = []
    for symbol in tickers:
        result = backtest_strategy(symbol, split_date, end_date)
        if result:
            test_results.append(result)
    
    # Summary statistics
    if train_results:
        train_df = pd.DataFrame(train_results)
        print(f"\n📈 TRAINING PERIOD SUMMARY")
        print(f"Average Return: {train_df['Total_Return_%'].mean():.2f}%")
        print(f"Best Performer: {train_df.loc[train_df['Total_Return_%'].idxmax()]['Symbol']} ({train_df['Total_Return_%'].max():.2f}%)")
        print(f"Total Trades: {train_df['Total_Trades'].sum()}")
        print(f"Average Win Rate: {train_df['Win_Rate_%'].mean():.1f}%")
    
    if test_results:
        test_df = pd.DataFrame(test_results)
        print(f"\n🎯 OUT-OF-SAMPLE TEST SUMMARY")
        print(f"Average Return: {test_df['Total_Return_%'].mean():.2f}%")
        print(f"Best Performer: {test_df.loc[test_df['Total_Return_%'].idxmax()]['Symbol']} ({test_df['Total_Return_%'].max():.2f}%)")
        print(f"Worst Performer: {test_df.loc[test_df['Total_Return_%'].idxmin()]['Symbol']} ({test_df['Total_Return_%'].min():.2f}%)")
        print(f"Total Trades: {test_df['Total_Trades'].sum()}")
        print(f"Average Win Rate: {test_df['Win_Rate_%'].mean():.1f}%")
        print(f"Profitable Tickers: {len(test_df[test_df['Total_Return_%'] > 0])}/{len(test_df)}")
    
    print(f"\n✅ STRATEGY VALIDATION COMPLETE")
    
    # Save detailed results
    if test_results:
        test_df = pd.DataFrame(test_results)
        test_df.to_csv('strategy_validation_results.csv', index=False)
        print(f"📁 Detailed results saved to: strategy_validation_results.csv")

if __name__ == "__main__":
    main()