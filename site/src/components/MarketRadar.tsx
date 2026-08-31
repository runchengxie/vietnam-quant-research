import * as echarts from 'echarts'
import { useEffect, useRef } from 'react'
import type { MarketProfile } from '../data/types'

export function MarketRadar({ profiles }: { profiles: MarketProfile[] }) {
  const chartRef = useRef<HTMLDivElement>(null)
  const japan = profiles.find((profile) => profile.id === 'japan')!
  const vietnam = profiles.find((profile) => profile.id === 'vietnam')!

  useEffect(() => {
    if (!chartRef.current || navigator.userAgent.toLowerCase().includes('jsdom')) return
    const chart = echarts.init(chartRef.current, undefined, { renderer: 'svg' })
    chart.setOption({
      tooltip: {},
      legend: { data: [japan.label, vietnam.label], bottom: 0, textStyle: { color: '#9ca7b8' } },
      radar: {
        radius: '64%',
        indicator: japan.scores.map((item) => ({ name: item.label, max: 5 })),
        axisName: { color: '#b7c0cf', fontSize: 12 },
        splitNumber: 5,
      },
      series: [{
        type: 'radar',
        data: [
          { value: japan.scores.map((item) => item.score), name: japan.label },
          { value: vietnam.scores.map((item) => item.score), name: vietnam.label },
        ],
      }],
    })
    const resize = () => chart.resize()
    window.addEventListener('resize', resize)
    return () => { window.removeEventListener('resize', resize); chart.dispose() }
  }, [japan, vietnam])

  return (
    <section className="section" id="market-structure">
      <div className="section-heading">
        <div><span className="section-index">02</span><h2>市场结构雷达</h2></div>
        <p>成熟度与低效程度往往此消彼长。雷达图刻意把“好交易”和“有低效”放在同一张图里。</p>
      </div>
      <div className="radar-layout">
        <div ref={chartRef} className="radar-chart" aria-hidden="true" />
        <div className="radar-copy">
          {profiles.map((profile) => (
            <article key={profile.id} className={`thesis-card thesis-card--${profile.id}`}>
              <span>{profile.label}</span><h3>{profile.thesis}</h3>
              <dl>{profile.scores.map((item) => <div key={item.id}><dt>{item.label}</dt><dd>{item.score}/5</dd></div>)}</dl>
            </article>
          ))}
          <p className="micro-note">流动性 · 做空可用性 · 股票池广度 · 数据质量 · 策略容量 · 执行基础设施 · <strong>行为低效</strong> · 资金流信号机会</p>
        </div>
      </div>
    </section>
  )
}
