# 🚀 Quick Start - Trading Analysis Platform

## ✅ What We Built

A **24/7 cloud-hosted trading analysis platform** with:

- 🌐 **Web Dashboard** - Beautiful UI to view analysis results
- 📊 **REST API** - Automated analysis with scoring system
- 📱 **Telegram Alerts** - Real-time notifications for high-confidence signals
- 🗄️ **SQLite Database** - Historical tracking of all analyses
- ⏰ **Scheduler** - Runs 3x daily during market hours (9:30 AM, 12 PM, 3:30 PM ET)
- 🔄 **News Predictions** - AI-powered analysis of market-moving news

## 🎯 Quick Test Locally

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Test Database

```bash
python3 database.py
```

✅ You should see: `Database initialized: trading_analysis.db`

### 3. Start Web Dashboard

```bash
# macOS - Port 5000 is often used by AirPlay
PORT=8080 python3 app.py

# Linux/Windows
python3 app.py
```

### 4. Open Dashboard

Visit: **http://localhost:8080** (or :5000)

You should see:
- 📊 Trading Analysis Dashboard
- System Status panel
- Buttons: "Refresh Latest", "Run Analysis Now", "View Alerts"

### 5. Run Your First Analysis

**Option A: From Dashboard**
1. Click **"Run Analysis Now"** button
2. Wait 30-60 seconds
3. Results appear automatically!

**Option B: From Terminal**
```bash
python3 -c "from scheduler import run_manual; run_manual()"
```

### 6. Check API

```bash
# Health check
curl http://localhost:8080/api/health

# Latest results
curl http://localhost:8080/api/latest

# Stats
curl http://localhost:8080/api/stats
```

## 📱 Setup Telegram Bot (Optional)

### Get Bot Token

1. Open Telegram → Search **@BotFather**
2. Send: `/newbot`
3. Name: "My Trading Bot"
4. Username: "my_trading_analysis_bot"
5. **Copy token:** `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

### Get Chat ID

1. Search **@userinfobot** in Telegram
2. Start chat → Copy your **Chat ID**: `123456789`
3. Start your bot (click START button)

### Test Telegram

```bash
export TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
export TELEGRAM_CHAT_ID="123456789"

python3 telegram_bot.py
```

You should receive a test message! 🎉

## 🚀 Deploy to Railway (Free Hosting)

### Prerequisites

- GitHub account
- Railway account (sign up free at [railway.app](https://railway.app))
- NewsAPI key (get free at [newsapi.org](https://newsapi.org))

### Steps

1. **Push to GitHub**

```bash
git init
git add .
git commit -m "Trading analysis platform"

# Create repo
gh repo create trading-analysis --public --source=. --push
```

2. **Deploy to Railway**

- Go to [railway.app](https://railway.app)
- Click "New Project" → "Deploy from GitHub repo"
- Select your `trading-analysis` repo
- Wait for deployment (~2 min)

3. **Add Environment Variables**

In Railway → **Variables** tab:

```
NEWS_API_KEY=your_newsapi_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token  # Optional
TELEGRAM_CHAT_ID=your_telegram_chat_id      # Optional
```

4. **Access Your Dashboard**

Railway gives you a URL like: `https://your-app.railway.app`

🎉 **Done! Your platform is live 24/7!**

## 📊 What You'll See

### Dashboard Overview

```
Trading Analysis Dashboard
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

System Status
┌─────────────┬──────────────┬──────────┬─────────────┐
│ 150 Analyses│ 7 Tickers    │ 3 Alerts │ 09:35 AM    │
│ Total       │ Tracked      │ (24h)    │ Last Update │
└─────────────┴──────────────┴──────────┴─────────────┘

Latest Analysis Results
┌─────────────────────────────────────────────────┐
│ AAPL                               Score: 85    │
│ Category: STRONG_BUY                            │
│ Price: $180.25 | RSI: 28.5 | Trend: UPTREND   │
│                                                 │
│ News: 🟢 BULLISH (75%) | STRONG CONFLUENCE     │
│ Expected: SIGNIFICANT (3-5%)                    │
└─────────────────────────────────────────────────┘
```

### Telegram Alerts

```
🚀 AAPL - STRONG_BUY
━━━━━━━━━━━━━━━━━━━━

📊 Score: 85/100

💰 Price: $180.25
📉 RSI: 28.5
📈 Trend: UPTREND

📰 News Prediction:
🟢 BULLISH (75% confidence)

🎯 Alignment: STRONG CONFLUENCE
⚖️ Alignment Score: 9/10
```

## 🎯 How It Works

### Analysis Schedule

Automatically runs **3x daily**:
- **9:30 AM ET** - Market open
- **12:00 PM ET** - Midday check  
- **3:30 PM ET** - Before close

### Scoring System (0-100)

- **85-100:** 🚀 STRONG_BUY - Perfect setup
- **70-84:** 📈 BUY - Good opportunity
- **50-69:** 👀 WATCH - Monitor closely
- **40-49:** ➖ NEUTRAL - No clear signal
- **0-39:** ⛔ AVOID - Poor setup

### Alerts Trigger When:

- **Score ≥ 70** (STRONG_BUY or BUY)
- **News confidence ≥ 60%** (high-impact catalyst)

### What Gets Analyzed:

1. **Technical Indicators** (30%): RSI, Bollinger Bands, ATR
2. **Sentiment** (25%): News sentiment analysis
3. **Momentum** (20%): Volume, price action
4. **Catalysts** (15%): Market-moving news events
5. **Timing** (10%): Premarket volume, spread

### News Prediction:

Analyzes headlines for:
- 🟢 **BULLISH:** Earnings beats, upgrades, growth
- 🔴 **BEARISH:** Misses, downgrades, problems
- ⚪ **NEUTRAL:** No clear catalyst

Then checks **alignment**:
- ✅ **STRONG CONFLUENCE:** Bullish news + oversold + uptrend
- ⚠️ **DIVERGENCE:** Misaligned signals (wait for clarity)

## 📂 Project Structure

```
investing/
├── app.py                    # Flask API server
├── database.py               # SQLite database
├── scheduler.py              # Automated 3x daily runs
├── telegram_bot.py           # Telegram notifications
├── requirements.txt          # Dependencies
├── Procfile                  # Railway start command
├── railway.json              # Railway config
├── .env.example              # Environment variables template
├── DEPLOYMENT_GUIDE.md       # Full deployment docs
│
├── templates/
│   └── index.html            # Dashboard UI
│
├── premarket_analysis/
│   ├── main_with_predictions.py  # Enhanced analysis
│   ├── news_signals.py           # News prediction engine
│   ├── scoring.py                # Scoring system
│   ├── scoring_config.py         # Tunable parameters
│   └── ...                       # Other modules
│
└── trading_analysis.db       # SQLite database (created on first run)
```

## 🔧 API Endpoints

```bash
GET /                    # Web dashboard
GET /api/health          # Health check
GET /api/stats           # Database statistics
GET /api/latest          # Latest results for all tickers
GET /api/analyze         # Run new analysis
GET /api/alerts          # High-confidence signals (24h)
GET /api/history/:ticker # Historical data for ticker
```

## 💡 Tips

### Test Locally Before Deploy

```bash
# Run full analysis
python3 -c "from scheduler import run_manual; run_manual()"

# Test Telegram
python3 telegram_bot.py

# Test database
python3 database.py

# Start web dashboard
PORT=8080 python3 app.py
```

### Monitor Logs

**Railway:**
1. Dashboard → Your service → Deployments
2. Click "View Logs"

**Look for:**
- `✅ Database initialized`
- `🚀 Starting Trading Analysis API`
- `🔔 HIGH CONFIDENCE SIGNAL!`

### Update Tickers

Edit in `app.py` and `scheduler.py`:

```python
DEFAULT_TICKERS = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'NVDA', 'TSLA', 'META']
```

Or set environment variable:
```
ANALYSIS_TICKERS=AAPL,GOOGL,MSFT,AMZN,NVDA,TSLA,META,AMD,NFLX
```

## 📚 Documentation

- **DEPLOYMENT_GUIDE.md** - Complete deployment instructions
- **SCORING_SYSTEM_README.md** - How scoring works
- **TESTING_GUIDE.md** - Testing and optimization

## 🆘 Troubleshooting

### Port 5000 already in use (macOS)

```bash
PORT=8080 python3 app.py
```

### ImportError: cannot import name

```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### Telegram not sending messages

1. Start your bot in Telegram (click START)
2. Verify token and chat ID
3. Test: `python3 telegram_bot.py`

### No results on dashboard

Click **"Run Analysis Now"** button or wait for scheduled run (9:30 AM, 12 PM, 3:30 PM ET).

## 🎉 Next Steps

1. ✅ Test locally
2. ✅ Setup Telegram bot
3. ✅ Deploy to Railway
4. ✅ Monitor for 1-2 weeks
5. ✅ Collect forward test data
6. ✅ Optimize weights: `python3 scoring_optimizer.py`
7. ✅ Paper trade the signals
8. ✅ Go live! 🚀

---

**Happy Trading! 📈**

Questions? Check **DEPLOYMENT_GUIDE.md** for detailed instructions.
