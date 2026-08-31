import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { CapitalProfile } from './CapitalProfile'
import { MaturityCompare } from './MaturityCompare'
import { Methodology } from './Methodology'
import { capitalProfiles } from '../data/marketComparison'
import { evidence } from '../data/evidence'

describe('client explainers', () => {
  it('switches capital profile recommendations', () => {
    render(<CapitalProfile profiles={capitalProfiles} />)
    fireEvent.click(screen.getByRole('button', { name: '机构 / 大资金' }))
    expect(screen.getByText(/日本优势显著/)).toBeInTheDocument()
  })

  it('states the Vietnam research gate and the Japan private-strategy boundary', () => {
    render(<MaturityCompare />)
    expect(screen.getByText(/越南.*研究门槛.*尚未/i)).toBeInTheDocument()
    expect(screen.getByText(/日本.*私有策略.*收益/i)).toBeInTheDocument()
  })

  it('renders official methodology sources as links', () => {
    render(<Methodology evidence={evidence} />)
    expect(screen.getByRole('link', { name: /JPX Short Selling Restrictions/ })).toHaveAttribute('href', expect.stringContaining('jpx.co.jp'))
    expect(screen.getByRole('link', { name: /VSDC Securities lending and borrowing/ })).toHaveAttribute('href', expect.stringContaining('vsdc.vn'))
  })
})
