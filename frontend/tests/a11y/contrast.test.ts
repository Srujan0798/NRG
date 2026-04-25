import { ratio } from 'wcag-color'
import { colors } from '../../src/design-system/tokens/colors'

const AA_NORMAL_TEXT = 4.5
const UI_COMPONENT = 3

const textCombos = [
  ['light ink on surface', colors.role.ink.light, colors.role.surface1.light],
  ['light muted on surface', colors.role.inkMuted.light, colors.role.surface1.light],
  ['light danger on surface', colors.role.danger.light, colors.role.surface1.light],
  ['light warning on surface', colors.role.warning.light, colors.role.surface1.light],
  ['light success on surface', colors.role.success.light, colors.role.surface1.light],
  ['light tier 1 on surface', colors.role.tier1.light, colors.role.surface1.light],
  ['light tier 2 on surface', colors.role.tier2.light, colors.role.surface1.light],
  ['light tier 3 on surface', colors.role.tier3.light, colors.role.surface1.light],
  ['dark ink on surface', colors.role.ink.dark, colors.role.surface1.dark],
  ['dark muted on surface', colors.role.inkMuted.dark, colors.role.surface1.dark],
  ['dark danger on surface', colors.role.danger.dark, colors.role.surface1.dark],
  ['dark warning on surface', colors.role.warning.dark, colors.role.surface1.dark],
  ['dark success on surface', colors.role.success.dark, colors.role.surface1.dark],
  ['dark tier 1 on surface', colors.role.tier1.dark, colors.role.surface1.dark],
  ['dark tier 2 on surface', colors.role.tier2.dark, colors.role.surface1.dark],
  ['dark tier 3 on surface', colors.role.tier3.dark, colors.role.surface1.dark],
] as const

const uiCombos = [
  ['light focus ring on surface', colors.role.focus.light, colors.role.surface1.light],
  ['dark focus ring on surface', colors.role.focus.dark, colors.role.surface1.dark],
  ['light border against surface', colors.role.border.light, colors.role.surface1.light],
  ['dark border against surface', colors.role.border.dark, colors.role.surface1.dark],
] as const

describe('WCAG token contrast', () => {
  it.each(textCombos)('%s meets AA normal text contrast', (_name, foreground, background) => {
    expect(ratio(foreground, background)).toBeGreaterThanOrEqual(AA_NORMAL_TEXT)
  })

  it.each(uiCombos)('%s meets non-text contrast', (_name, foreground, background) => {
    expect(ratio(foreground, background)).toBeGreaterThanOrEqual(UI_COMPONENT)
  })
})
