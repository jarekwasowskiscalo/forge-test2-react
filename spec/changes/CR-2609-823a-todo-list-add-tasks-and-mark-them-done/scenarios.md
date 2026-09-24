# Scenarios — the to-do list: add tasks and mark them done

*Seeds. The implementation stage turns them into `.feature` files and binds the steps.*

The register is the one `e2e/suite/features/guestbook.feature` uses: somebody does a thing, the
thing "should be saved" or "should be refused as …", and the list "should hold N tasks". A task
is one line of text on the one shared to-do list, and it is **done** or **not done** (the words
of `requirements.md` § Goal). Every scenario starts from an empty to-do list, because the world is
cleaned before each one. `guestbook.feature` is not touched by this change, and its 22 scenarios
stay as they are (`SC-5`).

**Where each seed can be seen.** The black box (`e2e/suite/`) talks to the application, not to the
screen. So each seed says what observes it:

- **application**: what the application stores and gives back. The black box can bind it.
- **application, overlapping**: two changes must be sent before either is answered. A binding
  that sends them one after the other proves nothing (`requirements.md` § Self-check 19).
- **store-ordered**: the test has to decide which of two overlapping changes the store applies
  later. Only a test holding the database can do that. The black box cannot.
- **screen**: what the screen shows. The black box cannot see it, so its citation owner is a
  screen test, and choosing that owner is `design-testing`'s call. The UI smoke sees it too, but
  it owns no citation (`spec/design/testing.md` § The UI smoke is not a traceability surface).
- **person**: a person at acceptance. `R-11` is `**Verified-by:** manual`.

## Coverage
| Requirement | Scenarios | Unhappy path? | Observed through |
|---|---|---|---|
| R-1 | S-1, S-2, S-3, S-4 | yes (S-4) | application; S-3 on the screen |
| R-2 | S-5, S-6, S-7, S-8, S-9, S-10, S-11 | yes (S-6, S-8, S-11) | application; S-10 and S-11 on the screen |
| R-3 | S-12, S-13, S-14, S-15, S-16, S-17, S-18, S-19, S-20 | yes (S-20); the rest are ordering, proved by comparing reads | application; S-18 store-ordered; S-19 and S-20 on the screen |
| R-4 | S-21, S-22, S-23, S-24, S-25 | yes (S-23, S-24) | application; S-25 on the screen, contrast half unobservable (finding 1) |
| R-5 | S-26, S-27, S-28, S-29, S-30 | yes (S-30, the unknown address) | screen |
| R-6 | S-31, S-32, S-33 | yes (S-33) | application |
| R-7 | S-34, S-35, S-36 | yes (S-36) | application; S-35 and S-36 on the screen |
| R-8 | S-37, S-38, S-39 | yes (all three) | application |
| R-9 | S-40, S-41, S-42, S-43 | yes (all four are conflicts) | S-40 and S-42 application, overlapping; S-41 and S-43 store-ordered |
| R-10 | S-44, S-45, S-46, S-47, S-48 | yes (all five) | screen |
| R-11 | S-49, S-50, S-51, S-52, S-53 | yes (S-50, S-51) | person (manual) |

**"Observed through" says where a seed can be seen, not which suite binds it.** An "application"
seed is one the black box can bind; whether it does is `design-testing`'s call, written in
`spec/design/testing.md`, and a seed the black box leaves unbound is proved there by a cheaper
suite that reads the same values.

`R-1` clause 2 (no account, no sign-in) has no seed of its own. Every scenario here runs with
nobody signed in, so every one of them proves it, and no single scenario could prove it better.

## Scenarios

### S-1 — Adding the first task
```gherkin
  @req:CR-2609-823a/R-1
  Scenario: Adding the first task
    Given the to-do list is empty
    When somebody adds the task "Water the plants"
    Then the task should be saved
    And the to-do list should hold 1 task
    And the task "Water the plants" should be shown as not done
```
**Observed through:** application. **Data:** "Water the plants" (`R-1.1`).
**Fails if:** nothing is stored, the task is stored as done, or its text comes back changed.

### S-2 — The same text twice makes two separate tasks
```gherkin
  @req:CR-2609-823a/R-1
  Scenario: The same text added twice makes two separate tasks
    Given the to-do list holds the task "Buy bread"
    When somebody adds the task "Buy bread" again
    And somebody marks the newer "Buy bread" as done
    Then the to-do list should hold 2 tasks reading "Buy bread"
    And the older "Buy bread" should still be shown as not done
```
**Observed through:** application. **Data:** "Buy bread" (`R-1.2`).
**Fails if:** a repeated text is refused or merged into the first task, or the two share one
identity, so that marking one marks both.

### S-3 — A task added on the screen appears at the top without a reload
```gherkin
  @req:CR-2609-823a/R-1
  Scenario: A task added on the screen appears at the top without reloading
    Given the to-do screen is open, showing the tasks "First" and "Second"
    When somebody adds the task "Third" on that screen
    Then "Third" should appear at the top of the list without the page being reloaded
```
**Observed through:** screen. **Data:** "First", "Second", "Third" (`R-1.3`).
**Fails if:** the screen shows a new task only after a reload, or puts it anywhere but first.

### S-4 — A new task is never born done
```gherkin
  @req:CR-2609-823a/R-1
  Scenario: A task sent as already done is still saved as not done
    Given the to-do list is empty
    When somebody adds the task "Already finished", sent as if it were already done
    Then the task should be saved
    And the task "Already finished" should be shown as not done
```
**Observed through:** application. Only a caller that goes around the screen can send this,
because the field cannot. **Data:** "Already finished" (`R-1.4`).
**Fails if:** the application honours a done state claimed when the task is added.

### S-5 — A task at the boundary is accepted
```gherkin
  @req:CR-2609-823a/R-2
  Scenario Outline: A task at the boundary size is accepted
    Given the to-do list is empty
    When somebody adds a task in which <case>
    Then the task should be saved
    And the stored text should be <kept>

    Examples:
      | case | kept |
      | the text is at the maximum permitted length | exactly what was sent |
      | the text is emoji and at the maximum permitted length | exactly what was sent |
      | the text is decomposed accented letters and at the maximum length once composed | what was sent, with each letter composed |
      | the text is padded with spaces and at the maximum length after trimming | what was sent, without the spaces around it |
      | the text is one character long | exactly what was sent |
```
**Observed through:** application. **Data:** `tasks-boundary.json`, every case looked up by its
sentence (§ New fixtures; `R-2.2`, `R-2.3`, `R-2.4`, `R-2.5`).
**Fails if:** the application counts UTF-16 units or bytes rather than code points, measures before
normalizing or trimming, or places the bound anywhere but 200.

### S-6 — A task breaking a rule is not saved
```gherkin
  @req:CR-2609-823a/R-2
  Scenario Outline: A task breaking a rule is not saved
    Given the to-do list is empty
    When somebody tries to add a task in which <case>
    Then the task should be refused as <reason>
    And the to-do list should hold 0 tasks

    Examples:
      | case | reason |
      | the text was not given at all | having no text |
      | the text is three spaces | having no text |
      | the text is all whitespace | having no text |
      | the text is two hundred and five spaces | having no text |
      | the text is one character too long | being too long |
      | the text is emoji and one code point too long | being too long |
      | the text is decomposed accented letters and one past the maximum once composed | being too long |
      | the text is padded with spaces and one character too long after trimming | being too long |
```
**Observed through:** application. **Data:** `tasks-refused.json`, every case looked up by its
sentence (`R-2.1`, `R-2.2`, `R-2.3`, `R-2.5`).
**Fails if:** an empty text is stored, the bound lets through 201, or 205 spaces are refused as
"too long" rather than "no text". That last one is the trim-order defect `spec/design/api.md`
records.

### S-7 — Spaces between the words are kept exactly
```gherkin
  @req:CR-2609-823a/R-2
  Scenario: Spaces between the words of a task are kept as typed
    Given the to-do list is empty
    When somebody adds the task "Buy  two   lamps"
    Then the task should be saved
    And the stored text should be exactly "Buy  two   lamps", with its two and three spaces
```
**Observed through:** application. **Data:** "Buy  two   lamps", with two spaces after "Buy" and
three after "two" (`R-2.6`).
**Fails if:** inner whitespace is squeezed or trimmed along with the edges.

### S-8 — A task with a line break inside it is refused
```gherkin
  @req:CR-2609-823a/R-2
  Scenario: A task whose text runs over two lines is not saved
    Given the to-do list is empty
    When somebody tries to add a task in which the text has a line break between two words
    Then the task should be refused as being more than one line
    And the to-do list should hold 0 tasks
```
**Observed through:** application. Only a caller that goes around the screen can send it
(`Q-11`). **Data:** `tasks-refused.json` case "the text has a line break between two words",
whose text is "Buy bread", a line feed, then "and milk" (`R-2.7`, `R-2` clause 6). The other six
characters of that clause's set are proved at the rule, on both sides, by the additions to
`text-measurement.json` (§ New fixtures).
**Fails if:** the text is stored as given, stored with the break replaced, or refused with the
"no text" or "too long" reason instead of a reason of its own.

### S-9 — A line break at the end of a task is trimmed like a space
```gherkin
  @req:CR-2609-823a/R-2
  Scenario: A line break after the last word is trimmed, not refused
    Given the to-do list is empty
    When somebody adds the task "Buy bread" with a line break after it
    Then the task should be saved
    And the stored text should be exactly "Buy bread"
```
**Observed through:** application. **Data:** "Buy bread" followed by one line feed. The line
feed is in the written trim set (`R-2.7`; `R-2` clauses 1 and 6; `text-measurement.json` case
`only_the_line_feed`).
**Fails if:** the line break rule runs before trimming and refuses a text whose only line break
sits at its edge. That is the same class of defect as the one `api.md` records for measuring
before trimming.

### S-10 — The field takes 200 emoji whole
```gherkin
  @req:CR-2609-823a/R-2
  Scenario: The new-task field takes a text of 200 emoji without cutting it short
    Given the to-do screen is open
    When somebody pastes 200 grinning-face emoji into the new-task field
    Then the field should hold all 200 of them
    And the screen should let the task be added
```
**Observed through:** screen. **Data:** 200 × U+1F600, which is 400 UTF-16 code units
(`R-2.3`).
**Fails if:** the field carries a bound counted in UTF-16 units, and so stops at 100 emoji, or the
screen's rule refuses what the application stores. That is the `D-04` defect again.

### S-11 — The screen refuses 201 emoji for the same reason the application does
```gherkin
  @req:CR-2609-823a/R-2
  Scenario: The screen refuses a text of 201 emoji for the reason the application gives
    Given the to-do screen is open
    When somebody pastes 201 grinning-face emoji into the new-task field
    Then the field should hold all 201 of them
    And the screen should say the text is too long
    And nothing should be added to the list
```
**Observed through:** screen. **Data:** 201 × U+1F600 (`R-2.3`, `R-2` clause 5).
**Fails if:** the field silently cuts the text at 200 instead of saying why, or the screen's
reason differs from S-6's "being too long" for the same text.

### S-12 — The newest task is at the top
```gherkin
  @req:CR-2609-823a/R-3
  Scenario: The list shows the newest task at the top
    Given the to-do list holds the tasks "First", "Second" and "Third", added in that order
    When the to-do list is displayed
    Then it should read "Third", "Second", "First"
```
**Observed through:** application. **Data:** "First", "Second", "Third" (`R-3.1`).
**Fails if:** the list comes back oldest first, in text order, or in the order the store happens
to return.

### S-13 — The list shows everything people added, done and not done alike
```gherkin
  @req:CR-2609-823a/R-3
  Scenario: The list shows every task people added, done and not done alike
    Given people have already put their tasks on the list
    When the to-do list is displayed
    Then it should show every task that was added, done and not done alike
    And they should be ordered newest first
```
**Observed through:** application. **Data:** `tasks-ordinary.json`, in adding order. The
expectation is the reverse of the file, not a hand-written list.
**Fails if:** done tasks are filtered out or moved, a repeated text is dropped, characters
outside ASCII do not survive the trip, or the order is anything but newest first.

### S-14 — A hundred and one tasks are all on one list
```gherkin
  @req:CR-2609-823a/R-3
  Scenario: A hundred and one tasks are all shown on one list
    Given 101 tasks have been added, "Task 001" first and "Task 101" last
    When the to-do list is displayed
    Then all 101 tasks should be shown at once
    And "Task 101" should be at the top and "Task 001" at the bottom
```
**Observed through:** application. **Data:** the producing rule in § Inline values (`R-3.3`).
**Fails if:** the list is handed out in pieces of 20 or 100, as the guestbook's is, so that the
oldest task silently goes missing.

### S-15 — Ticking a task done does not move it
```gherkin
  @req:CR-2609-823a/R-3
  Scenario: Marking a task done leaves it where it was
    Given the to-do list holds the tasks "First", "Second" and "Third", added in that order
    When somebody marks "Second" as done
    Then the list should still read "Third", "Second", "First"
```
**Observed through:** application. **Data:** "First", "Second", "Third" (`R-3.4`).
**Fails if:** done tasks sink to the bottom or into a section of their own, or marking re-stamps
the moment of adding.

### S-16 — Correcting a task does not move it to the top
```gherkin
  @req:CR-2609-823a/R-3
  Scenario: Correcting a task's text leaves it where it was
    Given the to-do list holds the tasks "First", "Second" and "Third", added in that order
    When somebody changes the text of "Second" to "Second, corrected"
    Then the list should read "Third", "Second, corrected", "First"
```
**Observed through:** application. **Data:** "Second, corrected" (`R-3.4`, `R-3` clause 4).
**Fails if:** "newest" is read as "most recently changed", so an edited task jumps to the top
(`requirements.md` § Self-check 7).

### S-17 — Somebody else's new task appears after a reload
```gherkin
  @req:CR-2609-823a/R-3
  Scenario: A task somebody else added appears after a reload
    Given somebody has the to-do list open, showing the task "First"
    When somebody else adds the task "From the other window"
    And the first person reloads the list
    Then "From the other window" should be at the top of their list
```
**Observed through:** application (two readers, one after the other). **Data:** "First", "From
the other window" (`R-3.5`).
**Fails if:** the list is kept per visitor, or is read from the browser rather than from the
application.

### S-18 — Two tasks stored at the same moment keep one order
```gherkin
  @req:CR-2609-823a/R-3
  Scenario: Two tasks stored at the same moment are always shown in the same order
    Given the tasks "Left" and "Right" were stored at the same moment
    When the to-do list is displayed twice
    Then both displays should show "Left" and "Right" in the same order
```
**Observed through:** store-ordered. From outside the application nobody can make two tasks
share a moment of adding (finding 2). **Data:** "Left", "Right" (`R-3.2`).
**Fails if:** the order has no tie-break, so two reads of an equal pair can disagree.

### S-19 — An empty list says so and says what to do
```gherkin
  @req:CR-2609-823a/R-3
  Scenario: An empty to-do list says it is empty and how to begin
    Given the to-do list is empty
    When the to-do screen is opened
    Then the screen should say the list is empty
    And it should say how to add a first task
    And it should show no error
```
**Observed through:** screen. **Data:** none, the list is empty (`R-3.6`).
**Fails if:** the screen shows a blank area, or an error, where the empty-list sentence belongs.

### S-20 — A list where every task is done is not called empty
```gherkin
  @req:CR-2609-823a/R-3
  Scenario: A list whose tasks are all done still shows them
    Given the to-do list holds the tasks "Water the plants" and "Buy bread", both done
    When the to-do screen is opened
    Then both tasks should be shown, as done
    And the screen should not say the list is empty
```
**Observed through:** screen. **Data:** "Water the plants", "Buy bread" (`R-3` clause 1,
`requirements.md` § Attacks E-3).
**Fails if:** the screen treats "nothing left to do" as "no tasks" and hides the done ones.

### S-21 — Marking a task done survives a reload
```gherkin
  @req:CR-2609-823a/R-4
  Scenario: A task marked done stays done after a reload
    Given the to-do list holds the task "Buy bread", not done
    When somebody marks "Buy bread" as done
    And the list is reloaded
    Then "Buy bread" should be shown as done
    And its text should still be "Buy bread"
```
**Observed through:** application. **Data:** "Buy bread" (`R-4.1`, `R-4` clause 4).
**Fails if:** the done mark lives only on the screen, or marking touches the text.

### S-22 — Ticking a task back to not done
```gherkin
  @req:CR-2609-823a/R-4
  Scenario: A task marked done by mistake goes back to not done
    Given the to-do list holds the task "Buy bread", done
    When somebody marks "Buy bread" as not done
    And the list is reloaded
    Then "Buy bread" should be shown as not done
```
**Observed through:** application. **Data:** "Buy bread" (`R-4.2`).
**Fails if:** done is a one-way state (`Q-2`).

### S-23 — Marking done a task somebody else already marked done keeps it done
```gherkin
  @req:CR-2609-823a/R-4
  Scenario: Marking done a task that is already done leaves it done
    Given the to-do list holds the task "Buy bread", not done
    And somebody else has marked it done while this person's screen still shows it not done
    When this person marks "Buy bread" as done
    Then "Buy bread" should be shown as done
```
**Observed through:** application. **Data:** "Buy bread" (`R-4.3`; race `W-2`).
**Fails if:** marking flips the stored state instead of setting the chosen one, which switches
the task back to not done although both people chose done.

### S-24 — Marking not done a task somebody else already marked not done keeps it not done
```gherkin
  @req:CR-2609-823a/R-4
  Scenario: Marking not done a task that is already not done leaves it not done
    Given the to-do list holds the task "Buy bread", done
    And somebody else has marked it not done while this person's screen still shows it done
    When this person marks "Buy bread" as not done
    Then "Buy bread" should be shown as not done
```
**Observed through:** application. **Data:** "Buy bread" (`R-4` clause 3, the other direction).
**Fails if:** marking flips the stored state, which is the same defect as S-23 from the other
side.

### S-25 — Done and not-done tasks look different, and the done text stays readable
```gherkin
  @req:CR-2609-823a/R-4
  Scenario: A done task is shown differently and its text stays readable
    Given the to-do list holds the done task "Call the plumber" and the not-done task "Buy bread"
    When the to-do screen is opened
    Then "Call the plumber" should be shown as done and "Buy bread" as not done
    And the two tasks should look different
    And the text of "Call the plumber" should stand out from what is behind it by at least 4.5 to 1
```
**Observed through:** screen. The contrast line is observable by no suite that owns a citation
(finding 1). **Data:** "Call the plumber", "Buy bread" (`R-4.4`, `R-4` clauses 5 and 6).
**Fails if:** the two states look alike, or "done" is painted in the faint text colour that
measured 2.92:1 (`spec/design/ui/system-states.md` § Tokens).

### S-26 — The to-do list opens at its own address
```gherkin
  @req:CR-2609-823a/R-5
  Scenario: Entering the to-do list's own address opens it
    Given the to-do list holds the task "Water the plants"
    When somebody enters the to-do list's own address in the browser
    Then the to-do list should open, showing "Water the plants"
```
**Observed through:** screen. **Data:** "Water the plants" (`R-5.1`).
**Fails if:** the address is reachable only through the navigation, or entering it directly
lands on the not-found page or the guestbook.

### S-27 — From the guestbook to the to-do list without typing an address
```gherkin
  @req:CR-2609-823a/R-5
  Scenario: The to-do list can be reached from the guestbook
    Given somebody is on the guestbook screen
    When they follow the way to the to-do list
    Then the to-do list should open without an address being typed
```
**Observed through:** screen. **Data:** none (`R-5.2`).
**Fails if:** the guestbook screen offers no way to the other screen (`spec/design/ui/system-states.md`
§ One column: a second screen "must add navigation here").

### S-28 — From the to-do list back to the guestbook
```gherkin
  @req:CR-2609-823a/R-5
  Scenario: The guestbook can be reached from the to-do list
    Given somebody is on the to-do list screen
    When they follow the way to the guestbook
    Then the guestbook should open without an address being typed
```
**Observed through:** screen. **Data:** none (`R-5.2`).
**Fails if:** the way between the screens runs in only one direction.

### S-29 — The main address still opens the guestbook
```gherkin
  @req:CR-2609-823a/R-5
  Scenario: The application's main address still opens the guestbook
    When somebody opens the application's main address
    Then the guestbook should be shown
```
**Observed through:** screen. **Data:** none (`R-5.3`, `Q-5`).
**Fails if:** the main address is moved to the to-do list, or to a choice between the two screens.

### S-30 — No page says the application has only one screen
```gherkin
  @req:CR-2609-823a/R-5
  Scenario Outline: No page says the application has only one screen
    Given the application has the guestbook and the to-do list
    When somebody opens <page>
    Then nothing on it should say the application has only one screen

    Examples:
      | page |
      | the guestbook |
      | the to-do list |
      | an address the application does not know |
```
**Observed through:** screen. **Data:** none (`R-5.4`, `R-5` clause 4). The not-found sentence
today reads "There is one screen in this application: the guestbook."
**Fails if:** the not-found page, the footer or any other fixed text keeps a sentence that stopped
being true when the second screen arrived.

### S-31 — Correcting a typo
```gherkin
  @req:CR-2609-823a/R-6
  Scenario: Correcting a typo in a task
    Given the to-do list holds the task "Buy bred", not done
    When somebody changes its text to "Buy bread"
    Then the task should be saved
    And the list should show "Buy bread" in its place
    And "Buy bread" should be shown as not done
```
**Observed through:** application. **Data:** "Buy bred", "Buy bread" (`R-6.1`).
**Fails if:** an edit creates a second task, loses the change, or touches the done state.

### S-32 — Editing a done task keeps it done and in place
```gherkin
  @req:CR-2609-823a/R-6
  Scenario: Editing a done task keeps it done and where it was
    Given the to-do list holds the tasks "Call the plumber" and "Buy bread", added in that order
    And "Call the plumber" is done
    When somebody changes the text of "Call the plumber" to "Call the plumber again"
    Then the list should read "Buy bread", "Call the plumber again"
    And "Call the plumber again" should be shown as done
```
**Observed through:** application. **Data:** "Call the plumber", "Call the plumber again", "Buy
bread" (`R-6.2`, `R-6` clauses 2 and 3).
**Fails if:** editing resets the task to not done, refuses to edit a done task, or re-stamps the
moment of adding.

### S-33 — An edit that breaks a rule is refused and the old text stays
```gherkin
  @req:CR-2609-823a/R-6
  Scenario Outline: An edit breaking a rule is refused and the task keeps its text
    Given the to-do list holds the task "Buy bread"
    When somebody tries to change its text so that <case>
    Then the change should be refused as <reason>
    And the task should still read "Buy bread"

    Examples:
      | case | reason |
      | the text is three spaces | having no text |
      | the text is one character too long | being too long |
      | the text has a line break between two words | being more than one line |
```
**Observed through:** application. **Data:** "Buy bread", plus the texts of the three
`tasks-refused.json` cases of the same sentences (`R-6.3`, `R-6` clause 4).
**Fails if:** an edit is held to weaker rules than an add, or a refused edit still overwrites the
old text.

### S-34 — Deleting one task leaves the rest, for good
```gherkin
  @req:CR-2609-823a/R-7
  Scenario: Deleting one task leaves the others and does not come back
    Given the to-do list holds the tasks "Alpha", "Beta" and "Gamma"
    When somebody deletes "Beta" and confirms
    And the list is reloaded
    Then the to-do list should hold 2 tasks
    And there should be no task "Beta" on the list
    And "Alpha" and "Gamma" should be unchanged
```
**Observed through:** application. **Data:** "Alpha", "Beta", "Gamma" (`R-7.1`, `R-7` clauses 2
and 4).
**Fails if:** the wrong task goes, a neighbour is touched, or the deleted task comes back
(soft-deleted and still read).

### S-35 — Deleting asks first
```gherkin
  @req:CR-2609-823a/R-7
  Scenario: Deleting a task asks for confirmation before anything is deleted
    Given the to-do screen shows the task "Beta"
    When somebody asks to delete "Beta"
    Then they should be asked to confirm
    And "Beta" should still be on the list while they decide
```
**Observed through:** screen. **Data:** "Beta" (`R-7` clause 1).
**Fails if:** one click deletes with no question.

### S-36 — Cancelling a delete keeps the task
```gherkin
  @req:CR-2609-823a/R-7
  Scenario: Cancelling a deletion keeps the task
    Given the to-do screen shows the task "Beta"
    When somebody asks to delete "Beta"
    And they cancel when asked to confirm
    Then "Beta" should still be on the list, unchanged
```
**Observed through:** screen. **Data:** "Beta" (`R-7.2`, `R-7` clause 3).
**Fails if:** the deletion is sent before the confirmation, or cancelling changes the task.

### S-37 — Marking a task somebody else deleted
```gherkin
  @req:CR-2609-823a/R-8
  Scenario: Marking done a task that somebody else deleted
    Given the to-do list holds the task "Buy bread"
    And somebody else has deleted it while this person's screen still shows it
    When this person marks "Buy bread" as done
    Then the change should be refused as being about a task that no longer exists
    And after a reload there should be no task "Buy bread" on the list
```
**Observed through:** application. **Data:** "Buy bread" (`R-8.1`; race `W-3`).
**Fails if:** marking a missing task re-creates it, or reports success for a change it did not
make.

### S-38 — Editing a task somebody else deleted brings nothing back
```gherkin
  @req:CR-2609-823a/R-8
  Scenario: Editing a task that somebody else deleted creates nothing
    Given the to-do list holds the task "Buy bread"
    And somebody else has deleted it while this person's screen still shows it
    When this person changes the text of "Buy bread" to "Buy rye bread"
    Then the change should be refused as being about a task that no longer exists
    And there should be no task "Buy rye bread" on the list
    And the to-do list should hold 0 tasks
```
**Observed through:** application. **Data:** "Buy bread", "Buy rye bread" (`R-8.2`).
**Fails if:** an edit writes by upsert and brings the deleted task back under its new text.

### S-39 — Deleting the same task twice
```gherkin
  @req:CR-2609-823a/R-8
  Scenario: Deleting the same task twice
    Given the to-do list holds the task "Buy bread"
    When somebody deletes "Buy bread" and confirms
    And somebody deletes that task again
    Then the operation should be refused as being about a task that no longer exists
```
**Observed through:** application. **Data:** "Buy bread" (`R-8.3`, `R-8` clause 2).
**Fails if:** the second deletion reports a success it did not perform.

### S-40 — An edit and a tick at the same moment both stick
```gherkin
  @req:CR-2609-823a/R-9
  Scenario: An edit and a tick sent at the same moment are both kept
    Given the to-do list holds the task "Buy bread", not done
    When somebody changes its text to "Buy rye bread" and somebody else marks it done, both before either is answered
    Then the task should read "Buy rye bread"
    And it should be shown as done
```
**Observed through:** application, overlapping (finding 3). **Data:** "Buy bread", "Buy rye
bread" (`R-9.1`; race `W-1`).
**Fails if:** the edit writes the whole task back as it read it, so the tick it never saw is
silently undone, or the tick does the same to the edit.

### S-41 — Two edits at the same moment: the later one wins
```gherkin
  @req:CR-2609-823a/R-9
  Scenario: Two edits at the same moment end with the one applied later
    Given the to-do list holds the task "Buy bread"
    When somebody changes its text to "Buy rye bread" and somebody else changes it to "Buy white bread", both before either is answered
    And the change to "Buy white bread" is applied later
    Then the task should read "Buy white bread"
```
**Observed through:** store-ordered (finding 3). **Data:** "Buy bread", "Buy rye bread", "Buy
white bread" (`R-9.2`).
**Fails if:** the earlier-applied edit survives, or the two texts are merged.

### S-42 — Two people tick the same task done at the same moment
```gherkin
  @req:CR-2609-823a/R-9
  Scenario: Two people marking the same task done at the same moment leave it done
    Given the to-do list holds the task "Buy bread", not done
    When two people both mark it done, both before either is answered
    Then "Buy bread" should be shown as done
```
**Observed through:** application, overlapping. A binding that sends the two one after the other
still catches the flip defect. **Data:** "Buy bread" (`R-9.3`).
**Fails if:** marking flips the stored state, so the second tick undoes the first.

### S-43 — Opposite ticks at the same moment: the later one wins
```gherkin
  @req:CR-2609-823a/R-9
  Scenario: Opposite marks at the same moment end with the one applied later
    Given the to-do list holds the task "Buy bread", not done
    When somebody marks it done and somebody else marks it not done, both before either is answered
    And the mark "not done" is applied later
    Then "Buy bread" should be shown as not done
```
**Observed through:** store-ordered (finding 3). **Data:** "Buy bread" (`R-9` clause 3).
**Fails if:** the state ends as the one applied first, or as something neither person chose.

### S-44 — A tick that did not go through is not shown as made
```gherkin
  @req:CR-2609-823a/R-10
  Scenario: A tick that did not reach the application is not shown as made
    Given the to-do screen shows the task "Buy bread", not done
    And the application cannot be reached
    When somebody marks "Buy bread" as done
    Then the screen should say the change was not made
    And "Buy bread" should still be shown as not done
```
**Observed through:** screen. **Data:** "Buy bread" (`R-10.1`).
**Fails if:** the screen ticks the box ahead of the answer and never rolls it back.

### S-45 — A task that was not added does not appear
```gherkin
  @req:CR-2609-823a/R-10
  Scenario: A task that did not reach the application does not appear on the list
    Given the to-do screen is open and the list is empty
    And the application cannot be reached
    When somebody adds the task "Water the plants"
    Then the screen should say the task was not added
    And no new task should appear on the list
```
**Observed through:** screen. **Data:** "Water the plants" (`R-10.2`).
**Fails if:** the screen draws the new row before the application has stored it.

### S-46 — An edit or a delete that did not go through changes nothing on screen
```gherkin
  @req:CR-2609-823a/R-10
  Scenario Outline: An edit or a deletion that did not reach the application changes nothing
    Given the to-do screen shows the task "Buy bread"
    And the application cannot be reached
    When somebody <action>
    Then the screen should say the change was not made
    And the screen should still show <what stays>

    Examples:
      | action | what stays |
      | changes the text of "Buy bread" to "Buy rye bread" | the task "Buy bread" with its old text |
      | deletes "Buy bread" and confirms | the task "Buy bread" |
```
**Observed through:** screen. **Data:** "Buy bread", "Buy rye bread" (`R-10` clauses 1 and 2).
**Fails if:** the screen shows the new text or removes the row before the application has agreed.

### S-47 — A list that cannot be read is not called empty
```gherkin
  @req:CR-2609-823a/R-10
  Scenario: A to-do list that cannot be read is not called empty
    Given the application cannot be reached
    When the to-do screen is opened
    Then the screen should say the list failed to load
    And it should not say the list is empty
```
**Observed through:** screen. **Data:** none (`R-10.3`).
**Fails if:** a failed read falls through to the empty-list sentence of S-19.

### S-48 — A refused tick on a deleted task is not shown as made
```gherkin
  @req:CR-2609-823a/R-10
  Scenario: A tick the application refuses is not shown as made
    Given the to-do screen shows the task "Buy bread", not done
    And somebody else has deleted "Buy bread" since the screen was loaded
    When this person marks "Buy bread" as done on the screen
    Then the screen should say the task no longer exists
    And it should not show "Buy bread" as done
```
**Observed through:** screen. **Data:** "Buy bread" (`R-10` clause 1, the "refuses the change"
half; `R-8`).
**Fails if:** the screen treats only a network failure as "not made" and shows a refused change as
made.

### S-49 — A freshly created environment opens with example tasks, one of them done
```gherkin
  @req:CR-2609-823a/R-11
  Scenario: A freshly created environment opens with example tasks
    Given a freshly created environment in which neither the guestbook nor the to-do list holds anything
    When it is filled with example data
    Then the to-do list should show at least 3 example tasks
    And at least one of them should be shown as done
```
**Observed through:** person (manual; the black box starts with nothing filled). **Data:**
`golden-set/seed/tasks-welcome.json` (§ Seed data; `R-11.1`, `R-11.7`, `Q-8`, `Q-12`).
**Fails if:** the filler knows the guestbook alone, or adds the example tasks without marking the
done one after adding it.

### S-50 — Filling again adds nothing to a list that already has a task
```gherkin
  @req:CR-2609-823a/R-11
  Scenario: Filling an environment again adds no example task to a list that has one
    Given an environment whose to-do list holds the one task "Water the plants"
    When it is filled with example data again
    Then the to-do list should still hold exactly 1 task, "Water the plants"
```
**Observed through:** person. **Data:** "Water the plants" (`R-11.2`, `R-11` clause 4).
**Fails if:** example tasks pile up on every deploy.

### S-51 — Production is never given example tasks
```gherkin
  @req:CR-2609-823a/R-11
  Scenario: Production is never filled with example tasks
    Given a production environment whose to-do list is empty
    When filling it with example data is attempted
    Then no task should be added
```
**Observed through:** person. **Data:** none (`R-11.3`).
**Fails if:** the filler's production refusal guards the guestbook alone.

### S-52 — Guestbook entries and an empty list: the list is filled
```gherkin
  @req:CR-2609-823a/R-11
  Scenario: An environment with guestbook entries and an empty to-do list gets example tasks
    Given an environment whose guestbook holds its welcome entries and whose to-do list is empty
    When it is filled with example data
    Then the to-do list should show the example tasks
    And the guestbook should hold exactly the entries it held before
```
**Observed through:** person. **Data:** `golden-set/seed/entries-welcome.json`, as it stands, and
`tasks-welcome.json` (`R-11.5`, `Q-10`).
**Fails if:** the filler still treats "anything written anywhere" as one condition, which leaves
stage and every open preview with an empty list. It also fails if the welcome entries are posted
a second time.

### S-53 — Tasks on the list and an empty guestbook: only the guestbook is filled
```gherkin
  @req:CR-2609-823a/R-11
  Scenario: An environment with tasks and an empty guestbook fills only the guestbook
    Given an environment whose to-do list holds the one task "Water the plants" and whose guestbook is empty
    When it is filled with example data
    Then the guestbook should show its welcome entries
    And the to-do list should still hold exactly 1 task, "Water the plants"
```
**Observed through:** person. **Data:** "Water the plants", `entries-welcome.json` (`R-11.6`,
`R-11` clauses 4 and 5, `Q-10`).
**Fails if:** a task on the list stops the guestbook from being filled, or the example tasks are
added next to a task somebody already wrote.

## Requirements no scenario can fully observe

These are findings, not omissions. Each one names the half of a requirement that the seed above
cannot make fail.

1. **`R-4` clause 6 and the contrast half of `R-4.4`.** No suite that owns a citation can measure
   contrast. jsdom loads no application CSS. The UI smoke measures computed styles and
   `tests/fitness/test_design_tokens.py` holds every text token at 4.5:1 or better on every
   surface, but neither owns a citation (`spec/design/testing.md` § The UI smoke is not a
   traceability surface). S-25 proves "shown differently". Its contrast line has no owner unless
   `design-testing` names one, or the clause gets a manual check.
2. **`R-3.2` (two tasks with the same moment of adding).** Nobody outside the application can make
   two adds share a moment. From the black box, S-18 would pass by luck
   (`requirements.md` § Self-check 9). Only a test that stores two tasks with an equal moment can
   observe the tie-break, and that is a test with the database.
3. **`R-9` ("both before either is answered", "applied later").** The black box can send two
   changes together, which is what S-40 and S-42 need. It cannot choose which change the store
   applies later, which S-41 and S-43 need, so the deciding proof of those two belongs to a test
   that controls the interleaving. A binding that sends S-40's two changes one after the other
   passes over the whole-task write-back of race `W-1` and proves nothing
   (`requirements.md` § Self-check 19).
4. **The typing and pasting half of `R-2.3`.** Only a real browser sees a keystroke refused. A
   screen test can see that the field carries no bound counted in UTF-16 units and that the
   screen's rule agrees with the application's on the shared cases. The UI smoke sees the rest and
   owns no citation. S-10 and S-11 are written so that the first two can bind them
   (`requirements.md` § Self-check 5).
5. **`R-11` as a whole.** It is `**Verified-by:** manual`, and the black box starts the application
   with nothing filled. S-49 to S-53 are seeds for the acceptance script, not for the black box.
   `R-11.4` (every example obeys `R-2` and stays under 150 code points) has no scenario at all. The
   corpus's own fitness rules prove it (`tests/fitness/test_golden_set.py`), and they own no
   citation.
6. **The "no bin, no undo, no recovery" half of `R-7` clause 2.** It is an absence. S-34 shows
   that the task does not come back after a reload. That there is no undo anywhere is a fact about
   the screen's copy and controls, and no behaviour can be made to fail on it.
7. **The confirmation itself (`R-7` clauses 1 and 3).** It exists only on the screen. In the black
   box "deletes and confirms" binds to a plain deletion. S-35 and S-36 need a screen test.

## Test data

The reference corpus has two halves and they answer two different questions. **Fixtures**
(`golden-set/fixtures/`) are what a suite reads instead of inventing. **Seed data**
(`golden-set/seed/`) is what a freshly created environment opens with. A value that belongs to
both is two values. Nothing below is written into the corpus now. The implementation stage creates
it (`build-tests-integration` owns `golden-set/fixtures/` and `tests/_golden_set.py`).

### For reuse
| Fixture | What it shows | Requirement |
|---|---|---|
| `golden-set/fixtures/text-measurement.json` | How a field is trimmed and how long it is, read by both languages. Its 13 single-whitespace cases (`only_the_*`, `only_every_trimmed_code_point`) and its two content cases (`zero_width_space_is_content`, `mongolian_vowel_separator_is_content`) prove the one shared rule `R-2` clause 1 borrows, so they need no copy for the task's text **as long as both sides call that one rule**. If the design gives the to-do screen a rule of its own, they are owed again for it. The task's own bound needs cases of its own, specified under § New fixtures as additions to this file. | R-2 |
| `golden-set/seed/entries-welcome.json` | The guestbook's welcome entries, unchanged. S-52 and S-53 read "the guestbook holds its welcome entries" as this file. | R-11 (via `Q-10`) |
| `golden-set/fixtures/entries-ordinary.json`, `entries-boundary.json`, `entries-refused.json` | **Not reusable, and the difference is stated.** Each holds guest book entries (a signature and a message) sized to 80 and 1000. A task is one text sized to 200. Reading a task out of them would make a task test depend on the guestbook's bounds. | none |

### New fixtures
The corpus rules apply to every file below (`golden-set/README.md`). Each file has one story,
carries a `story` and a `demonstrates` line, is named `<story>.json` in lower case with hyphens and
unique across both halves, is registered in `tests/_golden_set.py` under `FIXTURE_FILES` or
`SEED_FILES`, uses code points as its unit, and **computes its bounds from the task's own length
constant** instead of transcribing 200. Nothing in any of them looks like somebody's data: the
texts are errands with no person, place or number in them.

- **`tasks-ordinary.json`** (fixtures). The rule: the whole list, done and not done alike, is
  shown newest first, and a repeated text is two tasks. The requirements: R-3 (clauses 1 and 2),
  R-1 (clause 5). The shape: a sequence in **adding order**, six tasks, each carrying its text and
  whether it is done. Being a sequence, it has no `case` and no `description`. The loader adds all
  six in order and then marks the done ones, because a new task is never born done (`R-1.4`):

  | # (adding order) | Text | Done |
  |---|---|---|
  | 1 | Water the plants | no |
  | 2 | Buy bread | yes |
  | 3 | Check that café · naïve · Ærø · 日本語 · Ωμέγα survive the whole stack | no |
  | 4 | x | no |
  | 5 | Buy bread | no |
  | 6 | Call the plumber | yes |

  S-13 expects the reverse of this table. Boundary values: none; task 4 is the one-character
  minimum as an ordinary value. Personal data: none. The non-ASCII line exists to prove the round
  trip and names nobody. **No line break anywhere**, because `Q-11` refuses one, which collides
  with a corpus rule (§ Bounds the requirements did not give, item 7).
- **`tasks-boundary.json`** (fixtures). The rule: values **exactly on** the bound, every one
  accepted. The requirement: R-2. The shape: five cases, each with a `case` and a sentence a
  scenario names:

  | case | description (the sentence S-5 uses) | Text as sent | Stored as |
  |---|---|---|---|
  | `text_at_maximum` | the text is at the maximum permitted length | 200 ASCII letters | the same 200 |
  | `text_at_maximum_in_emoji` | the text is emoji and at the maximum permitted length | 200 × U+1F600 (400 UTF-16 units) | the same |
  | `text_at_maximum_decomposed` | the text is decomposed accented letters and at the maximum length once composed | 200 × (U+0065 U+0301), 400 code points | 200 × U+00E9 |
  | `text_padded_to_maximum` | the text is padded with spaces and at the maximum length after trimming | 2 spaces + 200 ASCII letters + 2 spaces (204) | the 200 letters |
  | `text_at_minimum` | the text is one character long | "x" | "x" |

  Personal data: none, and every value is letters, emoji or spaces.
- **`tasks-refused.json`** (fixtures). The rule: texts the rules refuse, each naming the refusal it
  expects. The requirements: R-2 and R-6. Crossing a bound is by **one** code point. The shape:
  nine cases:

  | case | description (the sentence S-6, S-8 and S-33 use) | Text as sent | Refused as |
  |---|---|---|---|
  | `text_absent` | the text was not given at all | "" | no text |
  | `text_three_spaces` | the text is three spaces | 3 × U+0020 | no text |
  | `text_all_whitespace` | the text is all whitespace | U+0009 U+3000 U+0020 (tab, ideographic space, space; no line break, so the line-break rule cannot compete) | no text |
  | `text_spaces_past_maximum` | the text is two hundred and five spaces | 205 × U+0020 | no text, **not** too long |
  | `text_one_past_maximum` | the text is one character too long | 201 ASCII letters | too long |
  | `text_one_past_maximum_in_emoji` | the text is emoji and one code point too long | 201 × U+1F600 | too long |
  | `text_one_past_maximum_decomposed` | the text is decomposed accented letters and one past the maximum once composed | 201 × (U+0065 U+0301), 402 code points, 201 once composed | too long |
  | `text_padded_one_past_maximum` | the text is padded with spaces and one character too long after trimming | 2 spaces + 201 ASCII letters + 2 spaces | too long |
  | `text_line_break_inside` | the text has a line break between two words | "Buy bread", U+000A, "and milk" | more than one line (`Q-11`) |

  Personal data: none.
- **Additions to `text-measurement.json`** (fixtures, an existing file). The rule: the screen and
  the application give one verdict and one length for the task's text (`R-2` clause 5, the `D-04`
  lesson). The requirement: R-2. The shape: cases whose field is the task's text. Every input is
  written as an escape, and a length is stated exactly when the text is accepted:

  | Input | Verdict | Length |
  |---|---|---|
  | 200 ASCII letters | accepted | 200 |
  | 201 ASCII letters | too long | none |
  | 200 × U+1F600 | accepted | 200 |
  | 201 × U+1F600 | too long | none |
  | 101 × U+1F600, which is 202 UTF-16 units: under the bound in code points and over it in UTF-16 units | accepted | 101 |
  | 200 × (U+0065 U+0301) | accepted | 200 |
  | 201 × (U+0065 U+0301) | too long | none |
  | 2 spaces + 200 ASCII letters + 2 spaces | accepted | 200 |
  | 205 × U+0020 | empty | none |
  | "Buy bread" U+000A "and milk" | a new verdict for "more than one line" (`Q-11`) | none |
  | "Buy bread", then one of U+000D, U+000B, U+000C, U+0085, U+2028 and U+2029, then "and milk": six cases, one per character | more than one line | none |
  | "Buy" U+0009 "bread" | accepted | 9 |
  | "Buy bread" U+000A | accepted | 9 |

  The 101-emoji case is this field's known positive: a counter of UTF-16 units refuses it and a
  counter of code points accepts it. The seven line-break rows are the set of `R-2` clause 6.
  U+000B, U+000C and U+0085 are the ones on which the two languages' own defaults disagree
  (COH-requirements-4), so they fail a side that reads its language's default instead of the
  written set. U+0085 also fails a task rule borrowed from the signature's, which keeps it between
  two words (case `next_line_inside_is_kept`). The tab is whitespace outside the set, so it is kept
  between two words (`R-2` clause 4). The set is assumption `A-1`: under its other reading,
  U+000A and U+000D alone, the rows for U+000B, U+000C, U+0085, U+2028 and U+2029 become
  accepted. Two things are left to the design, because they touch rules
  the corpus states about itself. First, the verdict set is closed today (accepted, empty, too
  long), and it gains a fourth. Second, exactly one frontend module may read this file, and it
  lives inside the guestbook's folder. See § Bounds the requirements did not give, items 7 and 8.
- **101 tasks for S-14: a producing rule, not a file.** "Task 001" to "Task 101", zero-padded to
  three digits and added in that order. The expectation is derived: "Task 101" first, "Task 001"
  last, and 101 in total. A 101-row file would be a second copy of a counting rule.

### Inline values
Every quoted value a scenario names comes from here. Most are the acceptance values of
`requirements.md` itself, reused rather than invented.

| Value | Scenarios | Source |
|---|---|---|
| "Water the plants" | S-1, S-20, S-26, S-45, S-50, S-53 | `R-1.1` |
| "Buy bread" | S-2, S-9, S-20, S-21 to S-25, S-32, S-33, S-37 to S-44, S-46, S-48 | `R-1.2`, `R-4.1` |
| "Buy bred" | S-31 | `R-6.1` |
| "Buy rye bread", "Buy white bread" | S-38, S-40, S-41, S-46 | `R-8.2`, `R-9.1`, `R-9.2` |
| "Call the plumber", "Call the plumber again" | S-25, S-32 | `R-6.2` |
| "First", "Second", "Third" | S-3, S-12, S-15, S-16, S-17 | `R-3.1` |
| "Second, corrected" | S-16 | this document: an edit whose new text sorts nowhere near the old one |
| "From the other window" | S-17 | this document |
| "Left", "Right" | S-18 | this document: any two texts serve, because the scenario compares two reads rather than naming an order |
| "Already finished" | S-4 | this document |
| "Alpha", "Beta", "Gamma" | S-34, S-35, S-36 | `R-7.1` |
| "Buy  two   lamps" (two spaces, then three) | S-7 | `R-2.6` |
| "Buy bread" followed by U+000A | S-9 | `R-2.7` |
| 200 and 201 × U+1F600 ("grinning-face emoji") | S-10, S-11 | `R-2.3` |

### Seed data
- **`golden-set/seed/tasks-welcome.json`** (new). What it must show: a to-do list worth judging
  on a freshly created environment, with both states visible, the order visible, and characters
  outside ASCII surviving to the screen. The screen: the to-do list. It is a sequence in adding
  order with no `case` and no `description`, and the seeder adds all five and then marks number 3
  done (`Q-12`), because a new task is never born done (`R-1.4`). Nothing is near a bound (the
  longest is 112 code points, under the seed half's 150), nothing has a line break (`Q-11`), and
  no test asserts about it (`test_no_suite_reads_the_seed_corpus`).

  | # (adding order) | Text | Done | Code points |
  |---|---|---|---|
  | 1 | Characters outside ASCII: café · naïve · Ærø · 日本語 · Ωμέγα. If you can read them, they survived the whole stack. | no | 112 |
  | 2 | Delete this one when you have seen enough. It asks first, and a deleted task is gone for good. | no | 94 |
  | 3 | This one is already done. Ticking a task never moves it, and ticking it again brings it back. | yes | 93 |
  | 4 | Correct the words of any task; editing never changes whether it is done. | no | 72 |
  | 5 | These example tasks were put here when the environment was created. Newest first, so this one is at the top. | no | 108 |

  When to fill: the to-do list is filled when it holds no task, **whatever the guestbook holds**
  (`Q-10`), and never in production (`R-11` clause 3). The guestbook keeps its own condition and
  its own file (`entries-welcome.json`, unchanged).

### Multi-day sequences
None by day. No rule here compares one day's data with an earlier day's: there is no balance and
no import. The rules that need more than one state are sequences of **two people acting on one
list**, and the order of those acts is what each scenario proves:

| Sequence | First | Then | Then | What the order proves |
|---|---|---|---|---|
| A screen out of date, same choice (S-23, S-24) | both see "Buy bread" in one state | somebody else marks it the other state | this person marks that same other state | a mark sets the chosen state and never flips the stored one |
| Reload (S-17) | this person reads the list: "First" | somebody else adds "From the other window" | this person reads again | the list is the application's, read fresh every time |
| Deleted underneath (S-37, S-38, S-48) | both see "Buy bread" | somebody else deletes it | this person marks it or edits it | nothing is re-created, and the refusal is the "no longer exists" one |
| Deleted twice (S-39) | "Buy bread" exists | it is deleted and confirmed | it is deleted again | a second deletion refuses rather than reports success |
| Overlapping (S-40 to S-43) | "Buy bread", not done | two changes sent, neither answered yet | both answered, list read | text and state are kept apart, and the change applied later wins within each |
| Filling (S-50, S-52, S-53) | the environment as stated | filling runs | (S-50) filling runs again | each list is filled on its own, and only while it is empty |

### Boundary values
The corpus commits the values **on** the bound (`tasks-boundary.json`) and **one past** it
(`tasks-refused.json`). The value just below is ordinary and is listed here for completeness, not
committed.

| Rule | Just below | Exactly on the boundary | Just above |
|---|---|---|---|
| Task text length after NFC and trimming, ASCII | 199 letters, accepted | 200 letters, accepted and stored whole | 201 letters, refused as too long |
| The same, in emoji (U+1F600) | 199, accepted | 200 (400 UTF-16 units), accepted | 201, refused as too long by the screen and by the application |
| The same, decomposed (U+0065 U+0301 pairs) | 199 pairs, accepted | 200 pairs (400 code points as sent, 200 once composed), accepted and stored as 200 × U+00E9 | 201 pairs (402 as sent, 201 composed), refused as too long |
| The same, padded with two spaces each side | 2 + 199 + 2, accepted | 2 + 200 + 2 = 204 as sent, accepted and stored as the 200 | 2 + 201 + 2, refused as too long |
| Task text minimum after trimming | 0 ("", three spaces, 205 spaces), refused as no text | 1 ("x"), accepted | not a boundary |
| The UTF-16 detector | none | 101 emoji = 202 UTF-16 units, accepted (a UTF-16 counter refuses it) | none |
| Tasks in one read | 100 | 101, all shown with no pages | no ceiling is stated (reported below) |
| Contrast of a done task's text | under 4.5:1, fails | 4.5:1, passes | none |
| Example task length (seed) | none | every example stays under 150; the longest is 112 | none |

### Bounds the requirements did not give
Each item is a gap reported here, not a value chosen to fill it.

1. **Which refusal wins when one text breaks two rules.** A text over 200 code points with a line
   break inside it could be refused as "too long" or as "more than one line". No seed asserts it.
2. **A largest number of tasks.** 101 is the only size any seed uses, and it proves "no pages"
   rather than a ceiling. How many tasks the list holds or shows before one read stops being
   acceptable is unstated (`requirements.md` § Self-check 8).
3. **At least one example task not done.** `Q-12` says at least one is done. That at least one
   stays not done is what "one of the example tasks" suggests, and no floor is stated. The seed
   file shows four not done, which is inside anything the answer could mean, and S-49 does not
   assert the not-done half.
4. **A second press of "add" while the first is still unanswered** (`E-23`), **what the field holds
   after an add succeeds or fails** (`E-28`), **what the screen shows while a write waits 30 s**
   (`E-27`), and **whether the list drops a task at once after "no longer exists"**: no seed
   asserts any of them. S-37, S-38 and S-48 assert only what a reload shows and what the screen
   says.
5. **The words of every message.** "No text", "too long", "more than one line", "no longer
   exists", "not made" and "failed to load" name reasons, not copy. The copy is the mock-up's.
6. **Which change is "applied later" when two overlap.** `R-9` defines "the same moment" and leaves
   "applied later" to the store's order (`requirements.md` § Self-check 18). S-41 and S-43 name
   the later one, and only a test that controls the store's order can make that true.
7. **The corpus rules that collide with a task.** None of these is a value to pick, and each blocks
   the fixtures above until the implementation stage decides it:
   - `tests/fitness/test_golden_set.py::test_the_corpus_exercises_a_message_with_line_breaks`
     demands a line break in every sequence file. `Q-11` refuses a line break inside a task, so
     `tasks-ordinary.json` and `tasks-welcome.json` cannot carry one, and the rule has to be
     scoped to guest book entries.
   - The corpus knows two keys, `entries` for guest book entries and `cases` for inputs to a rule
     (`golden-set/README.md` § When you add a file). A task is neither, and a task file under
     `entries` would be held to `test_every_entry_carries_the_keys_an_entry_has`.
   - `text-measurement.json` has a closed set of verdicts, and `Q-11` adds one.
8. **Who reads the task cases in the browser.** `text-measurement.json` may be read by exactly one
   frontend module, and that module sits in the guestbook's folder
   (`test_the_frontend_reads_no_corpus_file`). If the to-do screen's text rule lives in a context
   of its own, either the shared rule moves out of the guestbook's folder or the exception names
   a second reader. That choice belongs to `design-architecture` and `design-testing`.
