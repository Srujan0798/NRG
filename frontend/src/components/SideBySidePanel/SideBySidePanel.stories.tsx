import type { Meta, StoryObj } from '@storybook/react'
import SideBySidePanel from './SideBySidePanel'

const meta: Meta<typeof SideBySidePanel> = {
  title: 'Components/SideBySidePanel',
  component: SideBySidePanel,
}

export default meta
type Story = StoryObj<typeof SideBySidePanel>

export const Default: Story = {}
