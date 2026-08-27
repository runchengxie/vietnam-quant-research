# APG/A32 补采与 50 只质量门槛复核

**复核日期：** 2026-08-28（Asia/Shanghai）  
**数据根目录：** `D:\data\vietnam-quant-research\pilot-v5`（仓库外）  
**样本：** 固定 50 只，HOSE/HNX/UPCoM = 30/10/10  
**区间：** 2018-01-01 至 2026-08-27  
**来源：** VCI + KBS；VCI listing 使用 `pilot-v2` 已保存的 raw listing 快照，日线请求仍使用真实 VCI/KBS adapter

## 结论

本次补采没有通过 50 只股票质量门槛，也不允许运行动量、反转或其他因子基线。APG 的 VCI 日线请求已经恢复，但 A32 的 VCI 请求仍超时，且 AAA 出现新的 VCI 超时；A32 的 KBS 历史 OHLC 仍有结构性异常。整体 `factor_ready=false`，主要阻断仍是未解决的价格语义、隔离异常和跨源差异。

## 采集结果

| 维度 | 结果 |
|---|---:|
| selected instruments | 50 |
| HOSE / HNX / UPCoM | 30 / 10 / 10 |
| source observations | 101（listing 1 + 日线 100） |
| VCI 日线成功 | 48/50 |
| KBS 日线成功 | 50/50 |
| bronze price rows | 171,447 |
| research price rows | 92,712 |
| research key duplicates | 0 |
| research date range | 2018-01-02 至 2026-08-27 |

VCI listing 端点在 `pilot-v3`、`pilot-v4` 连续超时；新加的具体 `ReadTimeout` 重试逻辑已生效，但 listing 仍未恢复。为不伪造选样，`pilot-v5` 只复用 `pilot-v2` 的 listing raw 快照作为输入，缓存路径和来源已写入 listing observation；日线数据没有从旧批次复制。

## APG/A32/AAA 证据

| 股票 | VCI | KBS | 研究视图处理 |
|---|---|---|---|
| APG | 2,160 行，`WARN`，2 条 `zero_volume` | 2,158 行，1 条 `invalid_ohlc` | 采用 VCI；无 quarantine，但 2 条零成交不可交易；两源有 861 个收盘差异 |
| A32 | `ReadTimeout`，0 行 | 899 行，39 条 `invalid_ohlc` | KBS fallback；860 行研究合资格，39 行 quarantine |
| AAA | `ReadTimeout`，0 行 | 2,158 行 | KBS fallback；本次新增的 VCI 失败样本 |

A32 的 39 条异常不是 parser 静默修正：原始 KBS 行中有 24 条 `close > high`、15 条 `close < low`，异常日期覆盖 2019-06-03 至 2025-04-10。例：2019-06-03 的 raw OHLC 为 `open=high=low=14452`、`close=13686`；这些行在 research view 中保留但标记为 quarantine。

APG 的 VCI 端点在完整区间请求中成功返回 2,160 行；不应因为 APG 请求恢复，就把 APG/KBS 的 861 个收盘差异解释为已确认的复权关系。当前 `price_semantics_report.json` 仍为 `unresolved`。

## 质量门槛

| 门槛 | 结果 | 证据 |
|---|---|---|
| 三交易所固定样本 | 通过 | 50 只，30/10/10 |
| VCI/KBS source observation 完整 | 未通过 | A32、AAA 的 VCI `ReadTimeout` |
| raw/normalized 分开且 source 可追溯 | 通过 | 171,447 bronze rows、100 个日线 observations |
| research composite key 唯一 | 通过 | `symbol/trading_date` duplicates = 0 |
| invalid OHLC | 未通过 | 492 条，25 只股票受影响，约 0.287% source rows |
| zero volume | 未通过 | 10,452 条，约 6.096% source rows |
| 跨源差异已解释 | 未通过 | 45/50 reconciliation entries 为 `WARN` |
| research view | 部分通过 | `PASS_WITH_QUARANTINE`，373 条 quarantine |
| price semantics | 未通过 | `unresolved` |
| `factor_ready` | 未通过 | `false` |

研究视图共有 92,339 条 `research_eligible`、82,201 条 `tradable` 记录；这些覆盖率不能抵消价格语义和异常 OHLC 尚未解释的问题。

## 已完成的工程修复

`pipeline.py` 现在会对 `ReadTimeout`、`ConnectTimeout` 等具体 requests 异常重试；同时将长区间 VCI `countBack` 限制在已验证可用的 2,200。离线回归测试覆盖了 listing 重试和长区间上限。小窗口不写盘诊断中，APG、A32、AAA 均以 `countBack=2200` 返回 HTTP 200，说明此前超时主要与长区间请求参数相关；完整批次中 A32/AAA 仍失败，需后续再做低并发、分段请求或 endpoint 级恢复验证。

## 下一步

1. 等 VCI listing 和 A32/AAA 日线 endpoint 稳定后，使用新鲜 listing 重新跑同一固定 50 只样本；不在 `pilot-v5` 原地追加，避免 observation 幂等键混合不同批次。
2. 逐事件核对 A32 的 39 条异常和 APG 的 861 个跨源差异，确认是否为供应商字段/调整口径问题；不填充、不删除、不把差异当作复权系数。
3. 价格语义、异常隔离和 50 只 gate 全部通过后，才从 `derived/research_price_daily.jsonl` 运行因子诊断与成本回测。

本记录只说明数据工程复核结果，不构成 Alpha 结论或投资建议。完整 raw、bronze、derived 和 metadata 文件均保存在仓库外。
