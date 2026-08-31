const japan = ['市场数据', '特征构建', '横截面模型', '残差收益预测', '做多高分组，做空低分组', '风险中性化', '组合优化', '执行']
const vietnam = ['市场、资金流与行为数据', '动量、成交量、外资流、涨跌停与基本面', '横截面排序', '预测未来 10–40 个交易日', '做多高分组', '分批建仓', '低换手执行', '可选：指数期货对冲']

function Pipeline({ market, subtitle, steps }: { market: string; subtitle: string; steps: string[] }) {
  return <article className="pipeline"><div className="pipeline__head"><span>{market}</span><p>{subtitle}</p></div><ol>{steps.map((step, index) => <li key={step}><b>{String(index + 1).padStart(2, '0')}</b><span>{step}</span></li>)}</ol></article>
}

export function ArchitectureCompare() {
  return (
    <section className="section" id="architecture">
      <div className="section-heading"><div><span className="section-index">04</span><h2>两个市场，需要两套组合流程</h2></div><p>日本更重视风险中性和组合工程。越南更重视持有期、成交可实现性和低换手。</p></div>
      <div className="pipeline-grid"><Pipeline market="日本" subtitle="横截面选股与市场中性" steps={japan} /><Pipeline market="越南" subtitle="行为因子、横截面选股与中期偏多" steps={vietnam} /></div>
    </section>
  )
}
