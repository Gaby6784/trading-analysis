"""
Pre-Market Stock Analysis Tool
Modular version with improved architecture

Modules:
- config: Configuration settings
- market_data: Market data fetching and time utilities
- technical_indicators: Technical analysis calculations
- news_fetching: Multi-source news fetching with caching
- sentiment_analysis: Sentiment scoring for news
- recommendation: Trading recommendation generation
- output: Display and formatting
- main: Main orchestration
"""

from .main import main

__version__ = "2.0.0"
__all__ = ['main']
