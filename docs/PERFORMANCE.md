# Performance & Database Strategy

This document outlines performance guidelines and database query optimization strategies for the **Flask + SQLite** implementation of iPortfolioTracker.

---

## 1. Zero Schema Alteration
- All database operations interact directly with existing Core Data tables (`ZASSET`, `ZASSETTRANSACTION`, `ZCATEGORY`, etc.).
- No new columns, tables, triggers, views, or indexes will be created or modified.

## 2. Parameterized Queries & Safe Connection Pooling
- All SQLite access uses parameterized queries (`?`) to prevent SQL injection and speed up execution plans.
- SQLite connections are managed per request using Flask `g` object (`teardown_appcontext`) with `PRAGMA foreign_keys = ON;`.

## 3. In-Memory Calculations & Batch Loading
- For portfolio networth calculation, asset holdings, and category aggregations, database queries use `JOIN`s to fetch assets with their categories, currencies, and subcategories in single roundtrips.
- Transaction records for an asset are fetched ordered by `ZDATE ASC, ZCREATEDAT ASC` so FIFO lot tracking and XIRR cash flow construction execute in $O(N)$ time per asset.

## 4. Local Desktop Packaging Optimizations
- Since the web server runs locally on `127.0.0.1`, lightweight static asset delivery (Tailwind CSS, Chart.js, Lucide Icons) will be bundled locally for offline execution.
