import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { TrafficInputForm } from '../TrafficInputForm'

describe('TrafficInputForm', () => {
  it('renders the form heading', () => {
    render(<TrafficInputForm onSubmit={vi.fn()} loading={false} />)
    expect(screen.getByRole('heading', { name: 'Traffic Feature Input' })).toBeInTheDocument()
  })

  it('renders the submit button with default text', () => {
    render(<TrafficInputForm onSubmit={vi.fn()} loading={false} />)
    expect(screen.getByRole('button', { name: 'Run Detection' })).toBeInTheDocument()
  })

  it('shows loading text when loading=true', () => {
    render(<TrafficInputForm onSubmit={vi.fn()} loading={true} />)
    expect(screen.getByRole('button', { name: 'Running Detection...' })).toBeInTheDocument()
  })

  it('disables the button while loading', () => {
    render(<TrafficInputForm onSubmit={vi.fn()} loading={true} />)
    expect(screen.getByRole('button')).toBeDisabled()
  })

  it('enables the button when not loading', () => {
    render(<TrafficInputForm onSubmit={vi.fn()} loading={false} />)
    expect(screen.getByRole('button')).toBeEnabled()
  })

  it('renders the Protocol select with default value tcp', () => {
    render(<TrafficInputForm onSubmit={vi.fn()} loading={false} />)
    const select = screen.getByRole('combobox')
    expect(select).toHaveValue('tcp')
  })

  it('renders Source Bytes input', () => {
    render(<TrafficInputForm onSubmit={vi.fn()} loading={false} />)
    expect(screen.getByLabelText(/Source Bytes/i)).toBeInTheDocument()
  })

  it('renders Destination Bytes input', () => {
    render(<TrafficInputForm onSubmit={vi.fn()} loading={false} />)
    expect(screen.getByLabelText(/Destination Bytes/i)).toBeInTheDocument()
  })

  it('renders Error Rate input', () => {
    render(<TrafficInputForm onSubmit={vi.fn()} loading={false} />)
    expect(screen.getByLabelText(/Error Rate/i)).toBeInTheDocument()
  })

  it('calls onSubmit with form payload when submitted', async () => {
    const user = userEvent.setup()
    const handleSubmit = vi.fn().mockResolvedValue(undefined)

    render(<TrafficInputForm onSubmit={handleSubmit} loading={false} />)

    await user.click(screen.getByRole('button', { name: 'Run Detection' }))

    expect(handleSubmit).toHaveBeenCalledOnce()
    const payload = handleSubmit.mock.calls[0][0]
    expect(payload).toMatchObject({
      protocol_type: 'tcp',
      service: 'http',
      flag: 'SF',
    })
  })

  it('updates protocol_type when a different option is selected', async () => {
    const user = userEvent.setup()
    const handleSubmit = vi.fn().mockResolvedValue(undefined)

    render(<TrafficInputForm onSubmit={handleSubmit} loading={false} />)

    await user.selectOptions(screen.getByRole('combobox'), 'udp')
    await user.click(screen.getByRole('button', { name: 'Run Detection' }))

    const payload = handleSubmit.mock.calls[0][0]
    expect(payload.protocol_type).toBe('udp')
  })
})
