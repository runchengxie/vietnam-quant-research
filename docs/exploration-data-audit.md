# 越南公开日线数据可得性审计

> 审计日期：2026-08-27（Asia/Shanghai；运行输出为 2026-08-26 UTC）
> 状态：小样本技术 smoke test，不能替代生产级数据验收。

## TL;DR

本次探针给出了一个偏积极但有条件的结论：**越南日线数据可以先做低成本原型，但数据仍需标准化和扩大样本后才能进入正式回测。**

- Vietcap/VCI 公共接口的证券列表请求返回 HTTP 200，共 3,586 条记录；返回的交易所代码包含 `HSX`，本项目将其规范为 `HOSE`，同时观察到 `HNX`、`UPCOM` 和 `DELISTED`。
- 6 个跨交易所样本的日线请求均返回 HTTP 200；必需字段在样本中没有空值，时间戳无重复且按升序排列。
- 一个低流动性样本出现较多 OHLC 关系异常：`A32` 65 行，另一个 HNX 样本 `ADC` 1 行。它们需要回看原始字段和证券状态，不能简单删除或填充。
- VCI 的请求使用 `to + countBack`，实际返回的是“截至结束时间向前的 N 根 K 线”，不是严格的 `start/end` 过滤；客户端必须明确计算 `countBack`，并在标准化层再次按交易日裁剪。
- FPT 的 2024 年 1 月 KBS 样本有 22 个交易日，与 VCI 对齐 22 天；KBS 原始返回倒序，标准化时要排序。两端价格按 VND 保存；早期探针曾在比较时除以 1000，但这只是缩放，不改变相对差，也不应被描述为端点的“千 VND”口径。这只是单股票、单月份的初步结果。

## 可复核的运行方式

探针脚本位于 [`exploration/01_public_ohlcv_probe.py`](../exploration/01_public_ohlcv_probe.py)。它只保存质量计数和请求元数据，不把完整行情写入 Git。运行前需要网络访问：

```text
python exploration/01_public_ohlcv_probe.py
```

在 Windows 本机上，脚本默认优先使用 `D:\\data\\vietnam-quant-research`；也可以显式指定：

```text
python exploration/01_public_ohlcv_probe.py --data-root D:\\data\\vietnam-quant-research
```

本次探针只写入外部目录的 `metadata/public_ohlcv_probe.json`，不保存完整 OHLCV 原始行情。完整下载任务应分别写入外部目录的 `raw/`、`bronze/` 或 `processed/`，而不是公开仓库。

本次使用的公开接口：

- VCI/Vietcap 证券列表：`https://trading.vietcap.com.vn/api/price/symbols/getAll`
- VCI/Vietcap 日线：`https://trading.vietcap.com.vn/api/chart/OHLCChart/gap-chart`
- KBS 日线：`https://kbbuddywts.kbsec.com.vn/iis-server/investment/stocks/{SYMBOL}/data_day`

接口路径来自当前公开的 vnstock VCI/KBS 适配器源代码：[VCI quote](https://raw.githubusercontent.com/thinh-vu/vnstock/main/vnstock/explorer/vci/quote.py)、[VCI listing](https://raw.githubusercontent.com/thinh-vu/vnstock/main/vnstock/explorer/vci/listing.py)、[KBS quote](https://raw.githubusercontent.com/thinh-vu/vnstock/main/vnstock/explorer/kbs/quote.py)。本项目使用这些路径做可得性验证，不代表取得了交易所或供应商的再分发授权。

## 审计范围与方法

| 项目 | 本次设置 |
|---|---|
| 证券列表 | VCI `getAll`，记录返回条数和交易所/证券类型分布 |
| 日线样本 | 每个 `HOSE/HNX/UPCOM` 取 2 个列表样本；另外固定测试 `FPT` 的跨来源对比 |
| 历史请求 | VCI 以 `ONE_DAY`、结束时间 2024-01-31、`countBack=1000` 请求；KBS 请求 2024-01-01 至 2024-01-31 |
| 质量规则 | 行数、必需字段缺失、时间戳重复、时间顺序、`high >= open/close`、`low <= open/close`、非负价格和成交量 |
| 跨来源规则 | 按交易日对齐；记录行数、匹配日期、价格单位换算后的收盘差异 |
| 未覆盖 | SSI FastConnect、VSDC、完整 50 只股票、连续多日稳定性、财报、公司行动、真实 point-in-time 和授权审查 |

## 实际观察

### 1. 证券列表有足够的原型覆盖，但不能直接当历史股票池

VCI 返回了 3,586 条记录。列表里同时存在交易中和 `DELISTED` 记录，这对建立 `instrument_master` 是好事，但也意味着不能把当前列表直接用作每个历史日期的股票池。

`HSX` 与 `HOSE` 是一个必须显式处理的字段差异。标准化层建议保留：

```text
exchange_raw = HSX
exchange = HOSE
source = VCI
retrieved_at = ...
```

而不是覆盖原始值后失去审计线索。

### 2. OHLCV 技术可读，但低流动性异常不能忽略

样本结果：

| 样本 | 来源响应 | 行数 | 缺失必需单元格 | 重复时间 | OHLC 异常 | 时间顺序 |
|---|---:|---:|---:|---:|---:|---|
| AAA / HOSE | 200 | 1,000 | 0 | 0 | 0 | 升序 |
| AAM / HOSE | 200 | 1,000 | 0 | 0 | 0 | 升序 |
| ADC / HNX | 200 | 1,000 | 0 | 0 | 1 | 升序 |
| ALT / HNX | 200 | 1,000 | 0 | 0 | 0 | 升序 |
| A32 / UPCOM | 200 | 1,000 | 0 | 0 | 65 | 升序 |
| AAH / UPCOM | 200 | 15 | 0 | 0 | 0 | 升序 |

这里的“OHLC 异常”是机械质量规则的触发，不等于已证明数据错误。低价股、停牌恢复、特殊交易状态、零成交或接口的占位值都可能触发它。下一步必须输出具体日期和原始字段，和交易所/第二来源逐条核对。

### 3. `countBack` 不是严格起止日期

VCI 日线接口的请求体只有 `timeFrame`、`symbols`、`to` 和 `countBack`。在本次测试中，虽然结束点设为 2024-01-31，`countBack=1000` 的样本起点回到了 2020-02-10 左右；这说明“请求能返回 1,000 行”与“返回 2024 年 1 月”是两回事。

生产适配器应：

1. 根据目标起止日期和频率估算足够的 `countBack`；
2. 请求后把时间戳转换为越南交易日；
3. 再做严格的 `[start, end]` 裁剪；
4. 把请求参数和最终裁剪行数写入 `source_observations`。

### 4. VCI/KBS 可以做初步交叉核验，但单位和顺序必须显式处理

固定测试的 FPT 结果：

- KBS 返回 22 个 2024 年 1 月交易日，顺序为倒序；vnstock 的 KBS 适配器会再排序。
- VCI 与 KBS 的交易日集合匹配 22 天。
- 两个公开端点的股票价格数值按越南盾返回；当前适配器保留 raw VND，并让 normalized VND 与 raw 数值一致。早期探针中的 `/1000` 只是比较时的缩放，数值上不影响相对差，但把它描述成“千 VND”是不正确的。
- KBS 原始返回倒序，适配器会再排序；两端比较仍应保留来源、日期和价格语义状态。

这个结果支持“两个公开聚合源可以用于样本校验”，但不支持“两个源完全等价”。单位修正后，仍然需要扩大到不同交易所、低流动性、公司行动和多个历史时期，并比较开高低收、成交量、成交额和复权状态。

## 数据质量判断

| 维度 | 当前证据 | 判断 |
|---|---|---|
| 可访问性 | 列表和样本日线 HTTP 200 | 适合继续做原型 |
| 结构完整性 | 样本必需字段无空值，时间无重复 | 暂时通过，但样本很小 |
| 时间口径 | VCI `countBack` 需要客户端裁剪；KBS 原始顺序倒序 | 中风险，必须在适配器修正 |
| 数值有效性 | A32/ADC 触发 OHLC 规则 | 中高风险，需按日期诊断 |
| 跨源一致性 | FPT 单月 22 天匹配，收盘差较小 | 初步通过，证据不足以外推 |
| 历史股票池 | 有 `DELISTED` 记录，但未构建有效期表 | 尚未通过 |
| point-in-time | 未测试财报/外资公告时间 | 未知，不能用于基本面回测 |
| 授权 | 只验证公开访问，未确认批量/存档/再分发许可 | 未通过 |

## Go / No-go

### 可以做

- 日频价格、成交量、换手率、波动率、动量、反转和涨跌停行为的研究原型；
- 用 VCI 做批量覆盖、KBS/SSI/交易所样本做交叉核验；
- 先把原始响应摘要、字段单位、抓取时间和 parser 版本建起来。

### 现在不应该直接做

- 把 VCI/KBS 单一源直接作为多年正式回测数据库；
- 使用当前证券列表回填历史股票池；
- 未核对复权和公司行动就计算长期收益；
- 把公开网页/API 当作可自动化、可长期存档、可再分发的授权证明；
- 仅凭这次样本宣称财报、外资 room、Tick 或 Level 2 已经可用。

## 下一轮审计建议

1. 扩展到 50 只证券：30 HOSE、10 HNX、10 UPCoM，加入低流动性、停牌、转板和退市案例；
2. 用最近 5 个交易日重复运行，记录失败、429、超时、行数变化和响应延迟；
3. 对每只股票进行严格日期裁剪，并检查交易日缺口、零成交和 OHLC 异常日期；
4. 对 VCI/KBS 至少比较 10 只股票的 OHLC、成交量、成交额和复权/原始口径；
5. 加入 SSI FastConnect 申请结果和 VSDC 外资 room/证券状态样本；
6. 通过质量门槛后，再做文献中的 VN-3/VN-4、动量、流动性和跨市场指数研究。

## v0 闭环试点更新

2026-08-27 已用实现后的 pipeline 在外部目录 `D:\data\vietnam-quant-research\pilot-v2` 完成 50 只股票试点，覆盖 HOSE 30、HNX 10、UPCoM 10，并分别请求 VCI 和 KBS。完整结果、原始快照和哈希不进入仓库，摘要见[日频数据闭环 v0 验收报告](daily-data-loop-v0.md)。

该批次得到 101 个 observations、171,447 条合并 `price_daily` 记录。质量门槛暂未通过：VCI 有 APG 和 A32 两次读超时，质量摘要包含 492 条 `invalid_ohlc`、10,452 条 `zero_volume`；跨源报告包含 3,095 条只在 primary 缺失的日期、10,882 条另一方向缺失日期和 16,869 条收盘差异记录。下一步是诊断和重跑，不是扩大到 2050 只或购买更高价数据。

## 公司行动与交易所锚点更新

本轮代码已增加 `corporate_action_events` 和 `price_semantic_anchors` 两类证据记录。仓库中的 APG/A32 fixture 只保存公开来源、事件日期、事件类型和置信度，不代表完整历史事件表，也不把缺失比例从价格跳点反推出来。

- APG 已记录两个官方 VSD 样例：2021-06-22 登记日及 2021-09-09 新增股份交易日，另有 2024-08-23 员工股份上市日。事件比例仍待逐公告读取，未写入调整因子。
- A32 已记录两个公开二手来源的现金分红除权日样例：2019-06-06 和 2020-06-16，每股金额为来源页面明确列出的 700 越南盾。登记日和支付日保持为空，不从价格序列推断。
- HNX UPCoM 页面解析器把交易所展示的 OHLC 保存为 `exchange_raw` 锚点。它用于核对 A32 的 VCI/KBS 历史价格，不会改写供应商记录，也不声称网页接口提供完整公司行动历史。
- SSI 解析器支持同时保存 raw OHLC 和明确命名的 `ClosePriceAdjusted`。VCI/KBS 的 adjusted 语义仍为 `unresolved`，因此 `factor_ready` 仍不能开启。

这一步完成的是证据层和解析边界。下一步仍是补齐 APG/A32 的完整逐事件来源、构造可审计的复权价格，并重新跑 50 只股票质量门槛。
