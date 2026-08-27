# 越南日频数据闭环 v0 验收报告

**试点日期：** 2026-08-27（Asia/Shanghai）
**最终试点目录：** `D:\data\vietnam-quant-research\pilot-v2`
**状态：** 采集完成，质量门槛未通过，因子基线阻断

## 结论

第一版日频数据闭环已经可以离线测试并显式联网运行，但本轮数据还不适合直接进入正式回测：

- VCI 列表返回 3,586 条证券记录；自动样本选出 50 只 `STOCK\)，覆盖 HOSE 30、HNX 10、UPCoM 10。
- 101 个来源 observations 已记录：列表 1 条，VCI 日线 50 条，KBS 日线 50 条。
- bronze `price_daily.jsonl` 有 171,447 条来源日线记录；raw 快照、请求参数、响应状态、延迟、哈希和 parser/schema 版本均写在外部目录。
- 质量摘要为 FAIL。VCI 的 APG、A32 请求超时；另有 492 条 `invalid_ohlc`、10,452 条 `zero_volume`。
- 50 个 VCI/KBS 对账条目中 45 个为 WARN，包含 3,095 个 primary 缺失日期、10,882 个 secondary 缺失日期和 16,869 条收盘差异。
- 本轮不运行 `03_factor_baseline.py`，不把试点结果解释为 alpha，也不批准 2050 只扩展。

## 可复核命令

网络试点命令：

```text
python exploration/02_daily_data_pipeline.py \
  --network \
  --data-root D:\data\vietnam-quant-research\pilot-v2 \
  --start 2018-01-01 \
  --end 2026-08-27 \
  --sample-size 50 \
  --primary-source vci \
  --secondary-source kbs \
  --rate-limit-seconds 0.05 \
  --strict
```

质量门槛通过后才运行因子基线：

```text
python exploration/03_factor_baseline.py \
  --price-path D:\data\vietnam-quant-research\pilot-v2\bronze\price_daily.jsonl \
  --output D:\data\vietnam-quant-research\pilot-v2\reports\factor_baseline.csv \
  --oos-fraction 0.3 \
  --cost-bps 0,50,100
```

上述第二条命令本轮没有执行，因为质量门槛失败。

## 输出目录

```text
D:\data\vietnam-quant-research\pilot-v2\
├── raw\vci\2026-08-27\*.json
├── raw\kbs\2026-08-27\*.json
├── bronze\instrument_master.jsonl
├── bronze\price_daily.jsonl
├── derived\research_price_daily.jsonl
├── metadata\source_observations.jsonl
├── metadata\quality_report.json
├── metadata\reconciliation_report.json
├── metadata\source_arbitration_report.json
├── metadata\price_semantics_report.json
└── metadata\research_quality_report.json
```

仓库只提交代码、fixture、数据契约和本报告，不提交这些 raw/bronze/metadata 文件。

## 覆盖与行数

| 项目 | 结果 |
|---|---:|
| VCI listing rows | 3,586 |
| selected instruments | 50 |
| selected stock types | 50 |
| HOSE / HNX / UPCoM | 30 / 10 / 10 |
| VCI daily observations | 50 |
| KBS daily observations | 50 |
| VCI parsed rows | 89,617 |
| KBS parsed rows | 81,830 |
| bronze price rows | 171,447 |
| source observations total | 101 |
| reconciliation entries | 50 |

`instrument_master.jsonl` 保存的是完整 VCI 当前列表；样本选择原因写入选中的记录。历史有效期字段仍为 null，当前列表不能证明历史上市、转板或退市有效期。

## 质量结果

| 质量维度 | 结果 | 处理 |
|---|---:|---|
| VCI/KBS HTTP 完成 | VCI 48/50 日线成功；KBS 50/50 | APG、A32 的 VCI 超时写入 FAIL observation |
| invalid OHLC | 492 | 原始行保留，默认因子阶段排除 |
| zero volume | 10,452 | 不填充，不当作正常可成交 |
| boundary price proxy | 88,145 | 只作代理，不声称已确认涨跌停 |
| KBS source reorder | 81,830 | 已排序后输出，raw 顺序保留在快照 |
| thousand VND conversion | 171,447 | raw 与 normalized 字段并列保留 |
| reconciliation WARN | 45/50 | 需要解释日期、单位、复权和来源差异 |

quality report 的 `diagnostic_rows` 只保存带 structural/zero-volume 标记的日期和原始/标准化字段；完整 API 响应仍在 raw 快照中。

## 研究派生层

后续运行会在 `derived/research_price_daily.jsonl` 写入按 symbol/date 去重的研究记录。它不替代 bronze：

- 有效 VCI 主源优先；VCI 缺失或 OHLC 无效时，使用有效 KBS 记录并记录 `secondary_fallback`；
- 两源都无效时保留一条可追溯记录，但标记 `quarantined`、`research_eligible=false`；不填充、不修正；
- 零成交记录保留，但 `tradable=false`；
- 两源收盘价超过 0.1% 差异时标记 `source_disagreement`，原始两源数值仍在 bronze 和 raw 中保留；
- `price_semantics_report.json` 将 VCI/KBS 的 raw/adjusted 口径状态保持为 `unresolved`，所以 `factor_ready` 在独立公司行动证据出现前仍为 false。

`quality_report.json` 是原始摄取门槛，`research_quality_report.json` 是隔离异常后的研究可用率门槛；两者都必须在因子回测前读取，不能只看派生行数。

## 门槛判定

| 门槛 | 判定 |
|---|---|
| 三交易所股票样本 30/10/10 | 通过 |
| VCI 主源 observation、哈希、parser/schema 版本 | 通过，2 个 VCI 请求超时需补采 |
| KBS 倒序和日期闭区间裁剪 | 通过代码测试和试点输出 |
| raw price 与 normalized price 分开 | 通过 |
| OHLC 异常可追溯且不静默删除 | 通过 |
| 无重复来源日线记录 | 通过复合身份写入 |
| 跨源差异已解释 | 未通过 |
| 默认因子输入不含未解释结构异常 | 未通过 |
| OOS 和成本逻辑可由离线测试复现 | 通过 |
| 是否允许扩展到 2050 只 | 否 |

## 下一步优先级

1. 使用固定 50 只样本运行研究派生层，并分别记录 raw gate、research gate 和 `factor_ready`。
2. 抽查 A32、APG 以及 ABR、ADP、ACE、ANT 的 quarantine 行和 source disagreement 样例。
3. 用独立公司行动/复权参考确认 VCI/KBS 价格语义；确认前不运行基础因子。
4. 价格语义确认且 `factor_ready=true` 后，才运行动量、反转、流动性、波动率基线。
5. 基础因子经过 0/50/100 bp、流动性过滤和 OOS 检验后，再决定是否扩展到 2050 只。
6. 仍未解决 SSI 凭证、VSDC 状态、point-in-time 财报和批量存档授权问题。

本报告是数据工程验收记录，不是投资建议，也不证明公开接口允许批量长期存档或再分发。
