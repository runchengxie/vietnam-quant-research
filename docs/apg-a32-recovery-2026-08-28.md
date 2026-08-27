# APG/A32 补采与 50 只质量门槛复核

**复核日期：** 2026-08-28（Asia/Shanghai）  
**数据根目录：** `D:\data\vietnam-quant-research\pilot-v6`（仓库外）
**样本：** 固定 50 只，HOSE/HNX/UPCoM = 30/10/10  
**区间：** 2018-01-01 至 2026-08-27  
**来源：** VCI + KBS；VCI listing 使用 `pilot-v2` 已保存的 raw listing 快照，日线请求使用真实 VCI/KBS adapter

## 结论

`pilot-v6` 已完成固定 50 只股票的双源日线补采。100 个日线 source observation 全部成功返回 HTTP 200，APG、A32、AAA 的 VCI 请求均恢复；但 50 只股票仍未通过质量门槛，因此不允许运行动量、反转或其他因子基线。当前 `factor_ready=false`，主要阻断已从传输层收敛为原始 OHLC/零成交异常、跨源差异和未解决的价格语义。

## 采集结果

| 维度 | 结果 |
|---|---:|
| selected instruments | 50 |
| HOSE / HNX / UPCoM | 30 / 10 / 10 |
| source observations | 101（listing 1 + 日线 100） |
| VCI 日线成功 | 50/50 |
| KBS 日线成功 | 50/50 |
| bronze price rows | 175,554（VCI 93,724；KBS 81,830） |
| research price rows | 93,762 |
| research key duplicates | 0 |
| research date range | 2018-01-02 至 2026-08-27 |

`pilot-v3`、`pilot-v4` 中 VCI listing 端点连续超时；新增的具体 `ReadTimeout` 重试逻辑虽然已生效，但 listing 仍未稳定。为不伪造选样，`pilot-v6` 复用 `pilot-v2` 的 listing raw 快照作为输入，缓存路径和来源写入 listing observation；日线数据没有从旧批次复制。`pilot-v5` 是 countBack 上限修复前的中间批次，不作为最终质量结论。

## APG/A32/AAA 证据

| 股票 | VCI | KBS | 研究视图处理 |
|---|---|---|---|
| APG | 2,160 行，`WARN`，2 条 `zero_volume` | 2,158 行，1 条 `invalid_ohlc` | 采用 VCI；无 quarantine，但 2 条零成交不可交易；source arbitration 有 861 个差异 |
| A32 | 1,947 行，`FAIL`，121 条 `invalid_ohlc`、949 条 `zero_volume` | 899 行，39 条 `invalid_ohlc` | 采用 VCI；1 行 fallback，120 行 quarantine；研究合资格 1,827 行 |
| AAA | 2,160 行，`WARN`，2 条 `zero_volume` | 2,158 行，`WARN` | 采用 VCI；无 fallback、无 quarantine |

A32 的 KBS 39 条异常不是 parser 静默修正：原始行中有 24 条 `close > high`、15 条 `close < low`，异常日期覆盖 2019-06-03 至 2025-04-10。例：2019-06-03 的 raw OHLC 为 `open=high=low=14452`、`close=13686`。

A32 的 VCI raw 也存在独立异常：首个异常日 2018-10-23 的原始值为 `open=11546.41`、`high=0`、`low=0`、`close=0`、`volume=0`；121 条 invalid OHLC 和 949 条 zero-volume 记录均保留在审计输出中，没有被填充或删除。这个结果说明问题不再只是 KBS 排序或单一供应商字段映射。

APG 的 VCI 端点已成功返回 2,160 行，但不能因为请求恢复，就把 APG 两源的 861 个 arbitration 差异（reconciliation close differences 为 862）解释为已确认的复权关系。当前 `price_semantics_report.json` 仍为 `unresolved`。

## 质量门槛

| 门槛 | 结果 | 证据 |
|---|---|---|
| 三交易所固定样本 | 通过 | 50 只，30/10/10 |
| VCI/KBS source observation 完整 | 通过 | VCI 50/50、KBS 50/50；100 个日线请求 HTTP 200 |
| raw/normalized 分开且 source 可追溯 | 通过 | 175,554 bronze rows、100 个日线 observations |
| research composite key 唯一 | 通过 | `symbol/trading_date` duplicates = 0 |
| invalid OHLC | 未通过 | 613 条，约占 source rows 的 0.349% |
| zero volume | 未通过 | 11,403 条，约占 source rows 的 6.496% |
| 跨源差异已解释 | 未通过 | 45/50 reconciliation entries 为 `WARN`，matched dates = 81,792 |
| research view | 部分通过 | `PASS_WITH_QUARANTINE`，454 条 quarantine，93,308 条合资格 |
| price semantics | 未通过 | `unresolved` |
| `factor_ready` | 未通过 | `false` |

研究视图共有 93,308 条 `research_eligible`、82,335 条 `tradable` 记录；这些覆盖率不能抵消价格语义和异常 OHLC 尚未解释的问题。

## 已完成的工程修复

`pipeline.py` 现在会对 `ReadTimeout`、`ConnectTimeout` 等具体 requests 异常重试；同时将长区间 VCI `countBack` 限制在已验证可用的 2,200。离线回归测试覆盖了 listing 重试和长区间上限。小窗口不写盘诊断中，APG、A32、AAA 均以 `countBack=2200` 返回 HTTP 200；随后完整 v6 批次的 100 个日线请求全部成功，说明 countBack 上限确实解决了本轮 APG/A32/AAA 的传输层失败。

## 下一步

1. 逐事件核对 A32 的两源异常、APG 的跨源差异和零成交区间，明确哪些是停牌/无成交、供应商边界代理值或复权口径差异。
2. 获取或构造可审计的公司行动事件表，明确 VCI/KBS 的 raw、adjusted 语义；在此之前不把跨源比例直接当作复权系数。
3. 重新定义并自动化异常隔离规则，完成 50 只 gate 的可复现重跑；新鲜 listing 恢复后，再使用新鲜样本重跑，不在 `pilot-v6` 原地追加。
4. 只有价格语义、异常隔离、跨源 reconciliation 和 50 只 gate 全部通过后，才从 `derived/research_price_daily.jsonl` 运行因子诊断与成本回测。

本记录只说明数据工程复核结果，不构成 Alpha 结论或投资建议。完整 raw、bronze、derived 和 metadata 文件均保存在仓库外。
