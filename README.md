# ETF Analysis v2.0 · ETF基金深度分析工作流

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.0.0-brightgreen)]()
[![Python](https://img.shields.io/badge/Python-3.8+-blue)]()

> **一句话**：输入ETF代码，输出包含15维评分卡、风险雷达、杀猪盘检测、定投策略的完整投资决策报告。

---

## 📖 目录

- [✨ 核心功能](#-核心功能)
- [🚀 快速开始](#-快速开始)
- [📊 v2.0 新增模块](#-v20-新增模块)
- [🔧 CLI 用法](#-cli-用法)
- [📁 项目结构](#-项目结构)
- [🔑 关键设计原则](#-关键设计原则)
- [⚠️ 已知问题与限制](#%EF%B8%8F-已知问题与限制)
- [📋 Changelog](#-changelog)

---

## ✨ 核心功能

### v1.x 基础能力（保留）

| Task | 功能 | 数据源 |
|------|------|--------|
| **Task 0** | 基金类型识别 + 代码确认 | akshare / web_search |
| **Task 1** | 实时行情数据采集（价格/净值/溢价率/成交量） | akshare `fund_etf_spot_em` |
| **Task 2** | 历史业绩计算（收益率/波动率/Sharpe/回撤/CAGR） | akshare `stock_zh_index_daily` |
| **Task 3** | 同类横向对比（至少10个竞品，含费率+跟踪误差） | akshare + web_search |
| **Task 4** | 底层资产分析（指数状态+宏观环境+持仓验证） | browser (CNBC) / 天天基金网 |

### v2.0 新增能力 🆕

| Task | 功能 | 输出 |
|------|------|------|
| **Task 5** | 🔥 **15维评分卡系统** — A/B/C三类15维度加权评分 | `S/A/B+/B/C+/C/D/F` 评级 + 红旗警告 |
| **Task 5.5** | 🎯 **风险雷达评估** — 6大风险维度量化 | 系统性/流动性/汇率/政策/集中度/溢价波动风险等级 |
| **Task 5.6** | 🔍 **ETF杀猪盘检测** — 5类陷阱自动扫描 | 溢价/流动性/规模/跟踪偏离/费率陷阱判定 |
| **Task 6** | 📅 **定投策略分析** — 智能买入区间+止盈止损 | 频率建议 + 金额规划 + 三级止盈线 |
| **Task 7** | 📄 **HTML报告生成** — 暗色主题自包含报告 | 响应式设计，支持打印和分享 |
| **Task 8** | ✅ **数据验证层** — API健康检查+时效性校验 | akshare可用性 + 溢价率交叉验证 |

---

## 🚀 快速开始

### 安装依赖

```bash
pip install akshare pandas
```

### 运行完整分析

```bash
cd scripts
python etf_analyzer.py 513100 --all
```

输出示例：
```
============================================================
🚀 ETF Analysis v2.0 — 分析启动
   代码: 513100
   模式: 完整分析(含v2.0新模块)
============================================================

✅ Task 0-4: 核心数据采集完成
✅ Task 5: 综合评分: 5.4/10 — 评级: C+
   ⚠️ 溢价7.6%，性价比偏低
✅ Task 5.5: 整体风险等级: 🟢 低风险
✅ Task 5.6: 🟢 无明显陷阱信号 — 产品健康度良好
✅ Task 6: 🟡 建议等待溢价回落后再开始定投
   推荐频率: 月度定投
✅ Task 7: 验证通过 — 4项检查，0项失败，1项警告
✅ Task 8: HTML报告已生成: .cache/etf_513100/reports/xxx.html (8.6KB)

████████████████████ 100% · 分析完成 (9/9 Tasks)
```

---

## 📊 v2.0 新增模块详解

### 🔥 Task 5: 15维评分卡系统

借鉴个股深度分析的22维打分理念，设计ETF专属评分体系：

| 类别 | 权重 | 维度 | 说明 |
|------|------|------|------|
| **A类：产品本身** | 40% | A1 溢价率 (12%) | 实时折溢价率判定 |
| | | A2 流动性 (10%) | 市值+成交量评估 |
| | | A3 费率水平 (6%) | 管理费+托管费对比 |
| | | A4 跟踪误差 (8%) | ETF与指数偏离度 |
| **B类：底层资产** | 35% | B1 估值安全边际 (12%) | PE/PB历史分位 |
| | | B2 历史业绩表现 (10%) | 多周期收益率+Sharpe |
| | | B3 持仓质量 (8%) | 集中度+持仓只数 |
| **C类：市场环境** | 25% | C1 宏观环境风险 (8%) | Agent判断+新闻分析 |
| | | C2 政策风险 (7%) | 监管变化/QDII额度 |
| | | C3 汇率风险 (10%) | QDII专属，非QDII满分 |

**评级标准：** S(≥9.0) → A(≥8.0) → B+(≥7.0) → B(≥6.0) → C+(≥5.0) → C(≥4.0) → D(≥3.0) → F(<3.0)

### 🎯 Task 5.5: 风险雷达评估

6大风险维度量化评分（0-100分）：

```
系统性风险 ──── 市场整体下跌风险（基于业绩/波动率/VIX）
流动性风险 ──── 买卖困难/冲击成本高（基于市值/成交量）
汇率风险   ──── QDII专属（基于货币敞口/汇率波动率）
政策风险   ──── 监管变化/QDII额度限制
集中度风险 ──── 持仓过于集中（基于前十大占比）
溢价波动风险 ── 折溢价剧烈变动
```

### 🔍 Task 5.6: ETF杀猪盘检测

自动扫描5类常见陷阱：

| 类型 | ID | 触发条件示例 | 严重等级 |
|------|-----|-------------|---------|
| **溢价陷阱** | T1 | 溢价 > 15% | 🔴 CRITICAL |
| **流动性陷阱** | T2 | 市值 < 2亿 + 成交量 < 5千手 | 🟠 HIGH |
| **规模陷阱** | T3 | 市值 < 5000万（清盘风险） | 🔴 CRITICAL |
| **跟踪偏离陷阱** | T4 | ETF回报与指数差异 > 20% | 🔴 CRITICAL |
| **费率陷阱** | T5 | 费率比同行高 0.5%+ | 🟡 MEDIUM |

### 📅 Task 6: 定投策略分析

基于历史数据生成智能定投建议：

- ✅ **最佳买入区间** — 基于52周高低点和历史回撤计算
- ✅ **三级止盈线** — 20%/50%/100%收益的减仓建议
- ✅ **止损保护** — 基于历史最大回撤设置硬性止损
- ✅ **频率优化** — 根据溢价率和波动率推荐定投频率
- ✅ **金额规划** — 按风险偏好计算月投入比例

### 📄 Task 7: HTML报告生成

自动生成暗色主题自包含HTML报告：
- 🎨 GitHub风格暗色配色
- 📱 响应式设计（手机/平板适配）
- 🖨️ 打印友好（自动切换浅色背景）
- 📊 内嵌JSON数据（支持后续交互扩展）

### ✅ Task 8: 数据验证层

确保分析数据的可靠性：
- akshare端点可用性检测（3个关键API）
- 行情数据时效性检查（>24h未更新报警）
- 持仓数据滞后检测（>2季度滞后警告）
- 溢价率交叉验证（计算值 vs 报告值一致性）

---

## 🔧 CLI 用法

```bash
# 完整分析（含所有v2.0模块）
python etf_analyzer.py 513100 --all

# 单独运行特定模块
python etf_analyzer.py 513100 --scoring      # 仅评分卡
python etf_analyzer.py 513100 --radar        # 仅风险雷达
python etf_analyzer.py 513100 --traps        # 仅杀猪盘检测
python etf_analyzer.py 513100 --sip          # 仅定投策略
python etf_analyzer.py 513100 --report       # 生成HTML报告
python etf_analyzer.py 513100 --validate     # 数据验证

# 组合使用
python etf_analyzer.py 513100 --scoring --traps --sip
```

### Python API 调用

```python
from _scoring import compute_etf_score
from _risk_radar import generate_radar_data
from _trap_detector import run_trap_detection
from _sip_strategy import generate_sip_strategy
from _report_generator import generate_html_report
from _validator import check_akshare_health, run_full_validation

# 评分卡
score_result = compute_etf_score(raw_data)
print(f"评级: {score_result['grade']}, 总分: {score_result['weighted_total']}")

# 风险雷达
radar = generate_radar_data(raw_data)
print(f"风险等级: {radar['overall_risk_level']}")

# 杀猪盘检测
traps = run_trap_detection(raw_data)
print(f"判定: {traps['overall_verdict']}")

# 定投策略
sip = generate_sip_strategy(raw_data)
print(f"建议: {sip['overall_sip_verdict']}")
```

---

## 📁 项目结构

```
etf-analysis/
├── SKILL.md                    # Hermes Skill 定义文件（Agent工作流指令）
├── README.md                   # 本文件
├── .gitignore                  # Git排除规则
│
├── scripts/                    # Python分析脚本
│   ├── etf_analyzer.py         # 🚀 主入口（v2.0重构版，~14KB）
│   ├── _core_fetch.py          # akshare数据获取层
│   ├── _tasks_core.py          # Task 0-3核心任务实现
│   ├── _tasks_holdings.py      # Task 4持仓分析
│   ├── _scoring.py             # 🔥 15维评分卡引擎（~530行）
│   ├── _risk_radar.py          # 🎯 风险雷达评估模块（~306行）
│   ├── _trap_detector.py       # 🔍 ETF杀猪盘检测器（~280行）
│   ├── _sip_strategy.py        # 📅 定投策略分析引擎（~270行）
│   ├── _report_generator.py    # 📄 HTML报告生成器（~430行）
│   └── _validator.py           # ✅ 数据验证层（~250行）
│
├── references/                 # 参考文档
│   ├── key-insights.md         # 关键洞察模板（禁止空泛话术示例）
│   └── session-notes.md        # Session分析记录
│
└── templates/                  # 报告模板
    └── report_template.md      # Markdown报告输出模板
```

---

## 🔑 关键设计原则

### 1. 溢价率是第一性原理

> 你多付的每一分钱都是确定的损失。

任何ETF分析必须明确标注当前溢价率及其风险等级：
- `🔴🔴🔴` 严重高估（>10%）— 每投入1万元，有X元是纯泡沫
- `🔴🔴` 明显高估（5-10%）— 建议寻找低溢价替代品
- `🟡` 轻度高估（2-5%）— 注意风险
- `🟢` 溢价合理或折价

### 2. 数据必须来自真实工具调用

禁止编造数字。所有数据必须通过 akshare、浏览器或 web_search 获取。

### 3. 矛盾必须呈现

底层资产看多但溢价过高时，把冲突写进报告——不做无脑推荐。

### 4. LOF/QDII 基金完整支持

- `fund_etf_spot_em()` **不包含LOF基金** — 自动fallback到 `fund_lof_spot_em()`
- SH/SZ双市场历史K线自动尝试
- QDII持仓为空时提供底层指数成分股作为代理数据

---

## ⚠️ 已知问题与限制

### akshare API 限制

| 问题 | 影响 | 解决方案 |
|------|------|---------|
| `fund_etf_spot_em()` 不包含LOF基金 | LOF代码查不到 | 自动fallback到 `fund_lof_spot_em()` |
| LOF数据缺少IOPV/折价率字段 | 无法直接获取溢价率 | 通过净值vs市价手动计算 |
| SH前缀对SZ市场基金抛异常 | 历史K线获取失败 | try/except保护，自动尝试SZ前缀 |
| QDII持仓可能为空（港股/美股） | 持仓分析缺失 | 用底层指数成分股代理 + 浏览器验证 |
| 持仓数据可能严重滞后 | 返回2024Q4而非最新 | **必须通过天天基金网验证**：`fundf10.eastmoney.com/ccmx_{code}.html` |

### v2.0 已知问题

- **评分卡部分维度需要web_search补充** — A3费率、A4跟踪误差、B1估值分位等维度在无数据时返回5.0（中性），需Agent通过web_search补充
- **C类市场环境维度依赖Agent判断** — C1宏观风险、C2政策风险需要结合实时新闻分析，纯脚本模式给默认值

---

## 📋 Changelog

### v2.0 (2026-06-11) 🚀 重大升级

借鉴deep-analysis的评分卡理念，新增：
- ✅ ETF专属15维评分卡系统（A/B/C三类，S/A/B+/B/C+/C/D/F评级）
- ✅ 风险雷达评估模块（6大风险维度量化+可视化数据）
- ✅ ETF杀猪盘检测器（溢价/流动性/规模/跟踪偏离/费率5类陷阱）
- ✅ 定投策略分析引擎（买入区间+三级止盈+止损保护+频率优化）
- ✅ HTML报告生成器（暗色主题自包含，支持打印和分享）
- ✅ 数据验证层（API健康检查+时效性校验+溢价率交叉验证）
- ✅ etf_analyzer.py主入口重构（支持--all/--scoring/--traps等CLI参数）

### v1.3 (2026-06-11)
- 竞品变量名bug修复、LOF溢价处理增强
- 流动性危机检测规则
- akshare持仓数据滞后警告（需浏览器验证）
- 指数成分股匹配陷阱

### v1.2 (2026-06-11)
- LOF/QDII基金支持 — `_get_fund_spot_df()`统一查询
- SH/SZ双市场fallback、持仓数据三层fallback
- is_target浮点数修复

### v1.1
- 自动关键词检测fallback、akshare代理错误处理
- 增强型ETF排除

### v1.0
- 初始版本

---

## 📄 License

MIT License — See [SKILL.md](SKILL.md) for details.
