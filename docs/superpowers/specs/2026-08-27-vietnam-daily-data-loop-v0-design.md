# 越南日频数据闭环 v0 设计说明

**日期：** 2026-08-27  
**状态：** 设计已确认，等待实施计划  
**目标：** 将当前公开接口 smoke test 升级为可审计的日频数据闭环，并在数据质量门槛后运行第一版基础因子基线。

## 1. 决策摘要

本阶段采用轻量、可测试、可扩展的 Python 模块化方案：

```text
VCI listing / OHLCV
        + KBS OHLCV
        + SSI adapter interface（有凭证时启用）
              ↓
raw snapshots + source observations
              ↓
normalized instrument_master / price_daily
              ↓
quality checks + source reconciliation
              ↓
factor features + cost-aware baseline backtest
              ↓
external quality report + factor result table
```

第一轮默认使用 50 只股票作为试点，覆盖 HOSE、HNX、UPCoM，并通过样本清单记录低流动性、停牌、退市或转板案例。采集器的 `sample_size` 参数允许后续扩展到 2050 只；不在第一轮直接把 2050 只当成数据质量验收样本。

VCI 作为主来源，KBS 作为第二来源。SSI 只先实现可插拔接口和配置检查；如果没有 SSI 凭证，VCI/KBS 的离线测试和网络试点仍可运行。VSDC 仅保留后续接入边界，本阶段不抓取需要额外授权确认的页面。

## 2. 目标与非目标

### 2.1 本阶段目标

- 建立 `instrument_master`、`price_daily`、`source_observations` 三类最小数据结构。
- 保存每次请求的原始响应快照到外部数据根目录，不把市场数据提交到 Git。
- 修正 VCI 的 `to + countBack` 语义、KBS 倒序、来源价格单位和严格日期裁剪。
- 不删除 A32、ADC 等异常行；输出具体日期、原始字段和质量标记。
- 对 VCI/KBS 同期数据做可追溯的日期、OHLC、成交量和缺失差异报告。
- 在日频价格/成交量数据上计算动量、反转、流动性、波动率和边界行为基线。
- 使用时间切分样本外、流动性过滤、不可交易条件和交易成本场景，生成第一张信号评估表。
- 为后续 2050 只扩展、SSI/VSDC 接入和基本面数据升级保留稳定接口。

### 2.2 非目标

- 不在本阶段实现 FiinPro、Bloomberg、LSEG 或交易所 Feed。
- 不实现 Tick、Level 2、逐笔成交或正式执行模拟。
- 不实现完整财报 point-in-time、公司行动复权数据库或历史指数成分库。
- 不把当前证券列表直接当作全部历史股票池。
- 不提交 API key、secret、token、账号信息、完整原始行情或商业数据文件。
- 不把基础因子结果表述为投资建议或已验证的可交易 alpha。

## 3. 项目结构

新增结构如下：

```text
vietnam-quant-research/
├── src/
│   └── vietnam_quant/
│       ├── __init__.py
│       ├── schemas.py
│       ├── adapters/
│       │   ├── __init__.py
│       │   ├── vci.py
│       │   ├── kbs.py
│       │   └── ssi.py
│       ├── storage.py
│       ├── quality.py
│       ├── universe.py
│       ├── factors.py
│       ├── backtest.py
│       └── pipeline.py
├── tests/
│   ├── fixtures/
│   │   ├── vci_listing.json
│   │   ├── vci_ohlcv.json
│   │   └── kbs_ohlcv.json
│   ├── test_adapters.py
│   ├── test_quality.py
│   ├── test_storage.py
│   ├── test_factors.py
│   └── test_backtest.py
├── exploration/
│   ├── 01_public_ohlcv_probe.py
│   ├── 02_daily_data_pipeline.py
│   └── 03_factor_baseline.py
├── pyproject.toml
└── docs/
    ├── data-contracts.md
    └── superpowers/specs/2026-08-27-vietnam-daily-data-loop-v0-design.md
```

`src/vietnam_quant` 提供可复用逻辑；`exploration` 只负责命令行入口和结果展示。测试只使用脱敏、最小化的 JSON fixture，不访问网络。

## 4. 数据契约

### 4.1 `instrument_master`

每条证券记录至少包含：

```text
instrument_id: str
symbol: str
issuer_name: str | None
exchange_raw: str | None
exchange: HOSE | HNX | UPCOM | DELISTED | UNKNOWN
security_type: str | None
listing_status: str
valid_from: date | None
valid_to: date | None
listing_date: date | None
delisting_date: date | None
selection_reason: str | None
source: str
retrieved_at_utc: datetime
```

当前 VCI 列表只能证明“本次观察到的当前/来源状态”，不能伪造历史有效期。缺失日期保留为 null，状态使用 `observed_current` 或来源提供的明确状态。`HSX` 必须规范为 `HOSE`，同时保留 `exchange_raw`。

### 4.2 `price_daily`

每条来源标准化后的日线记录至少包含：

```text
symbol: str
trading_date: date
source: str
event_time_raw: str
event_time_utc: datetime | None
exchange: str | None
raw_open: float | None
raw_high: float | None
raw_low: float | None
raw_close: float | None
raw_volume: float | None
raw_price_unit: str
normalized_open: float | None
normalized_high: float | None
normalized_low: float | None
normalized_close: float | None
normalized_price_unit: str
volume_unit: str | None
quality_flags: list[str]
source_observation_id: str
parser_version: str
schema_version: str
```

VCI/KBS 当前适配器观察到的股票价格按千 VND 暴露；标准化值统一为 VND，同时永远保留原始值和原始单位。成交量不在未经来源确认时强行换算，`volume_unit` 写入来源口径或 `unknown`。

同一来源、同一证券、同一交易日只能有一条标准化记录。重复记录不静默覆盖，必须进入质量报告。

### 4.3 `source_observations`

每次列表或行情请求至少记录：

```text
observation_id: str
source: str
endpoint: str
symbol: str | None
request_parameters: dict
retrieved_at_utc: datetime
response_status: int | None
latency_ms: float | None
raw_snapshot_path: str | None
raw_payload_sha256: str | None
row_count: int
first_trading_date: date | None
last_trading_date: date | None
quality_status: PASS | WARN | FAIL
quality_issue_count: int
parser_version: str
schema_version: str
error_type: str | None
error_message: str | None
```

`raw_snapshot_path` 指向外部数据根目录的文件，例如：

```text
<data-root>/raw/vci/2024-01-31/FPT.json
<data-root>/raw/kbs/2024-01-31/FPT.json
```

Git 仓库只保存路径、哈希和质量摘要，不保存完整行情。

## 5. 适配器接口与标准化规则

### 5.1 公共适配器接口

各来源适配器实现同一组行为：

```python
class MarketDataAdapter(Protocol):
    source_name: str

    def fetch_listing(self) -> FetchResult: ...

    def fetch_daily(
        self,
        symbol: str,
        end_date: date,
        count_back: int,
    ) -> FetchResult: ...

    def parse_listing(self, payload: Any) -> list[InstrumentRecord]: ...

    def parse_daily(
        self,
        payload: Any,
        symbol: str,
        requested_start: date,
        requested_end: date,
    ) -> list[RawPriceBar]: ...
```

`FetchResult` 同时携带 HTTP 状态、延迟、原始 payload、请求参数和错误信息。网络失败不会让其他证券全部中断；失败会被记录到 `source_observations`，`--strict` 模式下再根据失败比例返回非零状态。

### 5.2 VCI

- 列表使用当前已有的 `GET /price/symbols/getAll`。
- 日线使用当前已有的 `POST /chart/OHLCChart/gap-chart`。
- `count_back` 必须根据目标日期范围估算，响应后再次严格裁剪到闭区间 `[requested_start, requested_end]`。
- 对数组型 `t/o/h/l/c/v` 和行型响应都提供解析。
- 将 `HSX` 映射为 `HOSE`，但保留原始字段。

### 5.3 KBS

- 使用当前已有的 `GET /iis-server/investment/stocks/{SYMBOL}/data_day`。
- 解析 `data_day`、`data_1D`、`data_1d` 等已观察到的容器。
- 对原始倒序响应先按交易日升序排序，再做日期闭区间裁剪。
- 保留 KBS 原始时间字符串，统一生成 `trading_date`。

### 5.4 SSI

实现不依赖凭证的接口定义和配置校验：

```python
class SSIAdapter(MarketDataAdapter):
    source_name = "ssi"

    def check_credentials(self) -> CredentialStatus: ...
```

没有 `SSI_API_KEY`、`SSI_SECRET` 时，命令输出 `skipped_missing_credentials` 并写入观察记录，不伪造 SSI 数据。后续凭证可通过环境变量接入，不修改仓库代码或提交密钥。

### 5.5 质量处理

- 缺失必需字段：标记 `missing_required`，不删除原始行。
- 时间重复：标记 `duplicate_date`，质量状态 WARN 或 FAIL，不能静默去重。
- `high < max(open, close)`、`low > min(open, close)`、负价格或负成交量：标记 `invalid_ohlc`，保留原始行并在因子阶段默认排除。
- `raw_volume == 0`：标记 `zero_volume`；它可能代表停牌或无成交，不填充为正常交易。
- 原始顺序不是升序：记录 `reordered_source_rows`。
- 价格单位换算：记录 `unit_converted_thousand_vnd`，不覆盖 raw 字段。
- `close == high` 或 `close == low`：记录 `boundary_price_proxy`。如果没有正式涨跌停字段，只能作为边界代理，不能声称是已确认涨跌停。
- 所有质量判断必须关联 `source_observation_id`。

## 6. 样本选择与规模扩展

### 6.1 默认试点

`02_daily_data_pipeline.py` 默认 `--sample-size 50`，最少覆盖：

```text
HOSE: 30
HNX: 10
UPCOM: 10
```

样本清单允许用 `--symbols-file` 显式指定。自动选择时保持排序稳定，并在 `selection_reason` 记录 `exchange_quota`、`edge_case` 或 `explicit_symbol`。

低流动性、停牌、退市/转板案例优先通过显式样本清单加入；如果来源当前列表无法证明某种历史状态，记录 `status_not_proven_by_current_listing`，不把推断写成事实。`DELISTED` 来源记录可以进入独立 edge-case 集合，不回填为某个当前交易所。

### 6.2 扩展到 2050 只

`--sample-size 2050` 只改变样本规模和请求批次，不改变数据契约、质量规则和输出格式。扩展模式必须：

- 使用有界并发或串行限速；
- 每只证券单独记录 observation；
- 支持失败重试后继续；
- 支持断点续跑和已存在 raw snapshot 的幂等跳过；
- 先完成 50 只试点质量验收，再允许作为大批量运行。

## 7. 存储、幂等与运行参数

命令行入口：

```text
python exploration/02_daily_data_pipeline.py +  --data-root D:\data\vietnam-quant-research +  --start 2018-01-01 +  --end 2026-08-27 +  --sample-size 50 +  --primary-source vci +  --secondary-source kbs
```

默认目录：

```text
<data-root>/
├── raw/<source>/<run-date>/*.json
├── bronze/instrument_master.jsonl
├── bronze/price_daily.jsonl
├── metadata/source_observations.jsonl
├── metadata/quality_report.json
├── metadata/reconciliation_report.json
├── logs/pipeline.jsonl
└── reports/factor_baseline.csv
```

写入采用临时文件后原子替换；相同 `source + symbol + requested_window + payload_hash` 不重复写入。运行参数、代码版本和 schema 版本写入报告。

## 8. 基础因子基线

### 8.1 特征定义

使用标准化 close、open 和成交量，按交易日计算：

```text
momentum_1m  = close[t-1] / close[t-22]  - 1
momentum_3m  = close[t-1] / close[t-64]  - 1
momentum_6m  = close[t-1] / close[t-127] - 1
momentum_12m = close[t-1] / close[t-253] - 1
reversal_1m  = -momentum_1m
volatility_1m = std(daily_return[t-21:t-1])
volatility_3m = std(daily_return[t-63:t-1])
avg_volume_1m = mean(raw_volume[t-21:t-1])
amihud_1m = mean(abs(daily_return) / max(close * raw_volume, epsilon))
```

所有信号都使用 `t-1` 及以前的数据，避免使用当日收盘后才知道的值预测同一日收益。

规模因子需要时间点一致的市值或股本输入；本阶段没有可靠字段时输出 `blocked_missing_market_cap`，不使用股价代替规模。

涨跌停行为只在来源提供正式上下限字段时作为正式字段；否则输出 `boundary_price_proxy` 的数量和收益影响，并明确这是代理，不是正式涨跌停识别。

### 8.2 组合和交易规则

- 每月最后一个可用交易日形成组合，信号在下一个可用交易日开盘执行。
- 每个因子按横截面五分位分组；某日有效股票不足 10 只时跳过该形成日并记录原因。
- 默认报告最高分位多头、最低分位空头和多空组合，等权重。
- 开盘价缺失、开盘价非正、成交量为零、日期重复或 `invalid_ohlc` 的证券在对应交易日不可交易。
- `boundary_price_proxy` 默认保留并单独统计；可用 `--exclude-boundary-proxy` 作为敏感性分析，不把代理强制当成涨跌停。
- 流动性过滤默认去除形成日前 21 个交易日 `close * raw_volume` 代理值横截面最低 20% 的证券，并报告该代理受成交量单位不确定性的限制。
- 交易成本通过参数运行 `0/50/100` bp 场景。单期成本定义为：

```text
turnover_t = 0.5 × Σ_i |target_weight_i,t - previous_weight_i|
net_return_t = gross_return_t - cost_bps / 10000 × turnover_t
```

首次建仓的 previous weight 为 0；组合权重和、空仓和未成交名额都写入结果表。

### 8.3 样本外

按交易日时间顺序切分，默认最后 30% 为 OOS；不随机打乱。结果至少包含：

```text
factor
formation_date
period
universe_count
long_count
short_count
gross_return
turnover
net_return_cost_0bp
net_return_cost_50bp
net_return_cost_100bp
excluded_for_quality
excluded_for_liquidity
excluded_for_non_tradable
```

汇总表分别列出 IS、OOS 和全样本的累计收益、年化收益、波动率、最大回撤、Sharpe 代理、平均换手率、有效形成期数量和缺失比例。小样本或数据覆盖不足时输出 `insufficient_coverage`，不补值。

## 9. 错误处理与质量门槛

### 9.1 网络和来源错误

- 单次请求使用有限重试，重试只针对连接错误、429 和 5xx，并记录每次尝试。
- 4xx、解析错误和认证错误写入 observation 后继续其他证券。
- 所有失败都保留错误类型和消息摘要，不写入凭证内容。
- `--strict` 模式在没有完整来源覆盖、存在未处理解析错误或质量报告无法生成时返回非零状态。

### 9.2 进入因子阶段的门槛

在运行因子基线前，必须满足：

- 三个交易所配额样本已生成，所有样本都有 `instrument_master` 记录；
- VCI 主源的请求、响应、解析版本和 raw hash 均有 observation；
- KBS 交叉样本中，日期排序和日期闭区间裁剪已通过；
- 所有 OHLC 异常行都在质量报告中有具体日期和原始值；
- raw price 没有被 normalized price 覆盖；
- 任何有效交易日没有重复记录；
- OOS 切分和成本场景可由测试复现；
- 结果可以追溯到 `source_observation_id`。

质量门槛不要求异常数量为零，但要求异常可解释、可追溯、不会静默进入默认因子组合。

## 10. 测试策略

### 10.1 离线单元测试

必须覆盖：

- `HSX -> HOSE` 规范化且 raw 值保留；
- VCI 数组型响应解析；
- KBS 容器解析、倒序排序和日期闭区间裁剪；
- `count_back` 响应超出目标窗口时被严格裁剪；
- 千 VND 转 VND 时 raw/normalized 字段同时保留；
- 缺失、重复、负值、OHLC 关系异常和零成交产生正确质量标记；
- source observation 包含请求参数、哈希、行数和 parser/schema 版本；
- 动量特征只使用滞后数据；
- 五分位组合在有效样本不足时跳过；
- 零成交、无开盘价和 invalid OHLC 不产生交易；
- 交易成本、换手率和 OOS 切分在合成数据上可复现；
- 缺少市值时规模因子保持 blocked，而不是使用股价替代。

### 10.2 网络集成测试

网络测试不是默认单元测试的一部分，使用显式命令运行：

```text
python exploration/02_daily_data_pipeline.py --network --sample-size 50
```

网络运行结果写到外部数据根目录。公共仓库只提交代码、fixture、schema 和质量报告格式，不提交市场原始数据。

## 11. 实施顺序

1. 添加项目 Python 配置、数据契约和离线 fixtures。
2. 先为 VCI/KBS 解析、单位、排序、日期裁剪和质量标记写失败测试，再实现最小适配器。
3. 实现外部目录存储、source observation、幂等写入和 50 只样本选择。
4. 实现网络 pipeline，并用已有 A32、ADC、FPT 观察作为回归案例。
5. 实现因子特征、组合回测、成本场景和 OOS 汇总。
6. 在本机运行 50 只试点；只有质量门槛通过后再评估 2050 只扩展。
7. 更新 README 和审计文档，记录命令、输出路径、限制和第一份信号结果。

## 12. 验收产物

本阶段完成时，必须具备：

- 可离线运行的单元测试；
- 可通过参数运行的 VCI/KBS 日频 pipeline；
- 外部目录中的 raw、bronze、metadata、logs 和 factor report；
- 一份包含 IS/OOS、交易成本、流动性和不可交易排除统计的因子结果表；
- 一份质量/来源差异报告；
- 明确列出未解决的 SSI、VSDC、point-in-time 财报、公司行动和授权边界；
- README 中的下一步从“建立 prototype”更新为“运行试点并根据质量门槛决定是否扩展”。

