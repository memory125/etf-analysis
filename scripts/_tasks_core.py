# ============================================================
# Task 0-3: Core analysis tasks (preserved from v1.x)
# ============================================================

def task0_identify(code):
    """Task 0: 识别基金类型 + 确认代码"""
    print(f"\n{'='*60}")
    print(f"🔍 Task 0: 识别基金 {code}")
    print(f"{'='*60}")

    try:
        df, row, fund_type = _get_fund_spot_df(code)
        if row.empty:
            return None, "not_found"

        result = {
            "code": code,
            "fund_type": fund_type,
            "name": str(row['名称'].values[0]) if '名称' in row.columns else (str(row['基金简称'].values[0]) if '基金简称' in row.columns else "unknown"),
        }

        for col_name, result_key in [('最新价', 'price'), ('流通市值', 'market_cap')]:
            if col_name in row.columns:
                val = row[col_name].values[0]
                try:
                    result[result_key] = float(val) if result_key == 'price' else int(float(val))
                except (ValueError, TypeError):
                    pass

        print(f"✅ 已确认: {result['name']} ({code}) [{fund_type}]")
        return result, "ok"
    except Exception as e:
        print(f"❌ Task 0 失败: {e}")
        return None, "error"


def task1_realtime(code):
    """Task 1: 实时行情数据采集"""
    print(f"\n{'='*60}")
    print(f"📊 Task 1: 实时行情数据")
    print(f"{'='*60}")

    try:
        df, row, fund_type = _get_fund_spot_df(code)
        if row.empty:
            return {"status": "not_found"}

        data = {"fund_type": fund_type}
        for col in ['最新价', 'IOPV实时估值', '基金折价率', '涨跌额', '涨跌幅']:
            if col in row.columns:
                val = row[col].values[0]
                try:
                    data[col] = float(val)
                except (ValueError, TypeError):
                    data[col] = str(val)

        for col in ['成交量', '成交额', '最新份额', '流通市值', '总市值']:
            if col in row.columns:
                val = row[col].values[0]
                try:
                    data[col] = float(val)
                except (ValueError, TypeError):
                    data[col] = str(val)

        for col in ['主力净流入-净额', '主力净流入-净占比']:
            if col in row.columns:
                val = row[col].values[0]
                try:
                    data[col] = float(val)
                except (ValueError, TypeError):
                    data[col] = str(val)

        if '更新时间' in row.columns:
            data['update_time'] = str(row['更新时间'].values[0])

        premium = data.get('基金折价率')
        if premium is not None and isinstance(premium, (int, float)):
            if premium < -10:
                data['premium_risk'] = '🔴🔴🔴 严重高估'
            elif premium < -5:
                data['premium_risk'] = '🔴🔴 明显高估'
            elif premium < -2:
                data['premium_risk'] = '🟡 轻度高估'
            else:
                data['premium_risk'] = '🟢 溢价合理或折价'

        print(f"✅ Task 1 完成")
        return {"status": "ok", **data}
    except Exception as e:
        print(f"❌ Task 1 失败: {e}")
        return {"status": "error", "message": str(e)}


def task2_history(code):
    """Task 2: 历史业绩计算"""
    print(f"\n{'='*60}")
    print(f"📈 Task 2: 历史业绩分析")
    print(f"{'='*60}")

    try:
        df = None
        for prefix in ['sh', 'sz']:
            try:
                df = ak.stock_zh_index_daily(symbol=f'{prefix}{code}')
                if df is not None and not df.empty and 'close' in df.columns:
                    break
                df = None
            except Exception:
                df = None

        if df is None or df.empty:
            return {"status": "no_history"}

        result = {
            "data_range": f"{df['date'].min()} to {df['date'].max()}",
            "total_days": len(df),
            "current_price": float(df.iloc[-1]['close']),
        }

        for period_name, days in [("1M", 20), ("3M", 60), ("6M", 120), ("1Y", 250)]:
            last_n = df.tail(days)
            if len(last_n) > 0:
                ret = (df.iloc[-1]['close'] / last_n.iloc[0]['close'] - 1) * 100
                result[f'{period_name}_return'] = round(ret, 2)

        current_year = datetime.now().year
        ytd = df[df['date'] >= date(current_year, 1, 2)]
        if len(ytd) > 0:
            ret_ytd = (df.iloc[-1]['close'] / ytd.iloc[0]['close'] - 1) * 100
            result['YTD_return'] = round(ret_ytd, 2)

        inception = df.head(1)
        years = (df.iloc[-1]['date'] - inception.iloc[0]['date']).days / 365.25
        if years > 0:
            total_ret = (df.iloc[-1]['close'] / inception.iloc[0]['close'] - 1) * 100
            cagr = ((df.iloc[-1]['close'] / inception.iloc[0]['close']) ** (1/years) - 1) * 100
            result['total_return_since_inception'] = round(total_ret, 2)
            result['cagr'] = round(cagr, 2)

        peak = df['close'].expanding().max()
        drawdown = (df['close'] - peak) / peak * 100
        result['max_drawdown_ever'] = round(drawdown.min(), 2)
        result['current_drawdown_from_peak'] = round(drawdown.iloc[-1], 2)

        df['returns'] = df['close'].pct_change()
        ann_vol = df['returns'].std() * (252**0.5) * 100
        result['annualized_volatility'] = round(ann_vol, 2)

        daily_rf = 0.03 / 252
        sharpe = (df['returns'].mean() - daily_rf) / df['returns'].std() * (252**0.5)
        result['sharpe_ratio'] = round(sharpe, 2)

        last_250 = df.tail(250)
        if len(last_250) > 0:
            result['52w_high'] = float(last_250['close'].max())
            result['52w_low'] = float(last_250['close'].min())

        print(f"✅ Task 2 完成")
        return {"status": "ok", **result}
    except Exception as e:
        print(f"❌ Task 2 失败: {e}")
        return {"status": "error", "message": str(e)}


def task3_competitors(code, keyword=None):
    """Task 3: 同类横向对比"""
    print(f"\n{'='*60}")
    print(f"🔄 Task 3: 同类产品对比")
    print(f"{'='*60}")

    try:
        df_etf = ak.fund_etf_spot_em()
        target_row = df_etf[df_etf['代码'] == code]

        if target_row.empty:
            try:
                df_lof = ak.fund_lof_spot_em()
                if df_lof is not None and not df_lof.empty:
                    target_row = df_lof[df_lof['代码'] == code]
                    etf_cols = set(df_etf.columns)
                    lof_cols = set(df_lof.columns)
                    common_cols = list(etf_cols & lof_cols)
                    if '名称' in common_cols and '代码' in common_cols:
                        df_combined = pd.concat([df_etf[common_cols], df_lof[common_cols]])
                        df_etf = df_combined
            except Exception:
                pass

        if target_row.empty:
            return {"status": "not_found"}

        target_name = str(target_row['名称'].values[0])

        if keyword is None:
            kw_map = {
                '纳指': '纳指|纳斯达克', '沪深300': '沪深300', '恒生科技': '恒生科技',
                '半导体': '芯片|半导体', '标普': '标普', '互联网': '互联网|恒生科技|中概'
            }
            for trigger, kw in kw_map.items():
                if trigger in target_name:
                    keyword = kw
                    break
            if keyword is None:
                keyword = target_name.replace('ETF', '').replace('LOF', '').strip()

        competitors = df_etf[df_etf['名称'].str.contains(keyword, na=False)]
        if len(competitors) < 2:
            fallback_kw = target_name[:4]
            competitors = df_etf[df_etf['名称'].str.contains(fallback_kw, na=False)]

        if '增强' not in keyword:
            competitors = competitors[~competitors['名称'].str.contains('增强', na=False)]

        if len(competitors) < 2:
            return {"status": "few_competitors", "count": len(competitors), "competitors": []}

        has_premium = '基金折价率' in competitors.columns
        if has_premium:
            competitors = competitors.sort_values('基金折价率')

        output_cols = ['代码', '名称', '最新价', 'IOPV实时估值', '基金折价率', '涨跌幅', '成交量', '流通市值']
        available_cols = [c for c in output_cols if c in competitors.columns]

        result_list = []
        for _, row_data in competitors[available_cols].iterrows():
            entry = {}
            for col in available_cols:
                val = row_data[col]
                try:
                    entry[col] = float(val)
                except (ValueError, TypeError):
                    entry[col] = str(val)

            entry['is_target'] = (str(int(float(entry.get('代码', 0)))) == str(code))

            premium = entry.get('基金折价率')
            if isinstance(premium, (int, float)):
                if premium < -10: entry['premium_level'] = '🔴🔴🔴'
                elif premium < -5: entry['premium_level'] = '🔴🔴'
                elif premium < -2: entry['premium_level'] = '🟡'
                else: entry['premium_level'] = '🟢'

            result_list.append(entry)

        alternatives = [r for r in result_list if not r.get('is_target') and isinstance(r.get('基金折价率'), (int, float))]

        if has_premium and alternatives:
            best_alt = min(alternatives, key=lambda x: x['基金折价率'])
            target_premium = next((r['基金折价率'] for r in result_list if r.get('is_target')), 0)
            savings = target_premium - best_alt['基金折价率']

            print(f"✅ Task 3 完成 — 找到 {len(competitors)} 个同类产品")
            return {"status": "ok", "count": len(competitors), "competitors": result_list,
                    "best_alternative": best_alt}
        else:
            print(f"✅ Task 3 完成 — 找到 {len(competitors)} 个同类产品 (LOF无溢价数据)")
            return {"status": "ok", "count": len(competitors), "competitors": result_list,
                    "best_alternative": None, "note": "LOF基金无溢价数据"}

    except Exception as e:
        print(f"❌ Task 3 失败: {e}")
        return {"status": "error", "message": str(e)}
