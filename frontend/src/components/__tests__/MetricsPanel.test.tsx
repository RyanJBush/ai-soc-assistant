import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import type { ModelInfoResponse } from '../../types/api'
import { MetricsPanel } from '../MetricsPanel'

// Recharts uses ResizeObserver + SVG layout which is unavailable in jsdom.
// Replace the entire library with lightweight stubs.
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  BarChart: ({ children }: { children: React.ReactNode }) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
}))

const makeModelInfo = (overrides: Partial<ModelInfoResponse> = {}): ModelInfoResponse => ({
  model_name: 'random_forest',
  model_version: 'random_forest',
  selected_features: ['duration', 'src_bytes'],
  training_rows: 5000,
  test_rows: 1000,
  metrics: {
    precision: 0.95,
    recall: 0.93,
    f1_score: 0.94,
    roc_auc: 0.98,
    false_positive_rate: 0.02,
  },
  ...overrides,
})

describe('MetricsPanel', () => {
  it('renders empty state when modelInfo is null', () => {
    render(<MetricsPanel modelInfo={null} />)
    expect(screen.getByText('No model metrics loaded.')).toBeInTheDocument()
  })

  it('renders the section heading', () => {
    render(<MetricsPanel modelInfo={makeModelInfo()} />)
    expect(screen.getByRole('heading', { name: 'Model Performance' })).toBeInTheDocument()
  })

  it('renders model name', () => {
    render(<MetricsPanel modelInfo={makeModelInfo()} />)
    expect(screen.getByText(/random_forest/)).toBeInTheDocument()
  })

  it('renders training row count', () => {
    render(<MetricsPanel modelInfo={makeModelInfo()} />)
    expect(screen.getByText(/5000/)).toBeInTheDocument()
  })

  it('renders test row count', () => {
    render(<MetricsPanel modelInfo={makeModelInfo()} />)
    expect(screen.getByText(/1000/)).toBeInTheDocument()
  })

  it('renders the bar chart element', () => {
    render(<MetricsPanel modelInfo={makeModelInfo()} />)
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument()
  })
})
