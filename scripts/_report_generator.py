"""
ETF Report Generator v2.0 — 生成专业HTML分析报告

借鉴 deep-analysis 的 assemble_report 模式，为ETF分析生成自包含HTML报告。
支持暗色主题、风险雷达图可视化、评分卡展示。
"""

import json
import os
from datetime import datetime


def generate_html_report(analysis_data: dict, output_dir: str = "reports") -> str:
    """
    生成ETF分析HTML报告
    
    Args:
        analysis_data: 完整的分析数据字典（包含所有Task结果）
        output_dir: 输出目录
        
    Returns:
        生成的HTML文件路径
    """
    os.makedirs(output_dir, exist_ok=True)
    
    code = analysis_data.get("code", "unknown")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"etf_{code}_{timestamp}.html"
    filepath = os.path.join(output_dir, filename)
    
    # Build JSON data for embedding
    json_data = json.dumps(analysis_data, ensure_ascii=False, default=str)
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_esc(analysis_data.get('name', 'ETF'))} ({code}) 深度分析报告</title>
<style>
:root {{
    --bg-primary: #0d1117;
    --bg-secondary: #161b22;
    --bg-card: #1c2333;
    --border: #30363d;
    --text-primary: #e6edf3;
    --text-secondary: #8b949e;
    --accent-green: #3fb950;
    --accent-red: #f85149;
    --accent-yellow: #d29922;
    --accent-blue: #58a6ff;
    --accent-purple: #bc8cff;
}}

* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans SC', sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.6;
    padding: 20px;
}}

.container {{ max-width: 1200px; margin: 0 auto; }}

/* Header */
.header {{
    background: linear-gradient(135deg, #1a1f2e 0%, #0d1117 100%);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 32px;
    margin-bottom: 24px;
}}

.header h1 {{ font-size: 28px; margin-bottom: 8px; }}
.header .subtitle {{ color: var(--text-secondary); font-size: 14px; }}
.header .badge {{ 
    display: inline-block; padding: 4px 12px; border-radius: 20px; 
    font-size: 12px; font-weight: 600; margin-left: 8px;
}}
.badge-green {{ background: rgba(63,185,80,0.15); color: var(--accent-green); }}
.badge-red {{ background: rgba(248,81,73,0.15); color: var(--accent-red); }}
.badge-yellow {{ background: rgba(210,153,34,0.15); color: var(--accent-yellow); }}

/* Cards */
.card {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 24px;
    margin-bottom: 16px;
}}

.card h2 {{ 
    font-size: 18px; margin-bottom: 16px; 
    padding-bottom: 8px; border-bottom: 1px solid var(--border);
}}

/* Tables */
table {{ width: 100%; border-collapse: collapse; }}
th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid var(--border); }}
th {{ color: var(--text-secondary); font-weight: 600; font-size: 13px; text-transform: uppercase; }}
td {{ font-size: 14px; }}

/* Score display */
.score-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 16px;
}}

.score-item {{
    background: var(--bg-secondary);
    border-radius: 8px;
    padding: 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}}

.score-value {{
    font-size: 24px;
    font-weight: 700;
}}

/* Risk radar placeholder */
.radar-container {{
    text-align: center;
    padding: 20px;
}}

/* Alert boxes */
.alert {{
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
    border-left: 4px solid;
}}
.alert-critical {{ background: rgba(248,81,73,0.1); border-color: var(--accent-red); }}
.alert-warning {{ background: rgba(210,153,34,0.1); border-color: var(--accent-yellow); }}
.alert-info {{ background: rgba(88,166,255,0.1); border-color: var(--accent-blue); }}

/* Decision matrix */
.decision-table td:first-child {{ font-weight: 600; }}

/* Footer */
.footer {{
    text-align: center;
    color: var(--text-secondary);
    font-size: 12px;
    padding: 24px;
    border-top: 1px solid var(--border);
    margin-top: 32px;
}}

/* Print styles */
@media print {{
    body {{ background: white; color: black; }}
    .card {{ border: 1px solid #ddd; }}
}}
</style>
</head>
<body>
<div class="container">
{generate_header(analysis_data)}
{generate_scorecard(analysis_data)}
{generate_realtime_snapshot(analysis_data)}
{generate_premium_alert(analysis_data)}
{generate_performance(analysis_data)}
{generate_competitors(analysis_data)}
{generate_radar_section(analysis_data)}
{generate_trap_detection(analysis_data)}
{generate_sip_strategy(analysis_data)}
{generate_decision_matrix(analysis_data)}
{generate_footer()}
</div>

<script>
// Embedded data for potential interactivity
const analysisData = {json_data};
console.log('ETF Analysis Report loaded', new Date().toISOString());
</script>
</body>
</html>"""
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return filepath


def generate_header(data: dict) -> str:
    """Generate report header section"""
    name = data.get("name", "未知ETF")
    code = data.get("code", "")
    fund_type = data.get("fund_type", "ETF")
    grade = data.get("grade", "?")
    
    grade_class = "badge-green" if grade in ("S", "A", "B+") else ("badge-yellow" if grade in ("B", "C+") else "badge-red")
    
    return f"""<div class="header">
    <h1>{_esc(name)} ({code}) <span class="badge {grade_class}">评级: {grade}</span></h1>
    <p class="subtitle">
        基金类型: {_esc(fund_type)} | 
        数据截止: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 
        数据来源: akshare + CNBC + web_search
    </p>
</div>"""


def generate_scorecard(data: dict) -> str:
    """Generate scoring card section"""
    scores = data.get("scores", {})
    if not scores:
        return ""
    
    items_html = ""
    for dim_id, result in scores.items():
        score = result.get("score", 0)
        level = result.get("level", "")
        explanation = result.get("explanation", "")
        
        color = "#3fb950" if score >= 7 else ("#d29922" if score >= 5 else "#f85149")
        
        items_html += f"""<div class="score-item">
            <div>
                <strong>{_esc(level)}</strong><br>
                <small style="color:var(--text-secondary)">{_esc(explanation)}</small>
            </div>
            <div class="score-value" style="color:{color}">{score:.1f}</div>
        </div>"""
    
    total = data.get("weighted_total", 0)
    grade = data.get("grade", "?")
    
    return f"""<div class="card">
    <h2>📊 综合评分卡</h2>
    <p style="margin-bottom:16px;font-size:24px;font-weight:700;">总分: {total:.1f}/10 — 评级: {grade}</p>
    <div class="score-grid">{items_html}</div>
    
    {generate_red_flags(data.get("red_flags", []))}
</div>"""


def generate_red_flags(flags: list) -> str:
    """Generate red flags alert section"""
    if not flags:
        return ""
    
    alerts = "\n".join(f'<div class="alert alert-critical">⚠️ {_esc(f)}</div>' for f in flags)
    return f"<h3 style='margin-top:16px'>🚨 风险警报</h3>{alerts}"


def generate_realtime_snapshot(data: dict) -> str:
    """Generate realtime data snapshot"""
    rt = data.get("realtime", {})
    if not rt or rt.get("status") != "ok":
        return '<div class="card"><h2>📡 实时行情</h2><p>数据获取失败</p></div>'
    
    rows = []
    field_map = {
        "最新价": ("价格", lambda v: f"¥{v:.4f}"),
        "IOPV实时估值": ("净值(IOPV)", lambda v: f"¥{v:.4f}"),
        "基金折价率": ("折溢价率", lambda v: f"{v:.2f}%"),
        "涨跌幅": ("今日涨跌", lambda v: f"{v:.2f}%"),
        "成交量": ("成交量", lambda v: f"{v/1e4:.0f}万手"),
        "成交额": ("成交额", lambda v: f"{v/1e8:.2f}亿"),
        "流通市值": ("流通市值", lambda v: f"{v/1e8:.1f}亿"),
    }
    
    for field, (label, fmt) in field_map.items():
        if field in rt:
            rows.append(f"<tr><td>{label}</td><td>{fmt(rt[field])}</td></tr>")
    
    return f"""<div class="card">
    <h2>📡 实时行情快照</h2>
    <table>{"".join(rows)}</table>
    {f'<p style="margin-top:8px;color:var(--text-secondary)">更新时间: {_esc(rt.get("update_time", "未知"))}</p>' if rt.get("update_time") else ""}
</div>"""


def generate_premium_alert(data: dict) -> str:
    """Generate premium analysis section"""
    rt = data.get("realtime", {})
    premium = rt.get("基金折价率")
    
    if premium is None:
        return '<div class="card"><h2>💰 溢价率分析</h2><p>无溢价数据(LOF基金)</p></div>'
    
    actual_premium = -premium  # Convert to positive premium
    
    alert_class = "alert-critical" if actual_premium > 10 else ("alert-warning" if actual_premium > 3 else "alert-info")
    
    return f"""<div class="card">
    <h2>💰 溢价率深度分析</h2>
    <div class="alert {alert_class}">
        {'⚠️' if actual_premium > 5 else 'ℹ️'} 
        当前{'溢价' if actual_premium > 0 else '折价'}{abs(actual_premium):.1f}%。
        {'每投入1万元，有' + str(int(abs(actual_premium)*100)) + '元是纯泡沫' if actual_premium > 5 else '价格接近或低于净值，买入有安全边际'}
    </div>
</div>"""


def generate_performance(data: dict) -> str:
    """Generate performance history section"""
    hist = data.get("history", {})
    if not hist or hist.get("status") != "ok":
        return '<div class="card"><h2>📈 历史业绩</h2><p>无历史数据</p></div>'
    
    rows = []
    for period, label in [("ret_1m", "近1个月"), ("ret_3m", "近3个月"), 
                          ("ret_6m", "近6个月"), ("ret_1y", "近1年"),
                          ("YTD_return", "今年以来")]:
        if period in hist:
            val = hist[period]
            color = "#3fb950" if val >= 0 else "#f85149"
            rows.append(f'<tr><td>{label}</td><td style="color:{color}">{val:+.2f}%</td></tr>')
    
    risk_rows = []
    for key, label in [("annualized_volatility", "年化波动率"), ("sharpe_ratio", "Sharpe比率"),
                        ("max_drawdown_ever", "最大回撤"), ("cagr", "成立以来年化")]:
        if key in hist:
            risk_rows.append(f'<tr><td>{label}</td><td>{hist[key]}</td></tr>')
    
    return f"""<div class="card">
    <h2>📈 历史业绩表现</h2>
    <table>{"".join(rows)}</table>
    <h3 style="margin-top:16px">风险指标</h3>
    <table>{"".join(risk_rows)}</table>
</div>"""


def generate_competitors(data: dict) -> str:
    """Generate competitor comparison section"""
    comp = data.get("competitors", {})
    if not comp or comp.get("status") != "ok":
        return '<div class="card"><h2>🔄 同类对比</h2><p>无竞品数据</p></div>'
    
    competitors = comp.get("competitors", [])[:15]  # Limit to 15
    
    rows = []
    for c in competitors:
        is_target = "⭐" if c.get("is_target") else ""
        premium_level = c.get("premium_level", "")
        
        row = f'<tr><td>{is_target}{_esc(str(c.get("代码","")))} {_esc(str(c.get("名称","")))}</td>'
        for field in ["最新价", "基金折价率", "流通市值"]:
            val = c.get(field)
            if field == "基金折价率":
                row += f'<td>{val:.2f}% {premium_level}</td>' if isinstance(val, (int,float)) else "<td>—</td>"
            elif field == "流通市值":
                row += f'<td>{val/1e8:.1f}亿</td>' if isinstance(val, (int,float)) else "<td>—</td>"
            else:
                row += f"<td>{val}</td>"
        row += "</tr>"
        rows.append(row)
    
    return f"""<div class="card">
    <h2>🔄 同类产品横向对比 ({comp.get('count', 0)}个竞品)</h2>
    <table><tr><th>ETF</th><th>价格</th><th>折溢价率</th><th>流通市值</th></tr>
    {"".join(rows)}</table>
</div>"""


def generate_radar_section(data: dict) -> str:
    """Generate risk radar section"""
    radar = data.get("risk_radar", {})
    if not radar:
        return ""
    
    risks = radar.get("risks", {})
    overall = radar.get("overall_risk_level", "")
    
    alerts = ""
    for name, risk_data in risks.items():
        level = risk_data.get("level", 0)
        if level >= 5:
            signals = risk_data.get("signals", [])
            alerts += f'<div class="alert alert-{"critical" if level >= 7 else "warning"}">'
            alerts += f"<strong>{_esc(radar.get('risk_names', [''])).get(list(risks.keys()).index(name), name)}</strong>: {_esc(risk_data.get('description', ''))}"
            for s in signals[:2]:
                alerts += f"<br>&nbsp;&nbsp;• {_esc(s)}"
            alerts += "</div>"
    
    return f"""<div class="card">
    <h2>🎯 风险雷达评估</h2>
    <p style="font-size:18px;font-weight:600;margin-bottom:12px;">{overall}</p>
    {alerts}
</div>"""


def generate_trap_detection(data: dict) -> str:
    """Generate trap detection section"""
    traps = data.get("trap_detection", {})
    if not traps:
        return ""
    
    verdict = traps.get("overall_verdict", "")
    trap_list = traps.get("traps", [])
    
    alerts = ""
    for t in trap_list:
        if t.get("triggered"):
            severity = t.get("severity", "")
            alert_class = "alert-critical" if "CRITICAL" in severity else ("alert-warning" if "HIGH" in severity else "alert-info")
            alerts += f'<div class="alert {alert_class}">{_esc(t.get("message", ""))}</div>'
    
    return f"""<div class="card">
    <h2>🔍 ETF杀猪盘检测</h2>
    <p style="font-size:16px;font-weight:600;margin-bottom:12px;">{verdict}</p>
    {alerts}
</div>"""


def generate_sip_strategy(data: dict) -> str:
    """Generate SIP strategy section"""
    sip = data.get("sip_strategy", {})
    if not sip:
        return ""
    
    verdict = sip.get("overall_sip_verdict", "")
    freq = sip.get("frequency_recommendation", {})
    
    tp_items = ""
    for tp in sip.get("take_profit", []):
        tp_items += f"<tr><td>{_esc(tp['level'])}</td><td>{tp['target_return']}%</td><td>{_esc(tp['action'])}</td></tr>"
    
    sl_items = ""
    for sl in sip.get("stop_loss", []):
        sl_items += f"<tr><td>{_esc(sl['level'])}</td><td>{sl['threshold']}%</td><td>{_esc(sl['action'])}</td></tr>"
    
    return f"""<div class="card">
    <h2>📅 定投策略分析</h2>
    <p style="margin-bottom:16px;">{verdict}</p>
    
    <h3>推荐频率</h3>
    <p><strong>{_esc(freq.get('recommended', '周度定投'))}</strong>: {_esc(freq.get('reasoning', ''))}</p>
    
    <h3 style="margin-top:16px">止盈策略</h3>
    <table><tr><th>级别</th><th>目标收益</th><th>操作建议</th></tr>{tp_items}</table>
    
    <h3 style="margin-top:16px">止损策略</h3>
    <table><tr><th>级别</th><th>阈值</th><th>操作建议</th></tr>{sl_items}</table>
</div>"""


def generate_decision_matrix(data: dict) -> str:
    """Generate investment decision matrix"""
    # This section is primarily agent-generated, use data if available
    scenarios = data.get("decision_scenarios", [])
    
    if not scenarios:
        return '<div class="card"><h2>📋 投资决策矩阵</h2><p>请结合以上数据自行判断，或由分析师生成具体建议。</p></div>'
    
    rows = ""
    for s in scenarios:
        rows += f"<tr><td>{_esc(s.get('scenario', ''))}</td><td>{_esc(s.get('recommendation', ''))}</td><td>{_esc(s.get('reasoning', ''))}</td></tr>"
    
    return f"""<div class="card">
    <h2>📋 投资决策矩阵</h2>
    <table class="decision-table"><tr><th>场景</th><th>建议</th><th>理由</th></tr>{rows}</table>
</div>"""


def generate_footer() -> str:
    """Generate report footer"""
    return f"""<div class="footer">
    <p>免责声明：以上分析基于公开数据，不构成投资建议。ETF投资存在市场风险、汇率风险（QDII）、溢价波动风险等。</p>
    <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 由 Hermes ETF Analysis v2.0 自动生成</p>
</div>"""


def _esc(text: str) -> str:
    """HTML escape text"""
    if not isinstance(text, str):
        text = str(text)
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#39;"))
