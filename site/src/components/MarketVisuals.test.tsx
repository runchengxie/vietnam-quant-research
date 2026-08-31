import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { AlphaToPnL } from './AlphaToPnL'
import { ArchitectureCompare } from './ArchitectureCompare'
import { MarketRadar } from './MarketRadar'
import { marketProfiles } from '../data/marketComparison'

describe('market visual explainers', () => {
  it('keeps radar dimensions visible as text', () => {
    render(<MarketRadar profiles={marketProfiles} />)
    expect(screen.getAllByText('流动性')).toHaveLength(2)
    expect(screen.getAllByText('行为低效').length).toBeGreaterThanOrEqual(2)
  })

  it('explains implementation haircut without invented bps performance claims', () => {
    const { container } = render(<AlphaToPnL />)
    expect(screen.getAllByText('Gross Alpha')).toHaveLength(2)
    expect(screen.getAllByText('Net Alpha')).toHaveLength(2)
    expect(container.textContent).not.toMatch(/\d+\s*bps|年化\s*\d+%/i)
  })

  it('shows both strategy pipelines end to end', () => {
    render(<ArchitectureCompare />)
    expect(screen.getByText('Residual Return Forecast')).toBeInTheDocument()
    expect(screen.getByText('Optional Index Futures Hedge')).toBeInTheDocument()
  })
})
