"""What the browser actually computed, and what that means for contrast.

This module exists because the two properties this suite has to assert about are
invisible to every other room in the repository. `frontend/vitest.config.ts` runs
the component suite in jsdom, where the application's CSS is never loaded, `@layer`
is not implemented at all and `element.matches(':focus-visible')` is not supported --
so the cascade question "which layer won" cannot even be posed there. And
`frontend/src/styles/theme.test.ts` reads `theme.css` as *text*: it checks the names
of tokens, never their values and never where they are painted. A check for the
presence of `:focus-visible` in the source would pass on a screen whose focus ring
is entirely invisible, which is precisely the defect that produced this module.

**Everything here reads the page and computes; nothing here knows a colour.** A
contrast test that compares a value from the DOM against a hex constant copied out
of `theme.css` is a test of the copy. The background comes from the ancestor that
actually paints one, found by walking up the tree -- because a token list cannot say
which surface a given piece of text ended up on, and that is the whole question.

The arithmetic is WCAG 2.1's, written out rather than pulled in: relative luminance
(§ dfn-relative-luminance) and the contrast ratio (§ dfn-contrast-ratio). It is
fifteen lines, and a dependency for fifteen lines would have to be installed in the
`e2e` group, locked, and kept -- for arithmetic that has not changed since 2008.

Imports `playwright` and nothing else first-party: `tests/fitness/test_e2e_isolation.py`
allows `e2e/` to reach its own tree and no further, and `tests/fitness/test_ui_suite.py`
allows `playwright` under `e2e/ui/` and nowhere else. Both stay satisfied.
"""

import re
from typing import Final

from playwright.sync_api import Locator, Page

#: AA for body text (WCAG 2.1, success criterion 1.4.3). The large-text floor of
#: 3:1 is deliberately not offered: the sites this suite measures are 12px and
#: 13px, so an exemption by size would be an exemption nothing here qualifies for.
AA_NORMAL_TEXT: Final[float] = 4.5

#: `rgb(155, 151, 140)` and `rgba(155, 151, 140, 0.5)` -- the two shapes
#: `getComputedStyle` returns for a colour in Chromium. The alpha is captured
#: because a transparent background is the signal to keep walking up.
_RGB: Final = re.compile(r"rgba?\(\s*(\d+)[,\s]+(\d+)[,\s]+(\d+)\s*(?:[,/]\s*([\d.]+)\s*)?\)")

#: Walk up from the element until something paints. A background-color with an
#: alpha of 0 -- which is what `bg-transparent` and the initial value both compute
#: to -- is not a background; it is a hole through which the ancestor shows. The
#: walk ends at the documentElement, whose background is the page's own.
_PAINTED_BACKGROUND: Final[str] = """
(element) => {
  let node = element
  while (node) {
    const background = getComputedStyle(node).backgroundColor
    const match = background.match(/rgba?\\(\\s*\\d+[,\\s]+\\d+[,\\s]+\\d+\\s*(?:[,/]\\s*([\\d.]+)\\s*)?\\)/)
    const alpha = match && match[1] !== undefined ? parseFloat(match[1]) : 1
    if (alpha > 0) return background
    node = node.parentElement
  }
  return getComputedStyle(document.documentElement).backgroundColor
}
"""


def parse_rgb(value: str) -> tuple[int, int, int]:
    """The three channels of a computed colour.

    Raises rather than guessing: a colour the browser expressed in a form this
    does not read is a measurement that did not happen, and a default would turn
    it into a number somebody would believe.
    """
    found = _RGB.search(value)
    if found is None:
        raise ValueError(f"not an rgb() colour the browser produced: {value!r}")
    return int(found.group(1)), int(found.group(2)), int(found.group(3))


def relative_luminance(rgb: tuple[int, int, int]) -> float:
    """WCAG 2.1 § dfn-relative-luminance, on 8-bit sRGB channels."""
    channels = []
    for raw in rgb:
        value = raw / 255
        channels.append(value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4)
    red, green, blue = channels
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(foreground: str, background: str) -> float:
    """WCAG 2.1 § dfn-contrast-ratio, from two computed colours."""
    first = relative_luminance(parse_rgb(foreground))
    second = relative_luminance(parse_rgb(background))
    lighter, darker = max(first, second), min(first, second)
    return (lighter + 0.05) / (darker + 0.05)


def computed(locator: Locator, name: str, *, pseudo: str | None = None) -> str:
    """One computed property of the first match, optionally of a pseudo-element.

    `::placeholder` is why the pseudo argument exists: it carries the only label
    the composer's fields have, and its colour is reachable no other way.
    """
    return str(
        locator.first.evaluate(
            "(element, [property, selector]) => getComputedStyle(element, selector)"
            ".getPropertyValue(property)",
            [name, pseudo],
        )
    )


def painted_background(locator: Locator) -> str:
    """The background of the nearest ancestor that actually paints one.

    Read from the tree rather than assumed from the token the component names:
    which surface a piece of text ends up on is a property of where it was placed,
    and a test that takes it from a list is asserting its own assumption.
    """
    return str(locator.first.evaluate(_PAINTED_BACKGROUND))


def text_contrast(locator: Locator, *, pseudo: str | None = None) -> float:
    """The contrast of an element's text against the surface it is painted on."""
    return contrast_ratio(
        computed(locator, "color", pseudo=pseudo),
        painted_background(locator),
    )


def focus_ring_of_active_element(page: Page) -> dict[str, object]:
    """Everything the focus-ring assertion needs, in one round trip.

    The three facts travel together because the defect this suite was written for
    splits them: the utility that broke the ring cancels `outline-style` and leaves
    `outline-width` at the 2px the base rule set, so a test that read only the width
    would have passed on a screen with no ring at all.

    **`where` is built from attributes, never from `textContent`.** It ends up in an
    assertion message, and a focused element's text is whatever the guestbook happens
    to hold -- the one thing this suite's artefact policy keeps out of a report
    (Article XI, `e2e/ui/conftest.py`). An `aria-label`, a `name` or a `placeholder`
    is the author's own word for the control, which is a selector rather than a
    value; where none of them is set, the tag and the stop's position in the walk
    are what the reader gets, and that is enough to count along the screen.
    """
    return dict(
        page.evaluate(
            """() => {
              const element = document.activeElement
              if (element === null || element === document.body) return { present: false }
              const style = getComputedStyle(element)
              const attribute = ['aria-label', 'name', 'placeholder', 'id']
                .map((key) => element.getAttribute(key))
                .find((value) => value !== null)
              return {
                present: true,
                where: `<${element.tagName.toLowerCase()}${
                  attribute === undefined ? '' : ` ${attribute}`
                }>`,
                outlineStyle: style.outlineStyle,
                outlineWidth: style.outlineWidth,
                focusVisible: element.matches(':focus-visible'),
              }
            }"""
        )
    )
