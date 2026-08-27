# 越南市场量化研究

这是一个公开的、中文为主的越南股票市场数据获取与量化研究资料库。项目当前以资料整理和数据工程规划为主，覆盖 HOSE、HNX、UPCoM 及相关衍生品市场。

## 当前状态

当前已从 docs-first smoke test 升级为可离线测试、可显式联网运行的日频数据闭环：保存 raw snapshot、instrument master、price daily、source observation、质量摘要、VCI/KBS reconciliation，以及不改写 bronze 的研究派生视图。研究视图会隔离 invalid OHLC、标记零成交不可交易、记录来源仲裁和未确认的价格语义；事件—价格核对 CLI 可在外部 data root 生成只读公司行动证据。2026-08-27 的 50 只股票试点原始质量门槛未通过，因此尚未生成可用于研究结论的基础因子结果，也未批准扩展到 2050 只。

## 文档

- [数据源与接口能力](docs/data-sources-overview.md)
- [价格与人民币成本](docs/pricing-and-costs.md)
- [推荐数据栈与落地路线](docs/recommended-data-stack.md)
- [数据质量、回测与授权风险](docs/data-quality-and-risks.md)
- [越南专项量化文献地图](docs/literature-vietnam-specific.md)
- [跨市场论文解读](docs/literature-cross-market.md)
- [公开日线数据可得性审计](docs/exploration-data-audit.md)
- [日频数据闭环 v0 验收报告](docs/daily-data-loop-v0.md)
- [数据契约](docs/data-contracts.md)
- [事件—价格核对设计](docs/superpowers/specs/2026-08-28-event-price-reconciliation-design.md)

## 研究边界

越南市场的数据服务分散在交易所、VSDC、本地券商、聚合工具和商业数据商之间。文档会区分日线、盘中、实时、Tick/Level 2、基本面、外资额度和证券状态，不把“网页上能看到”当成“可以批量抓取、长期保存或再分发”。

## 下一步

旧的可得性探针见 [`exploration/01_public_ohlcv_probe.py`](exploration/01_public_ohlcv_probe.py)，当前闭环入口是 [`exploration/02_daily_data_pipeline.py`](exploration/02_daily_data_pipeline.py)，事件核对入口是 [`exploration/04_event_price_reconciliation.py`](exploration/04_event_price_reconciliation.py)，因子入口是 [`exploration/03_factor_baseline.py`](exploration/03_factor_baseline.py)。运行后先读取 raw gate、research gate 和 `factor_ready`；在价格语义确认且 `factor_ready=true` 前不运行因子基线，不购买 FiinPro、Tick/Level 2，也不把试点结果作为 alpha 结论。运行数据应保存在仓库之外。

## 本地数据目录

正式下载的数据不放进公开仓库，当前外部数据根目录为：

```text
D:\\data\\vietnam-quant-research\\
├── raw/        # 来源原始响应或原始文件
├── bronze/     # 初步标准化数据
├── derived/    # 异常隔离和来源仲裁后的研究派生数据
├── metadata/   # 抓取记录、质量审计和 source observations
├── logs/       # 运行日志
└── reports/    # 因子结果和研究报告
```

探针脚本会优先将审计摘要写入该目录的 `metadata/`；也可以通过 `--data-root` 或 `VIETNAM_QUANT_DATA_ROOT` 指定其他本地路径。仓库中的 `data/`、`artifacts/`、CSV、Parquet 等均已忽略，避免把市场原始数据提交到 GitHub。

## 公开仓库安全

请勿提交 API key、API secret、token、账号信息、商业数据原文件或受许可证限制的数据。未来如加入采集代码，应通过环境变量或本地密钥管理提供凭证，并将原始运行数据保留在仓库之外。

## 免责声明

本项目仅用于市场研究、数据工程规划和量化实验，不构成投资、法律、税务或数据许可意见。历史数据、供应商接口、价格和授权条款都可能变化，使用者应自行核实并承担使用责任。
