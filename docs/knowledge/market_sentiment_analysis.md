---
title: "Market Sentiment Analysis"
version: "2.0"
last_updated: "2025-07-16"
tags: [sentiment, social-data, options-flow, funding-rate]
---

## Key Takeaways
1. **Real-Time Social Data** – Farcaster & DeSo verdrängen Twitter-Monopol.  
2. **On-Chain Derivate-Signale** – Funding-Rate-Regime-Shifts präzisieren Trend-Brüche  
3. **Options-Flow** – 0DTE Calls indizieren Gamma-Squeezes auf BTC/ETH Perps.  
4. **Composite Sentiment Score (CSS)** – kombiniert Text, Flow, Volatility.  
5. **Lag Management** – GPT sollte Zeitstempel in Antworten beachten.  

## Use-in-GPT
- „Berechne den CSS für die letzten 24 Stunden auf Basis von Farcaster & Funding-Rate“  
- „Welche Extremwerte im Put/Call-Ratio führten 2025 zu 10 % BTC-Moves?“  

---

## 1 | Datenquellen
| Kategorie | API / Feed | Aktualität |
|-----------|------------|-----------|
| Social | Farcaster, X/Twitter, Reddit | < 60 s |
| On-Chain | Glassnode, Dune | 5 min |
| Derivate | Deribit, Amberdata | tick |

---

## 2 | Python-Snippet: CSS-Berechnung
```python
from textblob import TextBlob
import requests, pandas as pd, numpy as np

def fetch_farcaster(n=200):
    r = requests.get("https://api.neynar.com/posts/recent").json()
    return [p["text"] for p in r["result"]][:n]

text_score = np.mean([TextBlob(t).sentiment.polarity for t in fetch_farcaster()])
funding = requests.get("https://api.glassnode.com/funding_rate?asset=BTC").json()[-1]["value"]
options_flow = pd.read_csv("deribit_options_flow.csv")["delta_usd"].sum()

css = 0.4*text_score + 0.35*np.tanh(funding*10) + 0.25*np.tanh(options_flow/1e6)
print(round(css,3))
```

---

## 3 | Interpretation
* **CSS > 0.7** – Euphorisch; Risiko-Off-Hedge.  
* **CSS < –0.5** – Panik; Mean-Reversion-Setup.

---

## 4 | Lags & Data Quality
* Social-Spam → BM25 + User-Reputation-Filter  
* Exchange-API-Rate Limits → Request Batching  
* Batch-Versus-Stream – GPT-Antwort kennzeichnet Zeitfenster.

---

## 5 | Checkliste
1. CSS-Trend ↑ ?  
2. Funding < 0 ? (Short Bias)  
3. Put/Call-OI Ratio > 1.3 ?  
4. Whale TX (>$10 M) Spikes?  
