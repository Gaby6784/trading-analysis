# 🌐 Deployment Guide - Trading Analysis Platform

Complete guide to deploying your trading analysis platform to Railway with 24/7 operation.

## 📋 Table of Contents

1. [Local Testing](#local-testing)
2. [Telegram Bot Setup](#telegram-bot-setup)
3. [Railway Deployment](#railway-deployment)
4. [Environment Configuration](#environment-configuration)
5. [Monitoring & Maintenance](#monitoring--maintenance)

---

## 🧪 Local Testing

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Test Database

```bash
python3 database.py
```

You should see:
```
✅ Database initialized: trading_analysis.db
✅ Saved test result: {...}
```

### Step 3: Test Flask API

```bash
python3 app.py
```

Open browser: http://localhost:5000

You should see the dashboard!

### Step 4: Test Analysis

```bash
# From the Flask dashboard, click "Run Analysis Now"
# OR from terminal:
python3 -c "from scheduler import run_manual; run_manual()"
```

### Step 5: Test Telegram (Optional)

```bash
# Set environment variables first (see next section)
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"

# Test connection
python3 telegram_bot.py
```

---

## 📱 Telegram Bot Setup

### Create Your Bot

1. **Open Telegram** and search for `@BotFather`

2. **Create bot:**
   ```
   /newbot
   ```

3. **Choose name:** "My Trading Bot"

4. **Choose username:** "my_trading_analysis_bot"

5. **Copy the token:** `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

### Get Your Chat ID

1. **Search for** `@userinfobot` in Telegram

2. **Start chat** and it will show your Chat ID: `123456789`

3. **Start your bot:** Search for your bot username and click START

### Test Locally

```bash
export TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
export TELEGRAM_CHAT_ID="123456789"

python3 telegram_bot.py
```

You should receive a test message! 🎉

---

## 🚀 Railway Deployment

### Prerequisites

- GitHub account
- Railway account (sign up at [railway.app](https://railway.app))
- NewsAPI key (get free at [newsapi.org](https://newsapi.org))

### Step 1: Push to GitHub

```bash
# Initialize git (if not already)
git init

# Add all files
git add .

# Commit
git commit -m "Initial deployment of trading analysis platform"

# Create GitHub repo and push
gh repo create trading-analysis --public --source=. --remote=origin --push

# Or manually:
# 1. Create repo on GitHub
# 2. git remote add origin https://github.com/YOUR_USERNAME/trading-analysis.git
# 3. git push -u origin main
```

### Step 2: Deploy to Railway

1. **Go to** [railway.app](https://railway.app)

2. **Click** "New Project" → "Deploy from GitHub repo"

3. **Select** your `trading-analysis` repository

4. **Railway will automatically:**
   - Detect Python
   - Install dependencies from `requirements.txt`
   - Use `Procfile` for startup command
   - Assign a public URL

### Step 3: Configure Environment Variables

In Railway dashboard, go to **Variables** tab:

**Required:**
```
NEWS_API_KEY=your_newsapi_key_here
```

**Optional (for Telegram alerts):**
```
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
```

**Optional (for scheduler):**
```
SCHEDULER_ENABLED=true
ANALYSIS_TICKERS=AAPL,GOOGL,MSFT,AMZN,NVDA,TSLA,META
```

### Step 4: Enable Scheduler (24/7 Analysis)

Railway starts only the `web` process by default. To enable scheduled analysis:

**Option A: Background Worker (Recommended)**

1. In Railway, click **+ New** → **Empty Service**
2. Link to same GitHub repo
3. Change start command to: `python3 scheduler.py`
4. Add same environment variables

**Option B: Combined Process**

Edit `Procfile`:
```
web: bash start.sh
```

This will run both Flask API and scheduler together.

### Step 5: Access Your Dashboard

Railway will give you a URL like: `https://your-app-name.railway.app`

Visit it to see your dashboard! 🎉

---

## ⚙️ Environment Configuration

### Complete Environment Variables

```bash
# Flask
FLASK_ENV=production
PORT=5000  # Railway sets this automatically

# News API (REQUIRED)
NEWS_API_KEY=your_newsapi_key_from_newsapi.org

# Telegram Alerts (OPTIONAL)
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
TELEGRAM_CHAT_ID=your_telegram_user_id

# Scheduler (OPTIONAL)
SCHEDULER_ENABLED=true
ANALYSIS_TICKERS=AAPL,GOOGL,MSFT,AMZN,NVDA,TSLA,META

# Database
DATABASE_PATH=trading_analysis.db  # SQLite file
```

### Local Development (.env)

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
# Edit .env with your keys
```

Then use with:
```bash
python3 -m pip install python-dotenv

# Add to app.py:
from dotenv import load_dotenv
load_dotenv()
```

---

## 📊 Monitoring & Maintenance

### Check API Health

```bash
curl https://your-app.railway.app/api/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2026-02-10T12:00:00",
  "database": {
    "total_records": 150,
    "unique_tickers": 7,
    "alerts_24h": 3
  }
}
```

### View Logs

**Railway Dashboard:**
1. Click your service
2. Go to "Deployments" tab
3. Click "View Logs"

**Look for:**
- `✅ Database initialized`
- `🚀 Starting Trading Analysis API`
- `⏰ Scheduled analysis times`
- `🔔 HIGH CONFIDENCE SIGNAL!`

### Scheduled Analysis Times

The scheduler runs **3x daily** at:
- **9:30 AM ET** - Market open
- **12:00 PM ET** - Midday check
- **3:30 PM ET** - Pre-close check

### Database Cleanup

Run monthly to remove old data:

```bash
python3 -c "from database import Database; db = Database(); db.cleanup_old_data(days=30)"
```

Or add to scheduler in `scheduler.py`:

```python
# Add to schedule_jobs():
schedule.every().monday.at("00:00").do(lambda: self.db.cleanup_old_data(30))
```

### Update Tickers

**Method 1: Environment Variable**
```bash
# In Railway, edit ANALYSIS_TICKERS variable:
ANALYSIS_TICKERS=AAPL,GOOGL,MSFT,AMZN,NVDA,TSLA,META,AMD,NFLX,DIS
```

**Method 2: Edit Code**

In `app.py` and `scheduler.py`, change:
```python
DEFAULT_TICKERS = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'NVDA', 'TSLA', 'META']
```

---

## 🎯 Using Your Dashboard

### Manual Analysis

1. Visit your dashboard URL
2. Click **"Run Analysis Now"**
3. Wait 30-60 seconds
4. Results will appear automatically

### View High-Confidence Alerts

1. Click **"View Alerts"** button
2. See all signals with Score ≥ 70 or News Confidence ≥ 60%
3. Sorted by most recent

### API Endpoints

```bash
# Latest results
GET /api/latest

# Run new analysis
GET /api/analyze

# High-confidence signals (last 24h)
GET /api/alerts

# Ticker history (last 7 days)
GET /api/history/AAPL?days=7

# Database stats
GET /api/stats

# Health check
GET /api/health
```

### Telegram Alerts

If configured, you'll receive alerts for:

**High-Confidence Signals:**
- Score ≥ 70
- News confidence ≥ 60%

**Message Format:**
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

🕐 Time: 2026-02-10 09:35:00
```

---

## 🔧 Troubleshooting

### Dashboard shows "No results available"

**Solution:** Click "Run Analysis Now" button or wait for scheduled run.

### Telegram bot not sending messages

**Check:**
1. Bot token is correct
2. You started the bot in Telegram (click START)
3. Chat ID is correct (use `@userinfobot`)
4. Environment variables are set in Railway

**Test:**
```bash
python3 telegram_bot.py
```

### Analysis failing

**Check logs for:**
- `NewsAPI key invalid` → Get new key from newsapi.org
- `Rate limit exceeded` → NewsAPI free tier: 100 requests/day
- `No module named 'yfinance'` → Dependencies not installed

### Railway app sleeping

**Railway free tier:** Apps sleep after 30 min of inactivity.

**Solutions:**
1. Upgrade to Railway Pro ($5/month)
2. Use cron-job.org to ping `/api/health` every 5 minutes
3. Run scheduler as separate worker (keeps app awake)

---

## 💰 Cost Estimates

### Free Tier (Good for Testing)

- **Railway:** 500 hours/month free, then $0.000231/hour
- **NewsAPI:** 100 requests/day free
- **Telegram:** Free forever

**Monthly cost:** $0-5 depending on usage

### Recommended Setup

- **Railway Hobby Plan:** $5/month (no sleep, unlimited hours)
- **NewsAPI Developer:** $50/month (250,000 requests)
- **Telegram:** Free

**Monthly cost:** $55

### Enterprise

- **Railway Pro:** $20/month
- **Deploy to AWS/DigitalOcean:** $5-10/month
- **NewsAPI Business:** Custom pricing

---

## 🎉 You're All Set!

Your trading analysis platform is now:

✅ **Running 24/7** on Railway
✅ **Analyzing stocks** 3x daily during market hours
✅ **Sending alerts** via Telegram for high-confidence signals
✅ **Storing history** in SQLite database
✅ **Accessible** via web dashboard from anywhere

### Next Steps

1. **Monitor for 1-2 weeks** to see signal quality
2. **Collect 20+ forward test trades** for weight optimization
3. **Run optimizer:** `python3 scoring_optimizer.py`
4. **Fine-tune thresholds** in `scoring_config.py`
5. **Paper trade** the signals before going live

### Support

Need help? Check:
- Railway docs: https://docs.railway.app
- NewsAPI docs: https://newsapi.org/docs
- Telegram Bot API: https://core.telegram.org/bots/api

---

**Happy Trading! 📈🚀**
