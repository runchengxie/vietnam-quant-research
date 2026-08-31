export function HeroComparison() {
  return (
    <header className="hero">
      <div className="hero__inner">
        <div className="eyebrow">QUANT MARKET FIT · JAPAN × VIETNAM · 2026-08-31</div>
        <h1>同样是股票量化，两个市场需要两套策略 DNA</h1>
        <p className="hero__lede">
          这是一份面向非量化客户的策略适配度研究。重点不是猜哪个市场涨得更多，而是解释什么 alpha 更可能存在，以及这些 alpha 能不能在真实交易里兑现。
        </p>
        <div className="hero-grid">
          <article className="market-card market-card--japan">
            <div className="market-card__topline"><span>JP</span><span>Japan</span></div>
            <h2>弱信号，强工程</h2>
            <p className="formula">Small Alpha × Broad Universe × Long/Short × High Capacity</p>
            <p>更适合 market neutral、stat arb、ML cross-sectional 与大资金系统化管理。</p>
          </article>
          <article className="market-card market-card--vietnam">
            <div className="market-card__topline"><span>VN</span><span>Vietnam</span></div>
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
