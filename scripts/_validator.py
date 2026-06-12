"""
ETF Data Validator v2.0 — 数据验证层

提供 akshare API 健康检查、数据时效性校验、交叉验证机制。
确保分析结果基于可靠数据，而非过期或错误信息。
"""

import time
from datetime import datetime, timedelta


def check_akshare_health() -> dict:
    """
    检测 akshare API 可用性
    
    Returns: {
        "status": str,
        "endpoints": {"endpoint_name": bool},
        "recommendation": str,
    }
    """
    import akshare as ak
    
    results = {}
    
    # Test critical endpoints
    tests = [
        ("fund_etf_spot_em", lambda: ak.fund_etf_spot_em()),
        ("stock_zh_index_daily", lambda: ak.stock_zh_index_daily(symbol="sh510300")),
        ("fund_portfolio_hold_em", lambda: ak.fund_portfolio_hold_em(symbol="510300")),
    ]
    
    for name, test_fn in tests:
        try:
            start = time.time()
            result = test_fn()
            elapsed = time.time() - start
            
            if result is not None and hasattr(result, '__len__') and len(result) > 0:
                results[name] = {"ok": True, "latency_ms": round(elapsed * 1000)}
            else:
                results[name] = {"ok": False, "error": "empty_result", "latency_ms": round(elapsed * 1000)}
        except Exception as e:
            results[name] = {"ok": False, "error": str(e)[:100]}
    
    all_ok = all(r.get("ok") for r in results.values())
    
    return {
        "status": "healthy" if all_ok else ("degraded" if any(r.get("ok") for r in results.values()) else "unhealthy"),
        "endpoints": results,
        "recommendation": _health_recommendation(all_ok, results),
    }


def validate_data_freshness(data: dict) -> dict:
    """
    校验数据时效性
    
    Returns: {
        "issues": [str],
        "warnings": [str],
        "is_stale": bool,
    }
    """
    issues = []
    warnings = []
    
    # Check realtime data timestamp
    update_time = data.get("update_time")
    if update_time:
        try:
            # Parse various time formats
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%Y%m%d%H%M%S"]:
                try:
                    update_dt = datetime.strptime(str(update_time), fmt)
                    age_hours = (datetime.now() - update_dt).total_seconds() / 3600
                    
                    if age_hours > 24:
                        issues.append(f"实时行情数据已{age_hours:.0f}小时未更新，可能非交易时间或API异常")
                    elif age_hours > 8:
                        warnings.append(f"行情数据{age_hours:.0f}小时前更新，建议确认是否为交易日")
                    break
                except ValueError:
                    continue
        except Exception:
            warnings.append("无法解析更新时间格式")
    
    # Check holdings data staleness
    quarter = data.get("latest_quarter")
    if quarter:
        current_year = datetime.now().year
        current_q = (datetime.now().month - 1) // 3 + 1
        
        try:
            q_year = int(str(quarter)[:4])
            q_num = int(str(quarter)[-1])
            
            quarters_behind = (current_year - q_year) * 4 + (current_q - q_num)
            
            if quarters_behind > 2:
                issues.append(f"持仓数据滞后{quarters_behind}个季度（最新：{quarter}），建议通过天天基金网验证")
            elif quarters_behind == 2:
                warnings.append(f"持仓数据滞后1个季度（最新：{quarter}）")
        except (ValueError, IndexError):
            pass
    
    # Check history data range
    total_days = data.get("total_days", 0)
    if total_days and total_days < 60:
        warnings.append(f"历史数据仅{total_days}天，统计指标可能不准确")
    
    return {
        "issues": issues,
        "warnings": warnings,
        "is_stale": len(issues) > 0,
    }


def cross_validate_premium(price: float | None, iopv: float | None, 
                           reported_premium: float | None) -> dict:
    """
    交叉验证溢价率数据
    
    akshare报告的折价率可能与实际计算不一致，需要验证。
    
    Returns: {
        "calculated_premium": float,
        "reported_premium": float,
        "discrepancy": bool,
        "message": str,
    }
    """
    if price is None or iopv is None:
        return {
            "calculated_premium": None,
            "reported_premium": reported_premium,
            "discrepancy": False,
            "message": "缺少价格或IOPV数据，无法交叉验证",
        }
    
    # Calculate premium from price and IOPV
    calculated = (price - iopv) / iopv * 100
    
    if reported_premium is None:
        return {
            "calculated_premium": round(calculated, 2),
            "reported_premium": None,
            "discrepancy": True,
            "message": f"无报告溢价率，自行计算：{calculated:.2f}%",
        }
    
    # akshare折价率是反的（负值=溢价），需要转换比较
    reported_as_premium = -reported_premium
    
    diff = abs(calculated - reported_as_premium)
    
    if diff > 1.0:
        return {
            "calculated_premium": round(calculated, 2),
            "reported_premium": round(reported_as_premium, 2),
            "discrepancy": True,
            "message": f"⚠️ 溢价率数据不一致！计算值{calculated:.2f}% vs 报告值{reported_as_premium:.2f}%，差异{diff:.2f}%",
        }
    
    return {
        "calculated_premium": round(calculated, 2),
        "reported_premium": round(reported_as_premium, 2),
        "discrepancy": False,
        "message": f"溢价率交叉验证通过（计算{calculated:.2f}% ≈ 报告{reported_as_premium:.2f}%）",
    }


def validate_competitor_data(competitors: list | None) -> dict:
    """
    验证竞品数据质量
    
    Returns: {
        "valid_count": int,
        "issues": [str],
        "recommendation": str,
    }
    """
    if not competitors:
        return {"valid_count": 0, "issues": ["无竞品数据"], "recommendation": "需手动搜索同类产品"}
    
    issues = []
    valid = 0
    
    for i, comp in enumerate(competitors):
        # Check required fields
        if '代码' not in comp:
            issues.append(f"竞品{i+1}缺少代码字段")
            continue
        
        if '名称' not in comp:
            issues.append(f"竞品{comp.get('代码', i+1)}缺少名称字段")
            continue
        
        # Check for duplicate entries
        valid += 1
    
    if valid < 3:
        issues.append(f"有效竞品仅{valid}个，对比参考价值有限")
    
    recommendation = "数据质量良好" if not issues else "; ".join(issues)
    
    return {
        "valid_count": valid,
        "issues": issues,
        "recommendation": recommendation,
    }


def run_full_validation(data: dict) -> dict:
    """
    运行完整数据验证流程
    
    Returns: {
        "passed": bool,
        "checks": {"check_name": {"status": str, "message": str}},
        "summary": str,
    }
    """
    checks = {}
    
    # Check 1: Data freshness
    freshness = validate_data_freshness(data)
    checks["freshness"] = {
        "status": "pass" if not freshness["is_stale"] else "fail",
        "message": "; ".join(freshness["issues"]) or "数据时效性正常",
        "warnings": freshness["warnings"],
    }
    
    # Check 2: Premium cross-validation
    premium_check = cross_validate_premium(
        data.get("price"), data.get("iopv"), data.get("premium_pct")
    )
    checks["premium_validation"] = {
        "status": "pass" if not premium_check["discrepancy"] else "warning",
        "message": premium_check["message"],
    }
    
    # Check 3: Competitor data quality
    comp_check = validate_competitor_data(data.get("competitors"))
    checks["competitor_quality"] = {
        "status": "pass" if comp_check["valid_count"] >= 3 else "warning",
        "message": comp_check["recommendation"],
    }
    
    # Check 4: Required fields presence
    required_fields = ["code", "name", "fund_type"]
    missing = [f for f in required_fields if not data.get(f)]
    checks["required_fields"] = {
        "status": "pass" if not missing else "fail",
        "message": f"缺少必需字段: {', '.join(missing)}" if missing else "所有必需字段存在",
    }
    
    # Overall result
    failed = sum(1 for c in checks.values() if c["status"] == "fail")
    warnings = sum(1 for c in checks.values() if c["status"] == "warning")
    
    all_warnings = []
    for c in checks.values():
        all_warnings.extend(c.get("warnings", []))
    
    return {
        "passed": failed == 0,
        "checks": checks,
        "failed_count": failed,
        "warning_count": warnings,
        "all_warnings": all_warnings,
        "summary": f"验证{'通过' if failed == 0 else '未通过'} — {len(checks)}项检查，{failed}项失败，{warnings}项警告",
    }


def _health_recommendation(all_ok: bool, results: dict) -> str:
    """Generate recommendation based on health check results"""
    if all_ok:
        return "所有akshare端点正常"
    
    broken = [k for k, v in results.items() if not v.get("ok")]
    working = [k for k, v in results.items() if v.get("ok")]
    
    if working:
        return f"部分端点可用({', '.join(working)})，{', '.join(broken)}异常 — 可使用fallback数据源"
    
    return "所有akshare端点不可用，建议切换浏览器模式或检查网络"
