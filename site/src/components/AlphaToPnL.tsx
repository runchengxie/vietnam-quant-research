const japanStages = [
  ['Gross Alpha', '研究信号本身可能更薄'],
  ['Trading Cost', '流动性与执行工具让成本更可控'],
  ['Market Impact', '更容易通过分散与容量约束管理'],
  ['Borrow / Hedge', '股票借贷和衍生品让风险结构更完整'],
  ['Fill Constraints', '可成交性通常更稳定'],
  ['Net Alpha', '更适合工业化兑现与扩容'],
]

const vietnamStages = [
  ['Gross Alpha', '结构性行为和资金流信号可能更明显'],
  ['Trading Cost', '换手越高，折损越快'],
  ['Market Impact', '单票流动性与集中度更容易成为瓶颈'],
  ['Borrow / Hedge', '股票 short leg 的实务可用性有限'],
  ['Limit / Fill', '极端信号时成交概率可能反而下降'],
  ['Net Alpha', '低换手与 long-biased 架构更重要'],
]

function Funnel({ title, stages }: { title: string; stages: string[][] }) {
  return <article className="pnl-lane"><h3>{title}</h3>{stages.map(([name, note], index) => <div className="pnl-stage" key={name}><span>{name}</span><p>{note}</p>{index < stages.length - 1 ? <i>↓</i> : null}</div>)}</article>
}

export function AlphaToPnL() {
  return (
    <section className="section" id="alpha-to-pnl">
      <div className="section-heading">
        <div><span className="section-index">03</span><h2>Alpha 到 PnL，中间隔着一整条现实世界</h2></div>
        <p>回测发现信号只是开始。真正的比较对象应当是实施折损后的净 alpha，而不是最漂亮的 gross curve。</p>
      </div>
      <div className="pnl-grid"><Funnel title="Japan · 更薄的信号，更低的实现摩擦" stages={japanStages} /><Funnel title="Vietnam · 更明显的低效，更高的实现折损" stages={vietnamStages} /></div>
    </section>
  )
}
