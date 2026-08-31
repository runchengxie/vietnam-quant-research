const vietnam = [
  ['数据工程', 4], ['数据质量门槛', 3], ['因子研究', 2], ['组合构建', 1], ['交易执行', 1],
] as const
const japan = [
  ['数据工程', 5], ['因子研究', 5], ['回测', 5], ['多空组合', 4], ['可执行性', 4],
] as const

function MaturityCard({ market, items }: { market: string; items: readonly (readonly [string, number])[] }) {
  return <article className="maturity-card"><h3>{market}</h3>{items.map(([label, value]) => <div className="maturity-row" key={label}><span>{label}</span><div>{Array.from({ length: 5 }, (_, index) => <i className={index < value ? 'maturity-dot maturity-dot--on' : 'maturity-dot'} key={index} />)}</div></div>)}</article>
}

export function MaturityCompare() {
  return (
    <section className="section" id="maturity">
      <div className="section-heading"><div><span className="section-index">06</span><h2>项目成熟度：看工程进度，不看收益排名</h2></div><p>把研究做到哪一步讲清楚，客户才能正确理解页面中的结论。</p></div>
      <div className="maturity-grid"><MaturityCard market="越南研究" items={vietnam} /><MaturityCard market="日本 Nira" items={japan} /></div>
      <div className="boundary-notes">
        <p>越南：试点结果尚未达到已验证 alpha 的研究门槛。页面展示研究方向、制度约束和推荐架构。</p>
        <p>日本：私有策略工程较完整。公开页面不展示收益、持仓、模型参数、候选名单或专有因子实现。</p>
      </div>
    </section>
  )
}
