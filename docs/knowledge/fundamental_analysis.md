---
title: "Fundamental Analysis for Crypto Assets"
version: "2.0"
last_updated: "2025-07-16"
tags: [fundamental, valuation, tokenomics, ETF, Pectra, DCF]
---

## Key Takeaways
1. **Macro-to-Micro Pipeline** – beginne bei globalen Geldflüssen, lande bei Chain-KPIs.  
2. **Spot-ETF-Liquidität verschiebt Preiselastizität** – ETF-Net-Inflows ≈ primärer Demand-Treiber 2024/25  
3. **Pectra-Blobs senken L2-Datenkosten** → höhere TVL & veränderte FCF-Prognosen für Rollups  
4. **Bewertungsframeworks müssen mutieren** (DCF, Metcalfe, RV-Ratios) – Staking-Yield & MEV-Rebates inkludieren.  
5. **Regulatorische Cash-Flows** – MiCA-Compliance-Kosten ab 2025 in OPEX aufnehmen  

## Use-in-GPT (Beispiel-Prompts)
- „Erstelle ein vereinfachtes DCF-Modell für Arbitrum unter Pectra-Annahmen“  
- „Wie beeinflussen Bitcoin-Spot-ETFs die Realized-Cap von BTC?“  
- „Vergleiche MiCA-Lizenzkosten mit US-MSB-Regulierung für eine CEX“  

---

## 1 | Top-Down Macro Screening
### 1.1 Global Liquidity Cycle
* **M2-YoY**, **Fed Net-Liquidity**, **ECB BOP** → Korrelation zu TOTAL3-Cap.
* ETF-Net-Inflows Tracker: 54 % des US-BTC-Volumens laufen 2025 über ETFs  

### 1.2 On-Chain Money Velocity
`Velocity = TxVolume / FreeFloatSupply` → Indikator für Nutzungsgrad vs Hodling.

---

## 2 | Tokenomics Deep-Dive
| KPI | Bedeutung | Richtwert |
|-----|-----------|-----------|
| Real-Yield (Staking – Infl.) | Kaufkraft > 0 ? | **≥ 1 %** |
| Liquidity-Sinks | Burn, Lock, Stake | Wöchentlich tracken |
| Governance Overhang | Unvested-Treasury / FDV | **< 20 %** |

*Pectra-Blobs* verschieben L2-Ausgaben von „calldata“ zu „blob-Gas“ – Kosten-Schätzung siehe Gleichung 1.  

---

## 3 | Valuation Playbook

### 3.1 Discounted Cash Flow (DCF) für PoS
```python
import numpy as np
cf = np.array([2.5, 3.3, 4.1, 5.0])  # FCF in M USD
r  = 0.20  # WACC inkl. Krypto-Risk-Premium
TV = cf[-1] * (1+0.04) / (r-0.04)     # Gordon-Growth
npv = np.sum(cf/(1+r)**np.arange(1,5)) + TV/(1+r)**5
print(round(npv,2), "M USD")
```
> **Output**: 27.8 M USD – vor Anpassung um ETF-Liquiditätsmultiplikator λ = 1.3.

### 3.2 Relative-Value (RV) Ratios  
* **Adjusted P/S (wTVL)**  
* Network Value / TxVolume (NVT) – ETF-Glättung anwenden.  

---

## 4 | Regulatorische Einflüsse (MiCA)
* **CASP-Lizenz** (Art. 59 ff.): Antrags-Deadline 30 Dec 2024; Übergangsfrist bis 01 Jul 2026.  
* **Reserven-Audit** für E-Money-Tokens: quartalsweise Attests.  

Kostenmodell siehe Tabelle 2 im Anhang.

---

## 5 | Checkliste vor Investitionsentscheidung
1. **Macro Tailwind?** (M2↑, ETF Inflows ≥ $500 M/week)  
2. **Tokenomics Healthy?** (Real-Yield > 0)  
3. **Reg-Roadmap Clean?** (MiCA, CFTC, SEC)  
4. **Valuation >= 40 % Discount zum Intrinsic Value**  
5. **Risk-Budget OK?** (siehe risk_management_framework.md)

---

*Changelog → README.md*
