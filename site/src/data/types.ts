export type EvidenceType = 'fact' | 'judgment' | 'implementation'

export type StrategyCategory = 'frequency' | 'portfolio' | 'model' | 'alpha' | 'capacity'

export interface StrategyFit {
  id: string
  label: string
  japan: number
  vietnam: number
  verdict: string
  category: StrategyCategory
  japanRationale: string
  vietnamRationale: string
  evidenceIds: string[]
}

export interface Evidence {
  id: string
  type: EvidenceType
  title: string
  summary: string
  sourceName?: string
  sourceUrl?: string
  asOf?: string
  note?: string
}

export interface RadarScore {
  id: string
  label: string
  score: number
}

export interface MarketProfile {
  id: 'japan' | 'vietnam'
  label: string
  thesis: string
  scores: RadarScore[]
}

export interface CapitalProfile {
  id: 'small' | 'medium' | 'institutional'
  label: string
  headline: string
  explanation: string
  japanFit: number
  vietnamFit: number
  strategies: string[]
  constraints: string[]
}
