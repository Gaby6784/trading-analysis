# Pre-Market Stock Analysis Tool v2.0

**Modular, Production-Ready Pre-Market Analysis with 10 Major Improvements**

## 🚀 What's New in v2.0

### 1. **Cache Cleanup** ✅
- Automatic removal of cache files older than 24 hours
- Prevents cache directory bloat
- Runs on every new analysis

### 2. **Consistent ET Timezone** ✅
- All time calculations now use ET (Eastern Time)
- `get_et_time_naive()` used throughout for consistency
- News age and recency weights calculated in ET
- Sample headlines show accurate time-ago in ET

### 3. **Robust Earnings Detection** ✅
- Multiple fallback methods for yfinance API changes:
  - `stock.calendar` (primary)
  - `stock.get_earnings_dates()` (fallback 1)
  - `stock.earnings_dates` attribute (fallback 2)
- Handles DataFrame, dict, and list return types
- Earnings flag ("E") shown in output table

### 4. **Improved Session Filtering** ✅
- New `all_sessions` mode: 04:00-20:00 ET weekdays only
- `all` mode: truly no filtering (24/7 if needed)
- Proper weekend exclusion for all market-related sessions

### 5. **Fixed Finviz Date Parsing** ✅
- Correctly handles mixed date/time format:
  - First row: `Feb-09-26 08:12AM` (full date + time)
  - Following rows: `08:04AM` (time only, uses previous date)
- Tracks `current_date` while iterating rows
- Major accuracy improvement for Finviz source

### 6. **Data Quality Gate** ✅
- Minimum candle requirement before calculating indicators
- `min_required = max(RSI, BB, EMA, ATR, MACD) + 5`
- Returns "INSUFFICIENT DATA" if not enough candles
- Prevents garbage signals from sparse pre-market data

### 7. **Smart Recency Weighting** ✅
- Only applies exponential decay when `pub_date` is valid
- Skips articles where date parsing failed (instead of using fallback `datetime.now()`)
- Prevents broken dates from appearing "super fresh"
- Conservative approach: failed dates don't overweight sentiment

### 8. **Volatility-Adjusted Recommendations** ✅
- New warnings: "BUY - WATCH STOPS" when ATR > 5%
- "⚠️ WIDE STOPS" caution when ATR > 8%
- Prevents entering trades with unacceptable risk
- Uses `suggested_stop` distance in decision logic

### 9. **Enhanced Output Table** ✅
- New columns:
  - **Src**: News source (Y=Yahoo, F=Finviz, G=Google, N=NewsAPI, C=Cache)
  - **Earn**: Earnings flag ("E" if earnings within 7 days)
- Helps debug sentiment quality and earnings risk
- Compact single-letter abbreviations

### 10. **Modular Architecture** ✅
- Broken into 8 focused modules:
  - `config.py` - All configuration in one place
  - `market_data.py` - Data fetching and time utilities
  - `technical_indicators.py` - RSI, BB, MACD, ATR calculations
  - `news_fetching.py` - Multi-source news with caching
  - `sentiment_analysis.py` - Keyword and AI sentiment
  - `recommendation.py` - Trading signal generation
  - `output.py` - Display formatting
  - `main.py` - Orchestration
- Easier to maintain, test, and extend

## 📁 Project Structure

```
premarket_analysis/
  __init__.py              # Package initialization
  config.py                # All configuration constants
  market_data.py           # Market data fetching, time utils
  technical_indicators.py  # RSI, BB, MACD, ATR calculations
  news_fetching.py         # Multi-source news with caching
  sentiment_analysis.py    # Sentiment scoring
  recommendation.py        # Trading recommendations
  output.py                # Display and formatting
  main.py                  # Main orchestration

premarket_analysis_v2.py   # Launcher script
```

## 🏃 How to Run

```bash
# From investing directory:
python3 premarket_analysis_v2.py
```

## ⚙️ Configuration

Edit `premarket_analysis/config.py`:

```python
# Tickers to analyze
TICKERS = ['NVDA', 'META', 'MSFT', 'NFLX', 'AAPL', 'PUBM', 'AMZN']

# Market session: 'premarket', 'regular', 'extended', 'all_sessions', 'all'
MARKET_SESSION = 'all_sessions'  # 04:00-20:00 ET weekdays

# News sources priority
NEWS_SOURCES = ['yahoo_rss', 'finviz', 'newsapi']

# Cache settings
CACHE_DURATION_MINUTES = 15
CACHE_CLEANUP_HOURS = 24

# Thresholds
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
WIDE_STOPS_THRESHOLD = 8.0  # Warn if ATR > 8% of price
```

## 📊 Output Columns Explained

| Column | Description |
|--------|-------------|
| **Ticker** | Stock symbol |
| **Price** | Current price |
| **RSI** | Relative Strength Index (14-period) |
| **Trend** | ↑ Uptrend, ↓ Downtrend, → Sideways |
| **Vol** | Volatility: 🔥 High, ~ Medium, . Low |
| **Stop** | Suggested stop-loss (Price - 1.5×ATR) |
| **BB%** | % distance from Bollinger middle band |
| **Sentiment** | News sentiment (-1 to +1) |
| **News** | Number of articles analyzed |
| **Src** | News source: Y/F/G/N/C/X |
| **Earn** | "E" if earnings within 7 days |
| **Recommendation** | Trading signal |

## 🎯 Trading Signals

- **🟢 STRONG BUY**: RSI < 20, below lower BB, uptrend/sideways, positive news
- **🟢 BUY**: RSI < 30, trend OK, positive sentiment
- **🟢 BUY - WATCH STOPS**: Buy signal but high volatility (ATR > 5%)
- **⚠️ FALLING KNIFE**: Oversold but strong downtrend + negative MACD
- **⚠️ AVOID - NEWS RISK**: Technical buy but deeply negative sentiment
- **⚠️ WIDE STOPS**: Volatility too high for safe entry (ATR > 8%)
- **⚪ HOLD**: No clear signal
- **🔴 SELL**: RSI > 70, downtrend or negative news
- **🔴 STRONG SELL**: RSI > 80, above upper BB, downtrend, negative news

## 🔧 Dependencies

```bash
pip install yfinance pandas pandas-ta requests python-dateutil beautifulsoup4 prettytable
```

## 📝 Example Output

```
📊 ANALYSIS RESULTS
+--------+---------+-------+-------+-----+--------+-------+--------------+------+-----+------+--------------------------------+
| Ticker |   Price |   RSI | Trend | Vol |   Stop |   BB% | Sentiment    | News | Src | Earn | Recommendation                 |
+--------+---------+-------+-------+-----+--------+-------+--------------+------+-----+------+--------------------------------+
| NVDA   | $190.37 | 66.77 |   ↑   |  .  |  $4.19 | +3.8% | Bear (-0.31) |   10 |  C  |      | ⚪ HOLD                        |
| AMZN   | $209.02 | 31.69 |   ↓   |  .  |  $4.90 | -1.8% | Very (-1.0)  |   10 |  C  |   E  | ⚪ HOLD ⚠️  EARNINGS IN 3d     |
+--------+---------+-------+-------+-----+--------+-------+--------------+------+-----+------+--------------------------------+
```

## 🆚 Comparison: Old vs New

| Feature | Old (v1.0) | New (v2.0) |
|---------|------------|------------|
| Time consistency | Mixed (local/ET) | All ET timezone ✅ |
| Cache cleanup | Manual | Automatic (24h) ✅ |
| Finviz parsing | Broken date logic | Fixed mixed format ✅ |
| Earnings detection | Single method, brittle | 3 fallback methods ✅ |
| Data quality | No check | Min candle gate ✅ |
| Volatility warnings | Not used | Wide stops alerts ✅ |
| Recency weighting | All articles | Valid dates only ✅ |
| Output columns | 8 columns | 11 columns (Src, Earn) ✅ |
| Code structure | 1271-line monolith | 8 modular files ✅ |
| Session filtering | Basic | Improved (all_sessions) ✅ |

## 🐛 Known Limitations

1. **BeautifulSoup required for Finviz**: `pip install beautifulsoup4 lxml`
2. **yfinance API changes**: Earnings fallbacks handle most cases but not all
3. **Rate limits**: Yahoo RSS and Finviz are generous; NewsAPI limited to 100 req/day
4. **Pre-market data sparse**: Data quality gate helps but some tickers may show "INSUFFICIENT DATA"

## 🔮 Future Enhancements

- [ ] Support for custom ticker lists via command-line args
- [ ] Export to CSV/JSON
- [ ] Historical performance tracking
- [ ] Email/Slack alerts for signals
- [ ] Machine learning sentiment (BERT/FinBERT)
- [ ] Options flow integration
- [ ] Backtesting framework

## 📄 License

MIT License - Free to use and modify

## 🙏 Credits

Built with:
- **yfinance** - Market data
- **pandas-ta** - Technical indicators
- **beautifulsoup4** - News scraping
- **prettytable** - Output formatting

---

**Version**: 2.0.0  
**Last Updated**: February 2026  
**Maintainer**: Gabriel Indrei
