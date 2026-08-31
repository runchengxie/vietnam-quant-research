const japan = ['Market Data', 'Features', 'Cross-sectional Model', 'Residual Return Forecast', 'Long Top / Short Bottom', 'Risk Neutralization', 'Optimizer', 'Execution']
const vietnam = ['Market + Flow + Behavior', 'Momentum / Volume / Foreign Flow / Limit / Fundamentals', 'Cross-sectional Ranking', '10–40D Forecast', 'Long Top Bucket', 'Staggered Portfolio', 'Low-turnover Execution', 'Optional Index Futures Hedge']

function Pipeline({ market, subtitle, steps }: { market: string; subtitle: string; steps: string[] }) {
  return <article className="pipeline"><div className="pipeline__head"><span>{market}</span><p>{subtitle}</p></div><ol>{steps.map((step, index) => <li key={step}><b>{String(index + 1).padStart(2, '0')}</b><span>{step}</span></li>)}</ol></article>
}

export function ArchitectureCompare() {
  return (
    <section className="section" id="architecture">
      <div className="section-heading"><div><span className="section-index">04</span><h2>同一个研究团队，也应该搭两套组合机器</h2></div><p>日本侧把风险中性和组合工程放在核心；越南侧把信号持有期、成交可实现性和低换手放在核心。</p></div>
      <div className="pipeline-grid"><Pipeline market="JAPAN" subtitle="Cross-sectional + market neutral" steps={japan} /><Pipeline market="VIETNAM" subtitle="Behavioral cross-sectional + medium-term long bias" steps={vietnam} /></div>
    </section>
  )
}
