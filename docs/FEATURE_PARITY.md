# Feature Parity Matrix

This document tracks functional parity between the original **iPortfolioTracker** iOS application and the **Flask + Tailwind Web/Desktop Application**.

| iOS Screen / Feature | iOS File Location | Web Implementation Target | Status | Test Plan |
|----------------------|-------------------|---------------------------|--------|-----------|
| **Dashboard** | `DashboardView.swift` | `app/routes/dashboard.py` + `dashboard.html` | Pending | Verify Total Networth, Pie Chart, Category Breakdown & Drift Alerts match iOS |
| **All Assets View** | `AllAssetsView.swift`, `AssetListView.swift` | `app/routes/assets.py` + `assets.html` | Pending | Verify filtering (All, Investment, Non-Unitized), search, and recency status pills |
| **Market Asset Detail** | `MarketAssetDetailView.swift` | `app/routes/assets.py` + `asset_detail_market.html` | Pending | Verify units, cost basis, unrealized P&L, Lifetime/Active XIRR, FIFO lots, stock valuation |
| **Contract Asset Detail** | `ContractAssetDetailView.swift` | `app/routes/assets.py` + `asset_detail_contract.html` | Pending | Verify principal/premium, interest accrued, maturity date, payout schedule, ledger |
| **Bulk Asset Updates** | `BulkAssetUpdateView.swift` | `app/routes/assets.py` + `bulk_asset_update.html` | Pending | Verify bulk price, rate, and valuation updates for multiple assets |
| **Category List** | `CategoryListView.swift` | `app/routes/categories.py` + `categories.html` | Pending | Verify category listing, target allocations, exchange rates, sub-categories |
| **Category Detail** | `CategoryDetailView.swift` | `app/routes/categories.py` + `category_detail.html` | Pending | Verify sub-category management, category total invested/value, category assets |
| **Flows & Cash** | `PortfolioFlowsView.swift` | `app/routes/flows.py` + `flows.html` | Pending | Verify monthly inflow/outflow charts, filters, cash movement summary, transaction ledger |
| **Transaction Form** | `TransactionFormView.swift`, `EditTransactionSheet.swift` | `app/routes/transactions.py` + `transaction_form.html` | Pending | Verify Buy/Sell/Dividend/Deposit/Maturity forms, validation, and database inserts |
| **Passive Income** | `PassiveIncomeView.swift` | `app/routes/passive_income.py` + `passive_income.html` | Pending | Verify Dividend/Interest aggregation by Month, Quarter, Year, Category, Asset, Broker |
| **Reminders List** | `RemindersListView.swift`, `AssetReminderFormSheet.swift` | `app/routes/reminders.py` + `reminders.html` | Pending | Verify reminder creation, completion toggle, filtering, due date tracking |
| **Time to FI Tracker** | `FITrackerDetailView.swift`, `FICalculationCard.swift` | `app/routes/fi_tracker.py` + `fi_tracker.html` | Pending | Verify monthly compounding algorithm, target date, age at FI, 25%/50%/75%/100% milestones |
| **File Import Wizard** | `FileImportWizardView.swift`, `ImportEngine.swift` | `app/routes/import_wizard.py` + `import_wizard.html` | Pending | Verify CSV/XLSX file parsing, asset auto-matching by ticker/alias, statement import |
| **Bulk CMP & Forex Import** | `BulkCMPImportSheet.swift`, `BulkForexImportSheet.swift` | `app/routes/import_wizard.py` + modals | Pending | Verify bulk market price & exchange rate imports |
| **Portfolio Rebalancer** | `PortfolioRebalancerView.swift` | `app/routes/rebalancer.py` + `rebalancer.html` | Pending | Verify target allocation % config, drift calculation (>5%), exact Buy/Sell recommendations |
| **Tax Planner** | `TaxLiabilityView.swift`, `FifoCalculator.swift` | `app/routes/tax_planner.py` + `tax_planner.html` | Pending | Verify Indian Financial Year realized STCG (20%), LTCG (12.5%), Slab rate & active lots preview |
| **Brokers Manager** | `BrokerListView.swift` | `app/routes/settings.py` + `brokers.html` | Pending | Verify adding/editing/deleting brokers |
| **Currencies Manager** | `CurrencyListView.swift`, `BulkExchangeRateUpdateView.swift` | `app/routes/settings.py` + `currencies.html` | Pending | Verify currency rates, default currency designation, bulk rate updates |
| **Stock Value Analysis** | `StockValueAnalysisFormSheet.swift`, `StockValueAnalysisDetailSheet.swift` | `app/routes/analysis.py` + `value_analysis.html` | Pending | Verify Graham PE, margin of safety, EPS/DPS historical trends |
| **Stock DCF Analysis** | `StockDCFAnalysisFormSheet.swift` | `app/routes/analysis.py` + `dcf_analysis.html` | Pending | Verify FCF projection, discount rate, terminal growth rate, intrinsic value per share |
| **Stock Split / Merge** | `StockSplitMergeView.swift` | `app/routes/analysis.py` + `stock_split.html` | Pending | Verify stock split unit multiplier and historical price adjustment |
| **Portfolio Snapshots** | `PortfolioSnapshotsView.swift`, `SnapshotDetailView.swift` | `app/routes/snapshots.py` + `snapshots.html` | Pending | Verify manual/auto networth snapshot generation and historical comparison |
| **CSV Export** | `ExportCSVView.swift` | `app/routes/export.py` + `export.html` | Pending | Verify CSV file generation for holdings, transactions, and category metrics |
| **Asset Research Notes** | `AllAssetNotesView.swift`, `NoteFormView.swift` | `app/routes/notes.py` + `notes.html` | Pending | Verify note creation, tagging to assets, editing, deletion |
| **User & App Settings** | `LoginView.swift`, `AppState.swift` | `app/routes/auth.py` + `settings.html` | Pending | Verify user profile, slab rate setting, theme toggle, database backup/restore |

---

## Acceptance Status Legend
- **Pending**: Analysis complete; awaiting implementation
- **Implemented**: Code written and deployed to web app
- **Tested**: Unit & integration tests written and passing
- **Verified**: Result outputs matched 100% against iOS app / SQLite reference data
