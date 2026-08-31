const japanStages = [
  ['毛 alpha', '信号强度可能较低'],
  ['交易成本', '流动性和执行工具有助于控制成本'],
  ['市场冲击', '可以通过分散持仓和容量约束管理'],
  ['借券与对冲', '股票借贷和衍生品让风险管理更完整'],
  ['成交约束', '通常更容易成交'],
  ['净 alpha', '更适合规模化运行'],
]

const vietnamStages = [
  ['毛 alpha', '行为和资金流信号可能更明显'],
  ['交易成本', '换手越高，成本折损越快'],
  ['市场冲击', '单只股票的流动性和持仓集中度容易成为瓶颈'],
  ['借券与对冲', '普通股票的做空腿在实务中可用性有限'],
  ['涨跌停与成交', '信号最强时，成交概率可能下降'],
  ['净 alpha', '低换手和偏多组合更重要'],
]

function Funnel({ title, stages }: { title: string; stages: string[][] }) {
  return <article className="pnl-lane"><h3>{title}</h3>{stages.map(([name, note], index) => <div className="pnl-stage" key={name}><span>{name}</span><p>{note}</p>{index < stages.length - 1 ? <i>↓</i> : null}</div>)}</article>
}

export function AlphaToPnL() {
  return (
    <section className="section" id="alpha-to-pnl">
      <div className="section-heading">
        <div><span className="section-index">03</span><h2>从 alpha 到收益，中间还有交易现实</h2></div>
        <p>回测只能说明信号潜在有效。比较市场时，还要扣除交易成本、市场冲击、借券和成交约束。</p>
      </div>
      <div className="pnl-grid"><Funnel title="日本 · 信号较薄，实现摩擦较低" stages={japanStages} /><Funnel title="越南 · 低效更明显，实现折损更高" stages={vietnamStages} /></div>
    </section>
  )
}
