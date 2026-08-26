# 越南股票市场跨市场文献解读

> 更新时间：2026-08-27
> 研究对象：越南与中国 A 股、香港、日本、美国之间的因子结构、市场联动和投资者行为。

## 结论先行

越南没有一个简单的“最像哪个市场”的答案。按不同维度拆开，当前文献更支持下面这个工作假设：

```text
因子定价：越南部分接近中国的 EP-value 逻辑
规模效应：越南更接近美国式的小盘溢价，而不是简单复制 A 股壳价值
换手率：越南更可能混合了流动性、注意力和散户投机
跨市场传导：香港、美国和日本都有信息/波动传导，危机阶段联系增强
投资者行为：美国影响越南羊群行为，香港更多体现为信息渠道
```

这不是“越南等于 A 股”或“越南等于美股”，而是一个需要用统一样本和统一定义检验的分维度假设。

## 论文与比较对象

| 论文 | 比较对象/样本 | 方法与主要贡献 | 对本项目的用法 |
|---|---|---|---|
| [Huang, Liu & Shu (2023), *Factors and anomalies in the Vietnamese stock market*](https://www.sciencedirect.com/science/article/pii/S0927538X23002470) | 越南；以美国和中国因子文献为参照 | 21 个异象；VN-3（市场、规模、EP）和加入 12 个月换手率的 VN-4 | 越南因子研究总入口；要特别重做 EP/BM、size、turnover、momentum、investment 和 52-week high |
| [Liu, Stambaugh & Yuan (2019), *Size and value in China*](https://www.sciencedirect.com/science/article/pii/S0304405X19300625) | 中国 A 股 | JFE；规模因子排除最小 30% 的壳公司；价值因子用 EP，且 EP 吸收 BM 的中国价值信息 | A 股 benchmark；提醒我们对越南小盘股做壳价值/IPO 制度敏感性分析 |
| [Carpenter, Lu & Whitelaw (2021), *The Real Value of China’s Stock Market*](https://people.stern.nyu.edu/jcarpen0/pdfs/Carpenter%20Lu%20Whitelaw%20-%20The%20Real%20Value%20of%20China%27s%20Stock%20Market.pdf) | 中国与美国 | JFE；讨论价格信息含量、盈利预测和资本配置，区分国企与民企 | 不是越南专项因子论文，而是信息效率/资本配置的制度 benchmark |
| [Vo & Ellis (2018), *International financial integration*](https://www.sciencedirect.com/science/article/pii/S1566014117302935) | 越南、美国、香港、日本 | VAR 估计收益联动，BEKK-GARCH 估计波动传导；覆盖危机前、危机期和危机后 | 构造滚动相关、滞后收益/波动传导和危机分段的基准 |
| [Nasir et al. (2021), *Development of Vietnamese stock market*](https://onlinelibrary.wiley.com/doi/full/10.1002%2Fijfe.1857) | 越南、泰国、日本、香港、中国；2000-07 至 2016-12 | TV-SVAR；把越南宏观变量和区域市场冲击放进时变框架 | 检查市场联动是否随成熟度变化，以及香港/中国冲击的强度是否不同 |
| [Bui et al. (2018), *Herding in frontier stock markets*](https://onlinelibrary.wiley.com/doi/10.1111/acfi.12253) | 越南与美国、香港信息 | CSAD/CSSD 扩展；摘要报告美国影响越南羊群行为，香港主要影响市场信息 | 把跨市场变量放进羊群行为状态回归，而不只是做收益相关系数 |

## 第一层：因子定价上，越南为什么“像中国又像美国”

### EP value：越南与 A 股的可比性更强

Huang et al. 和 Liu–Stambaugh–Yuan 都把 EP（earnings-to-price）放在比 BM 更重要的位置。对我们来说，这个相似性不是一句“价值因子有效”就结束了，至少要拆成：

```text
EP = earnings / price
BM = book equity / market equity
```

要验证的是：

1. EP 是否比 BM 更能解释越南横截面收益；
2. EP 的结果是否由亏损公司、金融股或微盘股驱动；
3. 使用公告可得利润后，结论是否仍成立；
4. 统一交易成本和股票池后，VN-3 是否仍优于直接 FF3。

因此可以先提出：

```text
Vietnam EP-value ≈ China EP-value > 直接复制美国 BM-value
```

这是研究假设，不是已经由本仓库复现的结论。

### Size：不要把越南 SMB 当成 A 股 SMB

中国 JFE 论文明确把最小 30% 公司排除在规模因子之外，原因是这些公司具有规避 IPO 约束的壳价值。越南的确也可能存在微盘股、低流动性和投机交易，但其经济含义未必相同。

所以越南规模研究至少应报告三套结果：

```text
全样本 SMB
排除最小 10%/30% 后的 SMB
按流动性和停牌率过滤后的 SMB
```

如果小盘溢价只在最小、最不流动的一组出现，它更可能是交易摩擦/彩票偏好/数据缺失的组合，而不是一个干净的风险因子。

### Turnover：越南最值得与 A 股比较的变量

Huang et al. 的 VN-4 用 12 个月换手率补充 VN-3，并把高换手率与流动性、注意力和散户投机联系起来。对越南来说，换手率不能只解释为“流动性好”：高换手股票未来收益更低，且小盘、低机构持股股票的关系可能更强。

这给出一个比单纯 SMB 更有区分度的跨市场问题：

```text
高 turnover 是 liquidity，还是 retail attention/speculation？
```

在本项目中应同时计算：12 个月 turnover、Amihud、交易天数、成交额、零成交比例、机构/外资持股和涨停比例。只有这样才能区分“更容易交易”和“被投机者频繁交易”。

## 第二层：跨市场联动不是静态相关系数

Vo & Ellis 的论文使用 VAR 与 BEKK-GARCH，摘要报告越南与美国、香港、日本存在收益和波动传导，并且危机期间市场联系增强。Nasir et al. 使用 TV-SVAR，研究越南与中国、香港、日本、泰国及国内宏观变量的时变关系；论文摘要强调不同市场的影响强度不同，后期对冲击的响应较危机时期温和。

量化上应区分四件事：

1. **同日相关**：受交易时区和非同步交易影响，解释力有限；
2. **滞后收益传导**：美国收盘后对越南下一交易日的可交易预测；
3. **波动传导**：全球风险上升时，相关性是否增加；
4. **制度/危机状态切换**：平稳期的分散化收益是否在危机时消失。

因此，初期不要直接声称“越南和美国相关性高于中国”。用户提供的节选中出现了这一组数值，但本仓库尚未基于统一收盘时间、指数版本和样本区间重算；应作为待验证假设。

## 第三层：香港、美国与中国 A 股的信息角色不同

Nasir et al. 研究的是香港、中国、日本和泰国等区域市场；Bui et al. 的摘要则区分了美国对越南羊群行为的影响与香港的市场信息作用。由此可以形成一个可检验的机制分解：

```text
美国：全球风险偏好、利率、美元和跨国资金
香港：亚洲金融节点、国际机构和中国相关信息的汇聚
中国 A 股：本地政策、居民资金、产业与区域经济信息
日本/泰国：区域风险与供应链/金融周期信号
```

这只是经济解释框架，不能替代实证。实际模型需要把市场收益、波动、汇率、利率和交易时间放进同一时间轴，并明确哪个变量在越南开盘前已经可见。

## 跨市场研究的最小可行设计

### A. 先做指数级风险传导

| 模块 | 设计 |
|---|---|
| 市场 | VNINDEX、S&P 500、Hang Seng、Shanghai Composite，必要时加 Nikkei、SET |
| 频率 | 日频；以 `Asia/Ho_Chi_Minh` 和各市场本地收盘时间保留原始时间 |
| 结果变量 | 越南当日/下一交易日收益、实现波动、极端下跌指标 |
| 解释变量 | 海外市场当日收益、滞后收益、波动、美元/汇率和利率代理 |
| 方法 | 滚动相关 → 滞后回归/VAR → 危机/平稳状态分段；BEKK-GARCH 作为后续而不是第一步 |
| 必做检查 | 非同步交易、缺失日期、时区、指数是否含分红、样本起止一致 |

### B. 再做信号跨市场可迁移性

对越南、A 股和美国使用同一组定义：

```text
Size, EP, BM, 12M turnover, momentum, reversal,
52-week high, IVOL, profitability, investment
```

每个市场都报告：多空组合、市场调整 alpha、换手率、流动性分层、成本后收益、样本内/样本外和滚动稳定性。中国的最小 30% 壳价值处理应作为特殊敏感性分析，而不是悄悄套到所有市场。

### C. 最后做投资者行为和制度交互

候选模型包括：

```text
Vietnam herding_t
  ← US return/volatility
  + Hong Kong return/volatility
  + Vietnam market state
  + foreign room / ownership / turnover
```

以及：

```text
signal return
  ← signal
  × market regime
  × liquidity / size / foreign ownership
```

这一步需要更细的交易和外资数据，不能用一个价格 API 就假装已经完成。

## 与当前数据工程的连接

| 文献结论 | 数据工程要求 |
|---|---|
| EP 优于 BM | 财报公告日、可用日、修订版本和价格复权必须可追溯 |
| Size 受壳价值/微盘影响 | 历史股票池、退市/转板、最小市值、停牌和流动性过滤 |
| Turnover 可能含投机成分 | 成交量、成交额、交易天数、零成交、涨停和机构/外资持股 |
| 危机期间联动增强 | 统一时区、交易日、海外市场收盘时间、指数分红口径 |
| 美国/香港信息角色不同 | 变量的“越南开盘前是否可见”时间戳 |
| 羊群行为和监管事件 | 事件生效日、市场状态、盘口/价差或足够高频的成交数据 |

当前公开日线审计已经显示：VCI/Vietcap 与 KBS 的同一交易日样本可以对齐，但原始价格单位和返回顺序需要标准化；详见[数据可得性审计](exploration-data-audit.md)。这正是跨市场研究前要先做的数据治理工作。

## 文献地位与使用边界

- Huang et al.、Vo & Ellis、Nasir et al.、Bui et al. 是越南专项或越南核心样本研究；其方法和结论值得复现，但不自动代表 2026 年仍可交易。
- Liu–Stambaugh–Yuan 与 Carpenter–Lu–Whitelaw 是中国/美国制度与因子 benchmark，不是越南证据。
- 严格按 JF/JFE/RFS，JFE 论文主要提供中国和中国—美国比较框架；越南专项研究更多分布在 PBFJ、Emerging Markets Review、IJFE、Accounting & Finance 等国际期刊。
- 论文使用的商业数据库、历史修订数据和样本筛选可能无法由公开接口完整重建。复现报告必须列明数据源、可用时间、交易成本和授权边界。
