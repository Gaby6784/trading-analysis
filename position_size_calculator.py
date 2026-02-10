#!/usr/bin/env python3
"""
Position Size Calculator - CLI Tool
====================================
Calculates the exact number of shares to buy based on 1% risk management.

Usage:
    python3 position_size_calculator.py
    
    Then enter:
    - Your total account balance
    - Current stock price
    - Your stop-loss price

Risk Formula:
- Risk per share = Entry Price - Stop Loss Price
- Max risk (1% of account) = Account Balance × 0.01
- Position size = Max risk ÷ Risk per share (rounded down)

Example:
    Account: $10,000
    Stock Price: $150
    Stop Loss: $147
    → Buy 33 shares (risking $99 or 0.99%)
"""

import math


def calculate_position_size(account_balance, entry_price, stop_loss_price, risk_percent=0.01):
    """
    Calculate position size based on risk management.
    
    Args:
        account_balance: Total account balance
        entry_price: Current stock price (entry point)
        stop_loss_price: Stop loss price
        risk_percent: Risk per trade as decimal (default 0.01 = 1%)
    
    Returns:
        dict: Position sizing details
    """
    # Calculate risk per share
    risk_per_share = entry_price - stop_loss_price
    
    # Validation
    if risk_per_share <= 0:
        return {
            'error': 'Stop loss must be below entry price',
            'risk_per_share': risk_per_share
        }
    
    # Calculate maximum risk amount (1% of account)
    max_risk_amount = account_balance * risk_percent
    
    # Calculate maximum shares (before rounding)
    max_shares_exact = max_risk_amount / risk_per_share
    
    # Round down to nearest whole share
    shares_to_buy = math.floor(max_shares_exact)
    
    # Calculate actual cost and risk
    total_cost = shares_to_buy * entry_price
    actual_risk = shares_to_buy * risk_per_share
    
    # Calculate percentages
    risk_pct = (actual_risk / account_balance * 100) if account_balance > 0 else 0
    position_pct = (total_cost / account_balance * 100) if account_balance > 0 else 0
    
    return {
        'shares_to_buy': shares_to_buy,
        'total_cost': total_cost,
        'actual_risk': actual_risk,
        'risk_percent': risk_pct,
        'position_percent': position_pct,
        'risk_per_share': risk_per_share,
        'max_risk_amount': max_risk_amount,
        'remaining_cash': account_balance - total_cost
    }


def format_currency(amount):
    """Format number as currency with 2 decimal places."""
    return f"${amount:,.2f}"


def main():
    """Main CLI interface."""
    print("=" * 60)
    print("POSITION SIZE CALCULATOR")
    print("=" * 60)
    print("Calculate how many shares to buy with 1% account risk\n")
    
    try:
        # Get user inputs
        account_balance = float(input("Enter your total account balance: $"))
        entry_price = float(input("Enter the current stock price: $"))
        stop_loss_price = float(input("Enter your stop-loss price: $"))
        
        # Validate inputs
        if account_balance <= 0:
            print("\n❌ Error: Account balance must be positive")
            return
        
        if entry_price <= 0:
            print("\n❌ Error: Stock price must be positive")
            return
        
        if stop_loss_price <= 0:
            print("\n❌ Error: Stop loss price must be positive")
            return
        
        # Calculate position size
        result = calculate_position_size(account_balance, entry_price, stop_loss_price)
        
        # Check for errors
        if 'error' in result:
            print(f"\n❌ Error: {result['error']}")
            print(f"   Entry Price: {format_currency(entry_price)}")
            print(f"   Stop Loss: {format_currency(stop_loss_price)}")
            return
        
        # Display results
        print("\n" + "=" * 60)
        print("POSITION SIZE CALCULATION")
        print("=" * 60)
        
        print(f"\nAccount Details:")
        print(f"  Account Balance:     {format_currency(account_balance)}")
        print(f"  Max Risk (1%):       {format_currency(result['max_risk_amount'])}")
        
        print(f"\nTrade Parameters:")
        print(f"  Entry Price:         {format_currency(entry_price)}")
        print(f"  Stop Loss Price:     {format_currency(stop_loss_price)}")
        print(f"  Risk per Share:      {format_currency(result['risk_per_share'])}")
        print(f"  Stop Loss Distance:  {((entry_price - stop_loss_price) / entry_price * 100):.2f}%")
        
        print(f"\n{'🎯 RECOMMENDED POSITION:':^60}")
        print("=" * 60)
        print(f"  Shares to Buy:       {result['shares_to_buy']} shares")
        print(f"  Total Cost:          {format_currency(result['total_cost'])}")
        print(f"  Actual Risk:         {format_currency(result['actual_risk'])} ({result['risk_percent']:.2f}%)")
        print(f"  Position Size:       {result['position_percent']:.2f}% of account")
        print(f"  Remaining Cash:      {format_currency(result['remaining_cash'])}")
        
        if result['shares_to_buy'] == 0:
            print("\n⚠️  WARNING: Cannot afford even 1 share with 1% risk management")
            print("   Consider:")
            print("   • Using a tighter stop loss")
            print("   • Waiting for a better entry price")
            print("   • Trading a lower-priced stock")
        elif result['remaining_cash'] < 0:
            print("\n⚠️  WARNING: Insufficient funds for this position")
        else:
            print("\n✅ Position meets 1% risk management criteria")
        
        print("\n" + "=" * 60 + "\n")
        
    except ValueError:
        print("\n❌ Error: Please enter valid numbers")
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
