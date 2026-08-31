import type { Evidence } from '../data/types'

export function Methodology({ evidence }: { evidence: Evidence[] }) {
  const sources = evidence.filter((item) => item.sourceUrl && item.sourceName)
  return (
    <footer className="methodology" id="methodology">
      <div className="methodology__intro"><span className="section-index">07</span><h2>方法与证据</h2><p>页面区分三类信息：可核验的市场事实、用于比较的研究判断，以及两个项目当前的工程状态。评分需要结合证据阅读。</p></div>
      <div className="method-grid">
        <article><span className="evidence-type">FACT</span><h3>公开可核验</h3><p>交易制度、借贷用途、数据服务和市场规则。关键制度事实优先链接官方来源。</p></article>
        <article><span className="evidence-type">RESEARCH JUDGMENT</span><h3>有定义的研究判断</h3><p>评分综合考虑流动性、做空条件、容量、数据、执行和潜在低效。它用于比较策略适配度。</p></article>
        <article><span className="evidence-type">IMPLEMENTATION STATUS</span><h3>工程做到哪一步</h3><p>只描述可公开披露的工程成熟度。日本私有研究不向公开站点泄露策略产物。</p></article>
      </div>
      <div className="source-list"><h3>主要来源</h3>{sources.map((item) => <a key={item.id} href={item.sourceUrl} target="_blank" rel="noreferrer"><span>{item.sourceName}</span><small>{item.asOf ?? '未注明日期'} ↗</small></a>)}</div>
      <p className="disclaimer">本页面用于市场结构与量化研究方法展示，不构成投资、法律、税务或数据许可意见。市场制度与数据服务会变化，实际交易前应重新核验。</p>
    </footer>
  )
}
