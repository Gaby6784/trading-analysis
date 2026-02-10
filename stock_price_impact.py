#!/usr/bin/env python3
"""
Compare profit per trade: Expensive vs Cheaper stocks
"""

print("=" * 80)
print("PROFIT PER TRADE: Why Stock Price Matters")
print("=" * 80)
print()

ACCOUNT = 200
RISK_PCT = 0.02
RISK_AMOUNT = ACCOUNT * RISK_PCT  # $4
MAX_POSITION_PCT = 0.5
MAX_POSITION = ACCOUNT * MAX_POSITION_PCT  # $100

print(f"Account Size: ${ACCOUNT}")
print(f"Risk Per Trade: {RISK_PCT*100}% = ${RISK_AMOUNT}")
print(f"Max Position Value: {MAX_POSITION_PCT*100}% = ${MAX_POSITION}")
print()

# Scenario 1: META (expensive)
print("=" * 80)
print("SCENARIO 1: META @ $600/share")
print("=" * 80)
stock_price = 600
sl_distance = stock_price * 0.015  # 1.5% SL
position_size_by_risk = RISK_AMOUNT / sl_distance
max_shares_affordable = MAX_POSITION / stock_price
actual_shares = min(position_size_by_risk, max_shares_affordable)
actual_shares = int(actual_shares * 10) / 10  # Round to 0.1

print(f"Entry Price: ${stock_price}")
print(f"SL Distance: ${sl_distance:.2f} (1.5%)")
print(f"Position by Risk: {position_size_by_risk:.2f} shares")
print(f"Max Affordable: {max_shares_affordable:.2f} shares")
print(f"Actual Position: {actual_shares} shares (limited by affordability!)")
print()
print(f"Position Value: ${actual_shares * stock_price:.2f}")
print()

# Calculate profits with 3x R:R
win_per_share = sl_distance * 3
profit_per_win = actual_shares * win_per_share
loss_per_trade = actual_shares * sl_distance

print(f"With 3.0x R:R:")
print(f"  Profit per WIN: ${profit_per_win:.2f}")
print(f"  Loss per LOSS: $-{loss_per_trade:.2f}")
print()

# Scenario 2: Cheaper stock
print("=" * 80)
print("SCENARIO 2: Hypothetical $50 Stock")
print("=" * 80)
stock_price = 50
sl_distance = stock_price * 0.015  # 1.5% SL
position_size_by_risk = RISK_AMOUNT / sl_distance
max_shares_affordable = MAX_POSITION / stock_price
actual_shares = min(position_size_by_risk, max_shares_affordable)
actual_shares = int(actual_shares * 10) / 10  # Round to 0.1

print(f"Entry Price: ${stock_price}")
print(f"SL Distance: ${sl_distance:.2f} (1.5%)")
print(f"Position by Risk: {position_size_by_risk:.2f} shares")
print(f"Max Affordable: {max_shares_affordable:.2f} shares")
print(f"Actual Position: {actual_shares} shares")
print()
print(f"Position Value: ${actual_shares * stock_price:.2f}")
print()

# Calculate profits with 3x R:R
win_per_share = sl_distance * 3
profit_per_win = actual_shares * win_per_share
loss_per_trade = actual_shares * sl_distance

print(f"With 3.0x R:R:")
print(f"  Profit per WIN: ${profit_per_win:.2f}")
print(f"  Loss per LOSS: $-{loss_per_trade:.2f}")
print()

# Scenario 3: With $1000 account
print("=" * 80)
print("SCENARIO 3: META @ $600/share with $1,000 Account")
print("=" * 80)
ACCOUNT = 1000
RISK_AMOUNT = ACCOUNT * RISK_PCT
MAX_POSITION = ACCOUNT * MAX_POSITION_PCT

stock_price = 600
sl_distance = stock_price * 0.015
position_size_by_risk = RISK_AMOUNT / sl_distance
max_shares_affordable = MAX_POSITION / stock_price
actual_shares = min(position_size_by_risk, max_shares_affordable)
actual_shares = int(actual_shares * 10) / 10

print(f"Account: ${ACCOUNT}")
print(f"Risk: ${RISK_AMOUNT}")
print(f"Max Position: ${MAX_POSITION}")
print()
print(f"Entry Price: ${stock_price}")
print(f"Actual Position: {actual_shares} shares")
print(f"Position Value: ${actual_shares * stock_price:.2f}")
print()

win_per_share = sl_distance * 3
profit_per_win = actual_shares * win_per_share
loss_per_trade = actual_shares * sl_distance

print(f"With 3.0x R:R:")
print(f"  Profit per WIN: ${profit_per_win:.2f} ✅ (Now in your $6-8 range!)")
print(f"  Loss per LOSS: $-{loss_per_trade:.2f}")
print()

print("=" * 80)
print("CONCLUSION")
print("=" * 80)
print()
print("To make $6-8 profit per winning trade, you need EITHER:")
print("  1. Trade stocks under $100/share (like AMD, INTC)")
print("  2. Increase account to $1,000+ to afford more shares")
print()
print("Your current tickers are TOO EXPENSIVE for a $200 account!")
