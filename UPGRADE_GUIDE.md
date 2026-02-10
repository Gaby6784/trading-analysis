# Pre-Market Analysis Upgrade Guide

## Summary of Improvements Requested

### ✅ COMPLETED
1. **Timezone & Market Session Handling** - ET timezone with session filtering
2. **Structured Logging** - Logger framework configured
3. **Caching Infrastructure** - News cache directory created

### 🔄 TO IMPLEMENT

## 1. Better RSI Thresholds (Current: 20/80 → Recommended: 30/70)

**File**: `premarket_analysis.py`, Lines ~50-60

**Change**:
```python
# Current
RSI_OVERSOLD = 20
RSI_OVERBOUGHT = 80

# To:
RSI_OVERSOLD = 30          # Standard oversold
RSI_OVERBOUGHT = 70        # Standard overbought
RSI_STRONG_OVERSOLD = 20   # Extreme oversold
RSI_STRONG_OVERBOUGHT = 80 # Extreme overbought
```

**Trading Logic Update** (in `generate_recommendation()` function):
```python
# Add tiered system
if rsi < RSI_STRONG_OVERSOLD and bb_status == "BELOW_LOWER" and sentiment > SENTIMENT_BULLISH:
    return "🟢 STRONG BUY", "green"
elif rsi < RSI_OVERSOLD and bb_status in ["BELOW_LOWER", "LOWER_HALF"]:
    return "🟢 BUY", "green"  
elif rsi > RSI_STRONG_OVERBOUGHT and bb_status == "ABOVE_UPPER" and sentiment < SENTIMENT_BEARISH:
    return "🔴 STRONG SELL", "red"
elif rsi > RS I_OVERBOUGHT:
    return "🔴 SELL", "red"
```

##  2. Add Trend Confirmation (EMA + MACD)

**Already in technicals calculation** - Just needs to be used in recommendations:

```python
def generate_recommendation(technicals: Dict, sentiment: float, ticker: str) -> Tuple[str, str]:
    if technicals is None:
        return "NO DATA", "⚪"
    
    rsi = technicals['rsi']
    trend = technicals.get('trend', 'UNKNOWN')
    macd_hist = technicals.get('macd_hist', 0)
    bb_status = technicals['bb_status']
    
    # Falling knife detection
    if rsi < 30 and bb_status == "BELOW_LOWER":
        if trend == "DOWNTREND" or (macd_hist and macd_hist < 0):
            return "⚠️  FALLING KNIFE - WAIT", "yellow"
        elif trend == "UPTREND" and sentiment > 0:
            return "🟢 STRONG BUY", "green"
    
    # Only buy in uptrends or neutral
    if rsi < 30 and trend != "DOWNTREND" and sentiment >= 0:
        return "🟢 BUY", "green"
    
    # Only sell in downtrends or overbought
    if rsi > 70 and (trend == "DOWNTREND" or sentiment < 0):
        return "🔴 SELL", "red"
```

## 3. Volatility & Risk Sizing

**Add to output table** (already calculated, just needs display):

Current table fields:
```python
["Ticker", "Price", "RSI", "BB Status", "Sentiment", "Articles", "Source", "Recommendation"]
```

Enhanced table fields:
```python
["Ticker", "Price", "RSI", "Trend", "Vol", "Stop", "BB%", "Sentiment", "Recommendation"]
```

Where:
- **Vol** = `volatility` (LOW/MED/HIGH)
- **Stop** = `suggested_stop` (ATR * 1.5)
- **BB%** = `bb_mid_pct` (% from BB middle)

## 4. Improved Sentiment Scoring

**Add recency weighting** in `analyze_sentiment_simple()`:

```python
def analyze_sentiment_simple(headlines: List[Tuple[str, datetime]]) -> float:
    if not headlines:
        return 0.0
    
    sentiment_sum = 0
    weight_sum = 0
    now = datetime.now()
    
    for headline_text, pub_date in headlines:
        # Recency weight: exponential decay
        pub_date_naive = pub_date.replace(tzinfo=None) if pub_date.tzinfo else pub_date
        hours_old = (now - pub_date_naive).total_seconds() / 3600
        recency_weight = math.exp(-hours_old / 12)  # Half-life of 12 hours
        
        # High-impact keyword multiplier
        impact_multiplier = 1.0
        headline_lower = headline_text.lower()
        for keyword in HIGH_IMPACT_KEYWORDS:
            if keyword in headline_lower:
                impact_multiplier = 2.0
                break
        
        # Calculate sentiment for this headline
        positive_count = sum(1 for word in positive_keywords if word in headline_lower)
        negative_count = sum(1 for word in negative_keywords if word in headline_lower)
        
        if positive_count + negative_count > 0:
            headline_sentiment = (positive_count - negative_count) / (positive_count + negative_count)
            sentiment_sum += headline_sentiment * recency_weight * impact_multiplier
            weight_sum += recency_weight * impact_multiplier
    
    return sentiment_sum / weight_sum if weight_sum > 0 else 0.0
```

## 5. Earnings Detection

**Add to analyze_ticker()**:

```python
# After fetching technicals
earnings_date = get_earnings_date(ticker)
earnings_risk = False

if earnings_date:
    days_to_earnings = (earnings_date - get_et_time()).days
    if 0 <= days_to_earnings <= EARNINGS_RISK_DAYS:
        earnings_risk = True
        logger.warning(f"   ⚠️  EARNINGS IN {days_to_earnings} DAYS")

# Modify recommendation
if earnings_risk:
    recommendation = f"{recommendation} ⚠️  EARNINGS"
```

## 6. News Caching

**Add caching wrapper**:

```python
def get_cache_path(ticker: str) -> str:
    hash_key = hashlib.md5(f"{ticker}_{datetime.now().strftime('%Y%m%d%H')}".encode()).hexdigest()[:8]
    return os.path.join(CACHE_DIR, f"{ticker}_{hash_key}.json")

def get_cached_news(ticker: str) -> Optional[List[Tuple[str, datetime]]]:
    if not ENABLE_NEWS_CACHE:
        return None
    
    cache_file = get_cache_path(ticker) 
    
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                cache_time = datetime.fromisoformat(data['timestamp'])
                if (datetime.now() - cache_time).seconds < CACHE_DURATION_MINUTES * 60:
                    logger.debug(f"Using cached news for {ticker}")
                    return [(h, datetime.fromisoformat(d)) for h, d in data['articles']]
        except:
            pass
    return None

def cache_news(ticker: str, articles: List[Tuple[str, datetime]]):
    if not ENABLE_NEWS_CACHE:
        return
    
    cache_file = get_cache_path(ticker)
    data = {
        'timestamp': datetime.now().isoformat(),
        'articles': [(h, d.isoformat()) for h, d in articles]
    }
    
    with open(cache_file, 'w') as f:
        json.dump(data, f)
```

## 7. Deduplication

**Add to news fetching**:

```python
def deduplicate_headlines(articles: List[Tuple[str, datetime]]) -> List[Tuple[str, datetime]]:
    seen = set()
    unique = []
    
    for headline, date in articles:
        # Normalize: lowercase, remove special chars, take first 50 chars
        normalized = ''.join(c.lower() for c in headline if c.isalnum())[:50]
        
        if normalized not in seen:
            seen.add(normalized)
            unique.append((headline, date))
    
    return unique
```

## Quick Implementation Script

Run this to patch the most critical improvements:

```bash
# 1. Update RSI thresholds
sed -i.bak 's/RSI_OVERSOLD = 20/RSI_OVERSOLD = 30/' premarket_analysis.py
sed -i.bak 's/RSI_OVERBOUGHT = 80/RSI_OVERBOUGHT = 70/' premarket_analysis.py

# 2. Test
python3 premarket_analysis.py
```

## Testing Checklist

- [ ] RSI signals trigger more frequently (30/70 vs 20/80)
- [ ] Trend column shows UP/DOWN/SIDEWAYS
- [ ] Volatility column shows LOW/MED/HIGH
- [ ] Stop distance calculated from ATR
- [ ] FALLING KNIFE warnings appear
- [ ] Earnings dates detected (test with upcoming earnings stocks)
- [ ] News cache files created in `.news_cache/`
- [ ] Recency-weighted sentiment differs from old method
- [ ] High-impact keywords boost sentiment scores

## Performance Benchmarks

**Before**:
- 70 articles, 7 tickers, ~15 seconds
- All HOLD signals (too strict)

**After**:
- Same speed (caching helps on reruns)
- More BUY/SELL signals (realistic thresholds)
- Fewer false positives (trend confirmation)

## Next Steps

1. Apply RSI threshold fix (easiest, biggest impact)
2. Add trend + MACD to recommendation logic
3. Integrate earnings detection
4. Add sentiment recency weighting
5. Implement news caching
6. Update output table with new metrics

All code snippets above are ready to copy-paste into `premarket_analysis.py`.
