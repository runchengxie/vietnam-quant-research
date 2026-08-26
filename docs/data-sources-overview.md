# 越南市场数据源与接口能力

> 更新时间：2026-08-27  
> 用途：量化研究和数据工程选型，不构成投资或数据许可意见。

## 先看结论

越南市场不适合只找一个“万能 API”。实际建库通常要把行情、证券主数据、外资限制、公司行动和财报拆开，再用两个来源做交叉核验。

至少要分别考虑：

- **HOSE**（胡志明交易所）；
- **HNX**（河内交易所）；
- **UPCoM**（未上市公众公司交易市场）；
- **衍生品**；
- 以及不同来源对 OTC、债券和指数的额外覆盖。

网页上能看到一个价格，不代表可以批量抓取、长期保存、自动化使用或再分发。每个渠道都要单独确认数据历史、频率、字段、限流、账户条件和许可证。

## 能力矩阵

| 渠道 | 主要数据 | 覆盖/适用市场 | 访问方式 | 适合场景 | 主要限制 |
|---|---|---|---|---|---|
| [vnstock Community](https://vnstocks.com/docs/vnstock/du-lieu-thi-truong-hang-hoa-retail) | 日线 OHLCV、基础财务、公司信息、部分实时查询 | 越南股票研究原型 | Python 开源库/API key | 免费日频、因子原型、快速验证 | 依赖底层来源；有访问限额和历史范围；不等于原始数据授权 |
| [vnstock_data Sponsor](https://vnstocks.com/docs/vnstock-data/gioi-thieu-vnstock-data) | 更高限额、完整历史、实时/流式、扩展财务和宏观 | 越南市场 | 赞助包专用库 | 较低成本的批量研究和实时试验 | 商业/赞助条款、价格和再利用边界需复核 |
| [SSI FastConnect Data](https://guide.ssi.com.vn/ssi-products/fastconnect-data) | 证券列表、指数、日线/盘中 OHLCV、实时数据、WebSocket | API 文档覆盖 HOSE、HNX、UPCoM、DER 等市场参数 | REST、WebSocket；需 API key | 日频/盘中研究、实时行情、券商集成 | 需要 SSI 交易账户、申请批准和条款确认；盘中历史约 1 年；有 rate limit |
| [VSDC 公开数据](https://web.vsd.vn/vi/alc/82) | 外资持股上限、foreign room、证券登记/状态和部分事件 | 上市、登记和交易证券相关 | 官方公开页面 | 外资约束、security master、转板/注销线索 | 页面自动化、存档和再利用规则需单独确认 |
| [HOSE 官方服务](https://www.hsx.vn/) | EOD、实时/延迟、指数、市场数据 Feed、统计和披露 | HOSE 及其产品 | 官方页面、Webservice、Feed | 官方校验、正式实时数据、机构接入 | 连接、数据包、终端/用户和再分发授权可能分别计费 |
| [HNX 官方服务](https://www.hnx.vn/) | EOD、实时/延迟、Top 3/Top 10 深度、指数、外资、衍生品和披露 | HNX、UPCoM 及衍生品相关 | 官方页面、消息/XML、Feed | HNX/UPCoM 校验、深度行情和机构接入 | 产品按数据包和服务询价，授权边界需确认 |
| [FiinPro-X](https://fiingroup.vn/en/fiinpro-x.html) | 实时/历史行情、财报、估值、所有权、公司行动、宏观和研究工具 | 供应商页面列出 HOSE、HNX、UPCOM、OTC 等覆盖 | 商业平台、试用、合同 | 标准化基本面、公司行动、筛选和历史研究 | 订阅成本高；point-in-time、导出和再分发许可需确认 |
| [ICE HOSE 数据](https://developer.ice.com/fixed-income-data-services/catalog/ho-chi-minh-stock-exchange-hose) | 实时、延迟、EOD、历史、Level 1/Level 2、Tick/深度数据 | HOSE 及跨市场机构数据 | ICE Connect、Feed、API、文件 | 高频、执行、微观结构和跨市场系统 | 通常询价；需确认具体字段、历史档案和许可范围 |
| Bloomberg / LSEG | 全球终端、历史、实时、指数和企业数据 | 跨市场/机构场景 | 终端、数据 API、授权 Feed | 跨市场研究、正式数据服务和分发 | 通常询价，终端、API、指数和再分发权限分开 |

## 分渠道说明

### 1. vnstock：低成本研究入口

vnstock 的价值在于提供较一致的 Python 调用方式，把多个越南数据来源包装成适合研究的接口。官方文档区分了免费 `vnstock` 和赞助包专用 `vnstock_data`：

- Community 版本适合学习、快速查询和小规模研究；官方文档给出的限制包括最多约 60 requests/min、日线最多约 8 年、分钟线最多约 1 年（具体还取决于 API key 和底层来源）；
- Sponsor 版本提供更高访问限额、从上市日起的完整历史能力，以及更强的实时/流式和财务数据能力；
- `vnstock_data` 是独立分发的赞助包，不应把它当成完全等同于开源库的免费升级；
- 聚合工具底层来源和网页结构可能变化，因此应保存原始响应、抓取时间和来源，不要只保存最终 DataFrame。

参考：[Community 与 Sponsor 对比](https://vnstocks.com/docs/vnstock-data/gioi-thieu-vnstock-data)、[赞助计划](https://vnstocks.com/insiders-program)、[商店入口](https://vnstocks.com/store)。价格另见[价格与人民币成本](pricing-and-costs.md)。

### 2. SSI FastConnect：优先申请测试的券商 API

SSI 官方文档说明 FastConnect Data 提供 EOD 和 realtime market data。可见 API 包括：

- `Securities`、`SecuritiesDetails`；
- `IndexComponents`、`IndexList`；
- `DailyOhlc`、`IntradayOhlc`；
- `DailyIndex`、`DailyStockPrice`；
- WebSocket streaming。

官方 Developer Portal 的当前条件包括：需要 SSI 交易账户、通过 Developer Portal 申请并获批、同意使用条款。该页面还写明 daily OHLCV 可从证券开始交易起查询，盘中 OHLCV（1m、5m、15m、30m、1h）覆盖最近一年。API key、secret 和 token 不得提交到公开仓库。

参考：[FastConnect 使用条件与数据限制](https://developers.ssi.com.vn/docs/getting-started/terms-and-environments)、[API Specs](https://guide.ssi.com.vn/ssi-products/fastconnect-data/api-specs)、[系统概览](https://developers.ssi.com.vn/docs/getting-started/overview)。

### 3. VSDC：补齐外资约束和证券状态

VSDC（Vietnam Securities Depository and Clearing Corporation）公开发布外资持股比例、外资剩余可买数量等信息。它特别适合补充以下字段：

```text
foreign_ownership_limit
foreign_room_remaining
security_code / ISIN
listing_or_registration_status
transfer_or_cancellation_event
effective_date
```

公开页面按交易日或工作日持续发布外资持股公告。VSDC 也有证券代码分配、注销、转板等统计入口，可作为 `instrument_master` 的事件来源之一。公开可访问不等于允许无限制自动化或再分发，落地前应查看页面/数据使用规则。

参考：[VSDC 外资持股公开信息](https://web.vsd.vn/vi/alc/82)、[证券登记/统计入口](https://vsd.vn/en/tra-cuu-thong-ke/TK_MACK_BAOLUU?tab=2)。

### 4. HOSE/HNX：官方校验和机构级 Feed

交易所官方源的主要优势不是“字段最多”，而是源头、时间戳和许可关系更清楚。HNX 的数据服务目录包含实时或延迟行情、Top 3/Top 10 深度、外资交易、指数、衍生品和统计类产品。HOSE 的官方价格文件区分 Standard Feed、Webservice 和指数实时产品。

研究阶段可以把交易所公开页面作为样本校验源；如果需要稳定的实时、Level 2、消息流或再分发，应该直接询问交易所数据服务，而不是依赖网页抓取。

参考：[HOSE 官方网站](https://www.hsx.vn/)、[HOSE 数据服务价格文件](https://staticfile.hsx.vn/Uploads/UploadDocuments/2406142/Bieu%20gia%20dich%20vu%20cung%20cap%20tin.pdf)、[HNX 官方网站](https://www.hnx.vn/)、[HNX 2026 数据服务目录与价格文件](https://owa.hnx.vn/ftp/PORTALNEW/FileContent/HNX_Danh%20muc%20goi%20tin%20va%20bang%20gia%20dich%20vu%20CCTT%2820260105_145538_848%29.pdf)。

### 5. FiinPro-X：基本面和标准化数据

FiinPro-X 更像一个完整研究平台，而不只是行情 API。供应商页面列出的能力包括实时和历史市场数据、越南宏观数据、新闻、财报、公司信息、筛选和分析工具；官方英文页还列出 3,500+ 家上市公司及其他企业覆盖。

它适合在以下情况下评估：

- 需要统一口径的财报、估值指标和行业分类；
- 需要历史公司行动、所有权、股东或交易主体信息；
- 自己解析越南语/英语财报 PDF 的维护成本已经高于订阅成本；
- 需要 Excel 或研究平台直接使用，而不是从零构建数据治理。

重点是确认财报和事件是否 point-in-time、历史修订如何处理、下载/导出能否用于自动化研究，以及个人订阅是否允许团队或商业使用。

参考：[FiinPro-X 产品页](https://fiingroup.vn/en/fiinpro-x.html)、[FiinPro 定价页](https://fiinpro.com.vn/pricing)。

### 6. ICE、Bloomberg、LSEG：只有需求明确时再升级

ICE 的 HOSE 页面明确列出 realtime、delayed、EOD、historical 和 Level 1/Level 2 能力，并提供 ICE Connect、Consolidated Feed、Data API、文件和历史产品。Bloomberg/LSEG 则更适合已经有跨市场数据管理、终端或机构授权需求的场景。

此类供应商的核心成本通常不只是“每月订阅”：可能还包括终端、API、历史数据、指数许可、网络接入、用户数量和再分发。除非研究已进入执行、微观结构或产品化阶段，否则不建议作为第一批数据源。

## 按研究问题选择

| 研究问题 | 首选组合 | 为什么 |
|---|---|---|
| 先判断越南市场是否值得研究 | vnstock Community + VSDC | 成本低，能覆盖日频原型、证券状态和外资约束线索 |
| 构建全市场日频因子 | vnstock + SSI FastConnect 申请测试 | 用聚合工具拉取，用券商 API 或交易所样本校验 |
| 研究外资 room / foreign flow | VSDC + SSI/交易所数据 + FiinPro（如需要） | room、成交数据和标准化股东/资金字段需要分开处理 |
| 研究财报、估值和公司行动 | FiinPro-X + 交易所/VSDC 披露 | 商业标准化数据节省大量 PDF 解析和对齐工作 |
| 研究分钟、Tick、Level 2 和执行 | SSI 盘中能力 → HOSE/HNX/ICE 询价 | 先验证需求，再承担正式 Feed 和许可成本 |

## 最小可行起点

建议按以下顺序验证：

1. 用 vnstock 建立一个可重复拉取的日线样本；
2. 用 VSDC 补外资 room、证券状态和事件样本；
3. 申请 SSI FastConnect，核对符号、价格单位、交易日和历史边界；
4. 抽取一小组股票，比较两个来源的缺失、极值、停牌和复权差异；
5. 只有基本面问题成为瓶颈时，再试用 FiinPro-X；
6. 只有策略明确依赖盘口或执行质量时，再询价 HOSE/HNX/ICE。

