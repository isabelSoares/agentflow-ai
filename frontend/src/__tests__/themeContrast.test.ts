import { describe, expect, it } from 'vitest'

function channel(value: string): number {
  const c = parseInt(value, 16) / 255
  return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4
}

function luminance(hex: string): number {
  const hex6 = hex.replace('#', '')
  const r = channel(hex6.slice(0, 2))
  const g = channel(hex6.slice(2, 4))
  const b = channel(hex6.slice(4, 6))
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}

function contrastRatio(foreground: string, background: string): number {
  const [l1, l2] = [luminance(foreground), luminance(background)]
  return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05)
}

const AA_NORMAL_TEXT = 4.5

const PALETTES = {
  light: {
    bg: '#f4f0e8',
    panelStrong: '#fffdf8',
    text: '#17262b',
    muted: '#53676a',
    mutedStrong: '#3d5357',
    accent: '#155e63',
    accent2: '#243b53',
    warning: '#7a6110',
    danger: '#b3402e',
    onAccent: '#fffdf8',
  },
  dark: {
    bg: '#17262b',
    panelStrong: '#20383d',
    text: '#f4f0e8',
    muted: '#c4d0d0',
    mutedStrong: '#dfe7e7',
    accent: '#63b3b5',
    accent2: '#f2c94c',
    warning: '#f2c94c',
    danger: '#ff8fa0',
    onAccent: '#17262b',
  },
} as const

describe('theme color contrast (WCAG AA, normal text >= 4.5:1)', () => {
  for (const [mode, palette] of Object.entries(PALETTES)) {
    describe(`${mode} mode`, () => {
      const pairs: Array<[string, string, string]> = [
        ['text on background', palette.text, palette.bg],
        ['muted on background', palette.muted, palette.bg],
        ['muted-strong on background', palette.mutedStrong, palette.bg],
        ['muted on panel', palette.muted, palette.panelStrong],
        ['accent on background', palette.accent, palette.bg],
        ['accent-2 on background', palette.accent2, palette.bg],
        ['warning on background', palette.warning, palette.bg],
        ['danger on background', palette.danger, palette.bg],
        ['on-accent on accent', palette.onAccent, palette.accent],
        ['on-accent on accent-2', palette.onAccent, palette.accent2],
      ]

      for (const [label, fg, bg] of pairs) {
        it(`${label}: ${contrastRatio(fg, bg).toFixed(2)}:1`, () => {
          expect(contrastRatio(fg, bg)).toBeGreaterThanOrEqual(AA_NORMAL_TEXT)
        })
      }
    })
  }
})
