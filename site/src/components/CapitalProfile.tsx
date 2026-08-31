import { useState } from 'react'
import type { CapitalProfile as CapitalProfileData } from '../data/types'

export function CapitalProfile({ profiles }: { profiles: CapitalProfileData[] }) {
  const [selectedId, setSelectedId] = useState<CapitalProfileData['id']>('small')
  const selected = profiles.find((profile) => profile.id === selectedId) ?? profiles[0]
  return (
    <section className="section" id="capital-profile">
      <div className="section-heading"><div><span className="section-index">05</span><h2>资金规模一变，市场优先级也会变</h2></div><p>“哪个市场更好”缺少资金规模和组合目标时，其实是一个信息不完整的问题。</p></div>
      <div className="segmented" role="group" aria-label="资金规模">
        {profiles.map((profile) => <button key={profile.id} className={selected.id === profile.id ? 'segmented__button segmented__button--active' : 'segmented__button'} onClick={() => setSelectedId(profile.id)}>{profile.label}</button>)}
      </div>
      <div className="capital-panel">
        <div className="capital-panel__lead"><span>MARKET FIT</span><h3>{selected.headline}</h3><p>{selected.explanation}</p></div>
        <div className="fit-bars">
          <div><span>Japan</span><div className="fit-track"><i style={{ width: `${selected.japanFit * 20}%` }} /></div><b>{selected.japanFit}/5</b></div>
          <div><span>Vietnam</span><div className="fit-track"><i style={{ width: `${selected.vietnamFit * 20}%` }} /></div><b>{selected.vietnamFit}/5</b></div>
        </div>
        <div className="capital-lists"><div><h4>优先策略</h4><ul>{selected.strategies.map((item) => <li key={item}>{item}</li>)}</ul></div><div><h4>最该盯的约束</h4><ul>{selected.constraints.map((item) => <li key={item}>{item}</li>)}</ul></div></div>
      </div>
    </section>
  )
}
