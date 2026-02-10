from premarket_analysis.main_with_scoring import analyze_ticker_with_scoring

result = analyze_ticker_with_scoring('AMZN')

print('\n📊 AMZN CURRENT SCORE BREAKDOWN')
print('='*70)
print(f'Overall Score: {result["score"]:.1f}/100 - {result["score_category"]}')
print(f'Need: 75+ for STRONG_BUY, 65+ for BUY')
print()

print('🔍 CURRENT CONDITIONS:')
print(f'   RSI: {result["rsi"]:.1f} (need <30 for STRONG_BUY, <35 for BUY)')
print(f'   BB Status: {result["bb_status"]} (need BELOW_LOWER or LOWER_HALF)')
print(f'   Trend: {result["trend"]} (need UPTREND)')
print(f'   Sentiment: {result["sentiment"]:+.2f} (positive is good)')
print(f'   News Count: {result["news_count"]} articles')
print()

print('📊 COMPONENT SCORES:')
comps = result['score_components']
for name, data in comps.items():
    score = data['score']
    weight = data['weight']
    contribution = score * weight
    print(f'   {name.capitalize():12s}: {score:5.1f}/100 × {weight:.2f} = {contribution:5.1f} pts')

print()
base_score = result['score_components']['technical']['score'] * 0.30 + \
             result['score_components']['sentiment']['score'] * 0.25 + \
             result['score_components']['momentum']['score'] * 0.20 + \
             result['score_components']['catalyst']['score'] * 0.15 + \
             result['score_components']['timing']['score'] * 0.10
print(f'   BASE SCORE (before penalties): {base_score:.1f}')
print()

print('⚠️  ADJUSTMENTS/PENALTIES:')
if result['score_adjustments']:
    for adj in result['score_adjustments']:
        print(f'   • {adj}')
else:
    print('   (none)')

print()
print('='*70)
print('🎯 WHAT NEEDS TO CHANGE FOR AMZN TO SCORE 75+:')
print('='*70)

current_rsi = result["rsi"]
current_trend = result["trend"]
current_bb = result["bb_status"]

improvements_needed = []

if current_rsi > 30:
    improvements_needed.append(f'   📉 RSI: {current_rsi:.1f} → needs to drop to <30 (more selling)')

if current_trend != 'UPTREND':
    improvements_needed.append(f'   📈 TREND: {current_trend} → needs to become UPTREND (price reversal)')

if current_bb not in ['BELOW_LOWER', 'LOWER_HALF']:
    improvements_needed.append(f'   📊 BB: {current_bb} → needs BELOW_LOWER or LOWER_HALF (deeper dip)')

if improvements_needed:
    for improvement in improvements_needed:
        print(improvement)
else:
    print('   ✅ All technical requirements met!')

print()
print('SCENARIO: If AMZN reaches ideal entry conditions:')
print('   • RSI drops to 28 (oversold)')
print('   • Price dips to lower BB')
print('   • Trend reverses to UPTREND')
print('   • Sentiment stays positive')
print('   → Score would be: 85-90/100 (STRONG_BUY)')
print()
