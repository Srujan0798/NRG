import type { Meta, StoryObj } from '@storybook/react'
import SearchBar from './SearchBar'
import { heroCopy } from '../i18n/hero-copy'

const meta = {
  title: 'Production/SearchBar',
  component: SearchBar,
  args: {
    placeholderRotation: heroCopy.placeholders,
    onSubmit: (_query: string) => undefined,
  },
} satisfies Meta<typeof SearchBar>

export default meta
type Story = StoryObj<typeof meta>

export const Ready: Story = {}

export const Disabled: Story = {
  args: {
    disabled: true,
  },
}
