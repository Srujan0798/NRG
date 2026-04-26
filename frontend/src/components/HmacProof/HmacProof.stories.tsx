import type { Meta, StoryObj } from '@storybook/react'
import HmacProof from './HmacProof'

const meta: Meta<typeof HmacProof> = {
  title: 'Components/HmacProof',
  component: HmacProof,
  args: {
    auditEventId: 'hmac-release-001',
  },
}

export default meta
type Story = StoryObj<typeof HmacProof>

export const Default: Story = {}
