import type { Evidence, StrategyFit } from '../data/types'

interface EvidenceDrawerProps {
  row: StrategyFit | null
  evidence: Evidence[]
  onClose: () => void
}

const typeLabels = {
  fact: 'FACT',
  judgment: 'RESEARCH JUDGMENT',
  implementation: 'IMPLEMENTATION STATUS',
} as const

export function EvidenceDrawer({ row, evidence, onClose }: EvidenceDrawerProps) {
  if (!row) return null
  const items = evidence.filter((item) => row.evidenceIds.includes(item.id))

  return (
    <div className="drawer-backdrop" onMouseDown={onClose}>
      <aside className="evidence-drawer" role="dialog" aria-modal="true" aria-label={`${row.label} 的研究依据`} onMouseDown={(event) => event.stopPropagation()}>
        <div className="drawer-head">
          <div>
            <span className="drawer-kicker">WHY THIS SCORE</span>
            <h3>{row.label}</h3>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="关闭依据">×</button>
        </div>
        <div className="rationale-grid">
          <div><strong>日本 · {row.japan}/5</strong><p>{row.japanRationale}</p></div>
          <div><strong>越南 · {row.vietnam}/5</strong><p>{row.vietnamRationale}</p></div>
        </div>
        <div className="evidence-list">
          {items.map((item) => (
            <article className={`evidence-card evidence-card--${item.type}`} key={item.id}>
              <span className="evidence-type">{typeLabels[item.type]}</span>
              <h4>{item.title}</h4>
              <p>{item.summary}</p>
              {item.sourceUrl && item.sourceName ? <a href={item.sourceUrl} target="_blank" rel="noreferrer">{item.sourceName} ↗</a> : null}
              {item.asOf ? <small>截至 {item.asOf}</small> : null}
            </article>
          ))}
        </div>
      </aside>
    </div>
  )
}
