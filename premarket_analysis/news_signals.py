"""
Advanced News Parser and Market Signal Extractor
Analyzes news articles to predict market impact and direction
"""

import re
from typing import Dict, List, Tuple
from datetime import datetime


class NewsSignalExtractor:
    """Extracts actionable market signals from news articles."""
    
    # Market-moving keywords by category
    BULLISH_SIGNALS = {
        'earnings': [
            'beat earnings', 'exceeded expectations', 'surprise profit', 
            'strong earnings', 'record profit', 'earnings beat', 'topped estimates',
            'better than expected', 'blowout earnings', 'guidance raised'
        ],
        'growth': [
            'revenue surge', 'sales growth', 'record revenue', 'expanding market',
            'market share gain', 'user growth', 'customer growth', 'accelerating growth'
        ],
        'products': [
            'new product', 'product launch', 'innovation', 'breakthrough',
            'partnership', 'major deal', 'contract win', 'acquisition'
        ],
        'analyst': [
            'upgrade', 'price target raised', 'buy rating', 'outperform',
            'bullish', 'analyst optimistic', 'increased target'
        ],
        'guidance': [
            'raised guidance', 'increased forecast', 'optimistic outlook',
            'strong outlook', 'upbeat forecast', 'raised estimates'
        ]
    }
    
    BEARISH_SIGNALS = {
        'earnings': [
            'missed earnings', 'below expectations', 'earnings miss', 'profit warning',
            'disappointing results', 'weak earnings', 'missed estimates'
        ],
        'problems': [
            'lawsuit', 'investigation', 'regulatory', 'fine', 'scandal',
            'layoffs', 'job cuts', 'restructuring', 'bankruptcy', 'debt'
        ],
        'weakness': [
            'sales decline', 'revenue drop', 'losing market share', 'slowing growth',
            'demand weakness', 'margin pressure', 'competition'
        ],
        'analyst': [
            'downgrade', 'price target cut', 'sell rating', 'underperform',
            'bearish', 'analyst concerned', 'lowered target'
        ],
        'guidance': [
            'lowered guidance', 'cut forecast', 'weak outlook', 'cautious outlook',
            'reduced estimates', 'disappointing guidance'
        ]
    }
    
    # Magnitude indicators (multiply sentiment score)
    MAGNITUDE_HIGH = [
        'massive', 'huge', 'major', 'significant', 'substantial', 'dramatic',
        'record', 'unprecedented', 'historic', 'surge', 'plunge', 'soar'
    ]
    
    MAGNITUDE_MEDIUM = [
        'strong', 'solid', 'notable', 'considerable', 'meaningful'
    ]
    
    # Time urgency (affects catalyst score)
    URGENCY_IMMEDIATE = [
        'today', 'breaking', 'just announced', 'now', 'this morning',
        'moments ago', 'alert'
    ]
    
    URGENCY_NEAR = [
        'tomorrow', 'this week', 'upcoming', 'soon', 'next week'
    ]
    
    def __init__(self):
        self.signal_cache = {}
    
    def extract_signals(self, headline: str, article_text: str = None) -> Dict:
        """
        Extract market signals from news article.
        
        Args:
            headline: Article headline
            article_text: Full article text (optional, uses headline if None)
            
        Returns:
            Dictionary with signal analysis
        """
        text = (headline + " " + (article_text or "")).lower()
        
        # Extract signals
        bullish_signals = self._find_signals(text, self.BULLISH_SIGNALS)
        bearish_signals = self._find_signals(text, self.BEARISH_SIGNALS)
        
        # Calculate magnitude
        magnitude = self._calculate_magnitude(text)
        
        # Calculate urgency
        urgency = self._calculate_urgency(text)
        
        # Determine primary catalyst
        catalyst = self._identify_catalyst(bullish_signals, bearish_signals)
        
        # Calculate directional bias
        bullish_count = sum(len(v) for v in bullish_signals.values())
        bearish_count = sum(len(v) for v in bearish_signals.values())
        
        if bullish_count == 0 and bearish_count == 0:
            direction = 'NEUTRAL'
            confidence = 0.0
        elif bullish_count > bearish_count:
            direction = 'BULLISH'
            confidence = min(1.0, bullish_count / (bullish_count + bearish_count + 1))
        else:
            direction = 'BEARISH'
            confidence = min(1.0, bearish_count / (bullish_count + bearish_count + 1))
        
        # Calculate market impact score (0-100)
        base_impact = (bullish_count + bearish_count) * 10
        impact_score = min(100, base_impact * magnitude * urgency)
        
        return {
            'direction': direction,
            'confidence': round(confidence, 2),
            'impact_score': round(impact_score, 1),
            'magnitude': magnitude,
            'urgency': urgency,
            'catalyst': catalyst,
            'bullish_signals': bullish_signals,
            'bearish_signals': bearish_signals,
            'signal_count': bullish_count + bearish_count
        }
    
    def _find_signals(self, text: str, signal_dict: Dict) -> Dict[str, List[str]]:
        """Find matching signals in text."""
        found = {}
        for category, keywords in signal_dict.items():
            matches = [kw for kw in keywords if kw in text]
            if matches:
                found[category] = matches
        return found
    
    def _calculate_magnitude(self, text: str) -> float:
        """Calculate magnitude multiplier (1.0-2.0)."""
        high_count = sum(1 for word in self.MAGNITUDE_HIGH if word in text)
        medium_count = sum(1 for word in self.MAGNITUDE_MEDIUM if word in text)
        
        if high_count >= 2:
            return 2.0
        elif high_count == 1:
            return 1.5
        elif medium_count >= 1:
            return 1.2
        else:
            return 1.0
    
    def _calculate_urgency(self, text: str) -> float:
        """Calculate urgency multiplier (1.0-1.5)."""
        if any(word in text for word in self.URGENCY_IMMEDIATE):
            return 1.5
        elif any(word in text for word in self.URGENCY_NEAR):
            return 1.2
        else:
            return 1.0
    
    def _identify_catalyst(self, bullish: Dict, bearish: Dict) -> str:
        """Identify primary catalyst type."""
        all_signals = {**bullish, **bearish}
        
        if not all_signals:
            return 'NONE'
        
        # Find category with most signals
        max_category = max(all_signals.items(), key=lambda x: len(x[1]))
        return max_category[0].upper()
    
    def analyze_multiple_articles(self, articles: List[Tuple[str, datetime]]) -> Dict:
        """
        Analyze multiple articles for aggregate signals.
        
        Args:
            articles: List of (headline, publish_date) tuples
            
        Returns:
            Aggregated signal analysis
        """
        if not articles:
            return {
                'aggregate_direction': 'NEUTRAL',
                'aggregate_confidence': 0.0,
                'aggregate_impact': 0.0,
                'dominant_catalyst': 'NONE',
                'signal_consistency': 0.0,
                'recent_trend': 'NEUTRAL'
            }
        
        # Analyze each article
        signals = []
        for headline, pub_date in articles:
            signal = self.extract_signals(headline)
            signal['pub_date'] = pub_date
            signals.append(signal)
        
        # Calculate aggregate metrics
        bullish_count = sum(1 for s in signals if s['direction'] == 'BULLISH')
        bearish_count = sum(1 for s in signals if s['direction'] == 'BEARISH')
        neutral_count = len(signals) - bullish_count - bearish_count
        
        # Aggregate direction
        if bullish_count > bearish_count + 1:
            agg_direction = 'BULLISH'
            agg_confidence = bullish_count / len(signals)
        elif bearish_count > bullish_count + 1:
            agg_direction = 'BEARISH'
            agg_confidence = bearish_count / len(signals)
        else:
            agg_direction = 'MIXED'
            agg_confidence = max(bullish_count, bearish_count) / len(signals)
        
        # Average impact
        avg_impact = sum(s['impact_score'] for s in signals) / len(signals)
        
        # Dominant catalyst
        catalysts = [s['catalyst'] for s in signals if s['catalyst'] != 'NONE']
        if catalysts:
            dominant_catalyst = max(set(catalysts), key=catalysts.count)
        else:
            dominant_catalyst = 'NONE'
        
        # Signal consistency (how aligned are the signals?)
        max_direction_count = max(bullish_count, bearish_count, neutral_count)
        consistency = max_direction_count / len(signals)
        
        # Recent trend (last 3 articles weighted more)
        recent_signals = signals[:3]
        recent_bullish = sum(1 for s in recent_signals if s['direction'] == 'BULLISH')
        recent_bearish = sum(1 for s in recent_signals if s['direction'] == 'BEARISH')
        
        if recent_bullish > recent_bearish:
            recent_trend = 'BULLISH'
        elif recent_bearish > recent_bullish:
            recent_trend = 'BEARISH'
        else:
            recent_trend = 'NEUTRAL'
        
        return {
            'aggregate_direction': agg_direction,
            'aggregate_confidence': round(agg_confidence, 2),
            'aggregate_impact': round(avg_impact, 1),
            'dominant_catalyst': dominant_catalyst,
            'signal_consistency': round(consistency, 2),
            'recent_trend': recent_trend,
            'article_breakdown': {
                'total': len(signals),
                'bullish': bullish_count,
                'bearish': bearish_count,
                'neutral': neutral_count
            },
            'top_signals': sorted(signals, key=lambda x: x['impact_score'], reverse=True)[:3]
        }
    
    def get_prediction_confidence(self, aggregate_analysis: Dict) -> str:
        """
        Get human-readable prediction confidence.
        
        Args:
            aggregate_analysis: Output from analyze_multiple_articles
            
        Returns:
            Confidence level description
        """
        confidence = aggregate_analysis['aggregate_confidence']
        consistency = aggregate_analysis['signal_consistency']
        impact = aggregate_analysis['aggregate_impact']
        
        # High confidence criteria
        if confidence >= 0.7 and consistency >= 0.7 and impact >= 60:
            return 'HIGH - Strong predictive signal'
        elif confidence >= 0.6 and consistency >= 0.6 and impact >= 40:
            return 'MODERATE - Decent predictive signal'
        elif confidence >= 0.5:
            return 'LOW - Weak predictive signal'
        else:
            return 'VERY LOW - Noise, not predictive'
    
    def predict_direction(self, aggregate_analysis: Dict) -> Dict:
        """
        Make directional prediction based on news analysis.
        
        Returns:
            Prediction with confidence and reasoning
        """
        direction = aggregate_analysis['aggregate_direction']
        confidence = aggregate_analysis['aggregate_confidence']
        impact = aggregate_analysis['aggregate_impact']
        catalyst = aggregate_analysis['dominant_catalyst']
        recent_trend = aggregate_analysis['recent_trend']
        consistency = aggregate_analysis['signal_consistency']
        
        # Prediction logic
        if direction in ['BULLISH', 'BEARISH'] and confidence >= 0.6:
            prediction = direction
            strength = 'STRONG' if confidence >= 0.75 else 'MODERATE'
        elif recent_trend in ['BULLISH', 'BEARISH'] and impact >= 50:
            # Use recent trend if aggregate is mixed but recent news is strong
            prediction = recent_trend
            strength = 'EMERGING'
        else:
            prediction = 'NEUTRAL'
            strength = 'UNCLEAR'
        
        # Generate reasoning
        reasons = []
        if consistency >= 0.7:
            reasons.append(f'{int(consistency*100)}% of articles aligned')
        if impact >= 60:
            reasons.append(f'High impact catalyst: {catalyst}')
        if recent_trend != 'NEUTRAL' and recent_trend != direction:
            reasons.append(f'Recent trend shifting {recent_trend}')
        
        return {
            'prediction': prediction,
            'strength': strength,
            'confidence_score': round(confidence * 100, 0),
            'expected_move': self._estimate_move_size(impact, confidence),
            'catalyst': catalyst,
            'reasoning': reasons if reasons else ['Insufficient signal strength'],
            'confidence_level': self.get_prediction_confidence(aggregate_analysis)
        }
    
    def _estimate_move_size(self, impact: float, confidence: float) -> str:
        """Estimate expected price move magnitude."""
        combined = impact * confidence
        
        if combined >= 70:
            return 'LARGE (>5%)'
        elif combined >= 50:
            return 'MODERATE (2-5%)'
        elif combined >= 30:
            return 'SMALL (1-2%)'
        else:
            return 'MINIMAL (<1%)'


def format_signal_report(ticker: str, articles: List[Tuple[str, datetime]], 
                        extractor: NewsSignalExtractor) -> str:
    """
    Generate formatted report of news signals and prediction.
    
    Args:
        ticker: Stock ticker
        articles: List of (headline, datetime) tuples
        extractor: NewsSignalExtractor instance
        
    Returns:
        Formatted string report
    """
    agg = extractor.analyze_multiple_articles(articles)
    pred = extractor.predict_direction(agg)
    
    report = f"""
{'='*70}
📰 NEWS SIGNAL ANALYSIS: {ticker}
{'='*70}

📊 AGGREGATE ANALYSIS ({agg['article_breakdown']['total']} articles):
   Direction: {agg['aggregate_direction']} ({agg['aggregate_confidence']*100:.0f}% confidence)
   Impact Score: {agg['aggregate_impact']:.0f}/100
   Dominant Catalyst: {agg['dominant_catalyst']}
   Signal Consistency: {agg['signal_consistency']*100:.0f}%
   Recent Trend: {agg['recent_trend']}

🎯 MARKET PREDICTION:
   Prediction: {pred['prediction']} ({pred['strength']})
   Confidence: {pred['confidence_score']:.0f}%
   Expected Move: {pred['expected_move']}
   {pred['confidence_level']}

💡 KEY SIGNALS:
"""
    
    for i, signal in enumerate(agg['top_signals'], 1):
        report += f"\n   {i}. Impact: {signal['impact_score']:.0f}/100 | {signal['direction']} | {signal['catalyst']}\n"
        if signal['bullish_signals']:
            report += f"      Bullish: {', '.join(sum(signal['bullish_signals'].values(), []))}\n"
        if signal['bearish_signals']:
            report += f"      Bearish: {', '.join(sum(signal['bearish_signals'].values(), []))}\n"
    
    report += f"\n📈 REASONING:\n"
    for reason in pred['reasoning']:
        report += f"   • {reason}\n"
    
    report += f"\n{'='*70}\n"
    
    return report
