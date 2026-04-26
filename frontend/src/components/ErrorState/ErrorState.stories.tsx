import type { Meta, StoryObj } from '@storybook/react'
import { ErrorState } from './ErrorState'
import { t } from '../../i18n'

const meta = {
  title: 'Production/ErrorState',
  component: ErrorState,
} satisfies Meta<typeof ErrorState>

export default meta
type Story = StoryObj<typeof meta>

export const Restricted: Story = {
  args: {
    severity: 'warning',
    message: t('errors.restricted'),
    onRetry: () => undefined,
  },
}

export const Sensitive: Story = {
  args: {
    severity: 'error',
    message: t('errors.sensitive'),
    onGoHome: () => undefined,
  },
}

export const Critical: Story = {
  args: {
    severity: 'critical',
    message: t('errors.generic'),
    errorCode: 'TRACE-HIDDEN',
    onRetry: () => undefined,
  },
}
