# ============================================================
# Core data fetching functions (unchanged from v1.x)
# ============================================================

def _get_fund_spot_df(code):
    """Try ETF spot first, then LOF spot — returns (df, row, fund_type)"""
    try:
        df_etf = ak.fund_etf_spot_em()
        row = df_etf[df_etf['代码'] == code]
        if not row.empty:
            return df_etf, row, "ETF"
    except Exception:
        pass

    try:
        df_lof = ak.fund_lof_spot_em()
        if df_lof is not None and not df_lof.empty:
            row = df_lof[df_lof['代码'] == code]
            if not row.empty:
                return df_lof, row, "LOF"
    except Exception:
        pass

    try:
        df_name = ak.fund_name_em()
        row = df_name[df_name['基金代码'] == code]
        if not row.empty:
            return None, row, "LOF/QDII"
    except Exception:
        pass

    return None, pd.DataFrame(), "unknown"


def _extract_row_data(row):
    """Extract all available fields from a fund row"""
    data = {}
    for col in row.columns:
        val = row[col].values[0] if len(row) > 0 else None
        if val is not None and pd.notna(val):
            try:
                data[col] = float(val)
            except (ValueError, TypeError):
                data[col] = str(val)
    return data
