import type { Meta, StoryObj } from '@storybook/react'
import { ScaleStrip } from './ScaleStrip'

const meta = {
  title: 'Production/ScaleStrip',
  component: ScaleStrip,
} satisfies Meta<typeof ScaleStrip>

export default meta
type Story = StoryObj<typeof meta>

export const Animated: Story = {}
