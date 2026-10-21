import { useQueryClient } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { QueryClient } from '@tanstack/react-query'
import { useTheme } from 'styled-components'
import { expect, it, vi } from 'vitest'
import { GlobalStyles, theme } from '../design-system'
import { queryClient } from '../lib/queryClient'
import { AppProviders } from './AppProviders'

vi.mock('../design-system', () => import('../design-system/mocks'))

function Probe() {
  const client = useQueryClient()
  const currentTheme = useTheme()
  return (
    <>
      <p data-testid="client">
        {client === queryClient ? 'default' : 'custom'}
      </p>
      <p data-testid="theme">{currentTheme === theme ? 'theme' : 'other'}</p>
    </>
  )
}

it('renders children with the default query client, theme and global styles', () => {
  render(
    <AppProviders>
      <Probe />
    </AppProviders>,
  )
  expect(screen.getByTestId('client')).toHaveTextContent('default')
  expect(screen.getByTestId('theme')).toHaveTextContent('theme')
  expect(GlobalStyles).toHaveBeenCalled()
})

it('uses a query client passed as a prop', () => {
  render(
    <AppProviders client={new QueryClient()}>
      <Probe />
    </AppProviders>,
  )
  expect(screen.getByTestId('client')).toHaveTextContent('custom')
})
