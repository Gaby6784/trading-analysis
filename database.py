#!/usr/bin/env python3
"""
SQLite database for storing analysis results
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
import json


class AnalysisResult:
    """Model for analysis result"""
    
    def __init__(self, id, ticker, timestamp, score, category, rsi, trend, price,
                 news_direction, news_confidence, alignment, alignment_score):
        self.id = id
        self.ticker = ticker
        self.timestamp = timestamp
        self.score = score
        self.category = category
        self.rsi = rsi
        self.trend = trend
        self.price = price
        self.news_direction = news_direction
        self.news_confidence = news_confidence
        self.alignment = alignment
        self.alignment_score = alignment_score
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'ticker': self.ticker,
            'timestamp': self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp,
            'score': self.score,
            'category': self.category,
            'rsi': self.rsi,
            'trend': self.trend,
            'price': self.price,
            'news_direction': self.news_direction,
            'news_confidence': self.news_confidence,
            'alignment': self.alignment,
            'alignment_score': self.alignment_score
        }


class Database:
    """SQLite database manager"""
    
    def __init__(self, db_path: str = 'trading_analysis.db'):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                score REAL,
                category TEXT,
                rsi REAL,
                trend TEXT,
                price REAL,
                news_direction TEXT,
                news_confidence REAL,
                alignment TEXT,
                alignment_score REAL
            )
        ''')
        
        # Create indexes for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_ticker_timestamp 
            ON analysis_results(ticker, timestamp DESC)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON analysis_results(timestamp DESC)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_score 
            ON analysis_results(score DESC)
        ''')
        
        conn.commit()
        conn.close()
        
        print(f"✅ Database initialized: {self.db_path}")
    
    def save_analysis(self, ticker: str, score: float, category: str,
                     rsi: Optional[float], trend: Optional[str], price: Optional[float],
                     news_direction: str, news_confidence: float,
                     alignment: str, alignment_score: float) -> AnalysisResult:
        """Save analysis result to database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO analysis_results 
            (ticker, score, category, rsi, trend, price, 
             news_direction, news_confidence, alignment, alignment_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (ticker, score, category, rsi, trend, price,
              news_direction, news_confidence, alignment, alignment_score))
        
        result_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return AnalysisResult(
            id=result_id,
            ticker=ticker,
            timestamp=datetime.now(),
            score=score,
            category=category,
            rsi=rsi,
            trend=trend,
            price=price,
            news_direction=news_direction,
            news_confidence=news_confidence,
            alignment=alignment,
            alignment_score=alignment_score
        )
    
    def get_latest_results(self, limit: int = 50) -> List[AnalysisResult]:
        """Get latest analysis results"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT ticker, 
                   MAX(timestamp) as latest_timestamp,
                   id, score, category, rsi, trend, price,
                   news_direction, news_confidence, alignment, alignment_score
            FROM analysis_results
            GROUP BY ticker
            ORDER BY latest_timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        results = []
        for row in cursor.fetchall():
            results.append(AnalysisResult(
                id=row['id'],
                ticker=row['ticker'],
                timestamp=datetime.fromisoformat(row['latest_timestamp']) if row['latest_timestamp'] else None,
                score=row['score'],
                category=row['category'],
                rsi=row['rsi'],
                trend=row['trend'],
                price=row['price'],
                news_direction=row['news_direction'],
                news_confidence=row['news_confidence'],
                alignment=row['alignment'],
                alignment_score=row['alignment_score']
            ))
        
        conn.close()
        return results
    
    def get_ticker_history(self, ticker: str, days: int = 7) -> List[AnalysisResult]:
        """Get historical results for a ticker"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        since = datetime.now() - timedelta(days=days)
        
        cursor.execute('''
            SELECT * FROM analysis_results
            WHERE ticker = ? AND timestamp >= ?
            ORDER BY timestamp DESC
        ''', (ticker, since.isoformat()))
        
        results = []
        for row in cursor.fetchall():
            results.append(AnalysisResult(
                id=row['id'],
                ticker=row['ticker'],
                timestamp=datetime.fromisoformat(row['timestamp']) if row['timestamp'] else None,
                score=row['score'],
                category=row['category'],
                rsi=row['rsi'],
                trend=row['trend'],
                price=row['price'],
                news_direction=row['news_direction'],
                news_confidence=row['news_confidence'],
                alignment=row['alignment'],
                alignment_score=row['alignment_score']
            ))
        
        conn.close()
        return results
    
    def get_high_confidence_signals(self, hours: int = 24) -> List[AnalysisResult]:
        """Get high-confidence signals (score >= 70 or news confidence >= 60%)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        since = datetime.now() - timedelta(hours=hours)
        
        cursor.execute('''
            SELECT * FROM analysis_results
            WHERE timestamp >= ?
            AND (score >= 70 OR news_confidence >= 60)
            ORDER BY timestamp DESC
        ''', (since.isoformat(),))
        
        results = []
        for row in cursor.fetchall():
            results.append(AnalysisResult(
                id=row['id'],
                ticker=row['ticker'],
                timestamp=datetime.fromisoformat(row['timestamp']) if row['timestamp'] else None,
                score=row['score'],
                category=row['category'],
                rsi=row['rsi'],
                trend=row['trend'],
                price=row['price'],
                news_direction=row['news_direction'],
                news_confidence=row['news_confidence'],
                alignment=row['alignment'],
                alignment_score=row['alignment_score']
            ))
        
        conn.close()
        return results
    
    def get_stats(self) -> dict:
        """Get database statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Total records
        cursor.execute('SELECT COUNT(*) as total FROM analysis_results')
        total = cursor.fetchone()['total']
        
        # Unique tickers
        cursor.execute('SELECT COUNT(DISTINCT ticker) as unique_tickers FROM analysis_results')
        unique_tickers = cursor.fetchone()['unique_tickers']
        
        # Latest timestamp
        cursor.execute('SELECT MAX(timestamp) as latest FROM analysis_results')
        latest = cursor.fetchone()['latest']
        
        # High-confidence signals in last 24h
        since = datetime.now() - timedelta(hours=24)
        cursor.execute('''
            SELECT COUNT(*) as alerts 
            FROM analysis_results
            WHERE timestamp >= ?
            AND (score >= 70 OR news_confidence >= 60)
        ''', (since.isoformat(),))
        alerts = cursor.fetchone()['alerts']
        
        conn.close()
        
        return {
            'total_records': total,
            'unique_tickers': unique_tickers,
            'latest_analysis': latest,
            'alerts_24h': alerts
        }
    
    def cleanup_old_data(self, days: int = 30):
        """Remove data older than specified days"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cutoff = datetime.now() - timedelta(days=days)
        
        cursor.execute('''
            DELETE FROM analysis_results
            WHERE timestamp < ?
        ''', (cutoff.isoformat(),))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        print(f"🗑️  Cleaned up {deleted} old records (older than {days} days)")
        return deleted


if __name__ == '__main__':
    # Test database
    db = Database()
    
    # Save test entry
    result = db.save_analysis(
        ticker='TEST',
        score=75.5,
        category='BUY',
        rsi=28.5,
        trend='UPTREND',
        price=150.25,
        news_direction='BULLISH',
        news_confidence=65.0,
        alignment='CONFLUENCE',
        alignment_score=8.5
    )
    
    print(f"✅ Saved test result: {result.to_dict()}")
    
    # Get latest
    latest = db.get_latest_results(limit=5)
    print(f"\n📊 Latest {len(latest)} results:")
    for r in latest:
        print(f"  {r.ticker}: {r.score} ({r.category})")
    
    # Get stats
    stats = db.get_stats()
    print(f"\n📈 Database stats: {stats}")
