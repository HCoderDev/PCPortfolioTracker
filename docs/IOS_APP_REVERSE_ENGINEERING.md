# iPortfolioTracker — iOS App Reverse Engineering Specification

This document details the reverse-engineered specification of the **iPortfolioTracker** iOS application. It serves as the authoritative source of truth for creating an exact functional replica using Python Flask, Tailwind CSS, and Vanilla JavaScript while maintaining 100% database compatibility with the original Core Data SQLite database schema.

---

## 1. Application Architecture & Data Model Discovery

### Core Data SQLite Schema
The iOS application uses Apple SwiftData backed by a Core Data SQLite store. The database schema follows standard Core Data naming conventions (`Z_PK`, `Z_ENT`, `Z_OPT`, table prefix `Z` for entities).

| SQLite Entity Table | Purpose / Description | Primary Key | Key Foreign Keys | Key Attributes |
|---------------------|-----------------------|-------------|------------------|----------------|
| `ZASSET` | Individual asset holding (stocks, MFs, FDs, EPF, LIC, Bank) | `Z_PK` | `ZCATEGORY`, `ZSUBCATEGORY`, `ZVALUEANALYSIS`, `ZDCFANALYSIS` | `ZNAME`, `ZCURRENTPRICE`, `ZTAXCOUNTRYRAW`, `ZTAXASSETTYPERAW`, `ZHOLDINGTYPERAW`, `ZTICKERRAW`, `ZALIASESRAW`, `ZINTERESTRATERAW`, `ZPRINCIPALAMOUNRAW`, `ZMATURITYDATERAW`, `ZPAYOUTFREQUENCYRAW`, `ZPREMIUMAMOUNRAW`, `ZPREMIUMTERMYEARSRAW`, `ZPOLICYNUMBERRAW`, `ZINSTITUTIONNAMERAW` |
| `ZASSETTRANSACTION` | Buy, Sell, Dividend, Deposit, Payout, Interest ledger | `Z_PK` | `ZASSET`, `ZBROKER` | `ZTYPE` ("BUY", "SELL", "DIVIDEND"), `ZRAWTYPERAW`, `ZUNITS`, `ZPRICEPERUNIT`, `ZDATE` (Core Data timestamp float), `ZCREATEDAT`, `ZINREXCHANGERATE`, `ZNOTES` |
| `ZCATEGORY` | Asset category (e.g. Indian Stocks, US Stocks, Fixed Income) | `Z_PK` | None | `ZNAME`, `ZCURRENCYCODE`, `ZLASTINREXCHANGERATE`, `ZCONVERTTOINR`, `ZISINDIVIDUALEQUITY`, `ZTARGETALLOCATION`, `ZLTCGTHRESHOLDMONTHS`, `ZPASSIVETRANSACTIONTYPESRAW` |
| `ZSUBCATEGORY` | Sub-category (e.g. Large Cap, Mid Cap, Flexi Cap) | `Z_PK` | `ZCATEGORY` | `ZNAME` |
| `ZBROKER` | Broker / Custodian (e.g. Zerodha, Groww, INDmoney, IBKR) | `Z_PK` | None | `ZNAME` |
| `ZCURRENCY` | Currency rates (INR, USD, etc.) | `Z_PK` | None | `ZCODE`, `ZEXCHANGERATE`, `ZISDEFAULT` |
| `ZUSER` | User profile & global tax configuration | `Z_PK` | None | `ZUSERNAME`, `ZPASSWORDHASH`, `ZTAXSLABRATERAW` |
| `ZASSETNOTE` | Research thesis & earnings notes | `Z_PK` | `ZASSET` | `ZTITLE`, `ZNOTEDESCRIPTION`, `ZDATE`, `ZCREATEDAT` |
| `ZASSETREMINDER` | Reminders (Maturity, Premium due, Review) | `Z_PK` | `ZASSET` | `ZTITLE`, `ZNOTES`, `ZEVENTDATE`, `ZISCOMPLETED`, `ZCREATEDAT` |
| `ZSTOCKVALUEANALYSIS` | Graham & Value investment analysis model | `Z_PK` | `ZASSET` | `ZCMP`, `ZINTRINSICPE`, `ZINDUSTRYPE`, `ZBOOKVALUE`, `ZDEBTTOEQUITY`, `ZFREECASHFLOW`, `ZCONSENSUSGROWTHRATE`, `ZCONSENSUSDIVPAYOUTRATIO`, `ZEPSVALUESSTRING`, `ZDPSVALUESSTRING` |
| `ZSTOCKDCFANALYSIS` | Discounted Cash Flow valuation model | `Z_PK` | `ZASSET` | `ZCMP`, `ZSTARTINGFCF`, `ZGROWTHRATE`, `ZDISCOUNTRATE`, `ZTERMINALGROWTH`, `ZSHARES`, `ZANALYSISDATE` |
| `ZPORTFOLIOSNAPSHOT` | Point-in-time portfolio total networth snapshot | `Z_PK` | None | `ZDATE`, `ZTOTALINVESTEDINR`, `ZTOTALVALUEINR`, `ZNOTE` |
| `ZCATEGORYSNAPSHOT` | Point-in-time category snapshot | `Z_PK` | `ZPORTFOLIOSNAPSHOT` | `ZCATEGORYNAME`, `ZCURRENCYCODE`, `ZINVESTEDVALUE`, `ZCURRENTVALUE`, `ZINVESTEDVALUEINR`, `ZCURRENTVALUEINR`, `ZEXCHANGERATETOINR` |
| `ZASSETSNAPSHOT` | Point-in-time asset snapshot | `Z_PK` | `ZCATEGORYSNAPSHOT` | `ZASSETNAME`, `ZUNITS`, `ZCURRENTPRICE`, `ZINVESTEDVALUE`, `ZCURRENTVALUE`, `ZINVESTEDVALUEINR`, `ZCURRENTVALUEINR` |

> **Note on Timestamp Encoding:** Core Data stores dates as Floating Point seconds relative to January 1, 2001 00:00:00 UTC (Core Data Epoch).
> Conversion formula: `Unix Timestamp = CoreDataTimestamp + 978307200`.

---

## 2. Screen Inventory & UI Specifications

### 1. Dashboard (`DashboardView`)
- **Navigation:** Main Entry / Sidebar Item 1
- **Key Display Elements:**
  - Executive Total Portfolio Networth Header (in INR or user-selected currency)
  - Allocation Drift Alert Banner (triggers when category allocation deviates > ±5% from target)
  - Financial Independence (FI) Summary Card (Time to FI countdown, progress %)
  - Category-wise Asset Allocation Pie Chart
  - Category Performance Cards (Invested, Current Value, P&L, holdings count, list of top assets)
- **User Actions:**
  - Click Category Card -> Navigate to Category Detail
  - Click Asset Row -> Navigate to Asset Detail
  - Top Action Menu: Layout/Theme preferences, Export Database Backup, Import Database Restore

### 2. All Assets (`AssetListView`, `AllAssetsView`)
- **Navigation:** Overview -> All Assets
- **Key Display Elements:**
  - Filter tabs: All, Investment/Market (Stocks/MFs), Non-Unitized (FDs, EPF, LIC, Post Office)
  - Recency status filter pill: Active (<=30d), Moderate (30-90d), Dormant (>90d), Never Invested
  - Search bar (Filter by asset name or ticker)
  - Sort options: Name, Current Value, Invested Value, Gain/Loss, Recency
- **User Actions:**
  - Bulk Asset Update Modal (Update prices, interest rates, values in bulk)
  - Add New Asset Sheet
  - Click Asset Card -> Navigate to Asset Detail

### 3. Asset Detail Views (`MarketAssetDetailView`, `ContractAssetDetailView`)
- **Navigation:** All Assets -> Select Asset
- **Key Display Elements:**
  - **Market Asset (Stocks/MFs):** Current Price, Total Units, Current Value, Cost Basis, Unrealized P&L (Amount & %), XIRR (Lifetime vs Active mode selector), FIFO Tax Breakdown Lots (STCG, LTCG, Slab), Dividend history, Stock Valuation cards (Value Analysis & DCF), Stock Split/Merge action sheet, Reminders list, Research notes list, Timeline performance chart.
  - **Contract / Non-Unitized Asset (FD, EPF, LIC, PPF, Bank):** Principal/Premium amount, Interest rate %, Maturity Date, Payout frequency, Policy/Account #, Interest accrued, Payout schedule, Full transaction ledger (Deposits, Interest Credited, Payouts, Withdrawals, Maturity).
- **User Actions:**
  - Add/Edit/Delete Transaction
  - Add/Edit/Delete Research Note
  - Add/Edit/Delete Reminder
  - Run / Update Stock Value Analysis (Graham Model)
  - Run / Update Stock DCF Valuation Model
  - Record Stock Split / Reverse Split / Merger
  - Toggle Completed / Closed status

### 4. Categories (`CategoryListView`, `CategoryDetailView`, `ManageSubCategoriesView`)
- **Navigation:** Overview -> Categories
- **Key Display Elements:**
  - Grid/List of Categories with Target Allocation %, Actual Allocation %, Currency Code, Exchange Rate to INR, LTCG Threshold Months
  - Sub-category manager
- **User Actions:**
  - Add / Edit Category (Name, Currency, Exchange rate, Target allocation %, Is Individual Equity, LTCG Months, Passive Income Transaction filters)
  - Manage Sub-Categories

### 5. Flows & Cash (`PortfolioFlowsView`)
- **Navigation:** Transactions & Cash -> Flows & Cash
- **Key Display Elements:**
  - Cumulative & Monthly Inflows vs Outflows timeline chart
  - Filter by Year, Month, Category, Transaction Type, Broker
  - Net Cash Invested vs Net Cash Retrieved
  - Comprehensive Transaction Ledger Table (Date, Asset, Type, Units, Price, Total Amount, INR Value, Broker, Notes)
- **User Actions:**
  - Add Transaction
  - Edit / Delete Transaction

### 6. Passive Income (`PassiveIncomeView`)
- **Navigation:** Transactions & Cash -> Passive Income
- **Key Display Elements:**
  - Total Lifetime & Annual Passive Income (Dividends, Interest Payouts, Survival Benefits, Coupons, Rent)
  - Breakdown by Month, Quarter, Year, Category, Asset, Broker
  - Passive Income Yield % (Passive Income / Total Invested Value)
  - Category Passive Income Type Filter configuration
- **User Actions:**
  - Record Passive Income Transaction

### 7. Reminders (`RemindersListView`)
- **Navigation:** Transactions & Cash -> Reminders
- **Key Display Elements:**
  - List of reminders tagged to assets (FD Maturity dates, Insurance Premium due dates, SIP dates, Thesis review dates)
  - Filter by Pending vs Completed
- **User Actions:**
  - Add / Edit / Mark Complete / Delete Reminder

### 8. Time to FI / FI Tracker (`FITrackerDetailView`)
- **Navigation:** Analytics & Tools -> Time to FI
- **Key Display Elements:**
  - Financial Independence Calculator & Milestone Tracker
  - Inputs: Target FI Networth Goal (e.g. ₹7 Crore), Current Networth, Monthly SIP (e.g. ₹50,000), Expected Return Rate % (e.g. 12%), Inflation Rate % (e.g. 6%), Safe Withdrawal Rate % (e.g. 4%), Birth Date / Age
  - Results: Months & Years to FI, Age at FI, Projected Target Date, Annual & Monthly Passive Income at FI
  - Milestone Progress Timeline: 25% (Quarter FI), 50% (Half FI), 75% (Three-Quarter FI), 100% (Full Freedom)

### 9. File Import Wizard (`FileImportWizardView`)
- **Navigation:** Analytics & Tools -> Import Wizard
- **Key Display Elements:**
  - CSV & Excel Statement Importer (`CSVParser`, `XLSXParser`, `ImportEngine`)
  - Auto-matching uploaded statement rows to existing portfolio assets via Ticker, Name, or Aliases (`addAlias`)
  - Bulk Current Market Price (CMP) import sheet
  - Bulk Forex rate import sheet
- **User Actions:**
  - Upload CSV/XLSX file
  - Review mapped transactions and assets
  - Execute import

### 10. Portfolio Rebalancer (`PortfolioRebalancerView`)
- **Navigation:** Analytics & Tools -> Rebalancer
- **Key Display Elements:**
  - Category Target Allocation % vs Actual Portfolio Allocation %
  - Allocation Drift indicators (> ±5%)
  - Rebalance Action Recommendations: Exact buy/sell amount in local currency & INR to reach target allocation

### 11. Tax Liability Planner (`TaxLiabilityView`)
- **Navigation:** Analytics & Tools -> Tax Planner
- **Key Display Elements:**
  - Indian Financial Year (Apr 1 - Mar 31) Tax Calculator
  - Realized Gains in current FY: STCG (20%), LTCG (12.5%), Slab Rate (Debt)
  - Active Holding Lots Preview: Tax classification (STCG vs LTCG based on holding age and category LTCG threshold months), estimated unrealized tax liability

### 12. Settings Views (`BrokerListView`, `CurrencyListView`)
- **Navigation:** Settings -> Brokers / Currencies
- **Key Display Elements:**
  - Manage Brokers (Zerodha, Groww, INDmoney, IBKR, HDFC Sec, etc.)
  - Manage Currencies (Code, Exchange Rate to Base/INR, Default Currency flag)

---

## 3. Financial Calculation Specifications

### A. Asset Value & Invested Cost
1. **Unitized Assets (Stocks, Mutual Funds, ETFs):**
   $$\text{Total Units} = \sum \text{Buy Units} - \sum \text{Sell Units}$$
   $$\text{Invested Cost (FIFO)} = \sum_{\text{active lots}} (\text{Remaining Lot Units} \times \text{Lot Buy Price})$$
   $$\text{Current Value} = \text{Total Units} \times \text{Current Market Price}$$
   $$\text{Unrealized P\&L} = \text{Current Value} - \text{Invested Cost}$$

2. **Non-Unitized Assets (Fixed Deposit, EPF, LIC, Post Office, Bank):**
   $$\text{Invested Cost} = \sum \text{Outflow Amounts} - \sum \text{Inflow Amounts} \quad (\text{or Principal / Premium amount})$$
   $$\text{Current Value} = \max(\text{Accumulated Balance}, \text{Current Price}, \text{Principal})$$

3. **INR Conversion:**
   $$\text{Value (INR)} = \text{Value (Local)} \times \text{Category Exchange Rate to INR}$$

### B. FIFO (First-In, First-Out) Tax Engine
- When a `SELL` transaction occurs, lot consumption consumes the oldest remaining `BUY` lot first (ordered by `Date`, then `CreatedAt`).
- Realized Gain for a sold lot portion:
  $$\text{Realized Gain (Local)} = (\text{Sell Price} - \text{Lot Buy Price}) \times \text{Sold Units}$$
  $$\text{Realized Gain (INR)} = (\text{Sell Price} \times \text{Sell Rate}) - (\text{Lot Buy Price} \times \text{Lot Buy Rate}) \times \text{Sold Units}$$
- **Tax Classification Rules:**
  - Debt Assets (`taxAssetType == 'debt'`): Taxed at User's Slab Rate.
  - Equity Assets (`taxAssetType == 'equity'`):
    - Holding Age $> \text{LTCG Threshold Months}$ (default 12 months for India, 24 for US): **LTCG** (12.5% tax rate).
    - Holding Age $\le \text{LTCG Threshold Months}$: **STCG** (20.0% tax rate).

### C. XIRR (Extended Internal Rate of Return)
- Solves for annual discount rate $r$ such that Net Present Value equals zero:
  $$\text{NPV}(r) = \sum_{i=1}^{N} \frac{C_i}{(1 + r)^{(d_i - d_0)/365}} = 0$$
- Solved using Newton-Raphson method with multi-start initial guesses ($0.1, 0.05, -0.05, 0.2, -0.2, 0.5, -0.5, 1.0, -0.8$) and tolerance of $10^{-7}$.
- **Lifetime XIRR:** Includes all cash outflows (negative), cash inflows / dividends / interest (positive), and current market value as final cash inflow at valuation date.
- **Active XIRR:** Includes cost basis of active holding lots as initial cash outflows at purchase dates, plus dividends received during active holding period, plus current market value at valuation date.

### D. Financial Independence (FI) Projection Engine
$$\text{Monthly Rate } m = (1 + \text{ReturnRate}/100)^{1/12} - 1$$
Loop monthly compounding balance $B_{k+1} = B_k \times (1 + m) + \text{MonthlySIP}$ until $B \ge \text{TargetGoal}$.
$$\text{Annual Passive Income at FI} = \text{TargetGoal} \times (\text{SafeWithdrawalRate} / 100)$$
Milestones calculated at 25%, 50%, 75%, and 100% of TargetGoal.
