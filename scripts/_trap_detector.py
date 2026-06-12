"""
ETF Trap Detector v2.0 — ETF杀猪盘检测模块

借鉴 deep-analysis 的 trap detection 理念，专门针对ETF/LOF基金设计。
检测高溢价+低流动性+小规模的危险组合，防止散户被割韭菜。

检测类别：
  T1: 溢价陷阱 (Premium Trap) — 高溢价诱导追涨
  T2: 流动性陷阱 (Liquidity Trap) — 买得进卖不出  
  T3: 规模陷阱 (Size Trap) — 迷你基金清盘风险
  T4: 跟踪偏离陷阱 (Tracking Deviation) — 名不副实
  T5: 费率陷阱 (Expense Trap) — 隐性高成本
"""


def detect_premium_trap(premium_pct: float | None, is_qdii: bool = False) -> dict:
    """
    T1: 溢价陷阱检测
    
    QDII基金因额度限制容易出现持续高溢价，散户追涨被套。
    
    Returns: {"triggered": bool, "severity": str, "message": str}
    """
    if premium_pct is None:
        return {"triggered": False, "severity": "N/A", "message": "无溢价数据"}
    
    # akshare折价率：负值=溢价
    actual_premium = -premium_pct  # 转为正的溢价率
    
    if actual_premium >= 15:
        return {
            "triggered": True,
            "severity": "🔴 CRITICAL",
            "message": f"⚠️ 溢价陷阱！当前溢价{actual_premium:.1f}%，每投入1万元有{int(actual_premium*100)}元是纯泡沫。即使底层资产不跌，回归净值你就亏{actual_premium:.1f}%",
            "premium_pct": actual_premium,
        }
    elif actual_premium >= 8:
        return {
            "triggered": True,
            "severity": "🟠 HIGH",
            "message": f"溢价{actual_premium:.1f}%，性价比偏低。建议寻找低溢价替代品或等待溢价回落",
            "premium_pct": actual_premium,
        }
    elif actual_premium >= 3:
        return {
            "triggered": True,
            "severity": "🟡 MEDIUM",
            "message": f"轻度溢价{actual_premium:.1f}%，注意风险但可接受",
            "premium_pct": actual_premium,
        }
    
    return {"triggered": False, "severity": "🟢 OK", 
            "message": f"{'折价' if premium_pct > 0 else '合理'}{abs(premium_pct):.1f}%，无溢价陷阱"}


def detect_liquidity_trap(market_cap: float | None, volume: float | None, 
                          bid_ask_spread: float | None) -> dict:
    """
    T2: 流动性陷阱检测
    
    小盘ETF在恐慌时可能出现"买得进卖不出"的情况。
    
    Returns: {"triggered": bool, "severity": str, "message": str}
    """
    signals = []
    score = 0
    
    if market_cap is not None:
        cap_yi = market_cap / 1e8
        if cap_yi < 2:
            score += 3
            signals.append(f"流通市值仅{cap_yi:.1f}亿（迷你基金）")
        elif cap_yi < 5:
            score += 2
            signals.append(f"流通市值{cap_yi:.1f}亿，流动性偏低")
    
    if volume is not None:
        vol_wan = volume / 1e4
        if vol_wan < 0.5:
            score += 3
            signals.append("日成交量不足5千手，大额交易冲击成本极高")
        elif vol_wan < 2:
            score += 2
            signals.append(f"日成交仅{vol_wan:.1f}万手，流动性紧张")
    
    if bid_ask_spread is not None and bid_ask_spread > 0.5:
        score += 2
        signals.append(f"买卖价差{bid_ask_spread:.2f}%，交易成本高")
    
    if score >= 5:
        return {
            "triggered": True,
            "severity": "🔴 CRITICAL",
            "message": f"⚠️ 流动性陷阱！{'；'.join(signals)}。恐慌时可能无法及时卖出",
            "signals": signals,
        }
    elif score >= 3:
        return {
            "triggered": True,
            "severity": "🟠 HIGH",
            "message": f"流动性风险：{'；'.join(signals)}。建议控制仓位",
            "signals": signals,
        }
    
    return {"triggered": False, "severity": "🟢 OK", 
            "message": "流动性充足，无陷阱信号"}


def detect_size_trap(market_cap: float | None, total_shares: float | None, 
                      fund_age_days: int | None) -> dict:
    """
    T3: 规模陷阱检测
    
    迷你基金面临清盘风险。证监会规定：连续60个工作日资产低于5000万可能触发清盘。
    
    Returns: {"triggered": bool, "severity": str, "message": str}
    """
    if market_cap is None:
        return {"triggered": False, "severity": "N/A", "message": "无规模数据"}
    
    cap_yi = market_cap / 1e8
    
    if cap_yi < 0.5:  # < 5000万
        return {
            "triggered": True,
            "severity": "🔴 CRITICAL",
            "message": f"⚠️ 清盘风险！基金规模仅{cap_yi:.1f}亿，低于5000万警戒线。若持续60个工作日可能触发强制清盘",
            "market_cap_yi": cap_yi,
        }
    elif cap_yi < 1:  # < 1亿
        return {
            "triggered": True,
            "severity": "🟠 HIGH",
            "message": f"规模仅{cap_yi:.1f}亿，接近清盘警戒线。建议关注基金公告",
            "market_cap_yi": cap_yi,
        }
    elif cap_yi < 2:  # < 2亿
        return {
            "triggered": True,
            "severity": "🟡 MEDIUM",
            "message": f"规模{cap_yi:.1f}亿，属于小型基金。跟踪误差可能较大",
            "market_cap_yi": cap_yi,
        }
    
    return {"triggered": False, "severity": "🟢 OK", 
            "message": f"规模{cap_yi:.0f}亿，无清盘风险"}


def detect_tracking_trap(tracking_error: float | None, tracking_deviation: float | None,
                          etf_return_1y: float | None, index_return_1y: float | None) -> dict:
    """
    T4: 跟踪偏离陷阱检测
    
    ETF表现与底层指数严重偏离，可能是流动性危机或管理问题。
    
    Returns: {"triggered": bool, "severity": str, "message": str}
    """
    # Check return divergence (most important signal)
    if etf_return_1y is not None and index_return_1y is not None:
        divergence = abs(etf_return_1y - index_return_1y)
        
        if divergence > 20:
            return {
                "triggered": True,
                "severity": "🔴 CRITICAL",
                "message": f"⚠️ 严重跟踪偏离！ETF年回报{etf_return_1y:.1f}% vs 指数{index_return_1y:.1f}%，差异{divergence:.1f}个百分点。价格与底层资产脱钩！",
                "divergence_pct": divergence,
            }
        elif divergence > 10:
            return {
                "triggered": True,
                "severity": "🟠 HIGH",
                "message": f"跟踪偏离{divergence:.1f}个百分点，需关注原因",
                "divergence_pct": divergence,
            }
    
    # Check tracking error metric
    if tracking_error is not None and abs(tracking_error) > 3:
        return {
            "triggered": True,
            "severity": "🟠 HIGH",
            "message": f"跟踪误差{abs(tracking_error):.2f}%，超出可接受范围(3%)",
        }
    
    if tracking_deviation is not None and abs(tracking_deviation) > 2:
        return {
            "triggered": True,
            "severity": "🟡 MEDIUM",
            "message": f"跟踪偏离度{abs(tracking_deviation):.2f}%，略高但可接受",
        }
    
    return {"triggered": False, "severity": "🟢 OK", 
            "message": "跟踪精度良好，无明显偏离"}


def detect_expense_trap(management_fee: float | None, custody_fee: float | None,
                         competitors_avg_fee: float | None) -> dict:
    """
    T5: 费率陷阱检测
    
    某些ETF收取远高于同行的管理费，长期侵蚀收益。
    
    Returns: {"triggered": bool, "severity": str, "message": str}
    """
    if management_fee is None and custody_fee is None:
        return {"triggered": False, "severity": "N/A", "message": "无费率数据"}
    
    total = (management_fee or 0) + (custody_fee or 0)
    
    if competitors_avg_fee is not None:
        premium_over_market = total - competitors_avg_fee
        
        if premium_over_market > 0.5:
            return {
                "triggered": True,
                "severity": "🟠 HIGH",
                "message": f"费率{total:.2f}%/年，比同类平均({competitors_avg_fee:.2f}%)高{premium_over_market:.2f}%。10年累计多付{premium_over_market*10:.1f}%！",
            }
        elif premium_over_market > 0.2:
            return {
                "triggered": True,
                "severity": "🟡 MEDIUM",
                "message": f"费率略高于同类平均，建议对比低费率替代品",
            }
    
    if total > 1.5:
        return {
            "triggered": True,
            "severity": "🟠 HIGH",
            "message": f"总费率{total:.2f}%/年偏高（行业平均约0.8-1.0%）",
        }
    
    return {"triggered": False, "severity": "🟢 OK", 
            "message": f"费率{total:.2f}%/年在合理范围"}


def run_trap_detection(data: dict) -> dict:
    """
    运行完整的ETF杀猪盘检测
    
    Returns: {
        "traps": [trap_results],
        "critical_count": int,
        "high_count": int,
        "overall_verdict": str,
        "recommendation": str,
    }
    """
    traps = []
    
    # Run all detectors
    traps.append(detect_premium_trap(
        data.get("premium_pct"), 
        data.get("is_qdii", False)
    ))
    traps.append(detect_liquidity_trap(
        data.get("market_cap"),
        data.get("volume"),
        data.get("bid_ask_spread")
    ))
    traps.append(detect_size_trap(
        data.get("market_cap"),
        data.get("total_shares"),
        data.get("fund_age_days")
    ))
    traps.append(detect_tracking_trap(
        data.get("tracking_error"),
        data.get("tracking_deviation"),
        data.get("etf_return_1y"),
        data.get("index_return_1y")
    ))
    traps.append(detect_expense_trap(
        data.get("management_fee"),
        data.get("custody_fee"),
        data.get("competitors_avg_fee")
    ))
    
    # Count severities
    critical = sum(1 for t in traps if t.get("severity") == "🔴 CRITICAL")
    high = sum(1 for t in traps if t.get("severity") == "🟠 HIGH")
    medium = sum(1 for t in traps if t.get("severity") == "🟡 MEDIUM")
    
    # Overall verdict
    if critical > 0:
        verdict = f"🔴 发现{critical}个严重陷阱 — 建议谨慎或寻找替代品"
        recommendation = "除非你清楚风险并有对冲策略，否则不建议此时买入"
    elif high > 1:
        verdict = f"🟠 发现{high}个高风险信号 — 需要仔细评估"
        recommendation = "可以小仓位试探，但需设置止损线"
    elif high == 1 or medium >= 2:
        verdict = "🟡 存在部分风险 — 注意控制仓位"
        recommendation = "适合有经验的投资者，新手建议观望"
    else:
        verdict = "🟢 无明显陷阱信号 — 产品健康度良好"
        recommendation = "从产品角度看可以正常投资（仍需评估底层资产）"
    
    return {
        "traps": traps,
        "critical_count": critical,
        "high_count": high,
        "medium_count": medium,
        "overall_verdict": verdict,
        "recommendation": recommendation,
    }
