# 公司行动—价格核对报告

**运行日期：** 2026-08-28（Asia/Shanghai）  
**数据根目录：** `D:\data\vietnam-quant-research\pilot-v6`（仓库外）  
**输入：** `bronze/price_daily.jsonl`，175,554 行；APG/A32 离线事件 fixture，4 个事件  
**窗口：** 参考日前后各 5 根 source trading bars  
**输出：** `metadata/corporate_action_price_reconciliation.jsonl` 和 `.json`（均在仓库外）

## 结论

事件—价格核对层已对 pilot-v6 的 4 个 APG/A32 事件生成可追溯窗口。报告只描述事件日期与两源价格证据的对齐程度，不证明公司行动造成了价格变化，也不构造复权因子。VCI/KBS 的 `price_semantics` 仍为 `unresolved`，50 只质量门槛仍未通过，`factor_ready=false`。

## 事件结果

| 事件 | 参考日 | 状态 | VCI 窗口 | KBS 窗口 | 主要证据 |
|---|---|---|---:|---:|---|
| APG stock dividend/rights | 2021-09-09（`listing_date`） | `matched` | 11，invalid 0，zero 0 | 11，invalid 0，zero 0 | 共同 11 日，close difference 0，最大相对差异约 0.0068% |
| A32 cash dividend | 2019-06-06（`ex_date`） | `unresolved` | 11，invalid 7，zero 6 | 11，invalid 3，zero 0 | 共同 5 日，close difference 5，窗口 invalid 10，最大相对差异约 9.72% |
| A32 cash dividend | 2020-06-01（`ex_date`） | `unresolved` | 11，invalid 0，zero 7 | 11，invalid 0，zero 0 | 共同 4 日，close difference 4，缺失日期 14，最大相对差异约 2.26% |
| APG employee shares | 2024-08-23（`listing_date`） | `matched` | 11，invalid 0，zero 0 | 11，invalid 0，zero 0 | 共同 11 日，close difference 0，最大相对差异 0 |

A32 事件日期已按来源字段语义保存：2019 事件为除权日 2019-06-06、登记日 2019-06-07、支付日 2019-06-20；2020 事件为除权日 2020-06-01、登记日 2020-06-02、支付日 2020-06-16。支付日没有被当作除权日使用。

每个窗口记录都保留 raw/normalized close、volume、quality flags 和
`source_observation_id`。A32 2019 的 invalid OHLC 和 zero-volume 记录在证据中保留，
没有填充或删除；APG 2021 的 `matched` 仅表示日期和窗口质量足以对齐，不能解释为
复权关系已确认。

## 工程行为

- 参考日选择器支持 `ex_date`、上市/新增股份类事件的 `listing_date`，以及仅作时间锚的 announcement date；不会回退到 `record_date` 或 `payment_date`。
- 事件报告消费 bronze，不改写输入；本次 CLI 输出显示输入仍为 175,554 行。
- 相同 `event_id` 重跑采用 upsert，JSONL 与 JSON summary 保持一致，不追加重复事件。
- 该层不发起网络请求、不生成 adjusted OHLC、不修改 `factor_ready`，也没有运行因子基线。

本记录是数据质量和事件证据审计，不是 Alpha 结论或投资建议。完整行情和生成的事件报告均保存在仓库外。
