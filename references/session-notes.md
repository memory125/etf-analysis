# Session Notes — ETF Analysis Skill Updates

## v1.2 (2026-06-11) LOF/QDII Support & Bug Fixes

### Problem: 港美互联网LOF (160644) analysis failed on multiple tasks

**Root causes discovered:**
1. `fund_etf_spot_em()` does NOT include LOF funds — must query `fund_lof_spot_em()` separately
2. `stock_zh_index_daily(symbol='sh160644')` throws internal `KeyError: 'date'` for SZ-market funds
3. `fund_portfolio_hold_em()` returns quarters in ascending order — `iloc[0]` gets oldest quarter, not newest
4. QDII fund holdings (HK/US stocks) return empty from akshare A-share database
5. Code comparison fails because akshare returns float codes (`160644.0`) vs string input

### Fixes applied to etf_analyzer.py:

| Fix | Function | Change |
|-----|----------|--------|
| LOF support | `_get_fund_spot_df()` | New unified function: try ETF → LOF → fund_name_em |
| SH/SZ fallback | `task2_history()` | Loop through ['sh', 'sz'] with try/except per prefix |
| Latest quarter | `task4_holdings()` | Use `sorted(quarters)[-1]` instead of `iloc[0]` |
| QDII holdings | `task4_holdings()` | 3-layer fallback: hold_em → portfolio_em → index composition proxy |
| is_target fix | `task3_competitors()` | Convert to int string: `str(int(float(code))) == str(target)` |
| LOF competitors | `task3_competitors()` | Merge ETF+LOF using common columns only for concat |

### Key akshare API behavior notes:
- `fund_lof_spot_em()` returns subset of columns vs `fund_etf_spot_em()` — no IOPV, 折价率, or 主力净流入
- LOF column set is a SUBSET of ETF columns (no extra columns) — safe to concat with common_cols only
- `stock_zh_index_daily('sh{code}')` for SZ funds doesn't return empty — it THROWS internally
- Column names are lowercase: `date`, `close`, `volume` (not uppercase)

### Test results:
```
✅ Task 0: Correctly identifies 160644 as LOF/QDII type
✅ Task 1: Gets realtime data from LOF source  
✅ Task 2: SZ prefix fallback works, returns 1840 days of history
✅ Task 3: Finds 45 competitors including target fund marked correctly
✅ Task 4: Returns Q4 2024 holdings (TSM 9.75%, Tencent 9.72%, NVDA 9.12%...)
```

## v1.3 (2026-06-11) Competitor Bug Fixes & ETF Liquidity Crisis Detection

### Problem: Task 3 competitor comparison had variable name bug after LOF refactoring

**Root causes discovered:**
1. `task3_competitors()` still referenced old variable `df` instead of `df_etf` in fallback keyword search — caused `NameError: name 'df' is not defined`
2. `best_alternative` logic didn't handle missing premium column for LOF funds — returned None silently without explanation
3. akshare holdings data (`fund_portfolio_hold_em`) returns **stale 2024 Q4** data even when newer quarters exist on eastmoney

### Fixes applied to etf_analyzer.py:

| Fix | Function | Change |
|-----|----------|--------|
| Variable name bug | `task3_competitors()` | Changed `df[...]` → `df_etf[...]` in fallback keyword search |
| LOF premium handling | `task3_competitors()` | Added `has_premium` flag; if no premium data, recommend by market cap instead with note |
| Empty competitors list | `task3_competitors()` | Return `"competitors": []` in few_competitors status (was missing) |

### Key insight: ETF liquidity crisis detection (159507 case study)

**通信ETF广发 (159507)** showed extreme anomaly:
- 52-week high: ¥3.18, current: ¥1.012 → **-67.7% drawdown from peak**
- 1-month return: -65.65% (single month loss of 2/3 value)
- Underlying index (国证通信指数) did NOT drop this much — **price disconnect = liquidity crisis**
- Market cap only ¥6亿 vs competitor 通信ETF国泰 at ¥40亿

**Detection rule**: If ETF drawdown >> underlying index drawdown, flag as potential liquidity/premium crisis. Always compare ETF performance against tracking index performance.

### Key insight: akshare holdings data is stale for many funds

- `fund_portfolio_hold_em()` returned **2024 Q4** data even though eastmoney shows **2026 Q1**
- For accurate latest holdings, must scrape eastmoney directly: `https://fundf10.eastmoney.com/ccmx_{code}.html`
- Browser scraping is the authoritative source for current quarter holdings

### Key insight: Index constituent mismatch (399804 case)

- akshare `index_stock_cons(symbol='399804')` returned 41 stocks with ZERO actual communication companies
- This was because 399804 is **中证通信指数**, not the fund's actual tracking index **国证通信指数**
- Always verify which index the ETF actually tracks from fund documentation (eastmoney jbgk page) before analyzing constituents

### Test results:
```
✅ Task 3: Variable name fixed, returns 7 competitors for 159507
✅ Task 3: best_alternative correctly identifies 通信ETF国泰(515880) as better alternative
✅ Browser scraping: Successfully extracted 2026 Q1 holdings from eastmoney (新易盛9.87%, 中际旭创8.98%...)
```
