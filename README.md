# iPortfolioTracker — Flask + Tailwind CSS Web & Desktop Application

An exact functional replica of the **iPortfolioTracker** iOS application built with **Python + Flask**, **Tailwind CSS**, **Vanilla JavaScript**, and **SQLite**. It operates directly on the original Core Data SQLite database without modifying any schema or existing records.

---

## 🌟 Key Features

1. **Executive Dashboard:** Total Networth (INR/Local), Portfolio Allocation Drift Alert (> ±5%), Financial Independence summary, Category breakdown cards, Asset allocation doughnut chart.
2. **All Assets Manager:** Investment / Market Assets vs Non-Unitized Contract Assets (FD, EPF, LIC, Post Office, Bank), Recency status filters (Active, Moderate, Dormant, Never), Search & Sort options.
3. **Market Asset Detail:** Units, Cost Basis, Current Value, P&L, Lifetime vs Active XIRR, Active FIFO Tax Lots (STCG @ 20%, LTCG @ 12.5%, Slab rate @ 30%), Dividends, Stock Analysis (Graham Value & DCF), Stock Split/Merge tool, Notes & Reminders.
4. **Contract Asset Detail:** Principal/Premium, Interest Rate %, Maturity Date, Payout Frequency, Policy/Account #, Accrued Interest, Transaction Ledger.
5. **Categories & Subcategories:** Target Allocations %, Exchange rates to INR, LTCG threshold months, Passive income filters, Sub-category manager.
6. **Flows & Cash:** Money Outflows vs Inflows timeline, Net cash flows, Filters by Year/Month/Category/Broker, Full transaction ledger.
7. **Passive Income Tracker:** Aggregated Dividends/Interest by Month, Quarter, Year, Category, Asset, Broker.
8. **Reminders:** Asset reminders (Maturity, Premium due, SIP dates), Mark completed, Filter status.
9. **Time to FI (FI Tracker):** Financial Independence compounding projections, target date, age at FI, 25%/50%/75%/100% milestone progress.
10. **File Import Wizard:** CSV/Excel importer, Asset auto-matching via `addAlias`, Bulk CMP & Forex rate importer.
11. **Portfolio Rebalancer:** Target Allocation % vs Actual Allocation %, Drift calculations (> ±5%), Exact Buy/Sell recommendations in Local/INR currency.
12. **Tax Planner:** Indian FY (Apr 1 - Mar 31) Realized STCG, LTCG, Slab rate summary, Active lots unrealized tax preview.
13. **Stock Analysis:** Graham PE Value model, DCF 10-Year Valuation model, Stock Split/Merge ratio processor.
14. **Snapshots & CSV Export:** Historical portfolio networth snapshots, CSV export for holdings & transactions.

---

## 🚀 Running the Web Application

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start Local Server
```bash
python run.py
```
Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

---

## 🖥️ Running as Desktop WebView Application

To launch as a native desktop application in a dedicated window:

```bash
python desktop_app.py
```

---

## 🧪 Running Automated Tests

```bash
python tests/run_tests.py
```

---

## 📁 Reverse Engineering Specification Docs

Detailed technical specification and feature parity verification documents:
- [IOS_APP_REVERSE_ENGINEERING.md](docs/IOS_APP_REVERSE_ENGINEERING.md)
- [FEATURE_PARITY.md](docs/FEATURE_PARITY.md)
- [IOS_WEB_VERIFICATION.md](docs/IOS_WEB_VERIFICATION.md)
- [KNOWN_BEHAVIOR.md](docs/KNOWN_BEHAVIOR.md)
- [PERFORMANCE.md](docs/PERFORMANCE.md)
