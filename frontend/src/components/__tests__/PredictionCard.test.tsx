import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import type { InferenceResponse } from '../../types/api'
import { PredictionCard } from '../PredictionCard'

// Recharts uses ResizeObserver which is not available in jsdom
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

const makePrediction = (overrides: Partial<InferenceResponse> = {}): InferenceResponse => ({
  prediction_label: 'benign',
  malicious_probability: 0.12,
  confidence: 0.88,
  risk_level: 'low',
  top_contributors: [
    { feature: 'src_bytes', impact: 1.0 },
    { feature: 'dst_bytes', impact: 0.6 },
  ],
  explain_method: 'heuristic',
  model_version: 'random_forest_v1',
  timestamp: '2024-01-15T10:00:00Z',
  ...overrides,
})

describe('PredictionCard', () => {
  it('renders placeholder when prediction is null', () => {
    render(<PredictionCard prediction={null} />)
    expect(screen.getByText('No prediction yet.')).toBeInTheDocument()
  })

  it('renders the prediction label', () => {
    render(<PredictionCard prediction={makePrediction()} />)
    expect(screen.getByText('benign')).toBeInTheDocument()
  })

  it('renders confidence as a percentage', () => {
    render(<PredictionCard prediction={makePrediction({ confidence: 0.876 })} />)
    expect(screen.getByText('87.60%')).toBeInTheDocument()
  })

  it('renders malicious probability as a percentage', () => {
    render(<PredictionCard prediction={makePrediction({ malicious_probability: 0.123 })} />)
    expect(screen.getByText('12.30%')).toBeInTheDocument()
  })

  it('renders the risk level (CSS uppercase class applied)', () => {
    render(<PredictionCard prediction={makePrediction({ risk_level: 'high' })} />)
    // DOM text is lowercase; CSS class "uppercase" handles the visual transform
    expect(screen.getByText('high')).toBeInTheDocument()
    const el = screen.getByText('high')
    expect(el.className).toMatch(/uppercase/)
  })

  it('renders critical risk level with red styling', () => {
    const { container } = render(
      <PredictionCard prediction={makePrediction({ risk_level: 'critical' })} />,
    )
    expect(screen.getByText('critical')).toBeInTheDocument()
    expect(container.innerHTML).toMatch(/red/)
  })

  it('renders medium risk level with yellow styling', () => {
    const { container } = render(
      <PredictionCard prediction={makePrediction({ risk_level: 'medium' })} />,
    )
    expect(screen.getByText('medium')).toBeInTheDocument()
    expect(container.innerHTML).toMatch(/yellow/)
  })

  it('displays the explain_method', () => {
    render(<PredictionCard prediction={makePrediction({ explain_method: 'feature_importance+sensitivity' })} />)
    expect(screen.getByText(/feature_importance\+sensitivity/)).toBeInTheDocument()
  })

  it('renders model version', () => {
    render(<PredictionCard prediction={makePrediction()} />)
    expect(screen.getByText('random_forest_v1')).toBeInTheDocument()
  })

  it('renders top contributors', () => {
    render(<PredictionCard prediction={makePrediction()} />)
    expect(screen.getByText(/src_bytes/)).toBeInTheDocument()
    expect(screen.getByText(/dst_bytes/)).toBeInTheDocument()
  })

  it('applies red/danger style for malicious prediction', () => {
    const { container } = render(
      <PredictionCard prediction={makePrediction({ prediction_label: 'malicious' })} />,
    )
    expect(container.innerHTML).toMatch(/red/)
  })

  it('applies green/emerald style for benign prediction', () => {
    const { container } = render(<PredictionCard prediction={makePrediction()} />)
    expect(container.innerHTML).toMatch(/emerald/)
  })

  it('renders "Detection Result" heading', () => {
    render(<PredictionCard prediction={makePrediction()} />)
    expect(screen.getByRole('heading', { name: 'Detection Result' })).toBeInTheDocument()
  })
})
