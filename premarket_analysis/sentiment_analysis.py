"""
Sentiment analysis for news headlines
"""

from datetime import datetime
from typing import List, Tuple
import math
import logging
from .config import *
from .market_data import get_et_time_naive

logger = logging.getLogger(__name__)


def analyze_sentiment_simple(headlines: List[Tuple[str, datetime]]) -> float:
    """
    Enhanced keyword-based sentiment analysis with recency weighting.
    Only applies recency weighting when pub_date is valid.
    
    Args:
        headlines: List of (headline, datetime) tuples
        
    Returns:
        Sentiment score from -1 to 1
    """
    if not headlines:
        return 0.0
    
    # Define keyword lists
    positive_keywords = [
        'surge', 'rally', 'beat', 'exceeds', 'growth', 'bullish', 'buy',
        'upgrade', 'outperform', 'strong', 'record', 'profit', 'earnings beat',
        'innovation', 'breakthrough', 'partnership', 'acquisition', 'gain',
        'soars', 'jumps', 'rises', 'climbs', 'tops'
    ]
    
    negative_keywords = [
        'plunge', 'crash', 'decline', 'miss', 'bearish', 'sell', 'downgrade',
        'underperform', 'weak', 'loss', 'lawsuit', 'investigation', 'fine',
        'concern', 'risk', 'warning', 'layoff', 'cut', 'disappointing',
        'falls', 'drops', 'tumbles', 'slumps', 'sinks'
    ]
    
    # High-impact keywords (double weight)
    high_impact_keywords = [
        'earnings', 'lawsuit', 'investigation', 'fda approval', 'merger',
        'acquisition', 'bankruptcy', 'recall', 'scandal', 'fraud',
        'regulatory', 'sec', 'criminal'
    ]
    
    sentiment_sum = 0
    weight_sum = 0
    now = get_et_time_naive()
    
    for headline, pub_date in headlines:
        headline_lower = headline.lower()
        
        # Calculate recency weight only if pub_date is valid
        # (not a fallback datetime.now() from failed parsing)
        recency_weight = 1.0  # Default weight
        
        if pub_date is not None:
            try:
                # Ensure timezone-naive for safe datetime arithmetic
                pub_date_naive = pub_date.replace(tzinfo=None) if hasattr(pub_date, 'tzinfo') and pub_date.tzinfo else pub_date
                hours_old = (now - pub_date_naive).total_seconds() / 3600
                
                # Only apply recency decay if hours_old is reasonable (0 to NEWS_LOOKBACK_HOURS)
                if 0 <= hours_old <= NEWS_LOOKBACK_HOURS * 1.5:
                    recency_weight = math.exp(-hours_old / 12)  # Half weight after 8.3 hours
            except:
                # If date arithmetic fails, use default weight
                pass
        
        # Check for high-impact keywords (2x multiplier)
        impact_multiplier = 2.0 if any(keyword in headline_lower for keyword in high_impact_keywords) else 1.0
        
        # Count positive keywords
        positive_count = sum(1 for word in positive_keywords if word in headline_lower)
        
        # Count negative keywords
        negative_count = sum(1 for word in negative_keywords if word in headline_lower)
        
        # Calculate headline sentiment
        if positive_count + negative_count > 0:
            headline_sentiment = (positive_count - negative_count) / (positive_count + negative_count)
            final_weight = recency_weight * impact_multiplier
            sentiment_sum += headline_sentiment * final_weight
            weight_sum += final_weight
    
    # Weighted average sentiment
    if weight_sum > 0:
        avg_sentiment = sentiment_sum / weight_sum
        # Normalize to -1 to 1 range
        return max(-1.0, min(1.0, avg_sentiment))
    
    return 0.0


def analyze_sentiment_ai(headlines: List[Tuple[str, datetime]], ticker: str) -> float:
    """
    AI-powered sentiment analysis using Gemini API.
    
    Args:
        headlines: List of (headline, datetime) tuples
        ticker: Stock ticker symbol
        
    Returns:
        Sentiment score from -1 to 1
    """
    # Fallback to simple if AI not configured
    if not USE_AI_SENTIMENT or AI_API_KEY == "YOUR_AI_API_KEY_HERE":
        return analyze_sentiment_simple(headlines)
    
    try:
        import google.generativeai as genai
        
        # Configure Gemini
        genai.configure(api_key=AI_API_KEY)
        
        # Try multiple model names in order of preference
        model_names = [
            'gemini-2.5-flash',      # Current stable (Feb 2026)
            'gemini-flash-latest',   # Latest flash variant
            'gemini-2.0-flash',      # Fallback to 2.0
            'gemini-pro-latest'      # Fallback to pro
        ]
        
        model = None
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                logger.debug(f"   Using Gemini model: {model_name}")
                break
            except:
                continue
        
        if model is None:
            logger.warning(f"   No Gemini models available, falling back to keyword sentiment")
            return analyze_sentiment_simple(headlines)
        
        # Extract just headlines (up to 15 most recent)
        headline_texts = [h for h, _ in headlines[:15]]
        
        if not headline_texts:
            return 0.0
        
        # Limit to 10 headlines to keep prompt short
        headlines_str = "\n".join([f"{i+1}. {h[:100]}" for i, h in enumerate(headline_texts[:10])])
        
        prompt = f"""Analyze the sentiment of these {ticker} news headlines. Reply with only a decimal number between -1.0 and 1.0:

{headlines_str}

Score:"""
        
        # Call Gemini with simple settings
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=100,
                )
            )
        except Exception as api_error:
            error_msg = str(api_error)[:150]
            logger.warning(f"   Gemini API error for {ticker}: {error_msg}")
            return analyze_sentiment_simple(headlines)
        
        # Parse the response
        score_text = None
        
        # Try method 1: response.parts accessor (recommended)
        try:
            if response.parts:
                score_text = response.parts[0].text.strip()
                logger.debug(f"   Extracted via response.parts")
        except Exception as e:
            logger.debug(f"   Method 1 failed: {e}")
        
        # Try method 2: response.text simple accessor
        if not score_text:
            try:
                score_text = response.text.strip()
                logger.debug(f"   Extracted via response.text")
            except Exception as e:
                logger.debug(f"   Method 2 failed: {e}")
        
        # Try method 3: response.candidates path
        if not score_text:
            try:
                if response.candidates and response.candidates[0].content.parts:
                    score_text = response.candidates[0].content.parts[0].text.strip()
                    logger.debug(f"   Extracted via response.candidates")
            except Exception as e:
                logger.debug(f"   Method 3 failed: {e}")
        
        # If all methods failed, fall back
        if not score_text:
            logger.warning(f"   Could not parse Gemini response for {ticker}, using simple sentiment")
            return analyze_sentiment_simple(headlines)
        
        # Debug: show what we got
        logger.debug(f"   Raw Gemini response: '{score_text}'")
        
        # Extract number from response (handle various formats)
        import re
        numbers = re.findall(r'-?\d+\.?\d*', score_text)
        if numbers:
            score = float(numbers[0])
            # Clamp to [-1, 1]
            score = max(-1.0, min(1.0, score))
            logger.debug(f"   AI sentiment for {ticker}: {score:.2f}")
            return score
        else:
            logger.warning(f"   Could not parse AI response '{score_text}', using simple sentiment")
            return analyze_sentiment_simple(headlines)
            
    except ImportError:
        logger.warning("   google-generativeai not installed. Run: pip install google-generativeai")
        logger.warning("   Falling back to keyword-based sentiment")
        return analyze_sentiment_simple(headlines)
    except Exception as e:
        logger.warning(f"   AI sentiment error for {ticker}: {str(e)}")
        logger.warning("   Falling back to keyword-based sentiment")
        return analyze_sentiment_simple(headlines)


def get_sentiment_label(sentiment: float) -> str:
    """Convert sentiment score to label."""
    if sentiment > 0.7:
        return "Very Bull"
    elif sentiment > 0.3:
        return "Bullish"
    elif sentiment > -0.3:
        return "Neutral"
    elif sentiment > -0.7:
        return "Bearish"
    else:
        return "Very Bear"
