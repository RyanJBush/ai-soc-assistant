import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { StatusBanner } from '../StatusBanner'

describe('StatusBanner', () => {
  it('renders the message text', () => {
    render(<StatusBanner kind="info" message="System initialising" />)
    expect(screen.getByText('System initialising')).toBeInTheDocument()
  })

  it('applies error styles for kind=error', () => {
    const { container } = render(<StatusBanner kind="error" message="Something went wrong" />)
    const el = container.firstChild as HTMLElement
    expect(el.className).toMatch(/red/)
  })

  it('applies success styles for kind=success', () => {
    const { container } = render(<StatusBanner kind="success" message="Done!" />)
    const el = container.firstChild as HTMLElement
    expect(el.className).toMatch(/emerald/)
  })

  it('applies neutral styles for kind=info', () => {
    const { container } = render(<StatusBanner kind="info" message="Note" />)
    const el = container.firstChild as HTMLElement
    expect(el.className).toMatch(/slate/)
  })

  it('renders inside a div element', () => {
    const { container } = render(<StatusBanner kind="info" message="hi" />)
    expect(container.firstChild?.nodeName).toBe('DIV')
  })
})
