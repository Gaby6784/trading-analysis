import pandas as pd

df = pd.read_csv('backtest_results_detailed.csv')

print('🔍 Analyzing RSI at entry:')
print(f'   Average RSI: {df["rsi"].mean():.1f}')
print(f'   Oversold (RSI<30): {len(df[df["rsi"]<30])} trades')
print(f'   Overbought (RSI>70): {len(df[df["rsi"]>70])} trades')
print()

# Compare oversold vs overbought
oversold = df[df['rsi'] < 30]
overbought = df[df['rsi'] > 70]

print(f'📊 Oversold (RSI<30) Performance:')
print(f'   Trades: {len(oversold)}')
if len(oversold) > 0:
    print(f'   Win Rate: {oversold["win"].mean()*100:.1f}%')
    print(f'   Avg P&L: ${oversold["pnl"].mean():.2f}')
print()

print(f'📊 Overbought (RSI>70) Performance:')
print(f'   Trades: {len(overbought)}')
if len(overbought) > 0:
    print(f'   Win Rate: {overbought["win"].mean()*100:.1f}%')
    print(f'   Avg P&L: ${overbought["pnl"].mean():.2f}')
print()

# Show which RSI ranges won
print('📈 Win Rate by RSI Range:')
ranges = [
    (0, 20, 'Extreme Oversold'),
    (20, 30, 'Oversold'),
    (30, 50, 'Neutral-Low'),
    (50, 70, 'Neutral-High'),
    (70, 100, 'Overbought')
]

for rsi_min, rsi_max, label in ranges:
    subset = df[(df['rsi'] >= rsi_min) & (df['rsi'] < rsi_max)]
    if len(subset) > 0:
        win_rate = subset["win"].mean() * 100
        avg_pnl = subset["pnl"].mean()
        print(f'   {label:20s} (RSI {rsi_min:2d}-{rsi_max:2d}): {len(subset):2d} trades, {win_rate:4.1f}% win, ${avg_pnl:+6.2f} avg')
