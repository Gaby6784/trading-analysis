# 🎯 Advanced Scoring System for Trade Quality Assessment

## Overview

This scoring system rates each trading opportunity 0-100 based on **five key components**, helping you focus on high-probability setups and avoid low-quality trades.

## Quick Start

### Run Analysis With Scoring

```bash
python3 run_scored_analysis.py
```

This will analyze your tickers and display scores like:
```
📊 Analyzing NVDA...
   🟢 SCORE: 78.5/100 (BUY)
   
📊 SCORED ANALYSIS RESULTS
╒══════╤═════╤═════════════╤═════════╤═════╤════════════╤═══════╤══════╤════════════════════════╕
│ Ticker│ Score│ Category   │ Price   │ RSI │ BB Status  │ Sent  │ News │ Recommendation         │
╞══════╪═════╪═════════════╪═════════╪═════╪════════════╪═══════╪══════╪════════════════════════╡
│ NVDA  │ 78  │ STRONG_BUY │ $145.23 │ 25  │ BELOW_LOWER│ +0.65 │ 12   │ 🟢 STRONG BUY          │
│ META  │ 68  │ BUY        │ $520.11 │ 28  │ LOWER_HALF │ +0.42 │ 8    │ 🟢 BUY                 │
```

---

## How It Works

### 📊 Score Components & Weights

```python
WEIGHTS = {
    'technical': 0.30,    # RSI, Bollinger Bands, MACD
    'sentiment': 0.25,    # News sentiment (-1 to +1)
    'momentum': 0.20,     # Trend, volatility
    'catalyst': 0.15,     # News recency & volume
    'timing': 0.10        # Time of day
}
```

### 🎯 Score Interpretation

| Score Range | Category | Meaning |
|------------|----------|---------|
| **75-100** | 🟢 STRONG BUY | Very high conviction - multiple confirmations |
| **65-74** | 🟢 BUY | High conviction - good setup |
| **50-64** | 🟡 CAUTION | Mixed signals - proceed carefully |
| **35-49** | 🟠 AVOID | Weak setup - wait for better entry |
| **0-34** | 🔴 STRONG AVOID | Very low quality - stay away |

---

## Component Breakdown

### 1. Technical Score (30%)

**What it measures:**
- RSI position (oversold = high score)
- Bollinger Band location
- MACD histogram direction

**Scoring:**
- **40 pts max**: RSI component
  - RSI ≤ 15: Perfect (40 pts)
  - RSI ≤ 30: Strong (30-35 pts)
  - RSI 30-40: Good (20-30 pts)
  - RSI > 70: Poor (0-5 pts)

- **35 pts max**: Bollinger Band
  - Below lower band: 100%
  - Lower half: 70%
  - Upper half: 30%
  - Above upper: 20%

- **25 pts max**: MACD momentum
  - Strong bullish: 25 pts
  - Slightly bullish: 15 pts
  - Bearish: 0-10 pts

### 2. Sentiment Score (25%)

**What it measures:**
- News sentiment quality
- Number of articles (confidence)

**Scoring:**
- Very positive (≥0.8): 70 pts
- Positive (≥0.5): 50 pts
- Neutral (0): 30 pts
- Negative (<0): Penalized 2x

**Note:** Negative sentiment with bullish technicals triggers "NEWS RISK" penalty

### 3. Momentum Score (20%)

**What it measures:**
- Trend direction (EMA alignment)
- Volatility (ATR as % of price)

**Scoring:**
- Uptrend: 100 → 60 pts
- Sideways: 60 → 36 pts
- Downtrend: 20 → 12 pts

**Volatility sweet spot:** 3% ATR
- Too low: Less opportunity
- Too high (>8%): Dangerous

### 4. Catalyst Score (15%)

**What it measures:**
- News freshness
- News volume quality

**Scoring:**
- Very fresh (<6h): Max points
- Recent (<12h): Good points
- Stale (>24h): Reduced points

**Optimal:** 8+ articles, <12 hours old

### 5. Timing Score (10%)

**What it measures:**
- Time of day (ET)

**Scoring:**
- 9:30-10:30 AM ET: 100 pts (optimal)
- 10:30-15:00 ET: 80 pts (good)
- 15:30-16:00 ET: 40 pts (power hour volatility)
- Premarket: 50 pts
- After hours: 30 pts

---

## Penalties & Bonuses

### ⚠️ Penalties (Reduce Score)

| Condition | Penalty | Reason |
|-----------|---------|--------|
| **Falling Knife** | -50% | Oversold + downtrend + negative MACD |
| **News Risk** | -40% | Bearish sentiment despite bullish technicals |
| **Earnings Soon** | -20% | Earnings within 7 days |
| **Wide Stops** | -15% | ATR > 8% of price |
| **Insufficient Data** | -70% | Not enough candles for reliable signals |

### ⭐ Bonuses (Increase Score)

| Condition | Bonus | Reason |
|-----------|-------|--------|
| **Strong Confluence** | +15% | All signals aligned perfectly |
| **Oversold Uptrend** | +12% | Pullback in strong uptrend |
| **Fresh Catalyst** | +10% | Breaking news (<6h) |

---

## Optimization

### Tune Weights Based on Your Results

Once you have 20+ trades, optimize weights:

```bash
python3 scoring_optimizer.py --input AMZN_trades_FINAL_OPTIMIZED.csv
```

**Input CSV needs columns:**
- `ticker`: Stock symbol
- `pnl`: Profit/loss
- `rsi`: RSI at entry
- `sentiment`: Sentiment score
- `trend`: Trend at entry
- `bb_status`: Bollinger band position

**Output:**
```
📊 Weight Comparison:
Component       Original     Optimal      Change      
technical       0.300        0.350        +0.050
sentiment       0.250        0.280        +0.030
momentum        0.200        0.150        -0.050
...

💡 Improvement: 23.4%
```

Apply the suggested weights to `scoring_config.py`:

```python
WEIGHTS = {
    'technical': 0.350,
    'sentiment': 0.280,
    'momentum': 0.150,
    'catalyst': 0.140,
    'timing': 0.080
}
```

---

## Configuration

Edit `premarket_analysis/scoring_config.py` to tune:

### Score Thresholds
```python
SCORE_STRONG_BUY = 75       # Require 75+ for highest conviction
SCORE_BUY = 65              # Good setups
SCORE_CAUTION = 50          # Mixed signals
```

### Component Parameters
```python
RSI_PERFECT_OVERSOLD = 15   # Extremely oversold
VOLATILITY_OPTIMAL = 3.0    # Sweet spot ATR %
NEWS_FRESH = 6              # Hours for "fresh" news
```

### Penalties
```python
PENALTY_FALLING_KNIFE = 0.5     # 50% reduction
PENALTY_NEWS_RISK = 0.6         # 40% reduction
BONUS_STRONG_CONFLUENCE = 1.15  # 15% bonus
```

---

## Integration with Existing Code

The scoring system is **non-invasive** - your original files remain unchanged:

### Files Created:
```
premarket_analysis/
  ├── scoring.py              # Core scoring engine
  ├── scoring_config.py       # Tunable parameters
  └── main_with_scoring.py    # New entrypoint with scoring

run_scored_analysis.py        # Convenience runner
scoring_optimizer.py          # Weight optimization tool
```

### Original Files (Untouched):
```
premarket_analysis/
  ├── main.py                 # Original analysis
  ├── recommendation.py       # Original recommendation logic
  ├── config.py              # Original config
  └── ...                    # All other modules
```

You can still run the original analysis:
```bash
python3 premarket_analysis_v2.py  # Original
```

Or use the new scored version:
```bash
python3 run_scored_analysis.py    # With scoring
```

---

## Advanced Usage

### Debug Mode (See Component Breakdown)

Edit `premarket_analysis/config.py`:
```python
LOG_LEVEL = "DEBUG"
```

Output will show:
```
📊 Analyzing NVDA...
   🟢 SCORE: 78.5/100 (BUY)
   └─ Components: Tech=85, Sent=72, Mom=65, Cat=80, Time=100
   └─ Adjustments: OVERSOLD_UPTREND: +12%, FRESH_CATALYST: +10%
```

### Filter by Score in Your Code

```python
from premarket_analysis.main_with_scoring import analyze_ticker_with_scoring

result = analyze_ticker_with_scoring('NVDA')

if result['score'] >= 75:
    print(f"🟢 STRONG BUY at {result['price']}")
    # Execute your trade logic...
elif result['score'] >= 65:
    print(f"🟢 BUY with caution")
else:
    print(f"⚠️ Skip - score too low ({result['score']})")
```

### Batch Analysis with Score Filtering

```python
from premarket_analysis.main_with_scoring import analyze_ticker_with_scoring
from premarket_analysis.config import TICKERS

high_conviction_trades = []

for ticker in TICKERS:
    result = analyze_ticker_with_scoring(ticker)
    
    if result['score'] >= 70 and result.get('score_quality_flags') == []:
        high_conviction_trades.append({
            'ticker': ticker,
            'score': result['score'],
            'price': result['price'],
            'stop': result['suggested_stop']
        })

# Sort by score
high_conviction_trades.sort(key=lambda x: x['score'], reverse=True)

print(f"Found {len(high_conviction_trades)} high-quality setups")
```

---

## Example Score Calculation

**Scenario:** NVDA at $145, RSI 25, below lower BB, positive sentiment

```
Technical Score:
  RSI (25):         35/40 pts
  BB (below):       35/35 pts  
  MACD (+0.005):    20/25 pts
  ───────────────────────────
  Total:            90/100 pts → 90 * 0.30 = 27.0

Sentiment Score:
  Sentiment (+0.6): 60/70 pts
  News count (10):  28/30 pts
  ───────────────────────────
  Total:            88/100 pts → 88 * 0.25 = 22.0

Momentum Score:
  Trend (uptrend):  60/60 pts
  Volatility (3%):  40/40 pts
  ───────────────────────────
  Total:            100/100 pts → 100 * 0.20 = 20.0

Catalyst Score:
  Recency (8h):     50/60 pts
  Volume (10):      35/40 pts
  ───────────────────────────
  Total:            85/100 pts → 85 * 0.15 = 12.75

Timing Score:
  Time (9:45 AM):   100/100 pts → 100 * 0.10 = 10.0
  
═══════════════════════════════════════
BASE SCORE:                            91.75

Adjustments:
  + Oversold Uptrend Bonus:    +12%
  + Fresh Catalyst Bonus:      +10%
  
═══════════════════════════════════════
FINAL SCORE:                           100.0 (capped)

Category: 🟢 STRONG BUY
```

---

## Tips for Best Results

### 1. **Start Conservative**
- Initially only trade scores ≥75
- Gradually lower threshold as you validate performance

### 2. **Track Everything**
- Log every trade with entry score
- After 20+ trades, run optimizer
- Continuously refine weights

### 3. **Watch for Quality Flags**
```python
if result['score_quality_flags']:
    print(f"⚠️ Quality issues: {result['score_quality_flags']}")
    # Consider skipping trade
```

### 4. **Combine with Position Sizing**
```python
# Risk more on higher scores
if score >= 80:
    position_size = base_size * 1.5
elif score >= 70:
    position_size = base_size * 1.2
else:
    position_size = base_size * 0.8
```

### 5. **Monitor Score Distribution**
- If everything scores >70: weights too lenient
- If everything scores <40: weights too strict
- Ideal: Bell curve centered around 50-60

---

## FAQ

**Q: Can I use this for short positions?**
A: Currently optimized for long entries. For shorts, invert RSI logic (overbought = good) and sentiment scoring.

**Q: What if I don't have Gemini AI sentiment?**
A: Simple sentiment analysis is used by default. Scoring still works, just with slightly less accuracy on sentiment component.

**Q: How often should I re-optimize?**
A: After every 50 trades or quarterly, whichever comes first.

**Q: Can I add custom components?**
A: Yes! Edit `scoring.py` to add new components (e.g., volume analysis, options flow). Adjust weights accordingly.

**Q: Score seems off for a ticker?**
A: Enable DEBUG logging to see component breakdown. Check if specific component is over/under-weighted for your style.

---

## Next Steps

1. ✅ **Run your first scored analysis**
   ```bash
   python3 run_scored_analysis.py
   ```

2. ✅ **Take 10-20 trades, tracking entry scores**

3. ✅ **Optimize weights from results**
   ```bash
   python3 scoring_optimizer.py --input trades.csv
   ```

4. ✅ **Apply optimized weights and repeat**

5. ✅ **Build automated trade execution based on scores**

---

## Support

For questions or issues:
1. Check component breakdowns with `LOG_LEVEL = "DEBUG"`
2. Review `scoring_config.py` parameters
3. Validate input data quality (sufficient candles, news, etc.)

Happy trading! 🚀
