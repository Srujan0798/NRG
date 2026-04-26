import type { Meta, StoryObj } from '@storybook/react'
import PromptBlocked from './PromptBlocked'

const meta: Meta<typeof PromptBlocked> = {
  title: 'Components/PromptBlocked',
  component: PromptBlocked,
}

export default meta
type Story = StoryObj<typeof PromptBlocked>

export const SensitiveQuery: Story = {}
