import type { Meta, StoryObj } from '@storybook/react'
import { EmptyState } from './EmptyState'
import { t } from '../../i18n'

const meta = {
  title: 'Demo/EmptyState',
  component: EmptyState,
} satisfies Meta<typeof EmptyState>

export default meta
type Story = StoryObj<typeof meta>

export const NoData: Story = {
  args: {
    title: t('empty.noData.headline'),
    body: t('empty.noData.body'),
    primaryLabel: t('empty.noData.cta'),
    onPrimary: () => console.info('empty primary action'),
  },
}

export const NoAuditEvents: Story = {
  args: {
    title: t('empty.noAuditEvents.headline'),
    body: t('empty.noAuditEvents.body'),
    primaryLabel: t('empty.noAuditEvents.cta'),
    onPrimary: () => console.info('empty audit action'),
  },
}
