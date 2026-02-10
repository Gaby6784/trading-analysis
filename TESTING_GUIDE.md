# 🚀 Forward Testing & Backtesting Guide

## Overview

You now have two powerful testing tools:
1. **Backtest** - Analyze past trades to validate scoring
2. **Forward Test** - Paper trade scoring system in real-time

---

## 📊 Backtesting Historical Trades

### Quick Start
```bash
python3 backtest_scoring_system.py AMZN_trades_FINAL_OPTIMIZED.csv
```

### What It Does
- Calculates what score each historical trade would have received
- Shows performance by score bucket (STRONG_BUY, BUY, CAUTION, AVOID)
- Analyzes filter impact (what if you only traded >65 scores?)
- Identifies which trades would have been filtered out
- Creates visualization (score_vs_pnl.png)

### Key Findings from Your Data
```
Overall: 44.7% win rate, $21.46 total P&L
- Overbought entries (RSI>70): 45% win rate - would be filtered
- Oversold entries (RSI<30): 44% win rate - need trend confirmation
- Missing data: trend, BB status, sentiment
```

**Insight:** RSI alone is NOT enough. Need RSI + Trend + BB together.

---

## 🎯 Forward Testing (Paper Trading)

### Single Scan (Check Now)
```bash
python3 forward_test_simulation.py --score-threshold 65
```

Shows current opportunities based on scoring system.

### Continuous Mode (Real-Time Paper Trading)
```bash
python3 forward_test_simulation.py --score-threshold 65 --continuous --interval 30
```

Scans every 30 minutes, enters paper trades automatically.

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `--score-threshold` | Minimum score to enter (50-100) | 65 |
| `--max-positions` | Max concurrent trades | 3 |
| `--position-size` | $ amount per trade | 100 |
| `--continuous` | Run continuously | False |
| `--interval` | Scan interval (minutes) | 30 |

### Examples

**Conservative (only best setups):**
```bash
python3 forward_test_simulation.py --score-threshold 75 --max-positions 2
```

**Aggressive (more opportunities):**
```bash
python3 forward_test_simulation.py --score-threshold 60 --max-positions 5
```

**Day trading (frequent scans):**
```bash
python3 forward_test_simulation.py --continuous --interval 15
```

---

## 📈 How Forward Testing Works

### 1. **Entry Logic**
When a ticker scores above threshold:
- ✅ Enters paper trade at current price
- ✅ Sets stop loss: `entry - (1.5 × ATR)`
- ✅ Sets take profit: `entry + (2.5 × ATR)` (1.67:1 R:R)
- ✅ Tracks all entry conditions (RSI, trend, BB, sentiment)

### 2. **Exit Logic**
Exits when:
- 🔴 Price hits stop loss
- 🟢 Price hits take profit
- ⏰ 3 days pass (time-based exit)

### 3. **Position Updates**
Every scan:
- Updates all open positions with current price
- Shows unrealized P&L
- Checks exit conditions
- Logs all activity

---

## 📊 Output & Results

### Console Output
```
================================================================================
🔍 SCANNING FOR SIGNALS - 2026-02-10 09:30 ET
================================================================================
   ✅ NVDA: Score 78 - QUALIFIED
   ⏭️  META: Score 42 - Below threshold
   ⏭️  AMZN: Score 55 - Below threshold

🟢 ENTERED TRADE:
   Ticker: NVDA
   Entry: $189.50
   Score: 78/100
   Stop Loss: $185.30 (-2.2%)
   Take Profit: $197.25 (+4.1%)
   Position Size: $100.00

📊 SIMULATION SUMMARY
Closed Trades: 5
Win Rate: 60.0% (3W / 2L)
Total P&L: $+12.45
Open Positions: 1
```

### Log Files Generated

**JSON Log:** `forward_test_YYYYMMDD_HHMMSS.json`
- Complete trade history
- Entry/exit details
- Score breakdowns

**CSV Export:** `forward_test_YYYYMMDD_HHMMSS.csv`
- Easy to analyze in Excel
- Import into backtesting tools
- Track long-term performance

---

## 🎯 Recommended Workflows

### Workflow 1: Validate Scoring (1 Week)
```bash
# Run continuous mode for a week
python3 forward_test_simulation.py --score-threshold 65 --continuous --interval 60

# After 1 week, analyze results
python3 backtest_scoring_system.py forward_test_20260210_120000.csv
```

**Goal:** Validate scoring system predicts winners before risking real money.

---

### Workflow 2: Optimize Threshold
Test different thresholds in parallel:

**Terminal 1 (Conservative):**
```bash
python3 forward_test_simulation.py --score-threshold 75 --continuous
```

**Terminal 2 (Moderate):**
```bash
python3 forward_test_simulation.py --score-threshold 65 --continuous
```

**Terminal 3 (Aggressive):**
```bash
python3 forward_test_simulation.py --score-threshold 55 --continuous
```

After 2 weeks, compare which threshold performed best.

---

### Workflow 3: Daily Morning Scan
Add to your daily routine:

```bash
# Morning scan (9:30 AM ET)
python3 forward_test_simulation.py --score-threshold 70

# Review results
cat forward_test_*.csv | grep "QUALIFIED"
```

---

## 📊 Performance Metrics

The simulator tracks:

| Metric | Description |
|--------|-------------|
| **Win Rate** | % of trades that profit |
| **Total P&L** | Cumulative profit/loss |
| **Profit Factor** | Gross profit / gross loss |
| **Avg Win** | Average winning trade size |
| **Avg Loss** | Average losing trade size |
| **Trade Frequency** | Trades per day/week |

### Success Criteria
- ✅ Win rate > 55% (with 1.5:1 R:R)
- ✅ Profit factor > 1.5
- ✅ Score correlation > 0.3
- ✅ Avg win > 1.5 × avg loss

---

## 🔍 Analyzing Results

### After Collecting Forward Test Data

**1. Run backtest on forward test results:**
```bash
python3 backtest_scoring_system.py forward_test_20260210_120000.csv
```

**2. Compare score buckets:**
```
STRONG_BUY (75+): X% win rate
BUY (65-74): Y% win rate
```

**3. Adjust threshold based on results:**
- If 75+ scores win >60%: Use threshold 75
- If 65+ scores win >55%: Use threshold 65
- If all scores similar: Optimize weights with scoring_optimizer.py

---

## ⚠️ Important Notes

### Limitations
- ❌ **Not real fills** - assumes you get exact entry price
- ❌ **No slippage** - real trades have execution costs
- ❌ **No overnight gaps** - gaps can blow through stops
- ❌ **Limited to configured tickers** - edit config.py to add more

### Best Practices
- ✅ Run for at least 20 trades before drawing conclusions
- ✅ Paper trade for 1-2 weeks minimum
- ✅ Compare forward test results to backtest
- ✅ Start with conservative threshold (70+)
- ✅ Gradually lower threshold as you validate performance

---

## 🚀 Next Steps

### Phase 1: Validation (Week 1-2)
```bash
# Run continuous forward test
python3 forward_test_simulation.py --score-threshold 70 --continuous
```
**Goal:** 10+ paper trades, >55% win rate

### Phase 2: Optimization (Week 3-4)
```bash
# Optimize weights from forward test results
python3 scoring_optimizer.py --input forward_test_results.csv

# Apply optimized weights to scoring_config.py
```
**Goal:** Find optimal threshold and weights

### Phase 3: Small Real Money (Week 5+)
- Start with $50 per trade
- Only trade scores >75
- Track results and compare to paper trading

---

## 📝 Quick Reference Commands

```bash
# Check current opportunities
python3 run_scored_analysis.py

# Single forward test scan
python3 forward_test_simulation.py --score-threshold 65

# Start paper trading (continuous)
python3 forward_test_simulation.py --score-threshold 70 --continuous --interval 30

# Backtest historical trades
python3 backtest_scoring_system.py AMZN_trades_FINAL_OPTIMIZED.csv

# Optimize weights after collecting data
python3 scoring_optimizer.py --input forward_test_results.csv

# Analyze RSI performance
python3 analyze_rsi_performance.py
```

---

## 💡 Tips for Success

1. **Be Patient** - scoring system correctly shows NO trades when nothing qualifies
2. **Trust the Filters** - if score <65, there's a reason (RSI high, wrong trend, etc.)
3. **Track Everything** - forward test logs give you data to optimize
4. **Compare to Old Strategy** - your old 44% win rate vs new system
5. **Iterate** - use optimizer after 20+ forward test trades

---

## 🎯 Success Story Example

**Week 1-2:** Paper trade, 15 trades @ 65+ threshold → 47% win rate
**Week 3:** Raise threshold to 70+ → 12 trades → 58% win rate
**Week 4:** Optimize weights with scoring_optimizer.py
**Week 5:** Test optimized system → 67% win rate
**Week 6+:** Use real money with validated system ✅

---

Good luck! The system will only signal trades when conditions truly align. Be disciplined and wait for high scores! 🚀
