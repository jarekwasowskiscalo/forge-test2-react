"""Smoke, in a real browser: the built SPA, booted, walked and broken on purpose.

Each test's docstring names the screen document it holds -- `@pytest.mark.req`
needs an open change record and this suite guards standing behaviour, so the
binding to `spec/design/ui/` is prose here and gate `e2e-scenario`'s concern on future
changes.

**Assertions name roles, selectors, fixed UI copy and counts.** Never a value
read off the page -- the page's values are whatever the world happens to hold,
which for a product built from this template is real data (Article XI). The one
exception is a value this suite *typed in itself*, which it may then look for:
it is the suite's own fixture and is in git already.

What this suite exists for, and the HTTP scenarios cannot reach: the bundle is
built and served, a deep link resolves through the SPA catch-all, a failing
request renders as something a person can read instead of a blank screen, and
the controls the HTTP suite can only exercise as query parameters are actually
wired to something a person can click.
"""

from typing import Final

from playwright.sync_api import Page, Route, expect

from e2e.harness.client import ApiClient
from e2e.ui.conftest import UI_BASE_URL
from e2e.ui.styles import AA_NORMAL_TEXT, focus_ring_of_active_element, text_contrast

#: The heading that says the screen arrived. Asserted by role and name -- fixed
#: UI copy, never a value off the page.
_HEADING: Final[str] = "Leave a note"

#: The lockup, which is a link on every screen. It is the way back from the 404,
#: and the only navigation this application has (`spec/design/ui/system-states.md`
#: § One column).
#:
#: Matched exactly wherever it is used: the 404 also carries "Go to the guestbook",
#: and a substring match resolves to both links and fails as ambiguous rather than
#: as the thing the assertion means.
_LOCKUP: Final[str] = "Guestbook"

#: The route the SPA serves it under. English, like every other name in this
#: repository (spec/design/conventions.md § Language).
_GUESTBOOK: Final[str] = "/guestbook"

#: The list endpoint, exactly as the frontend calls it. Named once so a route
#: interception cannot drift from the request it means to intercept.
_ENTRIES_GLOB: Final[str] = "**/api/guestbook-entries*"

#: The most entries one read of the collection may carry
#: (`spec/design/api.md` § Collection read parameters).
#:
#: Written here rather than imported: this suite is a black box and may not
#: reach into the application for a number it is asserting about. It is the
#: boundary the screen used to stop at -- the address went on counting, the read
#: did not, and every entry past it was unreachable with no error anywhere.
_ONE_READ_MAX: Final[int] = 100

#: How far the focus walk goes before it gives up. A ceiling rather than a count:
#: the walk stops on its own when focus leaves the document, and this is only there
#: so a page that traps focus in a loop fails as an assertion instead of a timeout.
_MAX_TAB_STOPS: Final[int] = 30

#: What the walk must reach before a clean run means anything: the composer's two
#: fields and its button, the search box, the two order pills, the card's Delete
#: (its Edit is `disabled` while the editor is open, and a disabled control is not a
#: stop), and the editor's two fields with its Save and Cancel. A walk that stopped
#: after three would otherwise report a screen with rings everywhere it looked.
_EXPECTED_TAB_STOPS: Final[int] = 10


def _seed(api: ApiClient, author: str, message: str) -> str:
    """One entry through the harness; returns its id.

    Seeding through the API rather than the screen keeps a test about the screen
    from failing for a reason that belongs to the form.
    """
    answer = api.send("POST", "/guestbook-entries", body={"author": author, "message": message})
    assert answer.status == 201, f"seeding failed: the write answered {answer}"
    return str(answer.record()["id"])


def test_the_built_spa_boots_and_a_deep_link_resolves(page: Page) -> None:
    """`spec/design/ui/guestbook.md` (S-01): the gap this suite exists for.

    A direct entry on the route is served by the SPA catch-all; with no built
    bundle it is a 404 the HTTP suite never sees, because the HTTP suite never
    asks for a screen.
    """
    page.goto(f"{UI_BASE_URL}{_GUESTBOOK}")

    expect(page.get_by_role("heading", level=1, name=_HEADING)).to_be_visible()
    expect(page.get_by_role("link", name=_LOCKUP, exact=True)).to_be_visible()


def test_the_root_redirects_to_the_one_screen(page: Page) -> None:
    """`/` is a redirect, not a second address for the same screen.

    Two URLs for one screen is two things to keep working, and the one nobody
    links to is the one that quietly breaks.
    """
    page.goto(UI_BASE_URL)

    expect(page.get_by_role("heading", level=1, name=_HEADING)).to_be_visible()
    assert page.url.rstrip("/").endswith(_GUESTBOOK)


def test_the_web_fonts_do_not_gate_the_screen(page: Page) -> None:
    """`spec/design/ui/system-states.md` § One palette: the two families come
    from a font host, and a screen that needs that request to succeed before it
    says anything is blank on a bad connection. With the stylesheet blocked, the
    fallback stack in `theme.css` has to still render the page."""
    page.route("https://fonts.googleapis.com/**", lambda route: route.abort())
    page.goto(f"{UI_BASE_URL}{_GUESTBOOK}")

    expect(page.get_by_role("heading", level=1, name=_HEADING)).to_be_visible()


def test_an_empty_book_shows_its_empty_state(page: Page, empty_application: ApiClient) -> None:
    """S-01: the empty state, on a genuinely empty book.

    Not the same claim as "the page loaded": an empty list and a failed request
    look identical to a screenshot, and only one of them should invite a first
    entry.
    """
    page.goto(f"{UI_BASE_URL}{_GUESTBOOK}")

    expect(page.get_by_text("No entries yet. Be the first.")).to_be_visible()


def test_an_entry_written_through_the_form_appears_in_the_list(
    page: Page, empty_application: ApiClient
) -> None:
    """S-01: the write path walked entirely through the screen.

    The value asserted is the one this test typed in, which is why quoting it is
    allowed here and nowhere else in this file.
    """
    page.goto(f"{UI_BASE_URL}{_GUESTBOOK}")

    page.get_by_role("textbox", name="Your name").fill("Smoke")
    page.get_by_role("textbox", name="Your message").fill("An entry from the smoke suite")
    page.get_by_role("button", name="Post entry").click()

    # Scoped to the card, not to the page: the composer's own textarea would
    # match the same text, and a locator resolving to both cannot tell "the
    # entry is in the list" from "the text is still in the box I typed it into".
    expect(page.get_by_role("article")).to_have_count(1)
    expect(page.get_by_role("article").get_by_text("An entry from the smoke suite")).to_be_visible()
    # The composer emptied itself, so the next guest does not re-submit this entry.
    expect(page.get_by_role("textbox", name="Your message")).to_have_value("")


def test_a_signature_of_emoji_is_bounded_in_the_unit_the_server_uses(
    page: Page, empty_application: ApiClient
) -> None:
    """The defect of GitHub issue #28, walked in a real browser.

    Forty-one grinning faces are 41 code points and 82 UTF-16 code units. Before
    2026-09-17 the field carried `maxLength={80}`, which the DOM counts in code
    units, so the browser stopped accepting input after the fortieth -- silently,
    with no message anywhere -- and the validator behind it would have called 41
    too long anyway, while the API stored the same value with a 201.

    Only a browser can see this. The attribute is the DOM's own behaviour, so a
    unit test of `authorProblem` passes whether or not the field truncates, and a
    test of the source would have read `maxLength` and called it a bound. What is
    asserted is the value the field HOLDS after typing, which is the thing that
    used to be wrong.

    The message keeps to ASCII: what is under test is the signature's unit, and a
    second alphabet in the message would make a failure ambiguous.
    """
    page.goto(f"{UI_BASE_URL}{_GUESTBOOK}")
    signature = "\U0001f600" * 41

    page.get_by_role("textbox", name="Your name").fill(signature)
    page.get_by_role("textbox", name="Your message").fill("Forty-one code points, not eighty-two")

    # Nothing was cut on the way in.
    expect(page.get_by_role("textbox", name="Your name")).to_have_value(signature)
    # And the rule agrees the value fits, so the entry can actually be written.
    expect(page.get_by_role("button", name="Post entry")).to_be_enabled()

    page.get_by_role("button", name="Post entry").click()
    expect(page.get_by_role("article")).to_have_count(1)


def test_the_submit_button_is_closed_until_the_form_is_complete(page: Page) -> None:
    """The rule is unit-tested in `lib/guestbookEntry.ts`; what this proves is
    that the built bundle is wired to it -- the seam between a correct rule and a
    form that ignores it, which only a real browser can walk."""
    page.goto(f"{UI_BASE_URL}{_GUESTBOOK}")

    expect(page.get_by_role("button", name="Post entry")).to_be_disabled()
    page.get_by_role("textbox", name="Your name").fill("Smoke")
    expect(page.get_by_role("button", name="Post entry")).to_be_disabled()
    page.get_by_role("textbox", name="Your message").fill("anything at all")
    expect(page.get_by_role("button", name="Post entry")).to_be_enabled()


def test_searching_narrows_the_list_to_the_entry_that_matches(
    page: Page, empty_application: ApiClient
) -> None:
    """S-01: the search box is wired to the server's `q`, not to the array on
    screen. Both values here were typed by this suite."""
    _seed(empty_application, "Smoke", "A message about herring")
    _seed(empty_application, "Other", "A message about nothing in particular")

    page.goto(f"{UI_BASE_URL}{_GUESTBOOK}")
    expect(page.get_by_role("article")).to_have_count(2)

    page.get_by_role("searchbox", name="Search entries").fill("herring")

    expect(page.get_by_role("article")).to_have_count(1)
    expect(page.get_by_text("1 match for “herring”")).to_be_visible()


def test_a_search_that_matches_nothing_says_so_rather_than_looking_empty(
    page: Page, empty_application: ApiClient
) -> None:
    """The two counts, seen from the outside: "nothing matches" and "the book is
    empty" are different sentences, and only the first one is true here."""
    _seed(empty_application, "Smoke", "A message the search will not ask for")

    page.goto(f"{UI_BASE_URL}{_GUESTBOOK}")
    page.get_by_role("searchbox", name="Search entries").fill("no-such-word")

    expect(page.get_by_text("Nothing matches that search.")).to_be_visible()
    expect(page.get_by_text("No entries yet. Be the first.")).to_have_count(0)


def test_the_rest_of_the_book_is_reachable_from_the_screen(
    page: Page, empty_application: ApiClient
) -> None:
    """S-01: the first page shows four, and the rest has to be reachable -- a
    page size with no way past it is entries nobody can read."""
    for index in range(6):
        _seed(empty_application, f"Smoke {index}", f"Message number {index}")

    page.goto(f"{UI_BASE_URL}{_GUESTBOOK}")
    expect(page.get_by_role("article")).to_have_count(4)

    page.get_by_role("button", name="Load 2 more").click()

    expect(page.get_by_role("article")).to_have_count(6)
    # The button goes away at the end rather than offering nothing.
    expect(page.get_by_role("button", name="Load 2 more")).to_have_count(0)


def test_the_book_is_readable_past_what_one_request_can_carry(
    page: Page, empty_application: ApiClient
) -> None:
    """S-01: a guestbook longer than one read must still be readable to its end.

    The one case no smaller fixture reaches. A read of the collection carries at
    most a hundred entries, and the screen used to treat that cap as the limit of
    what it could *show*: past the hundredth, pressing for more changed the
    address and fetched nothing, so the button stayed on screen for ever
    offering entries it could no longer reach.
    """
    for index in range(_ONE_READ_MAX + 1):
        _seed(empty_application, f"Smoke {index:03d}", f"Message number {index}")

    # Straight to the cap, which is a link somebody could send: the address is
    # what says how much belongs on screen, and the screen restores it in as
    # many reads as that takes.
    page.goto(f"{UI_BASE_URL}{_GUESTBOOK}?shown={_ONE_READ_MAX}")
    expect(page.get_by_role("article")).to_have_count(_ONE_READ_MAX)

    page.get_by_role("button", name="Load 1 more").click()

    expect(page.get_by_role("article")).to_have_count(_ONE_READ_MAX + 1)
    expect(page.get_by_role("button", name="Load 1 more")).to_have_count(0)


def test_the_address_brings_back_the_same_stretch_of_the_book(
    page: Page, empty_application: ApiClient
) -> None:
    """S-01: what a press of "Load more" put on screen, a reload puts back.

    The address is the whole record of how far down the book a reader is, so a
    link copied out of the bar opens where it was copied from. A screen holding
    that in its own memory loses it on every refresh.
    """
    for index in range(6):
        _seed(empty_application, f"Smoke {index}", f"Message number {index}")

    page.goto(f"{UI_BASE_URL}{_GUESTBOOK}")
    page.get_by_role("button", name="Load 2 more").click()
    expect(page.get_by_role("article")).to_have_count(6)

    page.reload()

    expect(page.get_by_role("article")).to_have_count(6)


def test_reading_the_book_from_the_other_end_reverses_it(
    page: Page, empty_application: ApiClient
) -> None:
    """`BR-04` in both directions, driven from the control that switches it."""
    _seed(empty_application, "Smoke first", "The older entry")
    _seed(empty_application, "Smoke second", "The newer entry")

    page.goto(f"{UI_BASE_URL}{_GUESTBOOK}")
    expect(page.get_by_role("article").first.get_by_text("Smoke second")).to_be_visible()

    page.get_by_role("button", name="Oldest").click()

    expect(page.get_by_role("article").first.get_by_text("Smoke first")).to_be_visible()


def test_an_entry_is_corrected_inside_its_own_card(
    page: Page, empty_application: ApiClient
) -> None:
    """S-01: editing happens in place, which is the change this screen makes.

    Only the browser can prove the editor opens seeded from the right entry --
    the HTTP suite has no card to open.
    """
    _seed(empty_application, "Smoke", "The message before the correction")

    page.goto(f"{UI_BASE_URL}{_GUESTBOOK}")
    page.get_by_role("button", name="Edit").click()

    expect(page.get_by_role("textbox", name="Edit name")).to_have_value("Smoke")
    page.get_by_role("textbox", name="Edit message").fill("The message after the correction")
    page.get_by_role("button", name="Save").click()

    expect(
        page.get_by_role("article").get_by_text("The message after the correction")
    ).to_be_visible()
    # Derived from the two instants (`BR-02`), not from a stored flag.
    expect(page.get_by_text("· edited")).to_be_visible()


def test_deleting_asks_before_it_destroys(page: Page, empty_application: ApiClient) -> None:
    """`BR-03` is irreversible, and the button that starts it sits a few pixels
    from Edit. The dialog is the only warning a person gets."""
    _seed(empty_application, "Smoke", "The entry to be deleted")

    page.goto(f"{UI_BASE_URL}{_GUESTBOOK}")
    page.get_by_role("button", name="Delete", exact=True).click()

    dialog = page.get_by_role("dialog")
    expect(dialog).to_be_visible()
    expect(dialog.get_by_text("This cannot be undone.")).to_be_visible()


def test_a_backend_error_reaches_the_operator_as_an_alert(page: Page) -> None:
    """`spec/design/ui/system-states.md`: a 503 on the list renders the error
    state, announced with role=alert -- not a blank screen, not a spinner."""

    def unavailable(route: Route) -> None:
        route.fulfill(
            status=503,
            content_type="application/json",
            body='{"detail": "service unavailable"}',
        )

    page.route(_ENTRIES_GLOB, unavailable)
    page.goto(f"{UI_BASE_URL}{_GUESTBOOK}")

    expect(page.get_by_role("alert")).to_be_visible()


def test_an_unknown_address_says_so(page: Page) -> None:
    """`spec/design/ui/system-states.md`: the SPA's own 404, not the shell,
    and rendered inside the frame so the way back out is still on screen."""
    page.goto(f"{UI_BASE_URL}/no-such-route")

    expect(page.get_by_role("heading", level=1, name="Nothing here")).to_be_visible()
    expect(page.get_by_role("link", name=_LOCKUP, exact=True)).to_be_visible()


def test_every_keyboard_stop_on_the_screen_shows_a_focus_ring(
    page: Page, empty_application: ApiClient
) -> None:
    """`spec/design/ui/guestbook.md` § The composer card: "a focus ring in the
    accent colour". The promise is made in `frontend/src/index.css` too -- "this
    screen is walked with a keyboard" -- and the *built* stylesheet broke it.

    Only a browser can ask this. The ring is declared in `@layer base` and the
    `outline-none` utility lands in `@layer utilities`, a later layer, so the
    utility wins whatever its specificity; jsdom implements no layers, loads no
    application CSS, and does not support `:focus-visible` at all.

    **All three properties are asserted at every stop, and that is the design.**
    The utility cancelled `outline-style` and left `outline-width` at the 2px the
    base rule had already set, so a test that asked only about the width would have
    passed on a screen with no visible ring anywhere.
    """
    _seed(empty_application, "Smoke", "An entry whose card carries the two actions")

    page.goto(f"{UI_BASE_URL}{_GUESTBOOK}")
    expect(page.get_by_role("article")).to_have_count(1)
    # The screen has to be put in the state where every named stop exists at once.
    # The composer's button is `disabled` until both fields have content, and a
    # disabled control is not a tab stop -- so it is filled here to be walked over,
    # not to be submitted. The editor's two fields are only in the tree while it is
    # open, and they are two of the five sites that carried the utility.
    page.get_by_role("textbox", name="Your name").fill("Smoke")
    page.get_by_role("textbox", name="Your message").fill("Filled so the button is a stop")
    page.get_by_role("button", name="Edit").click()
    expect(page.get_by_role("textbox", name="Edit name")).to_be_visible()

    # Chromium keeps a *sequential focus navigation starting point* that survives a
    # blur, so Tab after `body.focus()` resumes from whatever was clicked last --
    # here the Edit button, half way down the screen. Clicking a non-focusable
    # element at the top moves that starting point instead of merely clearing focus.
    page.get_by_role("heading", level=1, name=_HEADING).click()
    page.keyboard.press("Tab")
    walked: list[str] = []
    ringless: list[str] = []
    for _ in range(_MAX_TAB_STOPS):
        ring = focus_ring_of_active_element(page)
        if not ring["present"]:
            break
        walked.append(str(ring["where"]))
        if (
            ring["outlineStyle"] == "none"
            or ring["outlineWidth"] == "0px"
            or not ring["focusVisible"]
        ):
            ringless.append(
                f"{ring['where']}: outline-style={ring['outlineStyle']} "
                f"outline-width={ring['outlineWidth']} :focus-visible={ring['focusVisible']}"
            )
        page.keyboard.press("Tab")

    assert len(walked) >= _EXPECTED_TAB_STOPS, (
        f"the walk found {len(walked)} focusable stops, fewer than the {_EXPECTED_TAB_STOPS} "
        "this screen has -- so a clean run would mean the walk stopped early rather than that "
        f"every stop has a ring. It reached: {walked}"
    )
    assert not ringless, (
        "a keyboard stop with no visible focus ring. The ring lives in @layer base "
        "(frontend/src/index.css) and any `outline-none` utility on the element beats it "
        f"from @layer utilities, whatever the specificity. The walk was {walked}. "
        "Found:\n  " + "\n  ".join(ringless)
    )


def test_the_quiet_text_clears_the_contrast_floor_where_it_is_painted(
    page: Page, empty_application: ApiClient
) -> None:
    """`spec/design/ui/system-states.md` § Tokens: the floor is a rule of the token,
    measured against the surface it is actually painted on.

    Both halves of every pair are read from the page -- the colour from the element,
    the background from the nearest ancestor that paints one. A test that took the
    background from the token list would be asserting its own assumption about where
    the text ended up, which is the half that goes wrong.

    `--color-faint` carried four of these sites at 2.9:1 on a white card, including
    the card's own Edit and Delete actions. `tests/fitness/test_design_tokens.py`
    holds the token itself; this holds the five places it lands.
    """
    _seed(empty_application, "Smoke", "An entry whose card carries the quiet chrome")

    page.goto(f"{UI_BASE_URL}{_GUESTBOOK}")
    card = page.get_by_role("article").first
    expect(card).to_be_visible()

    measured = {
        "the card's Edit action": card.get_by_role("button", name="Edit"),
        "the card's Delete action": card.get_by_role("button", name="Delete", exact=True),
        "the card's timestamp": card.locator("time"),
        "the composer's character counter": page.locator("[aria-live='polite']").first,
        "the page footer": page.locator("footer"),
    }

    failures = [
        f"{name}: {text_contrast(locator):.2f}:1"
        for name, locator in measured.items()
        if text_contrast(locator) < AA_NORMAL_TEXT
    ]
    assert not failures, (
        f"text below the {AA_NORMAL_TEXT}:1 floor of WCAG 1.4.3, measured against the "
        "background actually painted behind it. Darken the token in "
        f"frontend/src/styles/theme.css. Found:\n  " + "\n  ".join(failures)
    )


def test_the_only_label_the_composer_fields_have_clears_the_floor(page: Page) -> None:
    """The fields carry no visible label by decision (`spec/design/ui/guestbook.md`
    § The composer card), so the placeholder is the only thing on screen saying what
    goes in them -- and `frontend/src/index.css` paints it in the quietest token
    there is. Measured through `::placeholder`, which is the only way to reach it."""
    page.goto(f"{UI_BASE_URL}{_GUESTBOOK}")

    faint = [
        (name, text_contrast(page.get_by_role("textbox", name=name), pseudo="::placeholder"))
        for name in ("Your name", "Your message")
    ]
    failures = [f"{name}: {ratio:.2f}:1" for name, ratio in faint if ratio < AA_NORMAL_TEXT]
    assert not failures, (
        f"a placeholder below {AA_NORMAL_TEXT}:1. It is the field's only label, so it is "
        "text under 1.4.3 rather than decoration. Found:\n  " + "\n  ".join(failures)
    )
