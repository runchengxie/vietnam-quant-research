import { describe, expect, it } from 'vitest'
import { evidence } from './evidence'
import { capitalProfiles, marketProfiles, strategyFits } from './marketComparison'

const evidenceIds = new Set(evidence.map((item) => item.id))

describe('market comparison data contract', () => {
  it('keeps every strategy score on the approved 1-5 research-judgment scale', () => {
    expect(strategyFits).toHaveLength(10)
    for (const row of strategyFits) {
      expect(row.japan).toBeGreaterThanOrEqual(1)
      expect(row.japan).toBeLessThanOrEqual(5)
      expect(row.vietnam).toBeGreaterThanOrEqual(1)
      expect(row.vietnam).toBeLessThanOrEqual(5)
    }
  })

  it('links every strategy row to known evidence', () => {
    for (const row of strategyFits) {
      expect(row.evidenceIds.length).toBeGreaterThan(0)
      for (const id of row.evidenceIds) expect(evidenceIds.has(id)).toBe(true)
    }
  })

  it('keeps evidence typed and excludes private strategy URLs or performance claims', () => {
    for (const item of evidence) {
      expect(['fact', 'judgment', 'implementation']).toContain(item.type)
      expect(item.summary.length).toBeGreaterThan(20)
      expect(item.sourceUrl ?? '').not.toContain('guan-japanese-nira')
      expect(item.summary).not.toMatch(/sharpe|annualized return|年化收益|实盘收益/i)
    }
  })

  it('provides both market profiles and all three capital profiles', () => {
    expect(marketProfiles.map((profile) => profile.id)).toEqual(['japan', 'vietnam'])
    expect(capitalProfiles.map((profile) => profile.id)).toEqual(['small', 'medium', 'institutional'])
  })
})
