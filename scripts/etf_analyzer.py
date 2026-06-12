"""
ETF Analysis Script v2.0 — 一键采集ETF基金全维度数据 + 估值建模 + 产业链分析 + 评分卡 + 风险雷达 + 杀猪盘检测 + 定投策略

用法:
    python etf_analyzer.py <代码> [--all] [--scoring] [--radar] [--traps] [--sip] [--report] [--validate]

示例:
    python etf_analyzer.py 513100 --all          # 完整分析（含所有新模块）
    python etf_analyzer.py 513100 --scoring      # 仅评分卡
    python etf_analyzer.py 513100 --traps        # 仅杀猪盘检测

依赖: pip install akshare pandas

v2.0 新增模块:
  - Task 5: ETF专属15维评分卡系统 (_scoring.py)
  - Task 5.5: 风险雷达图评估 (_risk_radar.py)
  - Task 5.6: ETF杀猪盘检测 (_trap_detector.py)
  - Task 6: 定投策略分析 (_sip_strategy.py)
  - Task 7: HTML报告生成 (_report_generator.py)
  - Task 8: 数据验证层 (_validator.py)
"""

import sys
import json
import os
import argparse
from datetime import date, datetime

try:
    import akshare as ak
    import pandas as pd
except ImportError:
    print("ERROR: 请先安装依赖: pip install akshare pandas")
    sys.exit(1)

# ============================================================
# Import all modules
# ============================================================

# Core data fetching (preserved from v1.x)
from _core_fetch import _get_fund_spot_df, _extract_row_data

# Core tasks (preserved from v1.x)
from _tasks_core import task0_identify, task1_realtime, task2_history, task3_competitors

# Holdings analysis (preserved from v1.x)
from _tasks_holdings import task4_holdings

# NEW v2.0 modules
from _scoring import compute_etf_score, DIM_DEFINITIONS
from _risk_radar import generate_radar_data
from _trap_detector import run_trap_detection
from _sip_strategy import generate_sip_strategy
from _report_generator import generate_html_report
from _validator import run_full_validation, check_akshare_health


# ============================================================
# Utility functions
# ============================================================

def _ensure_cache_dir(code):
    """Create cache directory for this analysis"""
    cache_dir = os.path.join(".cache", f"etf_{code}")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def _save_json(path, data):
    """Save JSON with Chinese support"""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def _load_json(path):
    """Load JSON file"""
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


# ============================================================
# Main orchestrator
# ============================================================

def run_analysis(code: str, options: dict = None):
    """
    运行完整的ETF分析流程
    
    Args:
        code: ETF/LOF基金代码
        options: {
            "all": bool,       # Run all tasks including new v2.0 modules
            "scoring": bool,   # Run scoring system
            "radar": bool,     # Run risk radar
            "traps": bool,     # Run trap detection
            "sip": bool,       # Run SIP strategy analysis
            "report": bool,    # Generate HTML report
            "validate": bool,  # Run data validation
        }
    
    Returns:
        Complete analysis result dictionary
    """
    if options is None:
        options = {}
    
    run_all = options.get("all", False)
    cache_dir = _ensure_cache_dir(code)
    
    print(f"\n{'='*60}")
    print(f"🚀 ETF Analysis v2.0 — {_get_fund_spot_df(code)[1].get('名称', code) if False else '分析启动'}")
    print(f"   代码: {code}")
    print(f"   模式: {'完整分析(含v2.0新模块)' if run_all else '基础分析'}")
    print(f"{'='*60}\n")
    
    # ========================================
    # Phase 1: Core data collection (Tasks 0-4)
    # ========================================
    
    # Task 0: Identify fund type
    result_0, status_0 = task0_identify(code)
    if status_0 != "ok":
        print(f"\n❌ 分析失败：无法识别基金 {code}")
        return {"error": "fund_not_found", "code": code}
    
    # Task 1: Realtime data
    result_1 = task1_realtime(code)
    
    # Task 2: Historical performance
    result_2 = task2_history(code)
    
    # Task 3: Competitor comparison
    result_3 = task3_competitors(code)
    
    # Task 4: Holdings analysis
    result_4 = task4_holdings(code)
    
    # ========================================
    # Assemble raw data for v2.0 modules
    # ========================================
    
    raw_data = {
        "code": code,
        "name": result_0.get("name", ""),
        "fund_type": result_0.get("fund_type", "ETF"),
        
        # From Task 1 (realtime)
        "price": result_1.get("最新价"),
        "iopv": result_1.get("IOPV实时估值"),
        "premium_pct": result_1.get("基金折价率"),
        "market_cap": result_1.get("流通市值"),
        "volume": result_1.get("成交量"),
        "turnover": result_1.get("成交额"),
        "change_pct": result_1.get("涨跌幅"),
        "update_time": result_1.get("update_time"),
        
        # From Task 2 (history)
        "ret_1m": result_2.get("1M_return"),
        "ret_3m": result_2.get("3M_return"),
        "ret_6m": result_2.get("6M_return"),
        "ret_1y": result_2.get("1Y_return"),
        "YTD_return": result_2.get("YTD_return"),
        "cagr": result_2.get("cagr"),
        "max_drawdown": result_2.get("max_drawdown_ever"),
        "current_drawdown_from_peak": result_2.get("current_drawdown_from_peak"),
        "annualized_volatility": result_2.get("annualized_volatility"),
        "sharpe_ratio": result_2.get("sharpe_ratio"),
        "52w_high": result_2.get("52w_high"),
        "52w_low": result_2.get("52w_low"),
        "current_price": result_2.get("current_price"),
        
        # From Task 4 (holdings)
        "top10_concentration_pct": result_4.get("top10_concentration_pct"),
        "latest_quarter": result_4.get("latest_quarter"),
        "holdings_count": len(result_4.get("top_holdings", [])),
        
        # Derived fields
        "is_qdii": "QDII" in str(result_0.get("fund_type", "")) or 
                   any(kw in result_0.get("name", "") for kw in ["纳指", "标普", "恒生", "日经", "越南"]),
    }
    
    # Save raw data
    _save_json(os.path.join(cache_dir, "raw_data.json"), raw_data)
    
    # ========================================
    # Phase 2: v2.0 Analysis Modules
    # ========================================
    
    analysis_result = {
        **result_0,
        "realtime": result_1,
        "history": result_2,
        "competitors": result_3,
        "holdings": result_4,
        "raw_data": raw_data,
    }
    
    # Task 5: Scoring system (v2.0 NEW)
    if run_all or options.get("scoring"):
        print(f"\n{'='*60}")
        print(f"🏆 Task 5: ETF专属评分卡系统")
        print(f"{'='*60}")
        
        score_result = compute_etf_score(raw_data)
        analysis_result["scores"] = score_result["scores"]
        analysis_result["weighted_total"] = score_result["weighted_total"]
        analysis_result["grade"] = score_result["grade"]
        analysis_result["category_scores"] = score_result["category_scores"]
        analysis_result["red_flags"] = score_result["red_flags"]
        
        print(f"✅ 综合评分: {score_result['weighted_total']:.1f}/10 — 评级: {score_result['grade']}")
        if score_result["red_flags"]:
            for flag in score_result["red_flags"]:
                print(f"   ⚠️ {flag}")
        
        _save_json(os.path.join(cache_dir, "scores.json"), score_result)
    
    # Task 5.5: Risk radar (v2.0 NEW)
    if run_all or options.get("radar"):
        print(f"\n{'='*60}")
        print(f"🎯 Task 5.5: 风险雷达评估")
        print(f"{'='*60}")
        
        radar_result = generate_radar_data(raw_data)
        analysis_result["risk_radar"] = radar_result
        
        print(f"✅ 整体风险等级: {radar_result['overall_risk_level']}")
        max_risk = radar_result.get("max_risk", "")
        if max_risk and radar_result["risks"].get(max_risk, {}).get("level", 0) >= 5:
            risk_names = {"systematic": "系统性风险", "liquidity": "流动性风险", 
                         "fx": "汇率风险", "policy": "政策风险",
                         "concentration": "集中度风险", "premium_volatility": "溢价波动风险"}
            print(f"   ⚠️ 最高风险: {risk_names.get(max_risk, max_risk)}")
        
        _save_json(os.path.join(cache_dir, "risk_radar.json"), radar_result)
    
    # Task 5.6: Trap detection (v2.0 NEW)
    if run_all or options.get("traps"):
        print(f"\n{'='*60}")
        print(f"🔍 Task 5.6: ETF杀猪盘检测")
        print(f"{'='*60}")
        
        trap_result = run_trap_detection(raw_data)
        analysis_result["trap_detection"] = trap_result
        
        print(f"✅ {trap_result['overall_verdict']}")
        for trap in trap_result.get("traps", []):
            if trap.get("triggered"):
                print(f"   ⚠️ [{trap.get('severity', '')}] {trap.get('message', '')}")
        
        _save_json(os.path.join(cache_dir, "trap_detection.json"), trap_result)
    
    # Task 6: SIP strategy (v2.0 NEW)
    if run_all or options.get("sip"):
        print(f"\n{'='*60}")
        print(f"📅 Task 6: 定投策略分析")
        print(f"{'='*60}")
        
        sip_result = generate_sip_strategy(raw_data)
        analysis_result["sip_strategy"] = sip_result
        
        print(f"✅ {sip_result['overall_sip_verdict']}")
        freq = sip_result.get("frequency_recommendation", {})
        if freq:
            print(f"   推荐频率: {freq.get('recommended', 'N/A')}")
        
        _save_json(os.path.join(cache_dir, "sip_strategy.json"), sip_result)
    
    # Task 7: Data validation (v2.0 NEW)
    if run_all or options.get("validate"):
        print(f"\n{'='*60}")
        print(f"✅ Task 7: 数据验证")
        print(f"{'='*60}")
        
        validation = run_full_validation(raw_data)
        analysis_result["validation"] = validation
        
        print(f"✅ {validation['summary']}")
        for check_name, check in validation.get("checks", {}).items():
            status_icon = "✅" if check["status"] == "pass" else ("⚠️" if check["status"] == "warning" else "❌")
            print(f"   {status_icon} {check_name}: {check['message']}")
        
        _save_json(os.path.join(cache_dir, "validation.json"), validation)
    
    # Task 8: Generate HTML report (v2.0 NEW)
    if run_all or options.get("report"):
        print(f"\n{'='*60}")
        print(f"📄 Task 8: 生成HTML报告")
        print(f"{'='*60}")
        
        html_path = generate_html_report(analysis_result, 
                                         output_dir=os.path.join(cache_dir, "reports"))
        analysis_result["html_report_path"] = html_path
        
        file_size = os.path.getsize(html_path) if os.path.exists(html_path) else 0
        print(f"✅ HTML报告已生成: {html_path} ({file_size/1024:.1f}KB)")
    
    # Save complete analysis result
    _save_json(os.path.join(cache_dir, "analysis_result.json"), analysis_result)
    
    # ========================================
    # Progress bar
    # ========================================
    
    total_tasks = 8 if run_all else 5
    print(f"\n{'█' * 20} 100% · 分析完成 ({total_tasks}/{total_tasks} Tasks)")
    
    return analysis_result


# ============================================================
# CLI entry point
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="ETF Analysis v2.0")
    parser.add_argument("code", help="ETF/LOF基金代码 (如 513100)")
    parser.add_argument("--all", action="store_true", help="运行完整分析（含v2.0所有新模块）")
    parser.add_argument("--scoring", action="store_true", help="仅运行评分卡系统")
    parser.add_argument("--radar", action="store_true", help="仅运行风险雷达评估")
    parser.add_argument("--traps", action="store_true", help="仅运行杀猪盘检测")
    parser.add_argument("--sip", action="store_true", help="仅运行定投策略分析")
    parser.add_argument("--report", action="store_true", help="生成HTML报告")
    parser.add_argument("--validate", action="store_true", help="运行数据验证")
    
    args = parser.parse_args()
    
    options = {
        "all": args.all,
        "scoring": args.scoring,
        "radar": args.radar,
        "traps": args.traps,
        "sip": args.sip,
        "report": args.report,
        "validate": args.validate,
    }
    
    result = run_analysis(args.code, options)
    
    # Print summary
    if "error" in result:
        print(f"\n❌ 分析失败: {result['error']}")
        sys.exit(1)
    
    grade = result.get("grade", "N/A")
    total = result.get("weighted_total", "N/A")
    print(f"\n📊 最终结果:")
    print(f"   基金: {result.get('name', '未知')} ({args.code})")
    if grade != "N/A":
        print(f"   评分: {total}/10 — 评级: {grade}")
    
    traps = result.get("trap_detection", {})
    if traps:
        print(f"   陷阱检测: {traps.get('overall_verdict', '未运行')}")
    
    sip = result.get("sip_strategy", {})
    if sip:
        print(f"   定投建议: {sip.get('overall_sip_verdict', '未运行')}")


if __name__ == "__main__":
    main()
