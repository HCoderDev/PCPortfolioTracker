# Known Behavior & Intended Compatibility Rules

This document records specific domain rules, data structures, and edge-case behaviors discovered during reverse engineering of the original **iPortfolioTracker** iOS application. These behaviors must be intentionally preserved in the Flask application for full compatibility.

---

## 1. Core Data Timestamp Encoding
- Core Data represents dates as 64-bit floating-point numbers indicating seconds since `2001-01-01 00:00:00 UTC` (Apple Epoch).
- Unix Epoch (`1970-01-01 00:00:00 UTC`) offset is exactly **`978307200`** seconds.
- Python SQLite repository layer must convert timestamps bi-directionally:
  - `python_datetime.timestamp() - 978307200.0` for SQL writes
  - `datetime.fromtimestamp(sql_timestamp + 978307200.0, tz=timezone.utc)` for SQL reads

## 2. Non-Unitized Assets (FD, EPF, LIC, Post Office, Bank)
- Assets marked as non-unitized (`holdingType != 'investment'`) do NOT use stock units (`ZUNITS`). Units default to `1.0` or `0.0`.
- Transaction types for non-unitized assets (e.g. `DEPOSIT`, `INTEREST`, `INTEREST_PAYOUT`, `WITHDRAWAL`, `MATURITY`, `EMPLOYEE_CONTRIBUTION`, `EMPLOYER_CONTRIBUTION`, `PREMIUM`, `SURVIVAL_BENEFIT`, `SURRENDER`) have custom rules configured in `TransactionTypeRegistry`:
  - `cashDirection`: `outflow` (increases invested cost & balance), `inflow` (payout / reduces invested cost), or `internalAccrual` (interest credited directly to asset value without external cash movement).
  - `affectsInvestedAmount`, `affectsAssetValue`, `affectsProfit`, `closesAsset`.

## 3. Financial Independence (FI) Calculation Rules
- Progress % cap: capped at 100%.
- Return rate compounding: monthly return rate is computed using $(1 + r/100)^{1/12} - 1$ rather than simple division $r / 12$.
- Max calculation horizon: 1,200 months (100 years).

## 4. FIFO Tax Engine Rules
- Debt assets (`taxAssetType == 'debt'`) are always taxed at the user's slab rate (default 30%).
- Equity assets (`taxAssetType == 'equity'`) use `ltcgThresholdMonths` from the asset's category (default 12 months for domestic equity, 24 months for USD / US equity).
- Financial Year is hardcoded to Indian FY (April 1 to March 31).

## 5. XIRR Newton-Raphson Solver
- Uses 9 initial seed guesses ($0.1, 0.05, -0.05, 0.2, -0.2, 0.5, -0.5, 1.0, -0.8$) to guarantee convergence across diverse cash flow patterns.
- Returns `None` if cash flows do not contain both positive and negative amounts.
