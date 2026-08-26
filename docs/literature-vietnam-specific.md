# 越南股票市场量化文献地图

> 更新时间：2026-08-27
> 用途：把越南专项论文转译成可复现的研究问题、字段需求和回测检查项。

## 先说明“顶刊”的口径

如果把顶刊严格限定为 JF、JFE、RFS，越南作为单一核心样本的实证资产定价论文并不多。下面优先收录有出版社或作者版本链接、并且对量化研究有直接启发的论文；JFE 的中国论文以及全球样本论文放到[跨市场文献解读](literature-cross-market.md)，作为基准而不是越南专项证据。

本文是研究笔记，不复制论文全文。结论是对摘要、论文页面或用户提供节选的结构化改写；“尚未复现”表示仓库目前还没有用独立数据重做该结果。

## 第一批必读论文

| 论文 | 数据/方法 | 主要结论（研究笔记） | 对本项目的直接意义 |
|---|---|---|---|
| [Huang, Liu & Shu (2023), *Factors and anomalies in the Vietnamese stock market*](https://www.sciencedirect.com/science/article/pii/S0927538X23002470) | 越南股票横截面；Datastream/Worldscope；21 个异象；因子组合 | EP 比 BM 更能刻画价值效应；VN-3（市场、规模、EP）优于直接照搬 FF3；加入 12 个月换手率形成 VN-4 后，对多数异象的解释力提高 | 作为日频横截面研究的 baseline；需要价格、成交量、流通股/市值、盈利和账面价值，并检查 point-in-time |
| [Quach, Nguyen & Nguyen (2019), *How do investors price stocks?—Evidence with real-time data from Vietnam*](https://onlinelibrary.wiley.com/doi/abs/10.1002/ijfe.1693) | 2010-10 至 2014-04；“投资者当时可获得”的 real-time 数据；与历史数据样本对照 | 价值和低流动性效应不明显，规模效应较弱；成长股和高流动性股票表现更好。论文强调可用时间而非事后回填数据 | 这是本项目最重要的数据治理提醒：财报必须带 `announcement_at/available_at`，不能把今天修订后的历史字段直接回填到过去 |
| [Nguyen, Tran & Zeckhauser (2017), *Stock splits to profit insider trading*](https://www.sciencedirect.com/science/article/pii/S0261560617300487) | 越南 2007–2011；718 次拆股事件；事件研究、异常收益和成交量 | 拆股公告前出现异常收益和成交量上升，结果与部分拆股被用于内幕交易获利的解释一致 | 构建 `corporate_actions`、公告日/除权日和 CAR 事件窗口；不能把拆股信号当作无条件可交易 alpha |
| [Pham, Nguyen & Do (2022), *Effect of futures trading on the liquidity of underlying stocks*](https://www.sciencedirect.com/science/article/pii/S0927538X22000671) | VN30 股指期货推出；匹配样本 DiD；价差、Amihud、PIN | 期货推出后成分股流动性恶化、PIN 上升；期货折价与卖空限制下套利不足相一致 | 若研究微观结构，需要盘口/价差/成交明细、VN30 成分历史和期货合约生命周期；日线只能做弱版本复现 |
| [Chen et al. (2021), *Liquidity, informed trading, and a market surveillance system*](https://www.sciencedirect.com/science/article/pii/S0927538X21000743) | 2012-03 至 2014-03；270 只 HOSE 股票；MSS 事件；价差、Amihud、Pastor–Stambaugh、turnover、MRR | MSS 后总体流动性下降，小公司更明显；大而流动的公司知情交易有所下降，说明监管对市场质量的影响不是单向的 | 适合做制度事件研究；需要政策生效时间、历史交易频率、价差或盘口数据，不能只依赖收盘价 |

## 因子、行为与制度线索

### 动量、流动性和波动率

- [Vo & Truong (2018), *Does momentum work? Evidence from Vietnam stock market*](https://www.sciencedirect.com/science/article/pii/S2214635017300965)：用户提供的节选报告了按 Jegadeesh–Titman 方法测试动量的结果。它适合作为 `J/K` 参数网格的候选，但要重新检查交易成本、涨跌停、停牌和流动性过滤。
- [Hoang & Phan (2019), *Is Liquidity Priced in the Vietnamese Stock Market?*](https://onlinelibrary.wiley.com/doi/10.1111/1759-3441.12249)：把流动性放进多因子模型，适合与 Huang et al. 的 turnover 因子对照。需要统一 Amihud、turnover、价差和成交额的单位口径。
- [Batten & Vo (2014), *Liquidity and return relationships in an emerging market*](https://research.monash.edu/en/publications/liquidity-and-return-relationships-in-an-emerging-market/)：适合作为早期越南流动性—收益关系的基准，但样本阶段和市场制度距离现在较远，不能直接当作当前交易结论。
- [Fang, Wu & Nguyen (2017), *The Risk-Return Trade-Off in a Liberalized Emerging Stock Market: Evidence from Vietnam*](https://ideas.repec.org/a/mes/emfitr/v53y2017i4p746-763.html)：重点是系统风险、特质波动率和横截面定价，适合检验 IVOL 结果是否依赖市场阶段。
- [Duong & Bertrand (2022), *The size effect and default risk*](https://onlinelibrary.wiley.com/doi/10.1002/rfe.1149)：把规模溢价与违约风险/距离违约联系起来，提醒我们不能把小盘股收益简单解释成“规模因子”。

### 外资、羊群与市场行为

- [Vo (2015), *Foreign ownership and stock return volatility—Evidence from Vietnam*](https://www.sciencedirect.com/science/article/pii/S1042444X15000225)：外资持股与常态波动之间的关系值得重做，并与外资 room、流动性和公司规模交互分析。
- [Vo (2020), *Foreign Investors and Stock Price Crash Risk: Evidence from Vietnam*](https://onlinelibrary.wiley.com/doi/10.1111/irfi.12248)：与“外资降低日常波动”的结论并不矛盾；常态波动降低和尾部崩盘风险上升可以同时存在，因此回测不能只看均值波动。
- [Bui et al. (2018), *Herding in frontier stock markets: evidence from the Vietnamese stock market*](https://onlinelibrary.wiley.com/doi/10.1111/acfi.12253)：使用 CSAD/CSSD 类型方法，论文页面摘要报告了市场和行业层面的羊群行为、上涨和下跌状态下的行为差异，以及美国市场对越南羊群行为的影响。
- [Vo & Phan (2017), *Further evidence on the herd behavior in Vietnam stock market*](https://www.sciencedirect.com/science/article/abs/pii/S2214635017300035)：可作为羊群行为的另一套设定，用于检查结果是否稳健于市场状态与分组方法。

## 把论文翻译成数据字段

| 研究线 | 最低字段 | 关键 point-in-time / 可交易检查 |
|---|---|---|
| EP/BM/盈利能力 | 价格、总股本、流通股、净利润、账面权益、财报期间 | 财报公告时间、合并/单体口径、修订版本 |
| Size/turnover/liquidity | 市值、成交量、成交额、交易天数、价差或盘口 | 低成交、零成交、停牌、单位和复权口径 |
| Momentum/reversal/52-week high | 日收盘、复权因子、交易日历 | 下一交易日执行、涨跌停不可成交、停牌处理 |
| Corporate events | 拆股、分红、配股、增发、公告日、除权日 | 公告时间不能被除权日替代；事件前窗口不能使用未来事件 |
| Foreign ownership/crash risk | 外资持股、foreign room、公司所有权、收益尾部 | room 的观察时间和公告时间；尾部指标窗口不能跨越停牌/缺失 |
| Herding/market quality | 个股收益、指数收益、成交量、价差、交易频率、盘口 | CSAD/CSSD 采样频率、极端收益、市场状态定义 |

## 当前可复现性判断

目前仓库已对一个公开日线接口做了可得性和字段质量 smoke test，见[数据可得性审计](exploration-data-audit.md)。尚未用独立的 point-in-time 财报、完整公司行动或交易所历史 Feed 重做上述论文，因此文献结论应当视为研究假设和设计参考，而不是本项目已经验证的投资结论。

下一阶段优先复现顺序：

1. 用日线和成交量重做 size、turnover、1/3/6/12 个月动量、反转和 52-week high；
2. 对每个信号加入流动性过滤、涨跌停、停牌和成本；
3. 再接入外资 room 与历史证券状态；
4. 最后才做财报 point-in-time、MSS/VN30 期货事件和盘口级研究。
