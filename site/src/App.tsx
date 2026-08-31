import { AlphaToPnL } from './components/AlphaToPnL'
import { ArchitectureCompare } from './components/ArchitectureCompare'
import { CapitalProfile } from './components/CapitalProfile'
import { HeroComparison } from './components/HeroComparison'
import { MarketRadar } from './components/MarketRadar'
import { MaturityCompare } from './components/MaturityCompare'
import { Methodology } from './components/Methodology'
import { StrategyHeatmap } from './components/StrategyHeatmap'
import { evidence } from './data/evidence'
import { capitalProfiles, marketProfiles, strategyFits } from './data/marketComparison'

export function App() {
  return (
    <main>
      <HeroComparison />
      <div className="page-shell">
        <StrategyHeatmap rows={strategyFits} evidence={evidence} />
        <MarketRadar profiles={marketProfiles} />
        <AlphaToPnL />
        <ArchitectureCompare />
        <CapitalProfile profiles={capitalProfiles} />
        <MaturityCompare />
        <Methodology evidence={evidence} />
      </div>
    </main>
  )
}
