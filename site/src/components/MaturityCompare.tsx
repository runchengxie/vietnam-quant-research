const vietnam = [
  ['Data Engineering', 4], ['Data Quality Gate', 3], ['Factor Research', 2], ['Portfolio', 1], ['Execution', 1],
] as const
const japan = [
  ['Data Engineering', 5], ['Factor Research', 5], ['Backtest', 5], ['Long / Short', 4], ['Executability', 4],
] as const

function MaturityCard({ market, items }: { market: string; items: readonly (readonly [string, number])[] }) {
  return <article className="maturity-card"><h3>{market}</h3>{items.map(([label, value]) => <div className="maturity-row" key={label}><span>{label}</span><div>{Array.from({ length: 5 }, (_, index) => <i className={index < value ? 'maturity-dot maturity-dot--on' : 'maturity-dot'} key={index} />)}</div></div>)}</article>
}

export function MaturityCompare() {
  return (
    <section className="section" id="maturity">
      <div className="section-heading"><div><span className="section-index">06</span><h2>项目成熟度：这是工程能力，不是收益排行榜</h2></div><p>把“研究做到哪一步”公开讲清楚，比给客户一条没有上下文的漂亮曲线可靠得多。</p></div>
      <div className="maturity-grid"><MaturityCard market="Vietnam research" items={vietnam} /><MaturityCard market="Japan Nira" items={japan} /></div>
      <div className="boundary-notes">
        <p>越南：当前研究门槛尚未允许把试点结果解释成已验证 alpha；页面展示的是研究方向、制度约束和推荐架构。</p>
        <p>日本：私有策略工程已有更完整能力，但本公开页不展示收益、持仓、模型参数、候选名单或专有因子实现。</p>
      </div>
    </section>
  )
}
