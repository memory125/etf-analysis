"""
ETF Scoring System v2.0 — ETF专属多维度评分引擎

借鉴 deep-analysis 的22维打分理念，设计ETF专用15维评分体系。
每个维度独立打分(1-10)，加权汇总得出综合评分。

维度分类：
  A类 - 产品本身 (溢价率/流动性/费率/跟踪误差)
  B类 - 底层资产 (估值水平/业绩表现/持仓质量)  
  C类 - 市场环境 (宏观风险/政策风险/汇率风险)
"""

import math


# ============================================================
# Dimension definitions with weights
# ============================================================

DIM_DEFINITIONS = {
    # A类：产品本身 (权重40%)
    "A1_premium": {"name": "溢价率", "weight": 0.12, "category": "product"},
    "A2_liquidity": {"name": "流动性", "weight": 0.10, "category": "product"},
    "A3_expense_ratio": {"name": "费率水平", "weight": 0.06, "category": "product"},
    "A4_tracking_error": {"name": "跟踪误差", "weight": 0.08, "category": "product"},
    # B类：底层资产 (权重35%)
    "B1_valuation": {"name": "估值安全边际", "weight": 0.12, "category": "asset"},
    "B2_performance": {"name": "历史业绩表现", "weight": 0.10, "category": "asset"},
    "B3_holdings_quality": {"name": "持仓质量", "weight": 0.08, "category": "asset"},
    # C类：市场环境 (权重25%)
    "C1_macro_risk": {"name": "宏观环境风险", "weight": 0.08, "category": "market"},
    "C2_policy_risk": {"name": "政策风险", "weight": 0.07, "category": "market"},
    "C3_fx_risk": {"name": "汇率风险(QDII)", "weight": 0.10, "category": "market"},
}

# Total weight should sum to ~1.0 (allowing small rounding)


def score_premium(premium_pct: float | None) -> dict:
    """
    A1: 溢价率评分 (最重要维度)
    
    premium_pct < 0 = 折价(便宜，高分)
    premium_pct > 0 = 溢价(贵，低分)
    akshare的'基金折价率'字段：负值=溢价，正值=折价
    
    Returns: {"score": X, "level": str, "explanation": str}
    """
    if premium_pct is None:
        return {"score": 5.0, "level": "未知", "explanation": "无溢价率数据(LOF基金)"}
    
    # akshare的折价率：负值=溢价（贵），正值=折价（便宜）
    if premium_pct <= -15:
        return {"score": 1.0, "level": "🔴🔴🔴 极端高估", 
                "explanation": f"溢价{abs(premium_pct):.1f}%，每投1万有{int(abs(premium_pct)*100)}元纯泡沫"}
    elif premium_pct <= -10:
        return {"score": 2.0, "level": "🔴🔴 严重高估",
                "explanation": f"溢价{abs(premium_pct):.1f}%，建议寻找低溢价替代品"}
    elif premium_pct <= -5:
        return {"score": 3.5, "level": "🔴 明显高估",
                "explanation": f"溢价{abs(premium_pct):.1f}%，性价比偏低"}
    elif premium_pct <= -2:
        return {"score": 6.0, "level": "🟡 轻度高估",
                "explanation": f"溢价{abs(premium_pct):.1f}%，可接受但非最优"}
    elif premium_pct <= 0:
        return {"score": 8.0, "level": "🟢 合理定价",
                "explanation": f"溢价率接近零，价格合理"}
    else:
        return {"score": min(10.0, 8.5 + premium_pct * 0.3), "level": "🟢 折价(便宜)",
                "explanation": f"折价{premium_pct:.1f}%，买入有安全边际"}


def score_liquidity(market_cap: float | None, volume: float | None) -> dict:
    """
    A2: 流动性评分
    
    market_cap: 流通市值(元)
    volume: 成交量(手)
    
    Returns: {"score": X, "level": str, "explanation": str}
    """
    if market_cap is None and volume is None:
        return {"score": 5.0, "level": "未知", "explanation": "无流动性数据"}
    
    score = 5.0
    
    # Market cap scoring (亿)
    if market_cap is not None:
        cap_yi = market_cap / 1e8  # 转为亿
        if cap_yi >= 100:
            score += 2.5
        elif cap_yi >= 50:
            score += 1.5
        elif cap_yi >= 20:
            score += 0.5
        elif cap_yi >= 10:
            score -= 0.5
        else:
            score -= 2.0
    
    # Volume scoring (手)
    if volume is not None:
        vol_wan = volume / 1e4  # 转为万手
        if vol_wan >= 100:
            score += 2.5
        elif vol_wan >= 50:
            score += 1.5
        elif vol_wan >= 10:
            score += 0.5
        else:
            score -= 1.0
    
    score = max(1.0, min(10.0, score))
    
    if score >= 8:
        level = "🟢 流动性充裕"
    elif score >= 6:
        level = "🟡 流动性一般"
    else:
        level = "🔴 流动性不足"
    
    return {"score": round(score, 1), "level": level, 
            "explanation": f"流通市值{market_cap/1e8:.0f}亿，日成交{volume/1e4:.0f}万手" if market_cap and volume else "部分数据缺失"}


def score_expense(management_fee: float | None, custody_fee: float | None) -> dict:
    """
    A3: 费率水平评分
    
    management_fee: 管理费率(%)
    custody_fee: 托管费率(%)
    
    Returns: {"score": X, "level": str, "explanation": str}
    """
    if management_fee is None and custody_fee is None:
        return {"score": 5.0, "level": "未知", "explanation": "无费率数据，需web_search补充"}
    
    total = (management_fee or 1.0) + (custody_fee or 0.2)
    
    if total <= 0.5:
        score = 9.0
        level = "🟢 超低费率"
    elif total <= 1.0:
        score = 7.0
        level = "🟢 合理费率"
    elif total <= 1.5:
        score = 5.0
        level = "🟡 中等费率"
    else:
        score = 3.0
        level = "🔴 高费率"
    
    return {"score": score, "level": level, 
            "explanation": f"总费率{total:.2f}%/年（管理{management_fee or '未知'}%+托管{custody_fee or '未知'}%）"}


def score_tracking_error(tracking_error: float | None, tracking_deviation: float | None) -> dict:
    """
    A4: 跟踪误差评分
    
    tracking_error: 跟踪误差(%) — 越小越好
    tracking_deviation: 跟踪偏离度(%) — 越接近0越好
    
    Returns: {"score": X, "level": str, "explanation": str}
    """
    if tracking_error is None and tracking_deviation is None:
        return {"score": 5.0, "level": "未知", "explanation": "无跟踪误差数据"}
    
    err = abs(tracking_error or tracking_deviation or 0)
    
    if err <= 0.5:
        score = 9.0
        level = "🟢 极低跟踪误差"
    elif err <= 1.0:
        score = 7.0
        level = "🟢 良好跟踪精度"
    elif err <= 2.0:
        score = 5.0
        level = "🟡 可接受跟踪误差"
    else:
        score = max(1.0, 3.0 - (err - 2.0))
        level = "🔴 高跟踪误差"
    
    return {"score": round(score, 1), "level": level,
            "explanation": f"跟踪误差{err:.2f}%"}


def score_valuation(pe_percentile: float | None, pb_percentile: float | None) -> dict:
    """
    B1: 估值安全边际评分
    
    pe_percentile: PE历史百分位(0-100) — 越低越便宜
    pb_percentile: PB历史百分位(0-100) — 越低越便宜
    
    Returns: {"score": X, "level": str, "explanation": str}
    """
    if pe_percentile is None and pb_percentile is None:
        return {"score": 5.0, "level": "未知", "explanation": "无估值分位数据，需web_search补充"}
    
    percentile = pe_percentile or pb_percentile
    
    if percentile <= 10:
        score = 9.5
        level = "🟢 极度低估"
    elif percentile <= 30:
        score = 8.0
        level = "🟢 低估区间"
    elif percentile <= 50:
        score = 6.0
        level = "🟡 合理估值"
    elif percentile <= 70:
        score = 4.0
        level = "🟡 偏高估"
    else:
        score = max(1.0, 3.0 - (percentile - 70) / 25)
        level = "🔴 高估区间"
    
    return {"score": round(score, 1), "level": level,
            "explanation": f"估值处于历史{percentile:.0f}%分位"}


def score_performance(ret_1y: float | None, sharpe: float | None, max_dd: float | None) -> dict:
    """
    B2: 历史业绩表现评分
    
    ret_1y: 近1年收益率(%)
    sharpe: Sharpe比率
    max_dd: 最大回撤(%) — 负值
    
    Returns: {"score": X, "level": str, "explanation": str}
    """
    if ret_1y is None and sharpe is None:
        return {"score": 5.0, "level": "未知", "explanation": "无业绩数据"}
    
    score = 5.0
    
    # Return contribution (40% of this dimension)
    if ret_1y is not None:
        if ret_1y >= 30:
            score += 2.0
        elif ret_1y >= 15:
            score += 1.0
        elif ret_1y >= 0:
            score += 0.0
        else:
            score -= 1.5
    
    # Sharpe contribution (30%)
    if sharpe is not None:
        if sharpe >= 2.0:
            score += 1.5
        elif sharpe >= 1.0:
            score += 0.8
        elif sharpe >= 0.5:
            score += 0.3
        else:
            score -= 0.5
    
    # Drawdown penalty (30%)
    if max_dd is not None:
        dd_abs = abs(max_dd)
        if dd_abs <= 10:
            score += 1.5
        elif dd_abs <= 20:
            score += 0.5
        elif dd_abs <= 40:
            score -= 0.5
        else:
            score -= 1.5
    
    score = max(1.0, min(10.0, score))
    
    if score >= 8:
        level = "🟢 业绩优秀"
    elif score >= 6:
        level = "🟡 业绩一般"
    else:
        level = "🔴 业绩不佳"
    
    return {"score": round(score, 1), "level": level,
            "explanation": f"近1年{ret_1y or '未知'}%，Sharpe {sharpe or '未知'}，最大回撤{max_dd or '未知'}%"}


def score_holdings(top10_concentration: float | None, holdings_count: int | None) -> dict:
    """
    B3: 持仓质量评分
    
    top10_concentration: 前十大持仓占比(%) — 过高=集中风险，过低=分散过度
    holdings_count: 持仓总数
    
    Returns: {"score": X, "level": str, "explanation": str}
    """
    if top10_concentration is None and holdings_count is None:
        return {"score": 5.0, "level": "未知", "explanation": "无持仓数据"}
    
    score = 6.0
    
    if top10_concentration is not None:
        if 30 <= top10_concentration <= 60:
            score += 2.0  # 理想区间
        elif 60 < top10_concentration <= 80:
            score += 0.5  # 偏高但可接受
        elif top10_concentration > 80:
            score -= 1.5  # 过度集中
        else:
            score += 0.5  # 分散
    
    if holdings_count is not None:
        if 20 <= holdings_count <= 50:
            score += 1.0
        elif holdings_count < 10:
            score -= 1.0
    
    score = max(1.0, min(10.0, score))
    
    return {"score": round(score, 1), "level": "🟢" if score >= 7 else ("🟡" if score >= 5 else "🔴"),
            "explanation": f"前十大集中度{top10_concentration or '未知'}%，持仓{holdings_count or '未知'}只"}


def score_macro_risk(market_regime: str | None, vix_level: float | None) -> dict:
    """
    C1: 宏观环境风险评分
    
    market_regime: "bull"/"bear"/"sideways"/"unknown"
    vix_level: VIX恐慌指数 (越高=越危险)
    
    Returns: {"score": X, "level": str, "explanation": str}
    """
    score = 5.0
    
    if market_regime == "bull":
        score += 2.0
    elif market_regime == "bear":
        score -= 2.0
    # sideways = neutral
    
    if vix_level is not None:
        if vix_level < 15:
            score += 1.0
        elif vix_level > 30:
            score -= 2.0
        elif vix_level > 20:
            score -= 0.5
    
    score = max(1.0, min(10.0, score))
    
    return {"score": round(score, 1), "level": "🟢" if score >= 7 else ("🟡" if score >= 5 else "🔴"),
            "explanation": f"市场状态: {market_regime or '未知'}，VIX: {vix_level or '未知'}"}


def score_policy_risk(policy_direction: str | None, policy_events: list | None) -> dict:
    """
    C2: 政策风险评分
    
    policy_direction: "supportive"/"neutral"/"restrictive"/"unknown"
    policy_events: 近期政策事件列表
    
    Returns: {"score": X, "level": str, "explanation": str}
    """
    score = 5.0
    
    if policy_direction == "supportive":
        score += 3.0
    elif policy_direction == "restrictive":
        score -= 3.0
    
    if policy_events:
        negative_count = sum(1 for e in policy_events if isinstance(e, dict) and e.get("sentiment") == "negative")
        score -= negative_count * 0.5
    
    score = max(1.0, min(10.0, score))
    
    return {"score": round(score, 1), "level": "🟢" if score >= 7 else ("🟡" if score >= 5 else "🔴"),
            "explanation": f"政策方向: {policy_direction or '未知'}"}


def score_fx_risk(is_qdii: bool, currency_exposure: str | None, fx_volatility: float | None) -> dict:
    """
    C3: 汇率风险评分 (仅QDII基金适用)
    
    is_qdii: 是否为QDII基金
    currency_exposure: 货币敞口 ("USD"/"HKD"/"multi")
    fx_volatility: 汇率波动率(%)
    
    Returns: {"score": X, "level": str, "explanation": str}
    """
    if not is_qdii:
        return {"score": 10.0, "level": "N/A", "explanation": "非QDII基金，无汇率风险"}
    
    score = 5.0
    
    if currency_exposure == "USD":
        score += 1.0  # USD相对稳定
    elif currency_exposure == "multi":
        score -= 1.0  # 多币种更复杂
    
    if fx_volatility is not None:
        if fx_volatility > 10:
            score -= 2.0
        elif fx_volatility > 5:
            score -= 1.0
    
    score = max(1.0, min(10.0, score))
    
    return {"score": round(score, 1), "level": "🟢" if score >= 7 else ("🟡" if score >= 5 else "🔴"),
            "explanation": f"QDII汇率风险: {currency_exposure or '未知'}货币敞口，波动率{fx_volatility or '未知'}%"}


# ============================================================
# Master scoring function
# ============================================================

def compute_etf_score(data: dict) -> dict:
    """
    计算ETF综合评分
    
    Args:
        data: 包含所有维度的原始数据字典
        
    Returns:
        {
            "scores": {dim_id: {"score": X, "level": str, "explanation": str}},
            "weighted_total": float,
            "grade": str,
            "category_scores": {"product": X, "asset": X, "market": X},
            "red_flags": [str],
        }
    """
    scores = {}
    red_flags = []
    
    # A1: 溢价率
    premium = data.get("premium_pct")
    result = score_premium(premium)
    scores["A1_premium"] = result
    if result["score"] <= 3.5:
        red_flags.append(f"⚠️ {result['explanation']}")
    
    # A2: 流动性
    market_cap = data.get("market_cap")
    volume = data.get("volume")
    scores["A2_liquidity"] = score_liquidity(market_cap, volume)
    
    # A3: 费率 (需要从web_search获取，这里用默认值)
    mgmt_fee = data.get("management_fee")
    custody_fee = data.get("custody_fee")
    scores["A3_expense_ratio"] = score_expense(mgmt_fee, custody_fee)
    
    # A4: 跟踪误差 (需要从web_search获取)
    te = data.get("tracking_error")
    td = data.get("tracking_deviation")
    scores["A4_tracking_error"] = score_tracking_error(te, td)
    
    # B1: 估值分位
    pe_pct = data.get("pe_percentile")
    pb_pct = data.get("pb_percentile")
    scores["B1_valuation"] = score_valuation(pe_pct, pb_pct)
    
    # B2: 业绩表现
    ret_1y = data.get("ret_1y")
    sharpe = data.get("sharpe_ratio")
    max_dd = data.get("max_drawdown")
    scores["B2_performance"] = score_performance(ret_1y, sharpe, max_dd)
    
    # B3: 持仓质量
    conc = data.get("top10_concentration_pct")
    count = data.get("holdings_count")
    scores["B3_holdings_quality"] = score_holdings(conc, count)
    
    # C1: 宏观风险 (需要agent判断)
    regime = data.get("market_regime")
    vix = data.get("vix_level")
    scores["C1_macro_risk"] = score_macro_risk(regime, vix)
    
    # C2: 政策风险 (需要agent判断)
    policy_dir = data.get("policy_direction")
    policy_evts = data.get("policy_events")
    scores["C2_policy_risk"] = score_policy_risk(policy_dir, policy_evts)
    
    # C3: 汇率风险
    is_qdii = data.get("is_qdii", False)
    curr_exp = data.get("currency_exposure")
    fx_vol = data.get("fx_volatility")
    scores["C3_fx_risk"] = score_fx_risk(is_qdii, curr_exp, fx_vol)
    
    # Calculate weighted total
    weighted_total = 0.0
    weight_sum = 0.0
    category_scores = {"product": [], "asset": [], "market": []}
    
    for dim_id, result in scores.items():
        dim_def = DIM_DEFINITIONS.get(dim_id, {})
        weight = dim_def.get("weight", 1/len(scores))
        weighted_total += result["score"] * weight
        weight_sum += weight
        
        cat = dim_def.get("category", "other")
        if cat in category_scores:
            category_scores[cat].append(result["score"])
    
    # Normalize to 10-point scale (scores already on 0-10, weights sum ~1.0)
    if weight_sum > 0:
        weighted_total = weighted_total / weight_sum
    
    # Category averages
    for cat in category_scores:
        if category_scores[cat]:
            category_scores[cat] = round(sum(category_scores[cat]) / len(category_scores[cat]), 1)
        else:
            category_scores[cat] = None
    
    # Grade assignment
    grade_map = [
        (9.0, "S"), (8.0, "A"), (7.0, "B+"), (6.0, "B"), 
        (5.0, "C+"), (4.0, "C"), (3.0, "D"), (0, "F")
    ]
    grade = "F"
    for threshold, g in grade_map:
        if weighted_total >= threshold:
            grade = g
            break
    
    return {
        "scores": scores,
        "weighted_total": round(weighted_total, 1),
        "grade": grade,
        "category_scores": category_scores,
        "red_flags": red_flags,
    }
