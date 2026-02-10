# Pre-Market Stock Analysis Tool

A comprehensive Python script for analyzing tech stocks using technical indicators, news sentiment, and AI-powered recommendations.

## Features

- ✅ **Real-time Market Data**: Fetches 30 days of 1-hour interval data using `yfinance`
- ✅ **Technical Analysis**: RSI (14), Bollinger Bands (20, 2.0) using `pandas_ta`
- ✅ **News Integration**: Recent headlines from NewsAPI (last 24 hours)
- ✅ **Sentiment Analysis**: AI-powered (Gemini/OpenAI) or keyword-based sentiment scoring
- ✅ **Smart Trading Logic**: 
  - STRONG BUY: RSI < 20, Below Lower BB, Sentiment > 0.5
  - STRONG SELL: RSI > 80, Above Upper BB, Sentiment < -0.5
  - AVOID - NEWS RISK: Technical buy signal but deeply negative news
- ✅ **Clean Output**: Formatted terminal table with all key metrics

## Analyzed Tickers

- NVDA (NVIDIA)
- META (Meta/Facebook)
- MSFT (Microsoft)
- NFLX (Netflix)
- AAPL (Apple)
- PUBM (PubMatic)
- AMZN (Amazon)

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

#### NewsAPI (Required for real news data)
1. Get free API key from [NewsAPI.org](https://newsapi.org/)
2. Edit `premarket_analysis.py`:
   ```python
   NEWS_API_KEY = "your_actual_api_key_here"
   ```

#### AI Sentiment (Optional)
For enhanced sentiment analysis, configure one of:

**OpenAI:**
```python
AI_API_KEY = "your_openai_api_key"
USE_AI_SENTIMENT = True
```

**Google Gemini:**
```python
AI_API_KEY = "your_gemini_api_key"
USE_AI_SENTIMENT = True
```

### 3. Run the Script

```bash
python premarket_analysis.py
```

## Output Example

```
================================================================================
🚀 PRE-MARKET STOCK ANALYSIS
================================================================================
📅 Date: 2026-02-09 09:30:00
📊 Analyzing: NVDA, META, MSFT, NFLX, AAPL, PUBM, AMZN
================================================================================

📊 Analyzing NVDA...
📊 Analyzing META...
...

================================================================================
📊 ANALYSIS RESULTS
================================================================================
+---------+----------+-------+--------------+----------------------+------+---------------------------+
| Ticker  |    Price |   RSI | BB Status    | Sentiment            | News | Recommendation            |
+---------+----------+-------+--------------+----------------------+------+---------------------------+
| NVDA    |  $185.27 | 45.32 | LOWER HALF   | Bullish (0.45)       |    8 | 🟢 BUY                    |
| META    |  $523.14 | 68.21 | UPPER HALF   | Neutral (0.12)       |    6 | ⚪ HOLD                   |
| MSFT    |  $420.50 | 72.45 | ABOVE UPPER  | Bearish (-0.32)      |   12 | 🔴 SELL                   |
| NFLX    |  $612.89 | 28.67 | BELOW LOWER  | Very Bullish (0.78)  |    5 | 🟢 STRONG BUY             |
| AAPL    |  $189.45 | 55.12 | LOWER HALF   | Neutral (-0.05)      |   15 | ⚪ HOLD                   |
| PUBM    |   $24.56 | 32.10 | BELOW LOWER  | Very Bearish (-0.82) |    3 | ⚠️  AVOID - NEWS RISK     |
| AMZN    |  $178.23 | 81.34 | ABOVE UPPER  | Bearish (-0.56)      |   18 | 🔴 STRONG SELL            |
+---------+----------+-------+--------------+----------------------+------+---------------------------+

================================================================================
📈 ANALYSIS SUMMARY
================================================================================
Total Tickers Analyzed: 7
Buy Signals: 2
Sell Signals: 2
Hold Signals: 2
Avoid Signals: 1
================================================================================
```

## Configuration Options

Edit these variables in `premarket_analysis.py`:

```python
# Tickers to analyze
TICKERS = ['NVDA', 'META', 'MSFT', 'NFLX', 'AAPL', 'PUBM', 'AMZN']

# Technical parameters
RSI_PERIOD = 14
BB_PERIOD = 20
BB_STD = 2.0

# Trading thresholds
RSI_OVERSOLD = 20
RSI_OVERBOUGHT = 80
SENTIMENT_BULLISH = 0.5
SENTIMENT_BEARISH = -0.5

# News lookback period
NEWS_LOOKBACK_HOURS = 24
```

## Trading Signals Logic

### 🟢 STRONG BUY
- RSI < 20 (Extremely oversold)
- Price below Lower Bollinger Band
- News Sentiment > 0.5 (Bullish)

### 🔴 STRONG SELL
- RSI > 80 (Extremely overbought)
- Price above Upper Bollinger Band
- News Sentiment < -0.5 (Bearish)

### ⚠️ AVOID - NEWS RISK
- Technical indicators suggest buy (RSI < 30, low BB)
- BUT News Sentiment < -0.5 (Deeply negative)
- Example: AMZN with massive negative Capex news

### 🟢 BUY
- RSI < 30 (Oversold)
- Sentiment >= 0 (Neutral or positive)

### 🔴 SELL
- RSI > 70 (Overbought)
- Sentiment <= 0 (Neutral or negative)

### ⚪ HOLD
- No strong signals in either direction

## Code Structure

```
premarket_analysis.py
├── Configuration (API keys, parameters)
├── Market Data Functions (yfinance integration)
├── Technical Analysis (pandas_ta calculations)
├── News Fetching (NewsAPI integration)
├── Sentiment Analysis (AI or keyword-based)
├── Trading Logic (signal generation)
└── Output Formatting (PrettyTable display)
```

## Troubleshooting

### No data for ticker
- Check if market is open or if ticker is valid
- yfinance may have rate limits

### News API errors
- Verify your API key is valid
- Free tier has 100 requests/day limit
- Check NewsAPI status

### Missing dependencies
```bash
pip install --upgrade -r requirements.txt
```

## Extending the Script

### Add More Tickers
```python
TICKERS = ['NVDA', 'META', 'GOOGL', 'TSLA', 'AMD']  # Add your tickers
```

### Adjust Sensitivity
```python
RSI_OVERSOLD = 25  # Less aggressive (was 20)
SENTIMENT_BULLISH = 0.3  # More lenient (was 0.5)
```

### Export to CSV
```python
import pandas as pd
df = pd.DataFrame(results)
df.to_csv('premarket_analysis.csv', index=False)
```

## Disclaimer

⚠️ **This tool is for educational and informational purposes only.**
- Not financial advice
- Past performance does not guarantee future results
- Always do your own research before trading
- Consider consulting with a financial advisor

## License

MIT License - Feel free to modify and use for your own analysis.
