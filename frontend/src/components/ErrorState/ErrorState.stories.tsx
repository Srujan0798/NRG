import type { Meta, StoryObj } from '@storybook/react'
import { ErrorState } from './ErrorState'
import { t } from '../../i18n'

const meta = {
  title: 'Demo/ErrorState',
  component: ErrorState,
} satisfies Meta<typeof ErrorState>

export default meta
type Story = StoryObj<typeof meta>

export const Restricted: Story = {
  args: {
    severity: 'warning',
    message: t('errors.restricted'),
    onRetry: () => console.info('restricted retry'),
  },
}

export const Sensitive: Story = {
  args: {
    severity: 'error',
    message: t('errors.sensitive'),
    onGoHome: () => console.info('sensitive go home'),
  },
}

export const Critical: Story = {
  args: {
    severity: 'critical',
    message: t('errors.generic'),
    errorCode: 'DEMO-TRACE-HIDDEN',
    onRetry: () => console.info('critical retry'),
  },
}
