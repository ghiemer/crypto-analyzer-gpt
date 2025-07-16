# 📊 CustomGPT Technical Analysis Examples

## 🎯 Example 1: Complete Bitcoin Analysis

### **User Prompt**: "Analyze Bitcoin's current technical situation"

### **CustomGPT Response Process**:

```python
# Step 1: Collect comprehensive data
GET /candles?symbol=BTCUSDT&indicators=all&limit=200

# Step 2: Get market sentiment
GET /misc/feargreed

# Step 3: Check recent news
GET /news?coin=bitcoin

# Step 4: Futures data
GET /perp/funding?symbol=BTCUSDT
```

### **Expected Analysis Output**:

```markdown
# 📊 Bitcoin Technical Analysis
**Current Price**: $67,450 | **Timeframe**: 1H | **Updated**: 2025-07-16 14:30 UTC

## 🔍 Quick Summary
- **Trend**: Bullish (Short-term consolidation in uptrend)
- **Signal**: HOLD/BUY on dips
- **Confidence**: High (85%)
- **Risk Level**: Medium

## 📈 Trend Analysis
- **Short-term (SMA20)**: $66,200 - Price above, bullish
- **Medium-term (SMA50)**: $64,800 - Strong support, bullish
- **Long-term (SMA200)**: $58,500 - Well above, strong bull trend
- **EMA Crossover**: EMA12 (67,100) > EMA26 (66,500) - Bullish momentum

## ⚡ Momentum Indicators
- **RSI14**: 58.5 (Neutral - healthy pullback from overbought)
- **RSI21**: 62.1 (Slightly bullish, no divergence)
- **MACD**: 1,250 above signal line (850) - Bullish momentum
- **Stochastic**: %K(65) > %D(60) - Bullish crossover

## 📊 Volatility Analysis
- **Bollinger Bands**: Price near middle band (66,800)
- **Upper Band**: $69,200 (resistance)
- **Lower Band**: $64,400 (support)
- **Band Width**: Expanding (increasing volatility)

## 🎯 Key Levels
- **Immediate Resistance**: $68,500 (Previous high)
- **Major Resistance**: $70,000 (Psychological level)
- **Support**: $66,000 (SMA20 + previous low)
- **Strong Support**: $64,800 (SMA50)
- **Stop Loss**: $64,000 (Below SMA50)

## 😱 Market Sentiment
- **Fear & Greed Index**: 72 (Greed)
- **Sentiment Impact**: Bullish but approaching euphoria
- **Interpretation**: Market optimistic but watch for overheating

## 📰 News Impact
- **Recent News**: SEC Bitcoin ETF approval rumors
- **Market Impact**: Positive (driving institutional interest)
- **Funding Rate**: 0.02% (Slightly bullish, not extreme)

## 🎯 Trading Recommendation
**Action**: BUY on dips / HOLD existing positions
**Entry Zone**: $66,000 - $66,500
**Target 1**: $68,500 (3.5% gain)
**Target 2**: $70,000 (6% gain)
**Stop Loss**: $64,000 (3% risk)
**Risk/Reward**: 1:2 (Favorable)

## 📚 Educational Insight
The current setup shows a classic "bull flag" pattern with healthy consolidation after a strong move. The RSI cooling off from overbought levels while maintaining above 50 suggests continued bullish momentum. Watch for volume increase on the next move up.
```

---

## 🎯 Example 2: Ethereum Momentum Analysis

### **User Prompt**: "Is Ethereum showing bullish momentum?"

### **CustomGPT Response Process**:

```python
# Focus on momentum indicators
GET /candles?symbol=ETHUSDT&indicators=rsi14,rsi21,macd,macd_signal,ema12,ema26&limit=50

# Check broader context
GET /misc/feargreed
GET /news?coin=ethereum
```

### **Expected Analysis Output**:

```markdown
# ⚡ Ethereum Momentum Analysis
**Current Price**: $3,850 | **Focus**: Momentum Indicators

## 🚀 Momentum Assessment: BULLISH

### **RSI Analysis**
- **RSI14**: 67.2 (Approaching overbought - strong momentum)
- **RSI21**: 63.8 (Confirming bullish momentum)
- **Divergence**: None detected (healthy momentum)

### **MACD Analysis**
- **MACD Line**: 45.2 (Above signal line 38.7)
- **Histogram**: Expanding (increasing momentum)
- **Signal**: Recent bullish crossover 3 days ago

### **EMA Analysis**
- **EMA12**: $3,820 (Price above - bullish)
- **EMA26**: $3,750 (Strong upward slope)
- **Crossover**: EMA12 > EMA26 (Bullish momentum confirmed)

## 🎯 Momentum Conclusion
**Strength**: High (8/10)
**Sustainability**: Medium-High (momentum indicators healthy)
**Next Move**: Likely continuation to $4,000-$4,200

## ⚠️ Risk Factors
- RSI approaching overbought (70) - watch for pullback
- Need volume confirmation on next breakout
- General market correlation with Bitcoin

## 📊 Trading Implication
Strong momentum suggests continuation, but prepare for potential pullback at $4,000 psychological level.
```

---

## 🎯 Example 3: Multi-Timeframe Analysis

### **User Prompt**: "Give me a complete multi-timeframe analysis of Solana"

### **CustomGPT Response Process**:

```python
# Daily trend
GET /candles?symbol=SOLUSDT&granularity=1d&indicators=sma50,sma200,rsi14&limit=100

# 4H momentum
GET /candles?symbol=SOLUSDT&granularity=4h&indicators=macd,bb_upper,bb_lower,rsi14&limit=50

# 1H entry signals
GET /candles?symbol=SOLUSDT&granularity=1h&indicators=ema12,ema26,stoch_k,stoch_d&limit=30
```

### **Expected Analysis Output**:

```markdown
# 📊 Solana Multi-Timeframe Analysis
**Current Price**: $185.50

## 📅 Daily Timeframe (Trend)
- **Trend**: Bullish (Price above SMA50: $175)
- **SMA200**: $145 (Strong bull market)
- **RSI14**: 61.2 (Healthy uptrend)
- **Assessment**: Strong uptrend intact

## ⏱️ 4H Timeframe (Momentum)
- **MACD**: Bullish crossover confirmed
- **Bollinger Bands**: Price near upper band ($187)
- **RSI14**: 68.5 (Approaching overbought)
- **Assessment**: Strong momentum, nearing exhaustion

## 🔄 1H Timeframe (Entry)
- **EMA12/26**: Bullish crossover at $182
- **Stochastic**: %K(75) > %D(65) - Overbought
- **Assessment**: Short-term pullback likely

## 🎯 Multi-Timeframe Conclusion
- **Long-term**: Bullish trend
- **Medium-term**: Strong momentum
- **Short-term**: Overbought, pullback due

## 📈 Trading Strategy
**Approach**: Wait for pullback to $180-$182 area
**Target**: $195-$200 (next resistance zone)
**Stop**: $175 (Daily SMA50)
**Timeframe**: 3-7 days holding period
```

---

## 🎯 Example 4: Risk Assessment Analysis

### **User Prompt**: "What's the risk level of buying ADA right now?"

### **CustomGPT Response Process**:

```python
# Current technical state
GET /candles?symbol=ADAUSDT&indicators=all&limit=100

# Market context
GET /misc/feargreed
GET /news?coin=cardano
```

### **Expected Analysis Output**:

```markdown
# ⚠️ ADA Risk Assessment
**Current Price**: $0.485 | **Risk Level**: HIGH

## 🔍 Risk Factors Identified

### **Technical Risks**
- **Trend**: Bearish (Below all major SMAs)
- **RSI**: 35.2 (Oversold but no bounce yet)
- **MACD**: Still negative (Bearish momentum)
- **Support**: Limited support until $0.42

### **Market Risks**
- **Fear & Greed**: 28 (Fear) - General market weakness
- **Bitcoin Correlation**: 0.85 (High correlation risk)
- **Volume**: Declining (Lack of interest)

### **Fundamental Risks**
- **News**: Limited positive catalysts
- **Development**: Slow ecosystem growth
- **Competition**: Losing market share to other L1s

## 🎯 Risk Scoring
- **Technical Risk**: 7/10 (High)
- **Market Risk**: 6/10 (Medium-High)
- **Fundamental Risk**: 5/10 (Medium)
- **Overall Risk**: 7/10 (HIGH)

## 💡 Risk Management
If buying:
- **Position Size**: Maximum 1% of portfolio
- **Stop Loss**: $0.45 (7% risk)
- **Time Horizon**: Long-term only
- **DCA Strategy**: Consider dollar-cost averaging

## 🎯 Recommendation
**AVOID** short-term positions. Only consider for long-term DCA strategy with strict risk management.
```

---

## 🎯 Example 5: Divergence Analysis

### **User Prompt**: "Check for any divergences in Bitcoin's indicators"

### **CustomGPT Response Process**:

```python
# Get recent data for divergence analysis
GET /candles?symbol=BTCUSDT&indicators=rsi14,rsi21,macd,macd_signal&limit=50

# Check multiple timeframes
GET /candles?symbol=BTCUSDT&granularity=4h&indicators=rsi14,macd&limit=30
```

### **Expected Analysis Output**:

```markdown
# 🔍 Bitcoin Divergence Analysis
**Analysis Period**: Last 30 candles (1H timeframe)

## 📊 RSI Divergence Check
### **Bullish Divergence DETECTED**
- **Price Action**: Lower low at $65,200 (July 10)
- **RSI14**: Higher low at 28.5 (vs previous 25.1)
- **Confirmation**: RSI21 shows same pattern
- **Strength**: Medium (clear but not extreme)

## 📈 MACD Divergence Check
### **No Significant Divergence**
- **MACD**: Following price action normally
- **Histogram**: Decreasing but no divergence
- **Signal**: Neutral

## 🎯 Divergence Implications
### **Bullish RSI Divergence Suggests**:
- **Selling Pressure**: Decreasing
- **Reversal Probability**: 65%
- **Next Target**: $67,500 (previous resistance)
- **Confirmation Needed**: Break above $66,500

## 📊 Trading Strategy
**Setup**: Bullish divergence play
**Entry**: $65,800 - $66,200
**Target**: $67,500 (First resistance)
**Stop**: $64,800 (Below divergence low)
**Risk/Reward**: 1:2.5 (Favorable)

## ⚠️ Warnings
- Divergences are early signals, not guarantees
- Wait for price confirmation before entering
- Consider broader market context
```

---

## 🎯 Example 6: Scalping Setup Analysis

### **User Prompt**: "Give me a 15-minute scalping setup for Ethereum"

### **CustomGPT Response Process**:

```python
# Short-term data for scalping
GET /candles?symbol=ETHUSDT&granularity=15m&indicators=ema12,ema26,rsi14,stoch_k,stoch_d&limit=20

# Quick sentiment check
GET /misc/feargreed
```

### **Expected Analysis Output**:

```markdown
# ⚡ Ethereum 15M Scalping Setup
**Current Price**: $3,842 | **Timeframe**: 15-minute | **Style**: Scalping

## 🎯 Setup Identification
**Pattern**: EMA bounce setup
**Direction**: LONG
**Quality**: B+ (Good probability)

## 📊 Technical Setup
- **EMA12**: $3,840 (Price touching)
- **EMA26**: $3,835 (Support confluence)
- **RSI14**: 45.2 (Oversold bounce potential)
- **Stochastic**: %K(25) oversold, %D(35) - Bullish divergence

## 🎯 Scalping Parameters
**Entry**: $3,840 - $3,845 (Current area)
**Target 1**: $3,860 (20 pips) - Quick scalp
**Target 2**: $3,875 (35 pips) - Extended move
**Stop Loss**: $3,825 (15 pips risk)
**Risk/Reward**: 1:1.3 to 1:2.3

## ⏱️ Timing
- **Best Entry**: Next 15-30 minutes
- **Hold Time**: 30-90 minutes maximum
- **Exit Strategy**: Close 50% at Target 1, trail stop for remainder

## ⚠️ Scalping Warnings
- **High Risk**: Requires tight stops
- **Commission**: Consider trading fees
- **Slippage**: Use limit orders
- **Market Hours**: Best during high volume periods

## 📊 Confluence Factors
✅ EMA support
✅ RSI oversold bounce
✅ Stochastic bullish divergence
❌ Volume confirmation needed
❌ Broader trend mixed

**Confidence**: 65% (Medium)
```

---

## 🎓 Key Learning Points

### **For CustomGPT Implementation**:

1. **Always Structure Analysis**: Use consistent formatting
2. **Provide Context**: Include market sentiment and news
3. **Risk Management**: Always include stops and position sizing
4. **Educational Value**: Explain why indicators matter
5. **Confidence Levels**: Be honest about uncertainty
6. **Multiple Confirmations**: Never rely on single indicators
7. **Timeframe Awareness**: Match analysis to user's timeframe
8. **Clear Actionables**: Give specific entry/exit levels

### **Response Quality Indicators**:
- ✅ Specific price levels provided
- ✅ Risk/reward ratios calculated
- ✅ Multiple indicator confirmation
- ✅ Market context included
- ✅ Educational explanations given
- ✅ Confidence levels stated
- ✅ Proper risk management advice

These examples show how CustomGPT should leverage the API to provide comprehensive, actionable, and educational cryptocurrency analysis.
