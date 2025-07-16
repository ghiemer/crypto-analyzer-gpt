---
title: "Trading-GPT Knowledge Base"
version: "2.0"
last_updated: "2025-07-16"
schema_version: "2025-07-16"
tags: [index, navigation]
---

# Welcome to Trading-GPT KB v2.0

| Topic | File | Typical Queries |
|-------|------|-----------------|
| Fundamentals | `fundamental_analysis.md` | „Wie bewerte ich ARB nach Pectra?“ |
| Sentiment | `market_sentiment_analysis.md` | „Erstelle CSS für 24 h“ |
| Technicals | `technical_analysis_strategies.md` | „Pine-Script Funding-Div“ |
| Risk | `risk_management_framework.md` | „99 % VaR Portfolio“ |
| Psychology | `trading_psychology.md` | „Bias im Trade-Log?“ |

---

## Retrieval Hints
*Synonyme* → Hodl, HODL, Real-Cap, ETF-Inflows, Pectra-Blobs.  
*German & English* Begriffe gemischt.

---

## Changelog (excerpt)
| Date | Change |
|------|--------|
| 2025-07-16 | v2.0 – MiCA & ETF Update, Pectra, CSS, Funding-Div |

---

## Maintenance Calendar
* **Q1 & Q3** – Fundamental & Risk Update  
* **Monthly** – Sentiment API Key Rotation  
* **Weekly** – CSS Lag-Check  

---

## API Usage Examples
```bash
curl https://api.openai.com/v1/chat/completions   -H "Authorization: Bearer $KEY"   -H "Content-Type: application/json"   -d '{
    "model": "gpt-4o-trader",
    "messages": [{"role":"user","content":"Berechne 99% VaR (1 day) für BTC & ETH"}],
    "temperature": 0
}'
```
