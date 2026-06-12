"""
ETF SIP Strategy Analyzer v2.0 — 定投策略分析模块

为长期投资者提供基于数据的定投建议：
- 最佳买入区间计算（基于历史估值分位）
- 止盈/止损点设定
- 金额规划建议
- 定投频率优化
"""


def analyze_sip_zones(history_data: dict, current_price: float | None = None) -> dict:
    """
    分析定投最佳买入区间
    
    Args:
        history_data: Task 2的历史数据（含52周高低点、收益率等）
        current_price: 当前价格
        
    Returns: {
        "buy_zones": {"value_zone", "growth_zone", "technical_zone"},
        "take_profit_zones": [...],
        "stop_loss_zones": [...],
        "recommendation": str,
    }
    """
    price_52w_high = history_data.get("52w_high")
    price_52w_low = history_data.get("52w_low")
    max_dd = history_data.get("max_drawdown_ever", 0)
    current_dd = history_data.get("current_drawdown_from_peak", 0)
    
    if current_price is None:
        current_price = history_data.get("current_price")
    
    zones = {}
    
    # Value zone: 历史低点附近 + 最大回撤区间
    if price_52w_low and current_price:
        value_target = price_52w_low * 1.05  # 略高于最低点
        value_margin = (current_price - value_target) / current_price * 100
        
        zones["value_zone"] = {
            "target_price": round(value_target, 3),
            "discount_needed": round(value_margin, 1),
            "rationale": f"52周低点{price_52w_low}附近，安全边际充足",
            "suitable_for": "价值投资者 — 越跌越买策略",
        }
    
    # Growth zone: 突破关键阻力位时追涨
    if price_52w_high and current_price:
        growth_target = price_52w_high * 0.95  # 接近前高
        zones["growth_zone"] = {
            "target_price": round(growth_target, 3),
            "premium_needed": round((growth_target - current_price) / current_price * 100, 1),
            "rationale": f"接近52周高点{price_52w_high}，趋势确认",
            "suitable_for": "成长投资者 — 右侧交易策略",
        }
    
    # Technical zone: 均线支撑位
    zones["technical_zone"] = {
        "description": "建议在以下技术位加仓：",
        "levels": [
            {"level": "MA60附近", "condition": "价格回踩60日均线企稳"},
            {"level": "前低支撑", "condition": f"52周低点{price_52w_low or '未知'}上方"},
            {"level": "突破确认", "condition": f"放量突破{price_52w_high or '未知'}前高"},
        ],
    }
    
    return zones


def calculate_take_profit(ret_ytd: float | None, ret_1y: float | None, 
                           max_dd: float | None) -> list:
    """
    计算止盈点
    
    Returns: [{"level": str, "target_return": float, "action": str}]
    """
    profits = []
    
    # Tier 1: 短期止盈 (20%收益)
    profits.append({
        "level": "🟢 第一止盈线",
        "target_return": 20.0,
        "action": "减仓30%，锁定部分利润",
        "rationale": "ETF年化20%已属优秀表现，落袋为安",
    })
    
    # Tier 2: 中期止盈 (50%收益)
    profits.append({
        "level": "🟡 第二止盈线", 
        "target_return": 50.0,
        "action": "减仓50%，保留底仓继续持有",
        "rationale": "50%收益后市场可能进入过热阶段",
    })
    
    # Tier 3: 长期止盈 (100%收益)
    profits.append({
        "level": "🔴 第三止盈线",
        "target_return": 100.0,
        "action": "清仓或仅留10%观察仓",
        "rationale": "翻倍后风险收益比逆转，建议大幅减仓",
    })
    
    # Dynamic adjustment based on current performance
    if ret_1y is not None and ret_1y > 40:
        profits.append({
            "level": "⚠️ 动态止盈提醒",
            "target_return": round(ret_1y - 5, 1),
            "action": "当前已接近历史高位，建议立即减仓20%",
            "rationale": f"近1年收益{ret_1y:.1f}%，已进入高风险区间",
        })
    
    return profits


def calculate_stop_loss(max_dd: float | None, current_dd: float | None) -> list:
    """
    计算止损点
    
    Returns: [{"level": str, "threshold": float, "action": str}]
    """
    stops = []
    
    # Hard stop loss based on historical max drawdown
    if max_dd is not None:
        dd_abs = abs(max_dd)
        
        # Conservative stop: 80% of historical max drawdown
        conservative_stop = round(dd_abs * 0.8, 1)
        stops.append({
            "level": "🔴 硬性止损线",
            "threshold": -conservative_stop,
            "action": f"从买入价下跌{conservative_stop}%时强制止损",
            "rationale": f"历史最大回撤{dd_abs:.1f}%，设置80%作为安全边界",
        })
    
    # Current drawdown warning
    if current_dd is not None and abs(current_dd) > 20:
        stops.append({
            "level": "⚠️ 当前回撤警告",
            "threshold": round(current_dd, 1),
            "action": "已处于深度回撤中，建议暂停定投等待企稳",
            "rationale": f"距高点已回撤{abs(current_dd):.1f}%",
        })
    
    # Default stop if no historical data
    if not stops:
        stops.append({
            "level": "🔴 默认止损线",
            "threshold": -20.0,
            "action": "从买入价下跌20%时重新评估持仓",
            "rationale": "无历史回撤数据，采用保守默认值",
        })
    
    return stops


def recommend_sip_frequency(premium_pct: float | None, volatility: float | None) -> dict:
    """
    推荐定投频率
    
    Returns: {"recommended": str, "reasoning": str, "alternatives": [...]}
    """
    # High premium → less frequent (wait for premium to drop)
    if premium_pct is not None and -premium_pct > 5:
        return {
            "recommended": "月度定投",
            "reasoning": f"当前溢价{abs(premium_pct):.1f}%，建议降低频率等待溢价回落。周度定投在高溢价期会持续买入高估资产",
            "alternatives": [
                {"frequency": "双周定投", "condition": "溢价率降至3%以内时切换"},
                {"frequency": "手动择时", "condition": "溢价率>10%时暂停，<2%时加倍"},
            ],
        }
    
    # High volatility → more frequent (dollar-cost averaging works better)
    if volatility is not None and volatility > 25:
        return {
            "recommended": "周度定投",
            "reasoning": f"年化波动率{volatility:.1f}%，高波动环境下周度定投能更好地摊薄成本",
            "alternatives": [
                {"frequency": "双周定投", "condition": "波动率降至20%以下时切换"},
                {"frequency": "月度定投", "condition": "适合工作繁忙的投资者"},
            ],
        }
    
    # Default recommendation
    return {
        "recommended": "周度定投",
        "reasoning": "标准推荐。周度定投在大多数市场环境下表现最优，能充分利用市场波动摊薄成本",
        "alternatives": [
            {"frequency": "月度定投", "condition": "适合资金量较大或工作繁忙的投资者"},
            {"frequency": "双周定投", "condition": "折中方案，兼顾频率与操作便利性"},
        ],
    }


def calculate_sip_amount(monthly_income: float | None, risk_tolerance: str = "moderate") -> dict:
    """
    计算建议定投金额
    
    Args:
        monthly_income: 月收入（可选）
        risk_tolerance: "conservative" / "moderate" / "aggressive"
        
    Returns: {"monthly_amount": float, "percentage_of_income": float, "rationale": str}
    """
    allocation_map = {
        "conservative": 0.10,  # 10% of income
        "moderate": 0.20,      # 20% of income  
        "aggressive": 0.35,    # 35% of income
    }
    
    pct = allocation_map.get(risk_tolerance, 0.20)
    
    if monthly_income:
        amount = monthly_income * pct
        return {
            "monthly_amount": round(amount, 0),
            "percentage_of_income": pct * 100,
            "rationale": f"基于{risk_tolerance}风险偏好，建议将月收入的{pct*100:.0f}%用于定投",
            "weekly_equivalent": round(amount / 4.3, 0),
        }
    
    return {
        "monthly_amount": None,
        "percentage_of_income": pct * 100,
        "rationale": f"建议将月收入的{pct*100:.0f}%用于定投（请提供月收入以计算具体金额）",
    }


def generate_sip_strategy(data: dict) -> dict:
    """
    生成完整的定投策略报告
    
    Returns: {
        "buy_zones": ...,
        "take_profit": [...],
        "stop_loss": [...],
        "frequency_recommendation": ...,
        "amount_recommendation": ...,
        "overall_sip_verdict": str,
    }
    """
    # Check if this ETF is suitable for SIP at all
    premium = data.get("premium_pct")
    market_cap = data.get("market_cap")
    
    sip_warnings = []
    
    if premium is not None and -premium > 10:
        sip_warnings.append(f"⚠️ 当前溢价{-premium:.1f}%过高，建议等待溢价回落后再开始定投")
    
    if market_cap is not None and market_cap < 5e8:
        sip_warnings.append("⚠️ 基金规模过小(<5亿)，存在清盘风险，不建议长期定投")
    
    # Generate all components
    buy_zones = analyze_sip_zones(data, data.get("current_price"))
    take_profit = calculate_take_profit(
        data.get("YTD_return"), data.get("ret_1y"), data.get("max_drawdown_ever")
    )
    stop_loss = calculate_stop_loss(
        data.get("max_drawdown_ever"), data.get("current_drawdown_from_peak")
    )
    frequency = recommend_sip_frequency(premium, data.get("annualized_volatility"))
    amount = calculate_sip_amount(data.get("monthly_income"))
    
    # Overall verdict
    if sip_warnings:
        overall = "🟡 有条件推荐定投" + "；".join(sip_warnings)
    elif premium is not None and -premium > 5:
        overall = "🟡 建议等待溢价回落后再开始定投"
    else:
        overall = "🟢 适合长期定投 — 该产品流动性充足、无明显陷阱信号"
    
    return {
        "buy_zones": buy_zones,
        "take_profit": take_profit,
        "stop_loss": stop_loss,
        "frequency_recommendation": frequency,
        "amount_recommendation": amount,
        "warnings": sip_warnings,
        "overall_sip_verdict": overall,
    }
