# 数据质量、回测与授权风险

> 更新时间：2026-08-27  
> 目标：把数据源差异转化为可检查的建库和回测规则。

## 为什么越南市场需要单独做数据治理

越南市场至少同时涉及 HOSE、HNX、UPCoM 和衍生品；证券可能停牌、转板、注销或退市，外资 room 也会变化。单纯保存：

```text
date, ticker, open, high, low, close, volume
```

很容易在未来产生 survivorship bias、错误复权、未来信息泄漏或不可交易的回测结果。研究库必须保留“当时市场是什么状态”和“这个字段什么时候可以被看到”。

## 1. 证券主数据和股票池风险

### 需要处理的情况

- ticker、证券名称或 ISIN 发生变化；
- 同一发行人有股票、ETF、权证、债券或衍生品等不同证券；
- 股票在 HOSE、HNX、UPCoM 之间转板；
- 新上市、暂停交易、恢复交易、注销或退市；
- 今日股票池与历史股票池不同；
- 指数成分股的公告日、生效日和移除日不同。

### 建议规则

`instrument_master` 至少包含：

```text
instrument_id
ticker
isin
issuer_name
market
security_type
valid_from
valid_to
listing_date
delisting_date
status
source
retrieved_at
```

回测股票池必须按目标日期过滤 `valid_from`、`valid_to` 和 `status`，不能拿当前证券列表回填全部历史。转板也不能简单删除旧市场记录，应作为带有效日期的事件保存。

VSDC 的证券统计、证券代码和转板/注销信息可作为事件来源之一；SSI 的证券列表和交易所披露可做交叉核验。参考：[VSDC 统计入口](https://vsd.vn/en/tra-cuu-thong-ke/TK_MACK_BAOLUU?tab=2)、[SSI FastConnect API Specs](https://guide.ssi.com.vn/ssi-products/fastconnect-data/api-specs)。

## 2. 价格、成交量和复权风险

### 原始价格和复权价格必须分开

至少分成：

```text
raw_open / raw_high / raw_low / raw_close
adjusted_open / adjusted_high / adjusted_low / adjusted_close
raw_volume
adjustment_factor
```

原始字段永远不覆盖。复权价格必须能追溯到 `corporate_actions` 中的现金分红、拆分、配股、增发和除权事件。

### 常见错误

- 把供应商已经复权的 close 当作 raw close；
- 对成交量使用与价格相同的复权因子，或完全不调整成交量；
- 将公告日、登记日、除权日混成同一个日期；
- 把停牌日填成零成交，导致收益和流动性被扭曲；
- 忽略涨停/跌停和无法成交的价格；
- 不同来源对价格单位、成交额单位、批量单位和小数位口径不同；
- 把成交价、参考价、收盘价和平均价混成一个字段。

### 建议的最小验证

抽取现金分红、拆分、配股和大比例跳变日期，逐项核对：

1. 事件是否有公告或官方来源；
2. 除权前后价格跳变是否与事件比例一致；
3. raw 数据是否保持不变；
4. adjusted 数据是否只在预期日期开始变化；
5. 回测使用的价格是否符合交易时点和成本假设。

## 3. Point-in-time 基本面风险

财报所属期不是投资者可以使用信息的时间。一个“2025 年年度利润”字段至少要区分：

```text
period_end       = 财报所属期末
announcement_at  = 公司发布/披露时间
available_at     = 数据库可以获取的时间
statement_type   = 年报、季报、审计或单体/合并
revision         = 是否为修订版本
source           = 来源
```

回测在 `available_at` 之后才能使用这条记录。若供应商只提供当前修订后的历史财务字段，却没有公告时间和修订版本，就不能直接把它当成 point-in-time 数据。

FiinPro-X 适合用来减少标准化工作，但仍需询问历史修订、公告时间、导出和 point-in-time 口径；商业平台“有历史数据”不自动等于“历史回测无未来信息”。参考：[FiinPro-X 产品页](https://fiingroup.vn/en/fiinpro-x.html)。

## 4. 外资 room 和资金流风险

外资数据与价格行情不是同一类数据：

- `foreign_ownership_limit` 可能因为法规、公司章程或证券状态改变；
- `foreign_room_remaining` 是某个观察时间点的剩余额度，不应当被静态回填；
- 外资买卖量和金额的字段名、是否含大宗/协议交易、是否为成交口径，需要逐源确认；
- 公告发布时间可能晚于交易日，回测需要使用信息真正可用的时间；
- 外资“净买入”不等于可复制的策略成交信号。

VSDC 公开页面持续发布外资持股比例和剩余可买数量，可以作为 room 的重要来源；SSI 的 `DailyStockPrice` 等接口包含外资相关字段，可用作另一来源或抽样校验。参考：[VSDC 外资持股信息](https://web.vsd.vn/vi/alc/82)、[SSI DailyStockPrice API Specs](https://guide.ssi.com.vn/ssi-products/fastconnect-data/api-specs)。

## 5. 时间、交易日和交易阶段风险

统一保存三种时间：

```text
event_time_local  = 供应商/交易所原始本地时间
event_time_utc    = 统一后的 UTC 时间
trading_date      = 按越南市场时区归属的交易日
```

建议时区为 `Asia/Ho_Chi_Minh`，但不能只转换时区而丢掉原始时间。还要明确：

- 上午、午间休市和下午交易段；
- ATO、连续竞价、ATC；
- 盘前/盘后消息与下一交易日的关系；
- 交易日历、节假日和临时休市；
- API 返回时间与实际成交时间是否相同；
- 盘后修订数据是否覆盖原始记录。

SSI Developer Portal 当前文档列出了 HOSE/HNX 的 ATO、连续交易、午间休市和 ATC 时间，并说明 API/ WebSocket 可以全天访问，但非交易时段不会产生新的价格数据。参考：[SSI 使用条件与数据限制](https://developers.ssi.com.vn/docs/getting-started/terms-and-environments)。

## 6. 盘口、Tick 和成交明细风险

若未来研究分钟、Tick 或 Level 2，不能只看“有无字段”，还要确认：

- 是逐笔成交、聚合 K 线，还是盘口快照；
- 时间戳精度、时区和排序是否稳定；
- 是否有序列号、撤单/改价信息和断线重连机制；
- Top 3/Top 10 是价位深度还是逐笔订单；
- 是否包含大宗/协议交易、零股和异常交易；
- 历史文件是否存在缺口、重复、乱序或修订；
- 数据 Feed 是否允许内部研究、模拟执行和再分发。

HOSE/HNX 官方服务、ICE 等供应商的 Level 1/Level 2 产品不能简单用日线 API 替代。先用小样本检查盘口字段和交易状态，再决定是否承担 Feed 成本。参考：[HNX 2026 数据服务文件](https://owa.hnx.vn/ftp/PORTALNEW/FileContent/HNX_Danh%20muc%20goi%20tin%20va%20bang%20gia%20dich%20vu%20CCTT%2820260105_145538_848%29.pdf)、[ICE HOSE 数据产品](https://developer.ice.com/fixed-income-data-services/catalog/ho-chi-minh-stock-exchange-hose)。

## 7. 来源和工程运维风险

### 聚合工具风险

vnstock 能显著降低研究门槛，但其底层来源、接口字段和页面结构可能变化。生产采集不应只保存最终 DataFrame，应保留请求参数、状态码、原始响应摘要、来源和解析版本。

### API 和网页风险

- rate limit 导致部分股票静默缺失；
- 429、超时、分页边界和临时 5xx；
- 访问 token 过期或权限变化；
- 网页 HTML、下载链接和文件名变化；
- 供应商回补或修订历史数据；
- 多来源字段含义相同但单位不同。

最低的 `source_observations` 记录建议是：

```text
source
source_url_or_endpoint
request_parameters
retrieved_at_utc
response_status
raw_payload_hash
row_count
parser_version
schema_version
quality_status
error_message
```

## 8. 授权和公开仓库风险

免费访问、个人研究、内部研究、商业展示、API 自动化和再分发是不同权限。即使网页公开，也需要确认：

- 是否允许批量下载和长期存档；
- 是否允许 API 自动化和服务器部署；
- 是否允许团队共享或多个账号使用；
- 是否允许将数据用于回测报告、产品页面或客户服务；
- 是否允许再分发原始数据、派生数据或指数成分；
- 交易所 Feed、终端、API、历史文件和指数许可是否分别计费。

公开 GitHub 仓库只提交文档、代码和不受限的小样本元数据，不提交：

- API key、secret、token、账号或客户信息；
- FiinPro、ICE、Bloomberg、LSEG、交易所 Feed 下载的原始文件；
- 未确认许可证的全量 CSV、Parquet、JSON 或截图；
- 供应商明确限制复制或再分发的字段快照。

## 后续采集代码的验收清单

- [ ] 证券状态和有效日期已经记录；
- [ ] HOSE/HNX/UPCoM/衍生品市场字段已经区分；
- [ ] 日线主来源与第二来源完成抽样比对；
- [ ] 交易日、时区和交易阶段已统一并保留原始时间；
- [ ] raw price 与 adjusted price 分开保存；
- [ ] 分红、拆分、配股和除权事件有来源；
- [ ] 财报和外资数据带公告/可用时间；
- [ ] 回测股票池按历史有效状态生成；
- [ ] 停牌、涨跌停、零成交和缺失没有被不加区分地填充；
- [ ] API 限流、失败、重试和分页已记录；
- [ ] 每条标准化数据可以追溯到 source observation；
- [ ] API credentials 不出现在仓库、日志或异常信息中；
- [ ] 数据授权和再分发边界已经书面确认；
- [ ] 回测没有使用未来可得信息。

