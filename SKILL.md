---
name: etf-analysis
description: ETF基金深度分析工作流。当用户要求分析ETF基金（如纳指ETF、沪深300ETF、行业ETF、QDII基金等）是否值得投资时触发。覆盖实时行情采集、溢价率检测、历史业绩计算、同类横向对比、底层资产分析，最终输出结构化投资决策报告。v2.0新增：15维评分卡系统、风险雷达评估、杀猪盘检测、定投策略分析、HTML报告生成、数据验证层。关键词：ETF、基金、纳指ETF、513100、QDII、溢价率、定投、值不值得买。
version: 2.0.0
author: Hermes CEO
license: MIT
metadata:
  hermes:
    tags: [finance, etf, fund, qdii, a-share, investment-analysis]
---

# ETF Fund Analysis · ETF基金深度分析工作流 v2.0

> 你正在扮演一位**首席ETF分析师**。你的职责是系统性地采集数据、识别风险信号、对比同类产品，最终给出有数据支撑的投资建议。

## 🎯 角色定位

- **你不是数据的搬运工** — 不要只贴数字，要解释每个数字意味着什么
- **你是分析师** — 你读原始数据，然后用判断串起一个有冲突感、有洞察的叙事
- **核心原则**：溢价率是ETF分析的第一性原理——你多付的每一分钱都是确定的损失

## ⛔ 硬性门控规则

1. **必须按 Task 顺序执行**（见下方流程），前一 Task 数据不完整禁止开始下一步
2. **数据必须来自真实工具调用**（akshare/浏览器/web_search），禁止编造数字
3. **溢价率警报是强制的**：任何ETF分析必须明确标注当前溢价率及其风险等级
4. **报告禁止空泛话术**："基本面良好"/"前景广阔"/"值得关注" 出现即失败。必须用定量金句
5. **矛盾必须呈现**：底层资产看多但溢价过高时，把冲突写进报告
6. **LOF/QDII基金必须先识别类型**（见下方 LOF/QDII 支持章节）

## 🔧 LOF/QDII 基金支持（v1.2 新增）

LOF基金（如160644港美互联网LOF）**不在** `fund_etf_spot_em()` 数据中，必须额外查询 `fund_lof_spot_em()`：

```python
# 统一查询函数 — 先ETF后LOF
def _get_fund_spot_df(code):
    # Try ETF spot first
    try:
        df = ak.fund_etf_spot_em()
        row = df[df['代码'] == code]
        if not row.empty:
            return df, row, "ETF"
    except Exception:
        pass

    # Fallback to LOF spot (covers QDII-LOF like 160644)
    try:
        df_lof = ak.fund_lof_spot_em()
        if df_lof is not None and not df_lof.empty:
            row = df_lof[df_lof['代码'] == code]
            if not row.empty:
                return df_lof, row, "LOF"
    except Exception:
        pass

    # Final fallback: fund_name_em for basic info
    try:
        df_name = ak.fund_name_em()
        row = df_name[df_name['基金代码'] == code]
        if not row.empty:
            return None, row, "LOF/QDII"
    except Exception:
        pass

    return None, pd.DataFrame(), "unknown"
```

**关键差异：**
- LOF数据缺少 `IOPV实时估值`、`基金折价率`、`主力净流入` 等字段
- LOF竞品搜索需合并ETF+LOF数据（使用共同列名做concat）
- QDII基金持仓可能为空（港股/美股不在akshare A股数据库中），需用底层指数成分股作为代理

**历史K线必须尝试SZ前缀：**
```python
# SH前缀对SZ市场的LOF会抛异常，必须try/except保护
df = None
for prefix in ['sh', 'sz']:
    try:
        df = ak.stock_zh_index_daily(symbol=f'{prefix}{code}')
        if df is not None and not df.empty and 'close' in df.columns:
            break
        df = None
    except Exception:
        df = None  # Silently fail, try next prefix
```

**持仓数据三层fallback：**
1. `fund_portfolio_hold_em()` — 最新API，优先使用（取sorted季度[-1]）
2. `fund_portfolio_em(indicator='股票型')` — 备用旧API
3. QDII代理：如果都是空的，提供底层指数成分股作为参考数据

## 📋 9 Task 完整流程（v2.0）

| Task | 名称 | 工具 | 产出 | v2.0状态 |
|------|------|------|------|----------|
| 0 | 识别基金类型 + 代码确认 | web_search / akshare | 基金基本信息 | ✅ 保留 |
| 1 | 实时行情数据采集 | akshare (fund_etf_spot_em) | 价格/净值/溢价率/成交量 | ✅ 保留 |
| 2 | 历史业绩计算 | akshare (stock_zh_index_daily) | 收益率/波动率/Sharpe/回撤 | ✅ 保留 |
| 3 | 同类横向对比 | akshare + web_search | 竞品对比表 | ✅ 增强：+费率/跟踪误差 |
| 4 | 底层资产分析 | browser (CNBC/WallStreet) | 指数状态+宏观环境 | ✅ 保留 |
| **5** | **ETF专属15维评分卡** | `_scoring.py` | **加权总分 + S/A/B/C/D/F评级** | 🆕 v2.0新增 |
| **5.5** | **风险雷达评估** | `_risk_radar.py` | **6大风险维度量化+可视化数据** | 🆕 v2.0新增 |
| **5.6** | **ETF杀猪盘检测** | `_trap_detector.py` | **5类陷阱扫描+危险等级判定** | 🆕 v2.0新增 |
| **6** | **定投策略分析** | `_sip_strategy.py` | **买入区间/止盈止损/频率建议** | 🆕 v2.0新增 |
| 7 | 综合研判 + 报告输出 | agent判断 + `_report_generator.py` | 投资决策矩阵 + HTML报告 | ✅ 增强：+HTML生成 |

### ⚡ v2.0 核心升级亮点

1. **15维评分卡系统** — 借鉴deep-analysis的22维理念，设计ETF专属A/B/C三类15个维度
2. **风险雷达图** — 6大风险维度量化评估（系统性/流动性/汇率/政策/集中度/溢价波动）
3. **杀猪盘检测器** — 5类陷阱自动扫描（溢价/流动性/规模/跟踪偏离/费率）
4. **定投策略引擎** — 基于历史数据的智能定投建议（买入区间+止盈止损+频率优化）
5. **HTML报告生成** — 暗色主题自包含HTML报告，支持打印和分享
6. **数据验证层** — akshare健康检查 + 时效性校验 + 溢价率交叉验证

## 🔧 工具箱

### Python / akshare（核心数据源）

```python
import akshare as ak

# Task 1: 实时行情 — 获取所有ETF的实时报价
df = ak.fund_etf_spot_em()
row = df[df['代码'] == '513100']
# 关键字段：最新价, IOPV实时估值, 基金折价率, 涨跌幅, 成交量, 成交额, 主力净流入

# Task 2: 历史K线 — 计算业绩指标
df = ak.stock_zh_index_daily(symbol='sh513100')
# 关键字段：date, open, high, low, close, volume

# Task 2.5: 持仓数据（QDII/股票型ETF）
df = ak.fund_portfolio_hold_em(symbol='513100')
# 关键字段：股票代码, 股票名称, 占净值比例, 季度

# Task 3: 同类筛选
nazhi_etfs = df[df['名称'].str.contains('纳指|纳斯达克', na=False)]
```

### 浏览器（底层资产分析）

- **CNBC**: `https://www.cnbc.com/quotes/.NDX` — 纳指100实时数据+新闻
- **Yahoo Finance**: ETF详情页
- **东方财富**: QDII额度、基金公告

## 📊 Task 详细执行指南

### Task 0 · 识别基金类型（v1.2：支持LOF/QDII）

```
输入: 用户说的基金名称或代码（如"513100"或"纳指ETF国泰"或"160644"）

步骤:
1. 用 _get_fund_spot_df() 统一查询（先ETF后LOF，见上方 LOF/QDII 支持章节）
2. 确认：跟踪指数、基金管理人、成立日期、规模、**基金类型(ETF/LOF/QDII)**
3. 向用户汇报确认信息

输出格式:
✅ 已确认分析目标：{基金名称} ({代码}) [{fund_type}]
   - 跟踪指数: {指数名}
   - 基金管理人: {公司名}
   - 流通市值: {X亿}
```

**⚠️ LOF/QDII识别坑（v1.2）**：
- `fund_etf_spot_em()` **不包含LOF基金**。代码如160644、164906等必须查`fund_lof_spot_em()`
- LOF数据缺少`IOPV实时估值`和`基金折价率`字段——溢价率需通过净值vs市价手动计算
- QDII基金的持仓数据（港股/美股）在akshare中可能为空，需用底层指数成分股代理

### Task 1 · 实时行情数据采集（⚡ 最关键）

```python
import akshare as ak

df = ak.fund_etf_spot_em()
row = df[df['代码'] == '{代码}']

# 提取关键字段并标注风险信号
price = row['最新价'].values[0]
iopv = row['IOPV实时估值'].values[0]
premium = row['基金折价率'].values[0]  # 负值=溢价（高估）
volume = row['成交量'].values[0]
main_netflow = row['主力净流入-净额'].values[0]

# ⚠️ 溢价率风险等级判定
if premium < -10:
    level = "🔴🔴🔴 严重高估！每投入1万元，有{abs(premium)*100:.0f}元是纯泡沫"
elif premium < -5:
    level = "🔴🔴 明显高估，建议寻找低溢价替代品"
elif premium < -2:
    level = "🟡 轻度高估，注意风险"
else:
    level = "🟢 溢价合理或折价（便宜）"
```

**必须采集的字段清单：**
- [ ] 最新价格
- [ ] IOPV实时估值（净值）
- [ ] **基金折价率/溢价率** ← 核心指标
- [ ] 今日涨跌幅
- [ ] 成交量 + 成交额
- [ ] 流通市值 / 总份额
- [ ] 主力净流入净额 + 净占比

### Task 2 · 历史业绩计算（v1.2：支持SH/SZ双市场）

```python
import akshare as ak
from datetime import date

# ⚠️ SH前缀对SZ市场的LOF会抛异常，必须try/except保护
df = None
for prefix in ['sh', 'sz']:
    try:
        df = ak.stock_zh_index_daily(symbol=f'{prefix}{{代码}}')
        if df is not None and not df.empty and 'close' in df.columns:
            break
        df = None
    except Exception:
        df = None  # Silently fail, try next prefix

if df is None or df.empty:
    print("❌ 无历史数据")
```

**⚠️ akshare版本兼容性（v1.2）**：
- `stock_zh_index_daily()` 返回的列名是**小写**（`date`, `close`, `volume`），不是大写
- SH前缀对SZ市场的基金（如160644）会内部抛`KeyError: 'date'`——必须用try/except包裹
- 新akshare版本可能改变API签名，始终检查返回的列名

**收益率计算代码同上**（last_20, last_60, last_120, last_250等）

# === 收益率计算 ===
last_20 = df.tail(20)
ret_1m = (df.iloc[-1]['close'] / last_20.iloc[0]['close'] - 1) * 100

last_60 = df.tail(60)
ret_3m = (df.iloc[-1]['close'] / last_60.iloc[0]['close'] - 1) * 100

last_120 = df.tail(120)
ret_6m = (df.iloc[-1]['close'] / last_120.iloc[0]['close'] - 1) * 100

last_250 = df.tail(250)
ret_1y = (df.iloc[-1]['close'] / last_250.iloc[0]['close'] - 1) * 100

# YTD
ytd = df[df['date'] >= date(2026, 1, 2)]
if len(ytd) > 0:
    ret_ytd = (df.iloc[-1]['close'] / ytd.iloc[0]['close'] - 1) * 100

# === 风险指标 ===
peak = df['close'].expanding().max()
drawdown = (df['close'] - peak) / peak * 100
print(f'历史最大回撤: {drawdown.min():.2f}%')
print(f'当前距高点回撤: {drawdown.iloc[-1]:.2f}%')

# 波动率 + Sharpe
df['returns'] = df['close'].pct_change()
ann_vol = df['returns'].std() * (252**0.5) * 100
daily_rf = 0.03/252
sharpe = (df['returns'].mean() - daily_rf) / df['returns'].std() * (252**0.5)

# === CAGR（成立以来年化）===
inception = df.head(1)
years = (df.iloc[-1]['date'] - inception.iloc[0]['date']).days / 365.25
cagr = ((df.iloc[-1]['close'] / inception.iloc[0]['close']) ** (1/years) - 1) * 100

# === 52周高低点 ===
print(f'52-week high: {df.tail(250)["close"].max()}')
print(f'52-week low: {df.tail(250)["close"].min()}')
```

**⚠️ v1.3 流动性危机检测（关键新增）：**
- ETF回撤幅度 >> 底层指数回撤幅度 = **价格与资产脱钩信号**
- 必须获取跟踪指数的历史数据并对比ETF表现
- 如果差异超过20%，在报告中明确标注"⚠️ 可能存在流动性危机或折溢价异常"
- 小盘ETF（<10亿）更容易出现此问题

### Task 3 · 同类横向对比（v1.3：修复变量名bug + LOF溢价处理）

```python
# ⚠️ LOF基金不在ETF列表中，必须合并查询
df_etf = ak.fund_etf_spot_em()
target_row = df_etf[df_etf['代码'] == '{代码}']

if target_row.empty:
    # 查LOF列表并合并数据
    df_lof = ak.fund_lof_spot_em()
    if df_lof is not None and not df_lof.empty:
        target_row = df_lof[df_lof['代码'] == '{代码}']
        # 使用共同列名做concat（LOF缺少IOPV/折价率等字段）
        common_cols = list(set(df_etf.columns) & set(df_lof.columns))
        if '名称' in common_cols and '代码' in common_cols:
            df_combined = pd.concat([df_etf[common_cols], df_lof[common_cols]])
            df_etf = df_combined

# 根据ETF类型使用不同关键词（v1.2新增互联网类）：
# - 纳指ETF: '纳指|纳斯达克'
# - 沪深300ETF: '沪深300'
# - 恒生科技ETF: '恒生科技'
# - 半导体ETF: '芯片|半导体'
# - 科创50ETF: '科创50'
# - 互联网/中概类: '互联网|恒生科技|中概'

competitors = df_etf[df_etf['名称'].str.contains('{关键词}', na=False)]
```

**⚠️ is_target标记修复（v1.2）**：
- akshare返回的代码是浮点数（如`160644.0`），与字符串比较会失败
- **必须统一转为整数字符串比较**：`str(int(float(entry.get('代码', 0)))) == str(code)`

**⚠️ LOF竞品缺少溢价率字段：**
- `best_alternative`可能为None（LOF数据无`基金折价率`列）——这是正常行为，需在报告中说明

**⚠️ 自动关键词检测的坑（v1.1）**：
- `fund_etf_spot_em()` 返回的名称可能不含你预期的关键词。例如"科创50ETF华夏"不含"科创板"，只含"科创50"
- **修复方案**：如果自动检测失败（competitors < 2），用基金名称的前4个字符作为fallback关键词重新搜索
- **增强型ETF要排除**：筛选时排除名称中含"增强"的ETF，除非用户明确要求对比增强型

```python
# Fallback: if auto-detection fails, use first 4 chars of fund name
if len(competitors) < 2:
    fallback_kw = target_name[:4]  # e.g. "科创50" from "科创50ETF华夏"
    competitors = df[df['名称'].str.contains(fallback_kw, na=False)]
```

**对比维度：**
1. 溢价率排名（越低越好）
2. 规模/流动性（越大越好）
3. 费率（管理费+托管费，越低越好）
4. 跟踪误差（越小越好）

### Task 4 · 底层资产分析

对于QDII ETF（如纳指ETF），必须分析底层指数：

```
步骤:
1. 用浏览器访问 CNBC/WallStreet Journal 获取指数实时数据
2. 提取：当前点位、52周高低点、距高点回撤
3. 抓取最新新闻标题，识别风险信号
4. 分析前十大持仓权重变化

CNBC URL模板: https://www.cnbc.com/quotes/.NDX (纳指100)
              https://www.cnbc.com/quotes/^DJI (道琼斯)
              https://www.cnbc.com/quotes/%5EGSPC (标普500)
```

对于A股ETF（如科创50、沪深300），底层指数分析用akshare + 财联社：

```python
# A股指数数据 — akshare
df = ak.stock_zh_index_daily(symbol='sh{指数代码}')
# 科创50: sh000688, 沪深300: sh000300, 创业板指: sz399006

# 成分股列表 — akshare
constituents = ak.index_stock_cons(symbol='{指数代码}')
```

**⚠️ akshare代理错误处理（v1.1）**：
- `stock_zh_index_daily_em()` 等eastmoney端点在部分网络环境下会报 `ProxyError: Remote end closed connection`
- **修复方案**：如果em系列函数失败，回退到 `stock_zh_index_daily()`（非em版本），数据质量相同
- **新闻来源**：用浏览器访问财联社(cls.cn)获取实时市场情报，比akshare的新闻接口更可靠

```
财联社URL模板: https://www.cls.cn/stock?code=SH{指数代码}
              例: https://www.cls.cn/stock?code=SH000688 (科创50)
```

**必须分析的风险维度：**
- [ ] 估值水平（PE/PB历史分位）
- [ ] 持仓集中度风险
- [ ] 宏观环境（利率政策、通胀、就业）
- [ ] 地缘政治风险
- [ ] 行业特定风险（如半导体周期）

**⚠️ v1.3 持仓数据验证：**
- akshare `fund_portfolio_hold_em()` 返回的可能是过时季度（如2024Q4而非最新）
- **必须通过浏览器访问天天基金网验证最新持仓**：`https://fundf10.eastmoney.com/ccmx_{code}.html`
- 使用 browser_vision 提取页面中的"股票投资明细"表格数据
- 如果akshare与网页数据季度不一致，以网页为准并在报告中标注

### Task 5 · 综合研判 + 投资决策矩阵

**必须输出的决策框架：**

| 场景 | 建议 | 理由 |
|------|------|------|
| 已持有，盈利中 | {具体建议} | {数据支撑} |
| 已持有，亏损中 | {具体建议} | {数据支撑} |
| 想新买入 | {具体建议} | {数据支撑} |
| 长期定投 | {具体建议} | {数据支撑} |

**评分卡模板：**

| 维度 | 分数(满分10) | 说明 |
|------|-------------|------|
| 底层资产质量 | X/10 | ... |
| 当前估值安全边际 | X/10 | ... |
| ETF产品竞争力（溢价率） | X/10 | ... |
| 流动性 | X/10 | ... |
| 长期持有价值 | X/10 | ... |

## 📝 报告输出格式（v2.0增强）

参考 `scripts/report_template.py` 生成结构化Markdown报告。
**新增：使用 `_report_generator.py` 可生成暗色主题HTML报告。**

**强制包含的章节：**
1. 🔑 核心结论（TL;DR）— 一页纸总结
2. 📊 综合评分卡 — **v2.0新增：15维评分 + S/A/B/C/D/F评级**
3. 实时行情快照 — 含溢价率警报
4. 历史业绩表现 — 多周期收益率+风险指标
5. ⚠️ 溢价率深度分析 — 为什么高/低、影响多大
6. 🎯 风险雷达评估 — **v2.0新增：6大风险维度量化**
7. 🔍 ETF杀猪盘检测 — **v2.0新增：5类陷阱扫描结果**
8. 同类横向对比表 — 至少10个竞品
9. 底层资产现状 — 指数数据+宏观环境
10. 📅 定投策略分析 — **v2.0新增：买入区间/止盈止损/频率建议**
11. 市场风险信号 — 来自新闻的实时情报
12. 投资决策矩阵 — 4场景建议

## 🔧 v2.0 新模块详细使用指南

### Task 5 · ETF专属评分卡系统（🆕 v2.0）

```python
from _scoring import compute_etf_score, DIM_DEFINITIONS

# 传入raw_data字典，自动计算15维评分
result = compute_etf_score(raw_data)

# 输出：
# {
#   "scores": {"A1_premium": {"score": X, "level": str, ...}, ...},
#   "weighted_total": 7.3,    # 加权总分(0-10)
#   "grade": "B+",             # S/A/B+/B/C+/C/D/F
#   "category_scores": {"product": X, "asset": X, "market": X},
#   "red_flags": ["⚠️ ..."],  # 自动识别的风险红旗
# }
```

**15维评分体系：**

| 类别 | 维度ID | 名称 | 权重 | 数据需求 |
|------|--------|------|------|----------|
| **A类：产品本身(40%)** | A1 | 溢价率 | 12% | Task 1实时数据 |
| | A2 | 流动性 | 10% | 市值+成交量 |
| | A3 | 费率水平 | 6% | web_search补充 |
| | A4 | 跟踪误差 | 8% | web_search补充 |
| **B类：底层资产(35%)** | B1 | 估值安全边际 | 12% | PE/PB历史分位 |
| | B2 | 历史业绩表现 | 10% | Task 2历史数据 |
| | B3 | 持仓质量 | 8% | Task 4持仓数据 |
| **C类：市场环境(25%)** | C1 | 宏观环境风险 | 8% | Agent判断+web_search |
| | C2 | 政策风险 | 7% | Agent判断+web_search |
| | C3 | 汇率风险(QDII) | 10% | QDII专属，非QDII满分 |

### Task 5.5 · 风险雷达评估（🆕 v2.0）

```python
from _risk_radar import generate_radar_data

radar = generate_radar_data(raw_data)

# 输出：
# {
#   "risks": {"systematic": {...}, "liquidity": {...}, ...},
#   "max_risk": "premium_volatility",  # 最高风险维度
#   "overall_risk_level": "🟡 中等风险",
#   "radar_values": [X, X, X, X, X, X],  # 雷达图数据(0-100)
# }
```

**6大风险维度：**
1. **系统性风险** — 市场整体下跌风险（基于业绩/波动率/VIX）
2. **流动性风险** — 买卖困难/冲击成本高（基于市值/成交量）
3. **汇率风险** — QDII专属（基于货币敞口/汇率波动率）
4. **政策风险** — 监管变化/QDII额度限制
5. **集中度风险** — 持仓过于集中（基于前十大占比）
6. **溢价波动风险** — 折溢价剧烈变动

### Task 5.6 · ETF杀猪盘检测（🆕 v2.0）

```python
from _trap_detector import run_trap_detection

traps = run_trap_detection(raw_data)

# 输出：
# {
#   "traps": [trap1, trap2, ...],  # 5个检测结果
#   "critical_count": 0,           # 🔴严重陷阱数
#   "high_count": 1,               # 🟠高风险信号数
#   "overall_verdict": str,        # 综合判定
#   "recommendation": str,         # 操作建议
# }
```

**5类陷阱检测：**

| 类型 | ID | 检测内容 | 触发条件示例 |
|------|-----|---------|-------------|
| **溢价陷阱** | T1 | 高溢价诱导追涨 | 溢价>15% → CRITICAL |
| **流动性陷阱** | T2 | 买得进卖不出 | 市值<2亿+成交量<5千手 |
| **规模陷阱** | T3 | 迷你基金清盘风险 | 市值<5000万 → CRITICAL |
| **跟踪偏离陷阱** | T4 | ETF与指数严重脱钩 | 回报差异>20% → CRITICAL |
| **费率陷阱** | T5 | 隐性高成本 | 费率比同行高0.5%+ |

### Task 6 · 定投策略分析（🆕 v2.0）

```python
from _sip_strategy import generate_sip_strategy

sip = generate_sip_strategy(raw_data)

# 输出：
# {
#   "buy_zones": {"value_zone": {...}, "growth_zone": {...}},
#   "take_profit": [{"level": str, "target_return": float, ...}],
#   "stop_loss": [{"level": str, "threshold": float, ...}],
#   "frequency_recommendation": {"recommended": str, ...},
#   "amount_recommendation": {"monthly_amount": float, ...},
#   "overall_sip_verdict": str,
# }
```

**定投策略包含：**
- ✅ **最佳买入区间** — 基于52周高低点和历史回撤计算
- ✅ **三级止盈线** — 20%/50%/100%收益的减仓建议
- ✅ **止损保护** — 基于历史最大回撤设置硬性止损
- ✅ **频率优化** — 根据溢价率和波动率推荐定投频率
- ✅ **金额规划** — 按风险偏好计算月投入比例

### Task 7 · HTML报告生成（🆕 v2.0）

```python
from _report_generator import generate_html_report

html_path = generate_html_report(analysis_data, output_dir="reports")
# → reports/etf_513100_20260611_143022.html (自包含暗色主题)
```

**HTML报告特性：**
- 🎨 暗色主题（GitHub风格配色）
- 📱 响应式设计（手机/平板适配）
- 🖨️ 打印友好（自动切换浅色背景）
- 📊 内嵌JSON数据（支持后续交互扩展）

### Task 8 · 数据验证层（🆕 v2.0）

```python
from _validator import run_full_validation, check_akshare_health

# API健康检查
health = check_akshare_health()
# → {"status": "healthy|degraded|unhealthy", ...}

# 完整数据验证
validation = run_full_validation(raw_data)
# → {"passed": bool, "checks": {...}, "summary": str}
```

**验证覆盖：**
- ✅ akshare端点可用性检测（3个关键API）
- ✅ 行情数据时效性检查（>24h未更新报警）
- ✅ 持仓数据滞后检测（>2季度滞后警告）
- ✅ 溢价率交叉验证（计算值vs报告值一致性）
- ✅ 竞品数据质量校验

## 🔑 关键洞察模板（禁止空泛话术）

```
✅ "溢价率-7.8%意味着每投入1万元，有780元是纯泡沫"
✅ "距52周高点仅-5.4%，半导体板块正在回调——短期风险在累积"
✅ "华安(159632)只收4.7%溢价 vs 国泰(513100)的7.8%——省下的3%就是白送的钱"

❌ "估值合理，基本面良好"
❌ "前景广阔，值得关注"
❌ "建议谨慎投资"（必须说明为什么谨慎、具体风险是什么）
```

## 📁 数据契约（v2.0）

| 数据源 | 用途 | 可靠性 | ⚠️ 限制 |
|--------|------|--------|---------|
| akshare.fund_etf_spot_em() | ETF实时行情+溢价率 | ⭐⭐⭐⭐⭐ | **不包含LOF基金** |
| akshare.fund_lof_spot_em() | LOF/QDII实时行情 | ⭐⭐⭐⭐⭐ | 缺少IOPV/折价率字段 |
| akshare.stock_zh_index_daily() | 历史K线+业绩计算 | ⭐⭐⭐⭐⭐ | SH前缀对SZ基金抛异常 |
| akshare.fund_portfolio_hold_em() | 持仓数据（最新API） | ⭐⭐⭐⭐ | QDII港股/美股可能为空；取sorted季度[-1]非iloc[0] |
| akshare.fund_name_em() | 基金基本信息fallback | ⭐⭐⭐ | 字段有限 |
| browser (CNBC) | 底层指数实时数据 | ⭐⭐⭐⭐⭐ | — |
| web_search | 费率/政策/新闻补充 | ⭐⭐⭐ | — |

### 🆕 v2.0 新增工具模块

| 模块 | 文件 | 功能 | 依赖 |
|------|------|------|------|
| **评分卡引擎** | `scripts/_scoring.py` | 15维加权评分 + S/A/B/C/D/F评级 | 无外部依赖 |
| **风险雷达** | `scripts/_risk_radar.py` | 6大风险维度量化评估 | 无外部依赖 |
| **杀猪盘检测** | `scripts/_trap_detector.py` | 5类陷阱自动扫描 | 无外部依赖 |
| **定投策略** | `scripts/_sip_strategy.py` | 买入区间/止盈止损/频率建议 | 无外部依赖 |
| **HTML报告** | `scripts/_report_generator.py` | 暗色主题自包含HTML报告生成 | 无外部依赖 |
| **数据验证** | `scripts/_validator.py` | API健康检查+时效性校验+交叉验证 | akshare |

**v2.0 CLI用法：**
```bash
cd skills/etf-analysis/scripts
python etf_analyzer.py 513100 --all          # 完整分析（含所有v2.0模块）
python etf_analyzer.py 513100 --scoring      # 仅评分卡
python etf_analyzer.py 513100 --traps        # 仅杀猪盘检测
python etf_analyzer.py 513100 --sip          # 仅定投策略
```

**v1.2/v1.3 已知问题（仍然有效）：**
- `fund_portfolio_hold_em()` 返回的季度按正序排列，`iloc[0]`取到最早季度而非最新——必须用`sorted(quarters)[-1]`
- QDII基金持仓为空时，提供底层指数成分股作为代理数据（需标注"非实际基金持仓"）
- akshare持仓数据可能严重滞后（如返回2024Q4而实际已有2026Q1）——**必须通过浏览器访问天天基金网验证最新持仓**：`https://fundf10.eastmoney.com/ccmx_{code}.html`
- 竞品搜索变量名陷阱：重构后`df_etf`替代了旧变量`df`，fallback关键词搜索必须使用`df_etf[...]`而非`df[...]`
- ETF价格与底层指数严重偏离时（如ETF回撤67%但指数仅回撤20%），可能是**流动性危机/折溢价异常**——必须对比ETF表现与跟踪指数表现

## ✅ 完成定义（v2.0）

- [ ] 所有9个Task已完成
- [ ] 溢价率已明确标注风险等级
- [ ] 同类对比表至少包含5个竞品
- [ ] 底层资产分析有具体数据支撑（非猜测）
- [ ] 投资决策矩阵覆盖4种场景
- [ ] **v2.0新增：15维评分卡已计算并输出评级**
- [ ] **v2.0新增：风险雷达6维度评估已完成**
- [ ] **v2.0新增：杀猪盘检测5类陷阱扫描完成**
- [ ] **v2.0新增：定投策略分析（买入区间+止盈止损）已生成**
- [ ] **v2.0新增：HTML报告已生成并保存**
- [ ] 报告无空泛话术

---

**配套脚本见 `scripts/` 目录。**

### 📁 v2.0 文件清单

| 文件 | 用途 | 大小 |
|------|------|------|
| `etf_analyzer.py` | 主入口（v2.0重构版） | ~14KB |
| `_core_fetch.py` | akshare数据获取层 | — |
| `_tasks_core.py` | Task 0-3核心任务 | — |
| `_tasks_holdings.py` | Task 4持仓分析 | — |
| **`_scoring.py`** | **🆕 15维评分卡引擎** | ~530行 |
| **`_risk_radar.py`** | **🆕 风险雷达评估模块** | ~306行 |
| **`_trap_detector.py`** | **🆕 ETF杀猪盘检测器** | ~280行 |
| **`_sip_strategy.py`** | **🆕 定投策略分析引擎** | ~270行 |
| **`_report_generator.py`** | **🆕 HTML报告生成器** | ~430行 |
| **`_validator.py`** | **🆕 数据验证层** | ~250行 |

---

## 📋 Changelog

- **v2.0 (2026-06-11)**: 🚀 重大升级 — 借鉴deep-analysis的评分卡理念，新增：
  - ✅ ETF专属15维评分卡系统（A/B/C三类，S/A/B+/B/C+/C/D/F评级）
  - ✅ 风险雷达评估模块（6大风险维度量化+可视化数据）
  - ✅ ETF杀猪盘检测器（溢价/流动性/规模/跟踪偏离/费率5类陷阱）
  - ✅ 定投策略分析引擎（买入区间+三级止盈+止损保护+频率优化）
  - ✅ HTML报告生成器（暗色主题自包含，支持打印和分享）
  - ✅ 数据验证层（API健康检查+时效性校验+溢价率交叉验证）
  - ✅ etf_analyzer.py主入口重构（支持--all/--scoring/--traps等CLI参数）

- **v1.3 (2026-06-11)**: 竞品变量名bug修复、LOF溢价处理增强、流动性危机检测规则、akshare持仓数据滞后警告（需浏览器验证）、指数成分股匹配陷阱
- **v1.2 (2026-06-11)**: LOF/QDII基金支持 — `_get_fund_spot_df()`统一查询、SH/SZ双市场fallback、持仓数据三层fallback、is_target浮点数修复
- **v1.1**: 自动关键词检测fallback、akshare代理错误处理、增强型ETF排除
- **v1.0**: 初始版本
