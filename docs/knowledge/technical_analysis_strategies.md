---
title: "Technical Analysis Strategies"
version: "2.0"
last_updated: "2025-07-16"
tags: [TA, order-flow, volume-profile, perp-funding, ATR]
---

## Key Takeaways
1. **Order-Flow & Volume-Profile** → Strukturelle Support/Resistance.  
2. **Perp-Funding-Divergenz** triggert Swing-Entries  
3. **ATR-Parameter 2025** – Krypto-Volatilität – 10-Day ATR x 2.6 für Breakout-SL.  
4. **Algorithmic Strategy Blocks** – GPT kann Snippets kombinieren.  
5. **Backtest → Walk-Forward** – Min 3 rolled periods.

## Use-in-GPT
- „Generiere Pine-Script für ETH Funding-Rate Divergence Strategy“  
- „Erstelle einen Volume-Profile Chart mit Value-Area für SOLUSDT“  

---

## 1 | Order-Flow Basics
* **CVD**, **Delta**, **Imbalance Heatmaps** – cluster auf 1 min.  
* Auction-Theory (POC, VAH, VAL) aus **Volume-Profile** – 70 %-Rule.

---

## 2 | Funding-Rate Divergence Strategy
```pinescript
indicator("Funding-Divergence", overlay=true)
fund = request.security("BINANCE:BTCUSDTPERP", "60", funding())
emaFund = ta.ema(fund, 24)
price = close

longCond  = fund < 0 and ta.crossover(fund, emaFund)
shortCond = fund > 0 and ta.crossunder(fund, emaFund)

strategy.entry("Long",  strategy.long,  when=longCond)
strategy.entry("Short", strategy.short, when=shortCond)
```

---

## 3 | ATR Breakout-SL
* `SL = Entry – 2.6 * ATR(10)`  (Backtest-P90 Drawdown < 9 %).  
* Trailing Every 4 h.

---

## 4 | Risk Overlay & Checklist
1. **Daily ATR < 12 %** für Trend-Signals.  
2. Funding Regime = Neutral.  
3. No Major Macro Event in next 48 h.  
