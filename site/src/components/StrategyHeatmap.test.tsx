import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { StrategyHeatmap } from './StrategyHeatmap'
import { evidence } from '../data/evidence'
import { strategyFits } from '../data/marketComparison'

describe('StrategyHeatmap', () => {
  it('filters rows by category and exposes accessible market scores', () => {
    render(<StrategyHeatmap rows={strategyFits} evidence={evidence} />)
    expect(screen.getByLabelText('日频高换手因子，日本适配度 5 / 5')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '组合结构' }))
    expect(screen.getByText('Long-short market neutral')).toBeInTheDocument()
    expect(screen.queryByText('行为金融 / 资金流')).not.toBeInTheDocument()
  })

  it('opens evidence detail from a strategy row', () => {
    render(<StrategyHeatmap rows={strategyFits} evidence={evidence} />)
    fireEvent.click(screen.getByRole('button', { name: /查看 Long-short market neutral 的依据/ }))
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByText(/RESEARCH JUDGMENT/)).toBeInTheDocument()
  })
})
