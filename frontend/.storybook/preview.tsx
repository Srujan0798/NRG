import type { Preview } from '@storybook/react'
import '../src/index.css'

const preview: Preview = {
  parameters: {
    a11y: {
      element: '#storybook-root',
    },
  },
}

export default preview
