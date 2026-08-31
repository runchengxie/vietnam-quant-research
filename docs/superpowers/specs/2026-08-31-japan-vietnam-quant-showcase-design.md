# 日本 vs 越南量化策略展示站设计

日期：2026-08-31  
状态：待实现  
目标分支：`codex/japan-vietnam-showcase`

## 1. 背景与目标

`vietnam-quant-research` 当前是越南股票市场的数据工程、数据治理和量化研究仓库；`guan-japanese-nira` 则是一个成熟度更高、且当前为私有仓库的日本股票多因子研究与策略工程。客户提出的核心问题并不是查看源代码，而是理解：

1. 日本市场与越南市场在量化策略适配度上有什么结构性差异；
2. 为什么同一类量化方法在两个市场中的可实现性、容量和执行成本会明显不同；
3. 当前越南研究与已有日本策略工程分别处于什么成熟度；
4. 如果客户资金规模、目标持有期或市场中性要求不同，应如何选择研究方向。

本次选择“方案 A”：先在 `vietnam-quant-research/site/` 内建设一个可独立迁移的公开展示层，将日本作为跨市场比较参照，而不合并两个研究仓库，也不引入 Git submodule。

展示站的主要受众是不了解量化或只具备基础投资知识的客户。它应优先解释策略逻辑、市场结构和实施摩擦，而不是把研究仓库简单包装成代码浏览器。

## 2. 非目标

本期明确不做以下事情：

- 不将 `guan-japanese-nira` 作为 submodule、package dependency 或构建依赖；
- 不公开日本私有仓库的源代码、模型参数、组合权重、收益曲线、交易候选或专有因子定义；
- 不把越南当前尚未通过研究门槛的数据试点结果包装成已验证 alpha；
- 不建设实时行情后端；
- 不建设客户登录、权限、数据库、在线回测或交易接口；
- 不把 1–5 星研究判断解释成收益预测、Sharpe 预测或投资评级；
- 不在本期创建跨市场执行 superproject。

## 3. 架构原则

### 3.1 研究与展示解耦

仓库保持三层职责：

```text
vietnam-quant-research
├── src/                      # 越南研究代码
├── exploration/              # 越南数据与研究探针
├── docs/                     # 研究文档与证据
└── site/                     # 面向客户的展示层
```

`site/` 只消费人工整理、可公开发布的静态研究摘要，不直接读取 Python 运行数据目录、商业数据、私有仓库或本机产物。

未来若需要独立品牌站，可将整个 `site/` 迁移到新的 `quant-market-showcase` 仓库，原研究仓库只保留导出规范和链接。

### 3.2 日本仓库仅作为能力来源，不作为构建依赖

日本 Nira 当前为私有项目，因此公开展示只允许描述以下级别的信息：

- 已具备日频/分钟/逐笔数据研究路径；
- 已具备多因子、模型、回测、top-bottom、做空可执行性和容量检查等能力；
- 日本市场更适合 long-short、market-neutral、stat-arb 和大股票池 cross-sectional 建模的原因；
- 已公开或可由官方市场规则验证的日本制度事实。

不允许公开：

- Nira 的实际 alpha 表现；
- 私有模型超参数；
- 实际持仓或候选名单；
- proprietary factor names/definitions，除非它们本身已公开；
- 私有仓库文件路径之外的敏感实现细节。

### 3.3 Facts / Judgment / Implementation 分层

所有展示内容必须标记为三类之一：

- **FACT**：有公开来源可验证的市场结构或制度事实；
- **RESEARCH JUDGMENT**：用于比较的 1–5 分主观研究判断；
- **IMPLEMENTATION STATUS**：本仓库或日本 Nira 当前已完成的工程能力。

页面上不得把 Judgment 与 Fact 使用完全相同的视觉编码。

## 4. 技术方案

### 4.1 前端栈

采用：

- Vite
- React
- TypeScript
- Apache ECharts
- 原生 CSS / CSS variables

不在本期引入 Next.js、SSR、数据库或后端框架。

理由：

- Vite 适合 GitHub Pages 与 Cloudflare Workers Static Assets 的纯静态输出；
- React 足够支撑筛选器、tooltip、交互式图表和可迁移组件；
- ECharts 能覆盖 radar、heatmap、bar、flow-like 图表，减少手写 SVG 维护成本；
- 站点无服务端依赖，未来迁移仓库时只需移动 `site/`。

### 4.2 建议目录

```text
site/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── styles/
│   │   └── app.css
│   ├── components/
│   │   ├── HeroComparison.tsx
│   │   ├── StrategyHeatmap.tsx
│   │   ├── MarketRadar.tsx
│   │   ├── AlphaToPnL.tsx
│   │   ├── ArchitectureCompare.tsx
│   │   ├── CapitalProfile.tsx
│   │   ├── MaturityCompare.tsx
│   │   └── EvidenceDrawer.tsx
│   └── data/
│       ├── marketComparison.ts
│       ├── evidence.ts
│       └── types.ts
└── public/
    └── favicon.svg
```

部署配置放在仓库级 `.github/workflows/` 和 `site/` 内的 Cloudflare 配置中。

### 4.3 URL 与构建产物约束

第一版不引入客户端路由，仅使用单页 section/anchor 导航。Vite 使用相对资源基址 `base: "./"`，因此同一个 `site/dist/` 可以同时部署到：

- GitHub Pages 的 `/vietnam-quant-research/` 子路径；
- Cloudflare Workers Static Assets 的站点根路径。

不得为了两个平台维护两套构建结果。若未来加入 history-based client routing，再重新设计 base path 与 fallback 规则。

## 5. 数据模型

展示页面使用静态 TypeScript 数据，不从远端 API 动态拉取。

### 5.1 市场比较记录

```ts
interface StrategyFit {
  id: string;
  label: string;
  japan: number;       // 1..5
  vietnam: number;     // 1..5
  verdict: string;
  category: "frequency" | "portfolio" | "model" | "alpha" | "capacity";
  japanRationale: string;
  vietnamRationale: string;
  evidenceIds: string[];
}
```

初始表格：

| 类型 | 日本 | 越南 | 判断 |
| --- | ---: | ---: | --- |
| 日频高换手因子 | 5 | 2 | 日本明显胜 |
| 日频信号、低换手执行 | 4 | 4 | 都可以 |
| 2周–3个月中频择股 | 4 | 5 | 越南很有意思 |
| Long-short market neutral | 5 | 1 | 日本压倒性 |
| Statistical Arbitrage | 5 | 2 | 日本压倒性 |
| ML Cross-sectional | 5 | 3 | 日本更适合建模，越南可能存在更肥的结构性 alpha |
| 行为金融/资金流 | 3 | 5 | 越南 |
| Fundamental quant | 5 | 4 | 日本 |
| 小资金 long-only | 4 | 5 | 越南可能更诱人 |
| 大资金系统化管理 | 5 | 2 | 日本 |

评分必须在 UI 中注明为研究判断，不能与收益预期绑定。

### 5.2 证据记录

```ts
interface Evidence {
  id: string;
  type: "fact" | "judgment" | "implementation";
  title: string;
  summary: string;
  sourceName?: string;
  sourceUrl?: string;
  asOf?: string;
  note?: string;
}
```

官方来源优先级：

1. JPX / J-Quants / 日本官方规则；
2. SSC / VSDC / HOSE / HNX / 越南政府正式文件；
3. FTSE Russell / LSEG 等指数机构；
4. 高质量新闻只用于补充背景，不作为关键交易制度的唯一依据。

页面必须显示 `as of` 日期。

## 6. 页面信息架构

### 6.1 Hero：一句话说明两个市场的“策略 DNA”

首屏并排展示：

日本：

```text
Small Alpha × Broad Universe × Long/Short × High Capacity
弱信号 × 大股票池 × 多空组合 × 高容量
```

越南：

```text
Structural Alpha × Smaller Universe × Long Bias × Lower Turnover
结构性机会 × 较窄股票池 × Long-biased × 低换手
```

页面首屏必须同时显示免责声明：这是“策略适配度研究”，不是市场收益预测或投资建议。

### 6.2 Strategy Fit Heatmap

将原始星级表转成 1–5 的可视化矩阵。

交互：

- hover/tap 显示日本与越南各自的理由；
- 支持按 `frequency / portfolio / model / alpha / capacity` 分类筛选；
- 点击可展开 Evidence Drawer；
- 无 JavaScript tooltip 时仍有可访问文本。

### 6.3 Market Structure Radar

初始维度：

- Liquidity
- Shortability
- Universe Breadth
- Data Quality
- Capacity
- Execution Infrastructure
- Behavioral Inefficiency
- Retail/Flow Signal Opportunity

雷达图评分同样属于 `RESEARCH JUDGMENT`。

必须在雷达图旁显示文本解释，避免雷达图成为“视觉上很科学、实际上定义不明”的装饰。

### 6.4 Gross Alpha → Realized PnL

这是展示站最重要的解释图之一。

两条并行路径：Japan / Vietnam。

概念流程：

```text
Gross Alpha
    ↓
Trading Cost
    ↓
Market Impact
    ↓
Borrow / Tax
    ↓
Limit / Fill Constraints
    ↓
Net Alpha
```

不展示伪造或未经研究验证的具体 bps；使用“低/中/高摩擦”或解释性标签。

核心文案：

- 日本：alpha 往往更难寻找，但市场基础设施更利于兑现和规模化；
- 越南：结构性低效可能更明显，但交易成本、流动性、做空和涨跌停等摩擦会造成更大的 implementation haircut。

### 6.5 Strategy Architecture Compare

日本侧：

```text
Market Data
  → Features
  → Cross-sectional Model
  → Residual Return Forecast
  → Long Top / Short Bottom
  → Risk Neutralization
  → Optimizer
  → Execution
```

越南侧：

```text
Market + Flow + Behavior
  → Momentum / Volume / Foreign Flow / Limit / Fundamentals
  → Cross-sectional Ranking
  → 10–40D Forecast
  → Long Top Bucket
  → Staggered Portfolio
  → Low-turnover Execution
  → Optional Index Futures Hedge
```

注意：这些是推荐研究架构，不声称越南当前仓库已实现完整策略链。

### 6.6 Capital Profile Explorer

提供三个档位：

- Small / Flexible
- Medium
- Institutional / Large

切换后更新：

- market attractiveness；
- 关键风险；
- 适合的策略类型；
- 主要执行约束。

第一版只使用规则驱动的静态结论，不做伪精确资金容量计算。

### 6.7 Project Maturity

公开说明两个工程的成熟度，且标签必须是“工程能力”而非“策略收益质量”。

越南：

- Data Engineering：较高
- Data Quality Gate：进行中
- Factor Research：早期
- Portfolio：早期/未批准形成正式 alpha 结论
- Execution：早期

日本 Nira：

- Data Engineering：成熟
- Factor Research：成熟
- Backtest：已具备
- Long/Short：已具备研究与可执行性检查
- Executability：已具备容量/做空代理/交易候选等组件

禁止将私有仓库成熟度条解释成收益评级。

### 6.8 Evidence / Methodology

底部提供：

- 数据与制度来源；
- 评分方法；
- 评分更新日期；
- 越南项目当前研究边界；
- 日本项目仅展示公开可描述能力，不公开私有策略细节；
- 投资与数据许可免责声明。

## 7. 视觉设计

目标风格：研究型、克制、客户可读，不做传统券商 PPT 风格。

语言以中文为主，保留 `Market Neutral`、`Stat Arb`、`Cross-sectional`、`Alpha`、`Execution` 等必要英文技术标签；本期不引入完整中英双语 i18n。

原则：

- Japan 与 Vietnam 使用稳定的双市场视觉编码；
- 不用红涨绿跌的文化特定颜色暗示“谁更好”；
- 评分采用长度、深浅和数字三重编码，避免仅依赖颜色；
- 关键结论优先用短句而非大段解释；
- 每个图表均有文本 fallback；
- 移动端按单列阅读，桌面端双列比较；
- 控制动画，只用于状态变化，不用作金融科技装饰。

## 8. 响应式与可访问性

最低要求：

- 360px 移动宽度可读；
- 1024px 以上提供双栏/多栏对比；
- 键盘可操作筛选器和 Evidence Drawer；
- 使用语义 heading 与表格结构；
- 所有视觉评分同时显示数字或文字；
- `prefers-reduced-motion` 下禁用非必要动画；
- 图表容器提供对应的 `aria-label` 和邻接文本解释。

## 9. 部署方案

### 9.1 GitHub Pages

使用 GitHub Actions：

1. checkout；
2. setup Node；
3. `npm ci`；
4. `npm run test`；
5. `npm run build`；
6. 上传 `site/dist`；
7. deploy Pages。

Vite 使用 `base: "./"`，确保部署到 GitHub Pages 仓库子路径时资源地址仍然有效。

### 9.2 Cloudflare

本期目标是 Cloudflare Workers Static Assets，直接发布同一个 `site/dist`，不重新构建。

如果 Cloudflare 凭证/连接在实现阶段不可用，则：

- 仍提交可运行的 Wrangler 配置；
- GitHub Pages 作为无需额外 Cloudflare 写权限的第一部署目标；
- PR 中明确标记 Cloudflare 实际部署是否完成。

未来若独立成 `quant-market-showcase`，Cloudflare 可变成主域名入口，GitHub Pages 作为公开镜像/备用。

## 10. 测试与质量门槛

### 10.1 单元测试

至少覆盖：

- strategy fit 数据评分必须在 1–5；
- 所有 `evidenceIds` 均存在；
- Fact 类型 evidence 必须包含 source 与 as-of；
- 日本 implementation status 不包含私有仓库 URL、实际持仓、策略参数或收益数据；
- Capital Profile 切换规则返回预期推荐；
- 页面渲染基本 smoke test。

测试框架采用 Vitest + React Testing Library。

### 10.2 构建检查

必须通过：

```bash
cd site
npm ci
npm test
npm run build
```

仓库原有 Python 测试也必须保持通过，至少运行：

```bash
python -m pytest
```

提交前额外检查：

```bash
git diff --check
```

### 10.3 内容检查

人工检查：

- 页面没有使用未经支持的收益或 Sharpe 数字；
- 越南状态没有夸大为已验证 alpha；
- 日本内容没有泄露私有仓库策略细节；
- 外部事实均有来源和日期；
- 页面在桌面和移动宽度均可读。

## 11. 安全与数据边界

- `site/` 不包含 API key、token、Cloudflare secret；
- GitHub/Cloudflare 凭证仅通过平台 secret 管理；
- 不提交 market raw data、Parquet、CSV 或私有策略产物；
- 不从 `guan-japanese-nira` 复制私有源文件到公开仓库；
- 展示站只包含静态、经审阅的研究摘要。

## 12. PR 范围

实现 PR 预计包含：

1. `site/` 完整前端；
2. 日本 vs 越南策略适配静态数据；
3. 公开证据与来源；
4. GitHub Pages workflow；
5. Cloudflare Workers Static Assets 配置；
6. 前端单元测试；
7. README 增加展示站入口；
8. 需要时补充展示方法论文档。

PR 不合并日本私有策略代码，也不建立 submodule。

## 13. 后续演进

满足以下条件之一时考虑从方案 A 迁移到独立 `quant-market-showcase`：

- 页面开始覆盖第三个市场；
- 展示站有独立品牌/域名；
- 客户展示的更新频率与越南研究发布节奏明显不同；
- 需要权限控制、客户专属内容或后端；
- 日本与越南两个研究仓库都开始输出标准化公开 snapshot。

届时建议接口变为：

```text
research repos
    → sanitized public snapshot
    → quant-market-showcase
```

而不是通过 submodule 直接读取研究仓库内部结构。

## 14. 验收标准

本期完成定义：

- 访问一个静态 URL 可完整理解日本与越南量化策略适配差异；
- 核心 10 项策略表已可视化并支持解释展开；
- 有市场结构 radar、alpha-to-PnL、策略架构、资金规模和项目成熟度视图；
- 每个事实型结论可以追溯到来源；
- 主观评分明确标记为 research judgment；
- 页面不依赖私有日本仓库即可构建；
- `npm test`、`npm run build` 和仓库相关质量检查通过；
- GitHub Pages 配置可发布 `site/dist`；
- Cloudflare Workers Static Assets 配置可复用同一构建产物；
- README 能引导客户先看展示页，再按需深入研究文档和代码。
