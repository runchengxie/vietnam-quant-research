import type { Evidence } from '../data/types'

export function Methodology({ evidence }: { evidence: Evidence[] }) {
  const sources = evidence.filter((item) => item.sourceUrl && item.sourceName)
  return (
    <footer className="methodology" id="methodology">
      <div className="methodology__intro"><span className="section-index">07</span><h2>方法论与证据</h2><p>页面把三种东西分开：可核验的市场事实、用于比较的研究判断、以及两个工程当前真正做到的实现状态。这样至少不会让一张雷达图假装自己是自然定律。</p></div>
      <div className="method-grid">
        <article><span className="evidence-type">FACT</span><h3>公开可核验</h3><p>交易制度、借贷用途、数据服务和市场规则。关键制度事实优先链接官方来源。</p></article>
        <article><span className="evidence-type">RESEARCH JUDGMENT</span><h3>有定义的主观评分</h3><p>综合流动性、shortability、容量、数据、执行和潜在低效。评分不是收益预测。</p></article>
        <article><span className="evidence-type">IMPLEMENTATION STATUS</span><h3>工程做到哪一步</h3><p>只描述可公开披露的工程成熟度。日本私有研究不向公开站点泄露策略产物。</p></article>
      </div>
      <div className="source-list"><h3>Primary sources</h3>{sources.map((item) => <a key={item.id} href={item.sourceUrl} target="_blank" rel="noreferrer"><span>{item.sourceName}</span><small>{item.asOf ?? 'source'} ↗</small></a>)}</div>
      <p className="disclaimer">本页面用于市场结构与量化研究方法展示，不构成投资、法律、税务或数据许可意见。市场制度与数据服务会变化，实际交易前应重新核验。</p>
    </footer>
  )
}
