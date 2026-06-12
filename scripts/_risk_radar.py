"""
ETF Risk Radar v2.0 — 风险雷达图模块

量化评估6大风险维度，生成可视化雷达数据 + 风险评估报告。

风险分类：
  1. 系统性风险 (市场整体下跌)
  2. 流动性风险 (买卖困难/冲击成本高)
  3. 汇率风险 (QDII专属)
  4. 政策风险 (监管变化/额度限制)
  5. 集中度风险 (持仓过于集中)
  6. 溢价波动风险 (折溢价剧烈变动)
"""


def assess_systematic_risk(ret_1y: float | None, max_dd: float | None, 
                           ann_vol: float | None, market_regime: str | None) -> dict:
    """
    系统性风险评估
    
    Returns: {"level": 0-10, "description": str, "signals": [str]}
    """
    level = 3.0  # Base moderate risk
    signals = []
    
    if ret_1y is not None and ret_1y < -20:
        level += 2.0
        signals.append("近1年跌幅超20%，市场处于下行周期")
    
    if max_dd is not None and abs(max_dd) > 30:
        level += 2.0
        signals.append(f"历史最大回撤{max_dd:.1f}%，波动剧烈")
    
    if ann_vol is not None and ann_vol > 30:
        level += 1.5
        signals.append(f"年化波动率{ann_vol:.1f}%，高于市场平均水平")
    
    if market_regime == "bear":
        level += 2.0
        signals.append("当前处于熊市环境")
    elif market_regime == "sideways":
        level += 0.5
    
    level = min(10.0, max(0.0, level))
    
    return {
        "level": round(level, 1),
        "description": _risk_description(level),
        "signals": signals,
    }


def assess_liquidity_risk(market_cap: float | None, volume: float | None, 
                          premium_pct: float | None) -> dict:
    """
    流动性风险评估
    
    Returns: {"level": 0-10, "description": str, "signals": [str]}
    """
    level = 2.0  # Base low risk
    signals = []
    
    if market_cap is not None and market_cap < 5e8:  # < 5亿
        level += 3.0
        signals.append(f"流通市值仅{market_cap/1e8:.1f}亿，属于微型ETF")
    elif market_cap is not None and market_cap < 10e8:  # < 10亿
        level += 2.0
        signals.append(f"流通市值{market_cap/1e8:.1f}亿，流动性偏低")
    
    if volume is not None and volume < 1e4:  # < 1万手
        level += 2.0
        signals.append("日成交量不足1万手，大额交易冲击成本高")
    
    if premium_pct is not None and abs(premium_pct) > 5:
        level += 1.5
        signals.append(f"折溢价率{abs(premium_pct):.1f}%，流动性定价失真")
    
    level = min(10.0, max(0.0, level))
    
    return {
        "level": round(level, 1),
        "description": _risk_description(level),
        "signals": signals,
    }


def assess_fx_risk(is_qdii: bool, currency_exposure: str | None, 
                   fx_volatility: float | None) -> dict:
    """
    汇率风险评估 (QDII专属)
    
    Returns: {"level": 0-10, "description": str, "signals": [str]}
    """
    if not is_qdii:
        return {
            "level": 0.0,
            "description": "非QDII基金，无汇率风险",
            "signals": [],
        }
    
    level = 3.0  # Base moderate for QDII
    signals = ["QDII基金存在汇率波动风险"]
    
    if currency_exposure == "multi":
        level += 1.5
        signals.append("多币种敞口增加汇率不确定性")
    
    if fx_volatility is not None and fx_volatility > 8:
        level += 2.0
        signals.append(f"汇率波动率{fx_volatility:.1f}%，显著影响净值")
    
    level = min(10.0, max(0.0, level))
    
    return {
        "level": round(level, 1),
        "description": _risk_description(level),
        "signals": signals,
    }


def assess_policy_risk(is_qdii: bool, policy_direction: str | None, 
                       qdii_quota_status: str | None) -> dict:
    """
    政策风险评估
    
    Returns: {"level": 0-10, "description": str, "signals": [str]}
    """
    level = 2.0  # Base low risk
    signals = []
    
    if policy_direction == "restrictive":
        level += 3.0
        signals.append("当前政策环境对该板块不利")
    
    if is_qdii and qdii_quota_status == "limited":
        level += 2.5
        signals.append("QDII额度紧张，可能导致持续高溢价")
    elif is_qdii and qdii_quota_status == "suspended":
        level += 3.0
        signals.append("QDII申购已暂停，溢价风险极高")
    
    if is_qdii:
        level += 1.0
        signals.append("QDII受外汇管制政策影响")
    
    level = min(10.0, max(0.0, level))
    
    return {
        "level": round(level, 1),
        "description": _risk_description(level),
        "signals": signals,
    }


def assess_concentration_risk(top10_pct: float | None, 
                               single_max_weight: float | None) -> dict:
    """
    集中度风险评估
    
    Returns: {"level": 0-10, "description": str, "signals": [str]}
    """
    level = 2.0  # Base low risk
    signals = []
    
    if top10_pct is not None and top10_pct > 80:
        level += 3.0
        signals.append(f"前十大持仓占比{top10_pct:.1f}%，过度集中")
    elif top10_pct is not None and top10_pct > 60:
        level += 1.5
        signals.append(f"前十大持仓占比{top10_pct:.1f}%，集中度偏高")
    
    if single_max_weight is not None and single_max_weight > 10:
        level += 2.0
        signals.append(f"单一标的权重达{single_max_weight:.1f}%，个股风险突出")
    
    level = min(10.0, max(0.0, level))
    
    return {
        "level": round(level, 1),
        "description": _risk_description(level),
        "signals": signals,
    }


def assess_premium_volatility(premium_pct: float | None, 
                               premium_history: list | None) -> dict:
    """
    溢价波动风险评估
    
    Returns: {"level": 0-10, "description": str, "signals": [str]}
    """
    level = 2.0  # Base low risk
    signals = []
    
    if premium_pct is not None and abs(premium_pct) > 5:
        level += 2.0
        signals.append(f"当前折溢价率{abs(premium_pct):.1f}%，偏离净值较大")
    
    if premium_history:
        # Check for volatility in premium history
        premiums = [p for p in premium_history if isinstance(p, (int, float))]
        if len(premiums) >= 2:
            max_premium = max(premiums)
            min_premium = min(premiums)
            swing = abs(max_premium - min_premium)
            
            if swing > 10:
                level += 3.0
                signals.append(f"溢价率波动幅度达{swing:.1f}%，极不稳定")
            elif swing > 5:
                level += 1.5
                signals.append(f"溢价率波动幅度{swing:.1f}%，存在不确定性")
    
    level = min(10.0, max(0.0, level))
    
    return {
        "level": round(level, 1),
        "description": _risk_description(level),
        "signals": signals,
    }


def generate_radar_data(data: dict) -> dict:
    """
    生成完整风险雷达数据
    
    Returns: {
        "risks": {risk_name: {"level": X, ...}},
        "max_risk": str,
        "overall_risk_level": str,
        "radar_values": [X, X, X, X, X, X],  # For chart rendering
    }
    """
    risks = {}
    
    # Run all assessments
    risks["systematic"] = assess_systematic_risk(
        data.get("ret_1y"), data.get("max_drawdown"),
        data.get("annualized_volatility"), data.get("market_regime")
    )
    
    risks["liquidity"] = assess_liquidity_risk(
        data.get("market_cap"), data.get("volume"),
        data.get("premium_pct")
    )
    
    risks["fx"] = assess_fx_risk(
        data.get("is_qdii", False),
        data.get("currency_exposure"),
        data.get("fx_volatility")
    )
    
    risks["policy"] = assess_policy_risk(
        data.get("is_qdii", False),
        data.get("policy_direction"),
        data.get("qdii_quota_status")
    )
    
    risks["concentration"] = assess_concentration_risk(
        data.get("top10_concentration_pct"),
        data.get("single_max_weight")
    )
    
    risks["premium_volatility"] = assess_premium_volatility(
        data.get("premium_pct"),
        data.get("premium_history")
    )
    
    # Find max risk
    max_risk_name = max(risks, key=lambda k: risks[k]["level"])
    
    # Overall assessment
    avg_level = sum(r["level"] for r in risks.values()) / len(risks)
    if avg_level >= 7:
        overall = "🔴 高风险"
    elif avg_level >= 4:
        overall = "🟡 中等风险"
    else:
        overall = "🟢 低风险"
    
    # Radar values for chart (normalized to 0-100)
    radar_values = [r["level"] * 10 for r in risks.values()]
    
    return {
        "risks": risks,
        "max_risk": max_risk_name,
        "overall_risk_level": overall,
        "radar_values": radar_values,
        "risk_names": ["系统性风险", "流动性风险", "汇率风险", 
                       "政策风险", "集中度风险", "溢价波动风险"],
    }


def _risk_description(level: float) -> str:
    """Convert risk level to human-readable description"""
    if level >= 8:
        return "极高风险 — 可能造成本金重大损失"
    elif level >= 6:
        return "高风险 — 需要高度警惕"
    elif level >= 4:
        return "中等风险 — 需密切关注"
    elif level >= 2:
        return "低风险 — 基本可控"
    else:
        return "极低风险 — 几乎无此维度风险"
