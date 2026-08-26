# 越南市场量化研究文档 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建一个公开的越南股票市场量化研究资料库首版，系统整理数据渠道、人民币成本、推荐组合和数据质量风险。

**Architecture:** 采用 docs-first 的静态 Markdown 仓库。文档按“数据源是什么 → 花多少钱 → 如何组合 → 哪些风险”分层，所有动态信息保留核验日期、原币种和来源链接；首版不实现采集代码或数据库。

**Tech Stack:** Markdown、Git、GitHub CLI；来源链接指向交易所、VSDC、券商、供应商和汇率页面。

**Spec:** `docs/superpowers/specs/2026-08-27-vietnam-data-research-design.md`

## Global Constraints

- 仓库公开，但不得提交 API key、secret、token、账号信息或商业数据文件。
- 价格必须同时保留 VND 原价和人民币估算，并标注汇率日期、VAT、连接费和授权费等未含项。
- 必须区分公开标价、历史观察价、免费公开数据、账户/审批条件和询价项目。
- 首版仅创建 README、四篇研究文档和安全相关的 `.gitignore`，不加入爬虫、API client、数据库或交易策略。
- 文档中的数据源结论必须附可点击来源链接；无法确认的内容写成待核实事项。

---

### Task 1: 建立公开仓库入口和安全边界

**Files:**
- Create: `README.md`
- Create: `.gitignore`

**Interfaces:**
- Produces: 文档入口、项目范围、更新规则和不提交凭证/商业数据的安全边界；后续四篇文档由 README 链接。

- [ ] **Step 1: Write the repository README**

  `README.md` 必须包含以下内容：

  - 项目标题“越南市场量化研究”；
  - 一句话说明：这是一个公开的、中文为主的越南股票市场数据获取与量化研究资料库；
  - “当前状态”段落：首版只整理数据源、价格和风险，不提供投资建议；
  - 文档入口链接：
    - `docs/data-sources-overview.md`
    - `docs/pricing-and-costs.md`
    - `docs/recommended-data-stack.md`
    - `docs/data-quality-and-risks.md`
  - 明确覆盖 HOSE、HNX、UPCoM、衍生品，并说明不同渠道覆盖范围不同；
  - 安全说明：不得提交凭证、原始商业数据或受许可证限制的数据；
  - 信息更新时间：`2026-08-27`，动态价格和条款需要复核；
  - 免责声明：资料用于研究和工程规划，不构成投资、法律或数据许可意见。

- [ ] **Step 2: Add repository safety patterns**

  `.gitignore` 至少包含以下模式，并保留注释说明用途：

  ```gitignore
  # Credentials and local secrets
  .env
  .env.*
  *.pem
  *.key
  secrets/

  # Local data and runtime outputs
  data/
  raw_data/
  outputs/
  *.parquet
  *.csv
  *.jsonl

  # Python and editor artifacts for future work
  __pycache__/
  .venv/
  .idea/
  .vscode/
  ```

- [ ] **Step 3: Validate the entry point**

  Run:

  ```text
  git diff --check
  ```

  Expected: no whitespace errors. Manually verify README 中的四个文档链接路径存在或将在后续任务创建。

- [ ] **Step 4: Commit the repository entry point**

  ```text
  git add README.md .gitignore
  git commit -m docs-add-repository-entrypoint
  ```

### Task 2: 整理数据源与可用字段

**Files:**
- Create: `docs/data-sources-overview.md`

**Interfaces:**
- Consumes: 已确认的设计说明和官方来源链接。
- Produces: 供价格文档和推荐架构文档引用的数据源能力矩阵。

- [ ] **Step 1: Write the source taxonomy**

  文档开头说明越南市场的基本边界：HOSE、HNX、UPCoM 和衍生品需要分别确认；“能看到行情”不等于拥有历史数据、自动化访问或再分发权。

- [ ] **Step 2: Add the source comparison table**

  表格至少包含以下行和列：

  | 渠道 | 主要数据 | 覆盖/适用市场 | 访问方式 | 适合场景 | 主要限制 |
  |---|---|---|---|---|---|
  | vnstock Community | 日线 OHLCV、基础财务、公司信息、部分实时查询 | 越南股票研究原型 | Python 开源库/API key | 免费日频和快速验证 | 依赖底层来源；限流和历史范围；不等于原始数据授权 |
  | vnstock_data Sponsor | 更高限额、完整历史、实时/流式、扩展财务 | 越南市场 | 赞助包专用库 | 较低成本的批量研究 | 商业条款和当前价格需复核 |
  | SSI FastConnect Data | 证券列表、指数、日线/盘中 OHLCV、实时与 WebSocket | HOSE、HNX、UPCoM、衍生品等 API 支持范围 | REST、WebSocket；需 API key | 研究、实时行情、券商集成 | 需要 SSI 账户和审批；盘中历史约 1 年；授权/限流 |
  | VSDC | 外资持股上限、foreign room、证券状态、部分证券主数据与事件 | 上市/登记证券相关 | 官方公开页面 | 外资约束、security master、状态变化 | 页面自动化和再利用规则需单独确认 |
  | HOSE/HNX 官方 | EOD、实时/延迟、指数、交易所消息、深度行情、统计和披露 | 对应交易所及产品 | 官方页面、Feed、XML/消息服务 | 校验、机构级行情和正式授权 | 接入、数据包、终端和再分发费用 |
  | FiinPro-X | 实时/历史、财报、估值、所有权、公司行动、宏观和研究工具 | HOSE、HNX、UPCoM、OTC 等供应商覆盖 | 商业平台/试用/合同 | 标准化基本面和历史研究 | 订阅成本高；point-in-time 和导出许可需确认 |
  | ICE/Bloomberg/LSEG | 多市场历史、实时、Tick/Level 1/Level 2 等 | 跨市场/机构场景 | 商业终端、API、Feed | 高频、跨市场和正式许可 | 通常询价，授权复杂 |

- [ ] **Step 3: Document evidence for key providers**

  在对应小节加入来源链接和可核实事实：

  - SSI 官方条款页：需要 SSI 交易账户并通过 FastConnect 申请；daily OHLCV 从证券开始交易，盘中 OHLCV 覆盖最近一年；
  - SSI API specs：列出 `Securities`、`IndexList`、`DailyOhlc`、`IntradayOhlc`、`DailyIndex`、`DailyStockPrice`；
  - VSDC foreign ownership 页面：持续发布外资持股比例和剩余可买数量；
  - FiinPro 官方英文页和 pricing 页：说明实时/历史市场数据、财务数据与不同页面存在报价差异；
  - HOSE 官方数据服务价格 PDF 与 HNX 2026 数据服务价格/产品 PDF：说明官方 Feed 的产品和授权属性；
  - vnstock 官方文档：Community 与 Sponsor 的历史范围、限流和实时能力差异。

- [ ] **Step 4: Add an acquisition decision guide**

  明确给出：

  - 只做日频价格/流动性：先用 vnstock + SSI/交易所交叉核验；
  - 需要外资限制和证券状态：补 VSDC；
  - 需要标准化财务与公司行动：评估 FiinPro-X；
  - 需要 Tick、Level 2、执行研究：进入交易所 Feed 或机构供应商询价。

- [ ] **Step 5: Validate and commit the source document**

  Run:

  ```text
  git diff --check
  findstr /s /i /n "api key secret token" README.md docs\data-sources-overview.md
  ```

  Expected: only security guidance is present; no credential-like value appears. Commit with:

  ```text
  git add docs/data-sources-overview.md
  git commit -m docs-map-vietnam-data-sources
  ```

### Task 3: 建立 VND 到人民币的价格表

**Files:**
- Create: `docs/pricing-and-costs.md`

**Interfaces:**
- Consumes: Task 2 的数据源分类和官方来源。
- Produces: 可供预算决策直接使用的价格快照，保留原币种、人民币估算、报价状态和待核实项。

- [ ] **Step 1: Define the conversion rule**

  记录本次预算换算基准：以 2026-08-25 Wise 页面显示的中间价 `1 VND = 0.0002574 CNY` 为估算基准，公式为：

  ```text
  CNY estimate = VND price × 0.0002574
  ```

  说明银行卡汇率、VAT、付款手续费和供应商合同折扣可能导致实际结算不同。

- [ ] **Step 2: Add the price snapshot table**

  首版表格至少记录以下数值，并将人民币结果四舍五入到元：

  | 数据源/套餐 | VND 价格 | 约合人民币 | 周期 | 状态 |
  |---|---:|---:|---|---|
  | vnstock Community | 0 | ¥0 | 持续 | 官方文档确认免费 |
  | vnstock Bronze | 180,000 | 约 ¥46 | 单位周期 | 价格页面动态，需复核 |
  | vnstock Silver | 189,000 | 约 ¥49 | 单位周期 | 价格页面动态，需复核 |
  | vnstock Golden | 2,399,000 | 约 ¥618 | 年 | 价格页面动态，需复核 |
  | vnstock Diamond | 5,400,000 | 约 ¥1,390 | 年 | 价格页面动态，需复核 |
  | SSI FastConnect | 未公开单列价格 | — | — | 需要 SSI 账户、审批和条款确认 |
  | VSDC 公开页面 | 0 | ¥0 | — | 页面公开访问；自动化/再利用规则需确认 |
  | FiinPro-X 英文价页 | 10,900,000 | 约 ¥2,806 | ID/月 | 官方英文页标价，VAT/合同需确认 |
  | FiinPro pricing 页 | 9,000,000 + 10% VAT | 约 ¥2,317，含 VAT 约 ¥2,548 | ID/月 | 与英文页存在差异，必须询价确认 |
  | HOSE Webservice realtime | 150,000,000 | 约 ¥38,610 | 年 | 官方价格 PDF；可能另有连接/授权项 |
  | HOSE Index realtime | 160,000,000 | 约 ¥41,184 | 年 | 官方价格 PDF；可能另有连接/授权项 |
  | HOSE Standard realtime | 300,000,000 | 约 ¥77,220 | 年 | 官方价格 PDF；可能另有连接/授权项 |
  | HNX Feed | 未公开统一数字 | — | — | 官方按数据包/服务询价 |
  | ICE/Bloomberg/LSEG | 询价 | — | — | 机构级许可和合同 |

- [ ] **Step 3: Explain price confidence and discrepancies**

  单独写明：

  - vnstock 商店页面是动态页面，Bronze/Silver/Golden/Diamond 的数值是当前研究记录中的价格快照，不应视为永久报价；
  - FiinPro 官方不同语言页面同时出现 `9,000,000 VND + 10% VAT` 和 `10,900,000 VND`，可能是页面版本、含税口径或产品方案不同，购买前必须向 FiinGroup 确认；
  - HOSE 官方 PDF 的连接费和市场数据费要分开，不能只看一个 Feed 价格；
  - HNX、ICE、Bloomberg、LSEG 没有可靠公开统一报价时，保留“询价”而不是估算。

- [ ] **Step 4: Add budget tiers**

  用人民币给出四档预算：

  1. `¥0/年`：vnstock Community + VSDC 公开页面，适合验证可行性；
  2. `约 ¥0–1,500/年`：在确认价格后加入 vnstock Golden 或同级 Sponsor，适合批量日频研究；
  3. `约 ¥2,300–2,800/月起`：FiinPro-X，适合标准化基本面和公司行动研究；
  4. `约 ¥3.9–7.7 万/年起`：HOSE 官方实时服务，仅在需要正式交易所 Feed、低延迟或再分发授权时考虑。

  说明这些预算不包含交易佣金、服务器、存储、汇率损耗、税费、连接线路和法律/再分发许可。

- [ ] **Step 5: Add source links and validate calculations**

  来源至少包括 Wise 汇率页、vnstock sponsor/data 文档与商店页、SSI 条款页、FiinPro 英文/定价页、HOSE 官方价格 PDF 和 HNX 2026 产品/价格 PDF。手算复核：

  ```text
  2,399,000 × 0.0002574 = 617.50 → ¥618
  10,900,000 × 0.0002574 = 2,805.66 → ¥2,806
  300,000,000 × 0.0002574 = 77,220 → ¥77,220
  ```

  Run `git diff --check` and commit:

  ```text
  git add docs/pricing-and-costs.md
  git commit -m docs-record-vietnam-data-costs
  ```

### Task 4: 写出推荐数据栈与落地路线

**Files:**
- Create: `docs/recommended-data-stack.md`

**Interfaces:**
- Consumes: Task 2 的能力矩阵和 Task 3 的预算层级。
- Produces: 分阶段的数据组合、数据流和建议表结构。

- [ ] **Step 1: Define the recommended starting stack**

  明确首选组合为：`vnstock Community/Sponsor + SSI FastConnect（申请测试）+ VSDC 公开数据`。解释各自职责：vnstock 用于快速覆盖和原型，SSI 用于官方券商 API 交叉核验和盘中能力，VSDC 用于外资额度与证券状态。

- [ ] **Step 2: Add phased adoption table**

  | 阶段 | 预算 | 数据 | 目标 | 升级条件 |
  |---|---:|---|---|---|
  | 0 原型 | ¥0 | vnstock Community + VSDC | 全市场日频、证券列表、外资限制初步建库 | API 限流或历史范围影响研究 |
  | 1 研究 | 约 ¥0–1,500/年 | 加 vnstock Sponsor，申请 SSI | 批量拉取、盘中验证、构建基础因子 | 需要 point-in-time 财务/公司行动 |
  | 2 标准化基本面 | 约 ¥2,300–2,800/月起 | FiinPro-X 试用/订阅 | 财报、估值、所有权、公司行动 | 需要 Tick/Level 2/正式许可 |
  | 3 机构行情 | 询价或数万元/年起 | HOSE/HNX/ICE/Bloomberg/LSEG | 执行、微观结构、正式再分发 | 仅在业务和策略价值覆盖成本时 |

- [ ] **Step 3: Add the data-flow diagram and table groups**

  文档要包含以下等价流程：

  ```text
  source adapters → raw snapshots → normalized tables → validation → factors/backtest
  ```

  建议的第一批表：

  - `instrument_master`
  - `price_daily`
  - `price_intraday`
  - `fundamentals`
  - `corporate_actions`
  - `foreign_ownership`
  - `index_membership`
  - `source_observations`

  强调每个原始快照要保留 `source`、`retrieved_at`、原始字段和 parser/version；标准化表再提供统一 ticker、交易日和字段。

- [ ] **Step 4: Add the first research milestones**

  文档应按顺序提出：

  1. 建 security master，合并 HOSE/HNX/UPCoM 和衍生品标识；
  2. 拉取全市场日线并和至少一个第二来源做缺失/极值校验；
  3. 记录停牌、转板、退市、拆分、分红和复权事件；
  4. 计算流动性、动量、反转、波动率、外资流和涨跌停行为；
  5. 只有当日频 alpha 经过成本和样本外验证后，再评估分钟、Tick 或基本面订阅。

- [ ] **Step 5: Validate and commit**

  Run `git diff --check`; verify all four planned table names and all four budget stages appear. Commit:

  ```text
  git add docs/recommended-data-stack.md
  git commit -m docs-propose-vietnam-data-stack
  ```

### Task 5: 记录数据质量、回测和授权风险

**Files:**
- Create: `docs/data-quality-and-risks.md`

**Interfaces:**
- Consumes: Task 2–4 的来源、价格和建库建议。
- Produces: 可作为后续采集代码验收清单的风险与验证规则。

- [ ] **Step 1: Add instrument and universe risks**

  覆盖：ticker 重用、HOSE/HNX/UPCoM 转板、退市、停牌、上市日期、证券类型、存活者偏差和指数成分历史。明确 `instrument_master` 必须有有效期字段和状态字段。

- [ ] **Step 2: Add price and corporate-action risks**

  覆盖：原始价/复权价、现金分红、配股、拆分、除权日与公告日的时间关系、涨跌停、成交量单位、越南盾价格精度和成交额。要求后续数据表同时保留 raw 与 adjusted 字段，不能覆盖原始值。

- [ ] **Step 3: Add point-in-time and timestamp risks**

  覆盖：财报公告时间而非财报所属期、外资 room 日更、交易日/时区 `Asia/Ho_Chi_Minh`、午间休市、AOT/ATC、盘后修订和 API 返回时间。明确回测只能使用当时已经可获得的信息。

- [ ] **Step 4: Add source, licensing and operational risks**

  覆盖：聚合库底层来源变化、限流、网页结构变化、API key 安全、商业数据的个人/商业使用边界、再分发限制、Feed 连接费、供应商 SLA 和价格变动。给出最低操作要求：raw snapshot、抓取日志、schema version、source URL、checksum 和失败重试记录。

- [ ] **Step 5: Add a validation checklist and commit**

  清单至少包含：

  - [ ] 证券状态和有效日期已记录；
  - [ ] 日线主来源与第二来源已抽样比对；
  - [ ] 复权事件有来源且未覆盖 raw price；
  - [ ] 财报/外资数据带可用时间；
  - [ ] API 限流、失败和重试有日志；
  - [ ] 数据授权和再分发边界已记录；
  - [ ] 回测排除了未来信息。

  Run `git diff --check` and commit:

  ```text
  git add docs/data-quality-and-risks.md
  git commit -m docs-document-vietnam-data-risks
  ```

### Task 6: 全量验证、更新文档状态并创建公开 GitHub 仓库

**Files:**
- Modify: `README.md`
- Modify: `docs/pricing-and-costs.md`

**Interfaces:**
- Consumes: Tasks 1–5 的所有文档和 Git 提交。
- Produces: 可公开发布的 `main` 分支和 GitHub 远程仓库。

- [ ] **Step 1: Run repository-wide Markdown and safety checks**

  Run:

  ```text
  git diff --check
  git status --short
  git ls-files
  ```

  Expected: tracked files only include Markdown and `.gitignore`; no `.env`, key, token, parquet, CSV or JSONL file is tracked.

- [ ] **Step 2: Check links and cross-references**

  Manually verify README 的四个相对链接均存在；verify each source section includes a full `https://` link; verify pricing page says “截至 2026-08-27” and calls out the FiinPro discrepancy and dynamic vnstock prices.

- [ ] **Step 3: Add final repository status note**

  In `README.md`, state that the initial repository is docs-only and that next work should be a small source-observation prototype before production ingestion. In `docs/pricing-and-costs.md`, state that all prices require rechecking before payment.

- [ ] **Step 4: Commit the final documentation state**

  ```text
  git add README.md docs/pricing-and-costs.md
  git commit -m docs-finalize-vietnam-research-notes
  ```

- [ ] **Step 5: Verify GitHub CLI authentication and create the public repository**

  Run:

  ```text
  gh auth status
  gh repo create runchengxie/vietnam-quant-research --public --source . --remote origin --push
  ```

  Expected: GitHub reports a public repository, `origin` points to `https://github.com/runchengxie/vietnam-quant-research.git`, and `main` is pushed.

- [ ] **Step 6: Verify the published remote**

  Run:

  ```text
  git status --short --branch
  git remote -v
  gh repo view runchengxie/vietnam-quant-research --json nameWithOwner,isPrivate,defaultBranchRef,url
  ```

  Expected: clean `main` branch, public repository (`isPrivate: false`), and default branch `main`.

