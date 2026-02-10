# Gemini AI Sentiment Analysis Setup

## ✅ API Key Added

Your Gemini API key has been configured in `premarket_analysis/config.py`.

## 🚀 How to Enable AI-Powered Sentiment

### 1. Install the Gemini SDK

```bash
pip install google-generativeai
```

### 2. Enable AI Sentiment in Config

Edit `premarket_analysis/config.py`:

```python
USE_AI_SENTIMENT = True  # Change from False to True
```

### 3. Run the Analysis

```bash
python3 premarket_analysis_v2.py
```

## 🤖 How It Works

When enabled, the tool will:

1. **Send headlines to Gemini** - Up to 15 most recent headlines per ticker
2. **Get AI sentiment score** - Gemini analyzes sentiment (-1 to +1)
3. **Fallback to keywords** - If API fails, uses keyword-based analysis

## 📊 Benefits of AI Sentiment

- **Context understanding**: Gemini understands nuance and sarcasm
- **Multi-word patterns**: Detects complex sentiment patterns
- **Entity recognition**: Better at distinguishing ticker-specific news
- **Adaptive scoring**: More accurate than fixed keyword lists

## 🆚 Comparison

| Method | Speed | Accuracy | Cost |
|--------|-------|----------|------|
| **Keyword-based** | Instant | Good | Free |
| **Gemini AI** | 2-3s/ticker | Excellent | Free tier: 60 req/min |

## ⚠️ Rate Limits

- **Free tier**: 60 requests per minute
- **7 tickers**: Should complete in ~7 seconds
- **Caching**: News cached for 15 min, so repeated runs are fast

## 🔍 Testing AI vs Keyword

To compare methods:

1. Run with `USE_AI_SENTIMENT = False` (keyword-based)
2. Note sentiment scores
3. Run with `USE_AI_SENTIMENT = True` (Gemini)
4. Compare differences

Example expected differences:
- **Keyword**: "Very Bearish (-1.0)" for articles with many negative words
- **Gemini**: "Bearish (-0.65)" if context shows less severe impact

## 💡 Tips

- **AI is best for**: Complex news with mixed signals
- **Keywords are fine for**: Clear positive/negative headlines
- **Use AI when**: Making real money decisions
- **Use keywords when**: Quick screening or testing

## 🛠️ Troubleshooting

### "google-generativeai not installed"
```bash
pip install google-generativeai
```

### "API key invalid"
Check that the key in `config.py` matches your Google AI Studio key.

### "Rate limit exceeded"
- Free tier: 60 requests/minute
- Wait 60 seconds or upgrade to paid tier

### "Falling back to keyword-based sentiment"
- Check internet connection
- Verify API key is active in Google AI Studio
- Review error message in terminal

## 📚 API Documentation

Google AI Studio: https://ai.google.dev/
Gemini API Docs: https://ai.google.dev/tutorials/python_quickstart

---

**Status**: ✅ API Key Configured  
**To Enable**: Set `USE_AI_SENTIMENT = True` in config.py  
**Required**: `pip install google-generativeai`
