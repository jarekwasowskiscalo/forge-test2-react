"""Article XIII, the half that had no mechanism: no raw hex, no magic pixel.

Of the eight prohibitions in Article XIII, exactly one had a full enforcement
mechanism and four had none at all. Three of the four were being kept by accident --
nobody had broken them yet. This one was not: an audit counted **33 arbitrary pixel
values across 9 files**, plus a `border-radius: 8px` in `index.css` that no grep over
Tailwind syntax would ever have found. A [CRITICAL] rule that nothing checks is a rule
that teaches everybody the articles are optional.

The rule is not about tidiness. `rounded-[14px]` stood in six files, so changing the
card radius meant six edits and one forgotten. The token is what makes it one edit --
and the token is also the only place a designer can read the system's own vocabulary.

**Scope, and why each boundary is where it is.**

`frontend/src/styles/theme.css` is exempt and must be: it is the one file where a value
is allowed to be a number, because that is what declaring a token means. Excluding it
by name rather than by pattern keeps the exemption a decision somebody made rather than
a hole a regex left.

Tailwind's own scale is not a magic number. `p-4.5` is eighteen pixels expressed in the
framework's spacing units, `gap-3.5` is fourteen, and both survive a change to the
scale's base. What this catches is the **arbitrary value** syntax -- `[14px]` -- which
is Tailwind's documented escape hatch out of the design system.

This module comes with a test that the detectors detect, on the same rule the rest of
this suite follows: a new detector arrives with proof that it fires, not merely with a
green run on the commit that introduced it.
"""

import pathlib
import re
from typing import Final

from tests._repo import REPO_ROOT

FRONTEND_SRC: Final[pathlib.Path] = REPO_ROOT / "frontend" / "src"

#: The one file where a value may be a number, because declaring tokens is its job.
TOKENS: Final[pathlib.Path] = FRONTEND_SRC / "styles" / "theme.css"

#: Tailwind's arbitrary-value syntax with a pixel literal: `rounded-[14px]`,
#: `text-[13px]`, `max-w-[860px]`. Deliberately NOT every `[...]`: an arbitrary
#: grid template or a selector is a different question, and a check that answers
#: several questions is a check nobody can act on.
_ARBITRARY_PX: Final = re.compile(r"\[\d+(?:\.\d+)?px\]")

#: A raw colour in a component. Three, six or eight digits, so `#fff`, `#1b1a17`
#: and `#1b1a17ff` are all caught.
_RAW_HEX: Final = re.compile(r"#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3}(?:[0-9a-fA-F]{2})?)?\b")

#: A raw radius in CSS that never passes through Tailwind at all -- the class the
#: audit's own grep missed, because it was looking for utility syntax.
_RAW_RADIUS: Final = re.compile(r"border-radius:\s*[\d.]+(?:px|rem|em)")


def _sources() -> list[pathlib.Path]:
    """Every component and stylesheet except the token declaration itself."""
    return sorted(
        path
        for suffix in ("*.tsx", "*.ts", "*.css")
        for path in FRONTEND_SRC.rglob(suffix)
        if path != TOKENS
        and not path.name.endswith(".test.ts")
        and not path.name.endswith(".test.tsx")
    )


def _hits(pattern: re.Pattern[str], paths: list[pathlib.Path]) -> list[str]:
    found: list[str] = []
    for path in paths:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for match in pattern.finditer(line):
                found.append(f"{path.relative_to(REPO_ROOT)}:{number}: {match.group(0)}")
    return found


def test_no_component_carries_an_arbitrary_pixel_value() -> None:
    sources = _sources()
    assert sources, "no frontend sources scanned at all -- the reader has stopped reading"
    hits = _hits(_ARBITRARY_PX, sources)
    assert not hits, (
        "Article XIII: a magic pixel size in a component. Name it in "
        "frontend/src/styles/theme.css and use the generated utility "
        "(`--radius-card` -> `rounded-card`), or express it on Tailwind's spacing "
        "scale (`p-4.5` is 18px). Found:\n  " + "\n  ".join(hits)
    )


def test_no_component_carries_a_raw_hex_colour() -> None:
    hits = _hits(_RAW_HEX, _sources())
    assert not hits, (
        "Article XIII: a raw hex colour outside theme.css. A colour nobody named is a "
        "token invisible to every later change of the palette. Found:\n  " + "\n  ".join(hits)
    )


def test_no_stylesheet_carries_a_raw_border_radius() -> None:
    hits = _hits(_RAW_RADIUS, _sources())
    assert not hits, (
        "A radius in plain CSS bypasses both the token and the Tailwind grep that "
        "would have caught the utility form. Use `var(--radius-*)`. Found:\n  " + "\n  ".join(hits)
    )


def test_the_detectors_would_see_a_violation() -> None:
    """Prove the three regexes fire. A detector that stopped matching passes silently
    exactly when the rule starts being broken -- which is the failure mode this whole
    suite is built to avoid, so a new detector arrives with its own evidence."""
    assert _ARBITRARY_PX.search('className="rounded-[14px] border"')
    assert _ARBITRARY_PX.search('className="text-[13px]"')
    assert _RAW_HEX.search("color: #1b1a17;")
    assert _RAW_HEX.search("color: #fff;")
    assert _RAW_RADIUS.search("border-radius: 8px;")

    # And that they do NOT fire on what is deliberately allowed, which is the half
    # that makes the assertions above mean something.
    assert not _ARBITRARY_PX.search('className="p-4.5 gap-3.5 rounded-card"')
    assert not _RAW_HEX.search("background: var(--color-card);")
    assert not _RAW_RADIUS.search("border-radius: var(--radius-card);")


def test_every_radius_and_type_token_is_actually_used() -> None:
    """A token nobody uses is a vocabulary entry for a thing that does not exist, and
    it invites the next author to add a sixth radius rather than reach for one of five."""
    declared = re.findall(
        r"--(radius|text|container)-([a-z-]+):", TOKENS.read_text(encoding="utf-8")
    )
    body = "\n".join(path.read_text(encoding="utf-8") for path in _sources())
    unused = [
        f"--{kind}-{name}"
        for kind, name in declared
        if f"{'rounded' if kind == 'radius' else 'max-w' if kind == 'container' else kind}-{name}"
        not in body
    ]
    assert not unused, f"declared in theme.css and used nowhere: {unused}"


# ---------------------------------------------------------------------------
# The contrast floor, as a rule of the token
# ---------------------------------------------------------------------------
#
# `--color-faint` was `#9b978c`: 2.92:1 on a white card, 2.67:1 on the page and
# 2.54:1 on `--color-surface-medium`. It painted the card's Edit and Delete
# actions, every timestamp, the character counter, the footer and -- through
# `::placeholder` -- the only label the composer's fields have. Nothing failed,
# because nothing was looking: `frontend/src/styles/theme.test.ts` reads this
# same file and checks the *names* of tokens, never their values.
#
# This is the token half of the rule. `e2e/ui/test_smoke.py` holds the other half
# in a browser, and the two answer different questions: the browser knows which
# surface a piece of text actually landed on, and can therefore only judge the
# sites a screen puts on display; this one judges the palette itself, including
# a pairing no screen currently renders (`Modal`'s `eyebrow` has no caller). A
# palette whose values are only checked where they happen to be used is a palette
# that fails on the day somebody uses one somewhere new.

#: WCAG 2.1 success criterion 1.4.3, for text below 18.66px bold / 24px regular.
#: Every site in this palette is under that, so the 3:1 large-text floor is not
#: offered here -- an exemption nothing qualifies for is an invitation.
AA_NORMAL_TEXT: Final[float] = 4.5

#: The two families the palette actually has. A single 8x5 product would be
#: honest arithmetic and a poor rule: eighteen of its forty cells are "this token
#: is never painted on that surface", and eighteen rows of that kind are where the
#: one real exemption below would go to hide.
_DARK_TEXT: Final[tuple[str, ...]] = ("ink", "muted", "faint", "danger", "accent", "accent-strong")
_LIGHT_SURFACES: Final[tuple[str, ...]] = ("card", "surface", "surface-medium")
_LIGHT_TEXT: Final[tuple[str, ...]] = ("inverse",)
_DARK_SURFACES: Final[tuple[str, ...]] = ("accent", "accent-strong")

#: Every pair let through, and why. One entry, and it is a decision rather than a
#: measurement that was inconvenient: WCAG 1.4.3 exempts the text of a disabled
#: control outright, and `--color-disabled` (1.82:1 on a card) exists for nothing
#: else. It is written here because `spec/design/ui/system-states.md` § Tokens
#: says it has to be written somewhere a reader can find it -- a default nobody
#: recorded is indistinguishable from an oversight.
PERMITTED_BELOW_FLOOR: Final[dict[str, str]] = {
    "disabled": (
        "WCAG 1.4.3 exempts an inactive control's text. The token has no other use: "
        "`Button`'s `disabled:text-disabled` is every occurrence."
    ),
}

#: `--color-hairline` and `--color-line` are borders and scrollbar thumbs. They
#: fall under 1.4.11 (non-text contrast, 3:1), which is a different rule with a
#: different floor, and answering two questions in one check produces a failure
#: nobody can act on. Named here so their absence is a decision.
_NOT_TEXT: Final[frozenset[str]] = frozenset({"hairline", "line"})


def _palette() -> dict[str, tuple[int, int, int]]:
    """Every `--color-<name>` in the theme, as channels."""
    declared = re.findall(
        r"--color-([a-z0-9-]+):\s*(#[0-9a-fA-F]{6})\b", TOKENS.read_text(encoding="utf-8")
    )
    return {name: _channels(value) for name, value in declared}


def _channels(hex_colour: str) -> tuple[int, int, int]:
    raw = hex_colour.lstrip("#")
    return int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    """WCAG 2.1 § dfn-relative-luminance."""
    linear = []
    for raw in rgb:
        value = raw / 255
        linear.append(value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4)
    red, green, blue = linear
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def _contrast(first: tuple[int, int, int], second: tuple[int, int, int]) -> float:
    """WCAG 2.1 § dfn-contrast-ratio."""
    lighter, darker = sorted((_relative_luminance(first), _relative_luminance(second)))[::-1]
    return (lighter + 0.05) / (darker + 0.05)


def _pairs_below_floor(
    palette: dict[str, tuple[int, int, int]],
    text: tuple[str, ...],
    surfaces: tuple[str, ...],
) -> list[str]:
    return [
        f"--color-{ink} on --color-{paper}: {_contrast(palette[ink], palette[paper]):.2f}:1"
        for ink in text
        for paper in surfaces
        if ink not in PERMITTED_BELOW_FLOOR
        and _contrast(palette[ink], palette[paper]) < AA_NORMAL_TEXT
    ]


def test_the_palette_declares_every_token_these_rules_name() -> None:
    """The product below is over names written out by hand, so a renamed or deleted
    token would otherwise shrink the check instead of breaking it."""
    palette = _palette()
    named = set(_DARK_TEXT + _LIGHT_SURFACES + _LIGHT_TEXT + _DARK_SURFACES)
    named |= set(PERMITTED_BELOW_FLOOR) | _NOT_TEXT

    assert named <= set(palette), (
        f"named by this module and gone from theme.css: {named - set(palette)}"
    )
    unjudged = set(palette) - named
    assert not unjudged, (
        "a colour token no rule in this module mentions: "
        f"{sorted(unjudged)}. Add it to a family, to PERMITTED_BELOW_FLOOR with a "
        "reason, or to _NOT_TEXT -- a token that is simply not listed is one nobody "
        "decided about."
    )


def test_every_text_token_clears_the_contrast_floor_on_every_surface_it_can_meet() -> None:
    palette = _palette()
    below = _pairs_below_floor(palette, _DARK_TEXT, _LIGHT_SURFACES)
    below += _pairs_below_floor(palette, _LIGHT_TEXT, _DARK_SURFACES)

    assert not below, (
        f"below the {AA_NORMAL_TEXT}:1 floor of WCAG 1.4.3 (`spec/design/ui/system-states.md` "
        "§ Tokens: the floor is measured against the DARKEST surface the token can be "
        "painted on, not against white). Darken the token in frontend/src/styles/theme.css, "
        "or add the pair to PERMITTED_BELOW_FLOOR with the reason it is exempt. "
        "Found:\n  " + "\n  ".join(below)
    )


def test_the_contrast_detector_would_see_a_violation() -> None:
    """This module's own rule (see the header): a detector arrives with proof it fires.

    Three probes, because three things can rot independently -- the arithmetic, the
    threshold, and the exemption list that stands between them and the assertion.
    """
    white, black = (255, 255, 255), (0, 0, 0)
    assert _contrast(white, black) == 21
    assert _contrast(white, white) == 1
    # The value `--color-faint` used to hold, on the card it was painted on.
    assert round(_contrast((0x9B, 0x97, 0x8C), white), 2) == 2.92

    broken = {"washed-out": (0x9B, 0x97, 0x8C), "card": white}
    assert _pairs_below_floor(broken, ("washed-out",), ("card",)), (
        "the product reported nothing on a pair that is deliberately below the floor"
    )
    # And the exemption really is what lets a pair through, rather than the
    # arithmetic quietly agreeing with it.
    assert not _pairs_below_floor(
        {"disabled": (0xC4, 0xC0, 0xB5), "card": white}, ("disabled",), ("card",)
    )
