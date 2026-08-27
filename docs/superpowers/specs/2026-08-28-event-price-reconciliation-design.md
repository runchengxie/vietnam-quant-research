# 公司行动—价格核对层设计

## 目标

在现有 `CorporateActionEvent`、`PriceDailyRecord` 和 VCI/KBS
reconciliation 输出之上，增加一个只读、可审计的“事件—价格核对”证据层。
它回答的是：某个已知公司行动日期附近，两家供应商分别提供了什么价格、成交量和
质量状态；它不回答该事件是否造成了价格变化，也不自动构造复权因子。

## 非目标

- 不修改或覆盖 `raw`、`bronze/price_daily.jsonl` 或现有研究价格记录；
- 不把 VCI、KBS 或 HNX 页面单独标记为 raw/adjusted 的权威口径；
- 不从价格跳点反推缺失的公司行动、除权日或调整比例；
- 不在本任务中生成 adjusted OHLC 或运行因子基线；
- 不新增网络抓取。事件来源仍由外部 evidence root 或离线 fixture 提供。

## 关键发现

现有事件 parser 和数据契约已存在，但目前事件只作为独立 metadata 保存，没有和
pilot-v6 的价格异常、跨源差异建立可复核关联。已发现的 A32 2020 事件 fixture
把支付日误填成了除权日；报告必须保留事件日期类型，不能只保存一个无语义的日期。

## 设计

### 事件日期语义

每条事件继续保留 `announcement_date`、`ex_date`、`record_date`、
`payment_date`、`listing_date`。报告只按显式字段选择价格参考日，并同时输出
`reference_date_kind`：

1. 有 `ex_date` 时使用 `ex_date`，因为现金分红/配股的价格断点应围绕除权日核对；
2. 没有 `ex_date` 且事件类型是上市/新增股份时使用 `listing_date`；
3. 其他情况下使用 `announcement_date` 作为“来源时间锚”，但标记为
   `reference_only`，不把它当成除权日；
4. 如果没有上述日期，报告状态为 `no_evidence`，不得从价格序列补日期。

`record_date` 和 `payment_date` 只作为事件上下文输出，永远不会被静默当成
`ex_date`。事件的 `source_url`、`source_kind`、`confidence` 和 `notes` 原样
进入报告，便于逐事件回到来源核对。

### 核对窗口与输出

默认取参考日前后各 5 个可用交易日；窗口按每个 source 自己的日期序列确定，不
用日历日硬填缺失交易日。每个事件输出一条稳定记录，包含：

- 事件身份：`event_id`、`symbol`、`event_type`、全部事件日期和 provenance；
- 参考信息：`reference_date`、`reference_date_kind`、窗口大小；
- 每个 source 的窗口 bars：交易日、raw/normalized close、volume、quality flags、
  `source_observation_id`；
- 每个 source 的摘要：参考日前最后一个可用 close、参考日/参考日后第一个可用
  close、窗口收益率、零成交数、invalid OHLC 数、可用 bar 数；
- 跨源摘要：共同窗口日期、close 差异数、相对差异的 median/max，以及是否存在
  一边缺失或一边无效的日期；
- `assessment`：`matched`、`nearby`、`no_evidence` 或 `unresolved`；
- `notes`：只记录证据和限制，不写入“已确认复权因子”。

状态定义：

- `matched`：参考日是至少一个 source 的交易日，且事件前后都有可用价格上下文；
- `nearby`：参考日不是交易日，但窗口内存在可用的前后价格上下文；
- `no_evidence`：没有任何 source 在参考日前后提供可用价格上下文；
- `unresolved`：存在上下文，但源之间覆盖、质量或价格差异不足以支持稳定判断。

这些状态只描述“事件日期与价格证据的对齐程度”，不表示公司行动导致了价格变化。

### 数据流与持久化

```text
metadata/corporate_action_events.jsonl
        + bronze/price_daily.jsonl
        -> event-price reconciliation
        -> metadata/corporate_action_price_reconciliation.jsonl
        -> metadata/corporate_action_price_reconciliation.json
```

输入和输出都位于外部 data root。写入使用现有 `ExternalDataStore` 的幂等能力，
稳定键为 `event_id`；重复运行不会追加重复事件。原始 price bars 只读，不在该
层做排序、填充、单位转换或异常修复。

### A32/APG 最小证据修正

离线 APG/A32 fixture 只修正已被来源明确支持的日期：A32 2019 事件补充登记日
和支付日；A32 2020 事件使用来源明确的除权日 2020-06-01、登记日 2020-06-02
和支付日 2020-06-16。事件金额、来源 URL、source kind 和 confidence 保留。
APG 现有官方 listing/新增股份事件不推断缺失比例。

### 质量边界

报告必须保留 source-level `invalid_ohlc`、`zero_volume`、
`reordered_source_rows` 和 `source_disagreement`。即使事件附近存在明显价格
变化，也只能输出证据窗口和 `unresolved`，不能把差异变成 adjustment factor，
也不能将 `price_semantics` 从 `unresolved` 改为 `confirmed`。

## 测试策略

先写失败测试，再实现最小代码：

- A32 2020 fixture 的 `ex_date`、`record_date`、`payment_date` 语义正确；
- 事件窗口优先使用 `ex_date`，不会误用 `payment_date`；
- 只有 announcement date 的事件被标记为 `reference_only`；
- 参考日非交易日时输出 `nearby`，不伪造一根价格 bar；
- invalid OHLC/zero volume/source disagreement 在事件报告中保留；
- 两源缺失或质量冲突时输出 `no_evidence`/`unresolved`，不推断日期或比例；
- 重复写入同一 `event_id` 保持幂等；
- 报告生成不改变输入 bronze 行数，也不产生 adjusted close。

完成后运行离线全量测试、compileall、`git diff --check`，再对仓库外的
`pilot-v6` 执行一次只读报告生成。该报告用于定位下一轮人工/官方来源核对，不
作为因子回测输入，也不改变 `factor_ready=false` 的门槛。
