# 越南市场数据价格与人民币成本

> 价格核验/整理日期：2026-08-27  
> 汇率基准：2026-08-25 Wise 中间价，`1 VND = 0.0002574 CNY`  
> 说明：人民币金额是预算估算，不代表银行卡结算价、供应商最终报价或授权费用。

## 先看结论

如果只是验证越南市场是否值得做量化，建议先把年度现金预算控制在 **¥0–1,500 左右**：使用 vnstock Community 或已确认价格的 Sponsor 套餐，加上 VSDC 公开页面，并尝试申请 SSI FastConnect。

如果研究需要标准化财报、公司行动和所有权数据，FiinPro-X 进入 **每月约 ¥2,300–2,800 起**的专业数据预算；如果需要 HOSE 官方实时 Feed，公开文件对应的费用已经是 **每年约 ¥3.9–7.7 万起**，还可能叠加连接、终端、税费和授权成本。

## 换算方法

本页统一使用：

```text
CNY estimate = VND price × 0.0002574
```

示例：

```text
2,399,000 × 0.0002574 = 617.50 → 约 ¥618
10,900,000 × 0.0002574 = 2,805.66 → 约 ¥2,806
300,000,000 × 0.0002574 = 77,220 → 约 ¥77,220
```

实际支付还会受人民币/越南盾汇率变化、银行卡点差、跨境付款手续费、VAT、供应商折扣和合同条款影响。Wise 只是换算参考，不是供应商结算机构。

参考：[Wise VND/CNY 历史汇率](https://wise.com/in/currency-converter/vnd-to-cny-rate/history)。

## 价格快照

### 低成本与个人研究层

| 数据源/套餐 | VND 价格 | 约合人民币 | 周期 | 报价状态与备注 |
|---|---:|---:|---|---|
| vnstock Community | 0 | ¥0 | 持续 | 官方文档确认免费；有访问限额和历史范围限制 |
| vnstock Bronze | 180,000 | 约 ¥46 | 单位周期 | 本项目早期价格快照；商店页动态，付款前需复核 |
| vnstock Silver | 189,000 | 约 ¥49 | 单位周期 | 本项目早期价格快照；商店页动态，付款前需复核 |
| vnstock Golden | 2,399,000 | 约 ¥618 | 年 | 本项目早期价格快照；商店页动态，付款前需复核 |
| vnstock Diamond | 5,400,000 | 约 ¥1,390 | 年 | 本项目早期价格快照；商店页动态，付款前需复核 |
| VSDC 公开页面 | 0 | ¥0 | — | 页面公开访问；自动化、存档和再利用规则需单独确认 |
| SSI FastConnect Data | 未发现公开单列价格 | — | — | 需要 SSI 账户、申请批准和服务条款确认 |

vnstock 官方文档确认 Community 与 Sponsor 的能力差异：Community 版本的速率、历史数据和财务期数受到限制，Sponsor 版本提供更高限额和更完整的历史/实时能力。商店页面是动态渲染页面，因此这里保留价格快照，而不是宣称这些数字永久有效。

参考：[vnstock 数据说明](https://vnstocks.com/docs/vnstock-data/gioi-thieu-vnstock-data)、[vnstock 赞助计划](https://vnstocks.com/insiders-program)、[vnstock 商店](https://vnstocks.com/store)。

### 专业标准化数据层

FiinPro 的官方页面目前出现两个需要特别标记的价格口径：

| 官方页面 | VND 价格 | 约合人民币 | 周期 | 解释 |
|---|---:|---:|---|---|
| FiinPro-X 英文产品页 | 10,900,000 | 约 ¥2,806 | ID/月 | 官方英文页显示的月价；VAT 和合同折扣需确认 |
| FiinPro pricing 页 | 9,000,000 + 10% VAT | 约 ¥2,317；含 VAT 约 ¥2,548 | ID/月 | 官方定价页显示的口径；可能是页面版本、含税规则或方案差异 |

按英文页价格粗略年化：`10,900,000 × 12 = 130,800,000 VND`，约 **¥33,668/年**，但不能据此推断年付价格或折扣。FiinPro 官方页面同时写有试用信息；试用资格、数据导出和商业使用条款需要注册后确认。

参考：[FiinPro-X 英文产品页](https://fiingroup.vn/en/fiinpro-x.html)、[FiinPro 官方 pricing 页](https://fiinpro.com.vn/pricing)。

### HOSE 官方数据服务层

HOSE 官方价格文件列出的项目包括连接和市场数据服务。按同一汇率换算，公开文件中的代表性项目为：

| HOSE 项目 | VND 价格 | 约合人民币 | 周期 | 备注 |
|---|---:|---:|---|---|
| 首次直接连接注册 | 4,000,000 | 约 ¥1,030 | 合同/一次性项目 | 不等同于年度数据费 |
| 1 Mbps 连接线路 | 48,000,000 | 约 ¥12,355 | 年 | 连接费，和数据 Feed 分开 |
| 2 Mbps 连接线路 | 72,000,000 | 约 ¥18,533 | 年 | 连接费，和数据 Feed 分开 |
| 3 Mbps 连接线路 | 84,000,000 | 约 ¥21,622 | 年 | 连接费，和数据 Feed 分开 |
| Standard realtime Feed | 300,000,000 | 约 ¥77,220 | 年 | 官方公开价格文件中的代表性项目 |
| Webservice realtime | 150,000,000 | 约 ¥38,610 | 年 | 官方公开价格文件中的代表性项目 |
| HOSE Index realtime | 160,000,000 | 约 ¥41,184 | 年 | 指数实时产品，权限另行确认 |
| Delayed/EOD Webservice | 约 80,000,000 | 约 ¥20,592 | 年 | 以官方文件版本和合同为准 |

HOSE 公开 PDF 可能被新版本替换，且总成本可能还包括终端/用户、连接、税费、数据使用和再分发许可。这里适合做量级判断，不适合作为采购订单报价。

参考：[HOSE 数据服务价格文件](https://staticfile.hsx.vn/Uploads/UploadDocuments/2406142/Bieu%20gia%20dich%20vu%20cung%20cap%20tin.pdf)、[HOSE 官方网站](https://www.hsx.vn/)。

### HNX、ICE、Bloomberg、LSEG

| 数据源 | VND 价格 | 人民币估算 | 当前判断 |
|---|---:|---:|---|
| HNX Feed | 未形成可靠统一数字 | — | 2026 官方产品/价格文件按数据包和服务报价；需要询价 |
| ICE HOSE/HNX 相关数据 | 询价 | — | 根据 Feed、历史、Level 1/2、API、连接和许可组合报价 |
| Bloomberg | 询价 | — | 终端、数据 API、指数和再分发许可可能分别计价 |
| LSEG/Refinitiv | 询价 | — | 根据产品、历史、API、用户和分发场景报价 |

HNX 官方 2026 数据服务文件明确区分实时/延迟、Top 3/Top 10 深度、衍生品、外资和其他消息包；没有一个适用于所有用户的单一“Feed 价格”。ICE 的 HOSE 产品页明确列出 realtime、delayed、EOD、historical、Level 1/Level 2 和不同交付方式，也没有公开个人研究统一价。

参考：[HNX 2026 数据服务目录与价格文件](https://owa.hnx.vn/ftp/PORTALNEW/FileContent/HNX_Danh%20muc%20goi%20tin%20va%20bang%20gia%20dich%20vu%20CCTT%2820260105_145538_848%29.pdf)、[ICE HOSE 数据产品](https://developer.ice.com/fixed-income-data-services/catalog/ho-chi-minh-stock-exchange-hose)。

## 按预算分层

### 预算 A：¥0/年左右——可行性验证

组合：

- vnstock Community；
- VSDC 公开页面；
- 交易所公开页面；
- 尝试申请 SSI FastConnect。

能做：全市场日频原型、动量、反转、流动性、波动率、成交量、基础外资约束研究。

不能假设：分钟历史完整、财报 point-in-time 完整、原始数据可以商业再分发。

### 预算 B：约 ¥0–1,500/年——个人研究起步

组合：

- 在价格确认后加入 vnstock Golden 或同级 Sponsor；
- VSDC 继续作为证券状态和外资数据补充；
- SSI FastConnect 做接口和盘中能力测试。

适合：批量日频、较大股票池、较稳定的研究刷新和基础实时试验。

### 预算 C：约 ¥2,300–2,800/月起——标准化基本面

组合：

- FiinPro-X 试用/订阅；
- vnstock/SSI 作为价格交叉核验；
- 交易所和 VSDC 作为公司行动与证券状态的外部校验。

适合：财报、估值、所有权、行业分类、公司行动、筛选和历史研究。要先确认：point-in-time 口径、历史修订、Excel/API 导出、用户数量、商业使用和再分发权限。

### 预算 D：约 ¥3.9–7.7 万/年起——机构级行情

组合：HOSE/HNX 官方 Feed 或 ICE/Bloomberg/LSEG 的定制方案。

适合：Tick、Level 2、执行、微观结构、低延迟和正式产品分发。除了表中数据费，还要核实线路、终端/用户、历史文件、API、网络、税费、交易所许可和再分发许可。

## 不要漏算的隐性成本

价格表之外至少要预算：

- 交易所或券商账户开户与资格要求；
- API key 申请、限流和人工审批带来的工程时间；
- 爬虫/API 维护、网页结构变化和失败重试；
- 原始数据存储、备份和跨区域部署；
- 时区、字段标准化、复权和公司行动清洗；
- 越南语/英语财报解析与 point-in-time 对齐；
- VAT、跨境付款、银行卡汇率损耗和合同折扣；
- 团队账号、商业用途、终端数量和再分发许可。

因此，“免费页面”不代表零成本，“年费”也不代表包含自动化和商业使用权。

## 购买前的询价清单

向供应商询价时，建议一次性确认：

1. 覆盖 HOSE、HNX、UPCoM、衍生品中的哪些市场？
2. 日线、分钟、Tick、Level 1/2 各保留多少历史？
3. 是否提供 raw trade、盘口、外资、公司行动、财报和证券状态？
4. 历史数据是否 point-in-time，修订如何留痕？
5. API、文件、终端、WebSocket 和 Excel 是否分别计费？
6. 是否允许自动化、内部研究、团队共享、商业展示和再分发？
7. 是否包含 VAT、连接费、历史回补费、用户费和最低合同期限？
8. 试用期是否能导出数据，试用数据能否保留或用于回测？

## 更新规则

后续更新价格时，保留以下字段：

```text
provider
product
price_vnd
price_cny_estimate
period
tax_included
license_scope
source_url
checked_at
confidence
notes
```

所有价格在实际付款前重新核验。尤其是 vnstock 动态商店页、FiinPro 不同语言页面和交易所 PDF，不能依赖本页旧快照完成采购。

