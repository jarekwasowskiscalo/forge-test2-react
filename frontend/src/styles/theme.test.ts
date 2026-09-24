import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

import { describe, expect, it } from 'vitest'

/**
 * A fitness function for the palette, held as code because prose did not hold it.
 *
 * Tailwind generates a `text-<name>` utility from every `--color-<name>` in
 * `@theme`. The scale it ships already has `text-xs` … `text-7xl` as **font
 * sizes**, so a colour token called `base` produced two rules named `.text-base`
 * -- and the colour one won. Every `text-base` on a white card therefore painted
 * white on white: the body of every entry and the title of `ErrorState`
 * were invisible, in the build, with nothing failing anywhere.
 *
 * It took a screenshot to notice, which is exactly the class of defect a check
 * like this exists to catch before a screenshot is taken.
 */

const THEME = readFileSync(fileURLToPath(new URL('./theme.css', import.meta.url)), 'utf8')

/**
 * Tailwind's own font-size scale. Written out rather than imported: the point is
 * to compare this project's names against the framework's, and importing the
 * framework's list from the framework would make the check agree with whatever
 * the framework currently thinks -- including after a rename that reintroduces
 * the collision.
 */
const TAILWIND_TEXT_SIZES = [
  'xs',
  'sm',
  'base',
  'lg',
  'xl',
  '2xl',
  '3xl',
  '4xl',
  '5xl',
  '6xl',
  '7xl',
  '8xl',
  '9xl',
]

/** Every `--color-<name>` the theme declares. */
function colourTokens(): string[] {
  return [...THEME.matchAll(/^\s*--color-([a-z0-9-]+):/gm)].map((match) => match[1]!)
}

describe('the palette', () => {
  it('declares some colours at all, so the checks below are not vacuous', () => {
    expect(colourTokens()).toContain('ink')
    expect(colourTokens()).toContain('accent')
  })

  it('names no colour after a Tailwind font size', () => {
    const shadowing = colourTokens().filter((name) => TAILWIND_TEXT_SIZES.includes(name))

    expect(shadowing).toEqual([])
  })

  it('has no `[data-theme=...]` block, because there is one palette', () => {
    // Not a style preference: `spec/design/ui/system-states.md` § One palette
    // retired the dark theme with the top bar that switched it. A second block
    // appearing here without that document changing is a theme nothing can turn
    // on and nobody can see.
    expect(THEME).not.toContain('data-theme')
  })
})
