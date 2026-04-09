import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { RiskBadge, StatusBadge } from '../AlertBadges'

describe('StatusBadge', () => {
  it('renders "new" status', () => {
    render(<StatusBadge status="new" />)
    expect(screen.getByText('new')).toBeInTheDocument()
  })

  it('renders "acknowledged" status', () => {
    render(<StatusBadge status="acknowledged" />)
    expect(screen.getByText('acknowledged')).toBeInTheDocument()
  })

  it('renders "escalated" status with amber class', () => {
    const { container } = render(<StatusBadge status="escalated" />)
    expect(container.firstChild).toHaveClass('bg-amber-900')
  })

  it('renders "resolved" status with emerald class', () => {
    const { container } = render(<StatusBadge status="resolved" />)
    expect(container.firstChild).toHaveClass('bg-emerald-900')
  })
})

describe('RiskBadge', () => {
  it('renders "low" risk', () => {
    render(<RiskBadge risk="low" />)
    expect(screen.getByText('low')).toBeInTheDocument()
  })

  it('renders "high" risk with red class', () => {
    const { container } = render(<RiskBadge risk="high" />)
    expect(container.firstChild).toHaveClass('bg-red-900')
  })

  it('renders unknown risk with fallback class', () => {
    const { container } = render(<RiskBadge risk="critical" />)
    expect(container.firstChild).toHaveClass('bg-slate-700')
  })
})
