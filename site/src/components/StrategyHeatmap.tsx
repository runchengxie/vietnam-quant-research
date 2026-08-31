import { useMemo, useState } from 'react'
import type { Evidence, StrategyCategory, StrategyFit } from '../data/types'
import { EvidenceDrawer } from './EvidenceDrawer'

interface StrategyHeatmapProps {
  rows: StrategyFit[]
  evidence: Evidence[]
}

const categories: Array<{ id: 'all' | StrategyCategory; label: string }> = [
  { id: 'all', label: '全部' },
  { id: 'frequency', label: '频率' },
  { id: 'portfolio', label: '组合结构' },
  { id: 'model', label: '模型' },
  { id: 'alpha', label: '信号来源' },
  { id: 'capacity', label: '资金与容量' },
]

function Score({ value, label }: { value: number; label: string }) {
  return (
    <div className="score" aria-label={label}>
      {Array.from({ length: 5 }, (_, index) => <span key={index} className={index < value ? 'score__block score__block--filled' : 'score__block'} />)}
      <b>{value}</b>
    </div>
  )
}

export function StrategyHeatmap({ rows, evidence }: StrategyHeatmapProps) {
  const [category, setCategory] = useState<'all' | StrategyCategory>('all')
  const [selected, setSelected] = useState<StrategyFit | null>(null)
  const filtered = useMemo(() => category === 'all' ? rows : rows.filter((row) => row.category === category), [category, rows])

  return (
    <section className="section" id="strategy-fit">
      <div className="section-heading">
        <div><span className="section-index">01</span><h2>策略适配度矩阵</h2></div>
        <p>先看适合哪些策略，再查看判断依据。分数表示实施适配度，不代表未来收益。</p>
      </div>
      <div className="filter-row" aria-label="策略分类筛选">
        {categories.map((item) => (
          <button key={item.id} className={category === item.id ? 'chip chip--active' : 'chip'} onClick={() => setCategory(item.id)}>{item.label}</button>
        ))}
      </div>
      <div className="matrix-wrap">
        <table className="matrix">
          <thead><tr><th>策略类型</th><th>日本</th><th>越南</th><th>判断</th><th>依据</th></tr></thead>
          <tbody>
            {filtered.map((row) => (
              <tr key={row.id}>
                <th scope="row">{row.label}</th>
                <td><Score value={row.japan} label={`${row.label}，日本适配度 ${row.japan} / 5`} /></td>
                <td><Score value={row.vietnam} label={`${row.label}，越南适配度 ${row.vietnam} / 5`} /></td>
                <td><span className="verdict">{row.verdict}</span></td>
                <td><button className="text-button" onClick={() => setSelected(row)} aria-label={`查看 ${row.label} 的依据`}>查看依据 →</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <EvidenceDrawer row={selected} evidence={evidence} onClose={() => setSelected(null)} />
    </section>
  )
}
