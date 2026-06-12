# ============================================================
# Task 4: Holdings analysis (preserved from v1.x)
# ============================================================

def task4_holdings(code):
    """Task 4: 获取持仓数据 — 支持QDII基金网页抓取"""
    print(f"\n{'='*60}")
    print(f"📦 Task 4: 持仓分析")
    print(f"{'='*60}")

    try:
        df = ak.fund_portfolio_hold_em(symbol=code)
        if df is not None and not df.empty:
            if '季度' in df.columns and len(df['季度'].unique()) > 0:
                quarters = sorted(df['季度'].unique())
                latest_quarter = quarters[-1]
                df = df[df['季度'] == latest_quarter]

            has_data = False
            for _, row_data in df.iterrows():
                name_val = row_data.get('股票名称', '')
                pct_val = row_data.get('占净值比例', 0)
                if pd.notna(name_val) and str(name_val).strip() not in ['', '?']:
                    has_data = True
                    break

            if has_data:
                holdings = []
                for _, row_data in df.head(20).iterrows():
                    entry = {}
                    for col in ['股票代码', '股票名称', '占净值比例', '持股数', '持仓市值']:
                        if col in row_data.index:
                            val = row_data[col]
                            try:
                                entry[col] = float(val)
                            except (ValueError, TypeError):
                                entry[col] = str(val)
                    holdings.append(entry)

                total_weight = sum(h.get('占净值比例', 0) for h in holdings[:10])
                return {
                    "status": "ok", "source": "akshare",
                    "latest_quarter": latest_quarter,
                    "top_holdings": holdings,
                    "top10_concentration_pct": round(total_weight, 2),
                }
    except Exception as e:
        print(f"⚠️ akshare持仓获取失败: {e}")

    try:
        df2 = ak.fund_portfolio_em(symbol=code, indicator='股票型')
        if df2 is not None and not df2.empty:
            quarters = sorted(df2['季度'].unique())
            latest_q = quarters[-1]
            q_data = df2[df2['季度'] == latest_q]

            has_data = False
            for _, row in q_data.iterrows():
                name_val = row.get('股票名称', '')
                if pd.notna(name_val) and str(name_val).strip() not in ['', '?']:
                    has_data = True
                    break

            if has_data:
                holdings = []
                for _, row in q_data.head(20).iterrows():
                    entry = {}
                    for col in ['股票代码', '股票名称', '占净值比例', '持股数', '持仓市值']:
                        if col in row.index:
                            val = row[col]
                            try:
                                entry[col] = float(val)
                            except (ValueError, TypeError):
                                entry[col] = str(val)
                    holdings.append(entry)

                total_weight = sum(h.get('占净值比例', 0) for h in holdings[:10])
                return {
                    "status": "ok", "source": "akshare_portfolio_em",
                    "latest_quarter": latest_q,
                    "top_holdings": holdings,
                    "top10_concentration_pct": round(total_weight, 2),
                }
    except Exception as e:
        print(f"⚠️ fund_portfolio_em也失败: {e}")

    return {"status": "no_holdings", "message": "持仓数据不可用，建议通过天天基金网验证"}
