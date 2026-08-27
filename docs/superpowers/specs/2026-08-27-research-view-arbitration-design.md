# 日频研究视图与来源仲裁设计

## 目标

在不改写 `raw` 和 `bronze` 的前提下，增加一个可审计的研究用派生视图，隔离 OHLC 异常、标记停牌/零成交、记录 VCI/KBS 来源仲裁，并输出复权/价格语义尚未确认的诊断。该视图用于下一轮 50 只股票质量门槛和后续因子研究；它不把异常数据静默修正为“干净数据”。

## 非目标

- 不删除、填充或修改任何 raw snapshot 或 `bronze/price_daily.jsonl` 记录。
- 不根据 VCI/KBS 的价格差异自动推断复权因子，也不在本任务中引入公司行动数据。
- 不接入 SSI、FiinPro、Tick 或 Level 2。
- 不在本任务中运行因子回测；只有研究视图和价格语义诊断完成后才允许进入下一阶段。

## 方案

### 数据流

网络采集和现有质量检查保持不变：

```text
raw snapshots
    -> bronze/price_daily.jsonl
        -> per-source validation
            -> source arbitration
                -> derived/research_price_daily.jsonl
                -> metadata/source_arbitration_report.json
                -> metadata/price_semantics_report.json
```

`bronze` 仍是来源事实层；`derived` 是带有研究资格和仲裁理由的派生层。每一条派生记录通过 `source_observation_id`、`source` 和日期追溯到原始来源。

### 研究记录

新增 `ResearchPriceDailyRecord`，复用 `PriceDailyRecord` 的全部 raw、normalized、质量和来源字段，并增加：

- `research_status`: `selected` 或 `quarantined`；
- `arbitration_reason`: `primary_valid`、`secondary_fallback`、`both_invalid_primary_kept`、`primary_only`、`secondary_only`；
- `research_eligible`: 是否可用于价格/收益率计算；
- `tradable`: 是否可作为交易执行日，要求研究记录有效且 `raw_volume > 0`。

派生视图按交易日输出最多一条记录。若主源有效，优先使用主源；主源缺失或含 `missing_required`、`invalid_ohlc`、`duplicate_date` 时，使用有效的次源；两源均无效时保留一条可追溯记录但标记 `quarantined` 和 `research_eligible=false`。零成交不删除，保留为有效价格记录但 `tradable=false`。

### 来源差异

如果两源在同一日期都有可用收盘价且相对差异超过现有 `0.1%` 阈值，派生记录增加 `source_disagreement`，并在仲裁报告中记录日期、两源价格、相对差异和选择结果。该标记不自动替换任何源，也不自动判定哪一方是复权价。

仲裁报告至少包含每个 symbol 的：主/次源行数、选中来源数、fallback 数、quarantine 数、零成交数、来源差异数、研究可用率、可交易率，以及少量可审计样例。

### 价格语义诊断

新增价格语义报告，对每个 symbol 汇总两源共同日期的收盘价比值/相对差异：共同日期数、差异数、median、p90、max 和相对差异的时间分段。报告状态固定为 `unresolved`，除非未来显式提供公司行动或复权口径参考；本任务不能通过统计相似性把 raw/adjusted 语义标成已确认。

### 质量门槛

保留现有 raw `quality_status`：任意来源存在 `invalid_ohlc` 时仍为 `FAIL`，使源数据缺陷可见。新增研究视图门槛：

1. 50 只股票均有主源或次源观察，且来源 HTTP/解析覆盖成功；
2. `research_price_daily` 不含 `research_eligible=true` 且带 `invalid_ohlc` 的记录；
3. 每只股票研究可用率至少为 90%，不足时整体 `research_quality_status=FAIL`；
4. `source_disagreement` 和 `price_semantics_status=unresolved` 不隐藏，且 `factor_ready=false`，直到价格语义被独立来源确认。

因此，研究视图可以在保留少量隔离行的前提下达到“可研究但有警告”，但不允许把它报告成复权口径已经确认。

## 错误处理

- 缺失两源记录：不生成伪造价格，只在仲裁报告计入缺口。
- 单源请求失败：若另一源有有效记录，生成 `secondary_fallback` 或 `primary_only` 记录并保留观察失败信息。
- 两源均有记录但均无效：保留主源记录作为审计锚点并 quarantine，不进入收益率和交易信号。
- 重复日期：不在派生层猜测哪条正确；该日期 quarantine，并在报告中计数。
- 报告和派生 JSONL 使用现有 `ExternalDataStore` 原子写入，运行时文件继续放在仓库外。

## 测试策略

先为以下行为编写失败测试，再实现最小代码：

- 有效主源优先，且记录 `primary_valid`；
- 主源 OHLC 无效时回退到有效次源；
- 两源均无效时记录 quarantine 而非删除或填充；
- 零成交保留但不可交易；
- 超过阈值的跨源收盘差异被记录；
- 研究质量统计正确计算每只股票的可用率和 `factor_ready=false`；
- pipeline 将派生记录和两个语义/仲裁报告写入外部 data root，且不改变 bronze 行数。

完成后运行全量 pytest、compileall、`git diff --check`，再用固定的 50 只股票样本重跑 pilot，分别报告 raw gate、research gate 和 factor readiness。

