import { ThemeToggle } from './ThemeToggle'

export function HeroComparison() {
  return (
    <header className="hero">
      <div className="hero__inner">
        <div className="hero__meta"><div className="eyebrow">QUANT MARKET FIT · JAPAN × VIETNAM · 2026-08-31</div><ThemeToggle /></div>
        <h1>同样是股票量化，两个市场需要两套策略 DNA</h1>
        <p className="hero__lede">
          这份研究面向不熟悉量化的读者，比较两个市场的策略适配度。核心问题是：哪些 alpha 值得研究，以及它们能否在真实交易中兑现。
        </p>
        <div className="hero-grid">
          <article className="market-card market-card--japan">
            <div className="market-card__topline"><span>JP</span><span>日本</span></div>
            <h2>弱信号，强工程</h2>
            <p className="formula">Small Alpha × Broad Universe × Long/Short × High Capacity</p>
            <p>更适合 market neutral、stat arb、ML cross-sectional 与大资金系统化管理。</p>
          </article>
          <article className="market-card market-card--vietnam">
            <div className="market-card__topline"><span>VN</span><span>越南</span></div>
            <h2>结构机会，低换手兑现</h2>
            <p className="formula">Structural Alpha × Smaller Universe × Long Bias × Lower Turnover</p>
            <p>更值得优先研究行为、资金流、流动性和 2 周–3 个月的中频择股。</p>
          </article>
        </div>
        <div className="hero__notice">评分属于研究判断，不代表收益预测、投资评级或已验证策略表现。</div>
      </div>
    </header>
  )
}
