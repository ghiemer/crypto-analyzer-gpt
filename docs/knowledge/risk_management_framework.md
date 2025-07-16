---
title: "Risk Management Framework"
version: "2.0"
last_updated: "2025-07-16"
tags: [risk, position-size, VaR, MiCA, depeg]
---

## Key Takeaways
1. **Position-Sizing = f(Portfolio VaR, Asset Vol, Conviction).**  
2. **MiCA-Lizenz & Proof-of-Reserve** jetzt Pflicht ab 2025  
3. **Stablecoin-Depeg Risiko** – Szenario-Bäume & Hedging  
4. **24/7 Automation** – Alert-Bots, Circuit-Breakers.  
5. **Stress-Test ≥ 3 Std Shock** + ETF-Gap-Risk.

## Use-in-GPT
- „Berechne 99 % VaR (1 day) auf Portfolio“  
- „Generiere Slack-Alert für Drawdown > 10 % in 2 h“  

---

## 1 | Portfolio-Level Limits
```python
import numpy as np, pandas as pd, yfinance as yf
prices = yf.download(["BTC-USD","ETH-USD"], period="180d")["Adj Close"]
rets   = np.log(prices/prices.shift(1)).dropna()
cov    = np.cov(rets.T)  # daily
weights = np.array([0.6,0.4])
port_sd = np.sqrt(weights.T@cov@weights)
var99 = 2.33 * port_sd * 1e6  # assuming $1 M equity
print("1-day 99% VaR:", round(var99,0),"$")
```

---

## 2 | Tail-Risk & Event VaR
| Shock | Rationale | Hedge |
|-------|-----------|-------|
| ETF Outflow $1 B | Liquidity drain | Short Micro-Futures |
| Stablecoin Depeg -3 % | Counterparty | Long Put on BTC |

---

## 3 | MiCA Compliance Checklist
1. CASP-License filed?  
2. Proof-of-Reserve Audit uploaded?  
3. Stablecoin Cap ≤ 200 M € before 30 Jun 2024?  

---

## 4 | 24/7 Ops Automation
* **Bot-Stack** – Node Alert → Slack → PagerDuty.  
* **Kill-Switch-Rules** – ΔEquity ≥ -15 % in 4 h.  

---

## 5 | Psychological Risk Overlay
Cross-link → `trading_psychology.md#emotional-discipline`  
