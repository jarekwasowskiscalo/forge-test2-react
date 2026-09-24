Feature: To-do list

  # The one to-do list everybody who opens the application shares, described in the
  # language a person uses about it. A task is one line of text, and it is done or
  # not done. This file is read instead of the code when somebody asks what the
  # to-do list actually does -- which is why there is no address, no field name and
  # no technical code in it.
  #
  # Every scenario starts from an empty to-do list: the world is cleaned before each
  # of them, so the numbers below are this scenario's numbers rather than the sum of
  # what earlier ones left behind.
  #
  # Nobody signs in anywhere in this file, and that is the point rather than an
  # omission: the application has no accounts, so every scenario below is also a
  # scenario in which nobody signed in.
  #
  # What is not here, and where it is proved instead. The tasks that sit exactly on
  # the size limit, the texts that are refused, and the long list of ordinary tasks
  # live in the reference corpus and are checked by a cheaper suite that reads the
  # corpus directly. What only the screen can show -- the confirmation before a
  # deletion, the look of a done task, what the screen says when a change did not go
  # through -- is checked by the screen's own tests. And which of two simultaneous
  # changes the application applies later can only be arranged by a test that holds
  # the stored list itself, so that one is not here either.

  # Adding a task.

  @req:CR-2609-823a/R-1
  Scenario: Adding the first task
    Given the to-do list is empty
    When somebody adds the task "Water the plants"
    Then the task should be saved
    And the to-do list should hold 1 task
    And the task "Water the plants" should be shown as not done

  # The same words twice are two tasks, never one merged into the other -- and
  # marking one of them done is what shows they are two.
  @req:CR-2609-823a/R-1
  Scenario: The same text added twice makes two separate tasks
    Given the to-do list holds the task "Buy bread"
    When somebody adds the task "Buy bread" again
    And somebody marks the newer "Buy bread" as done
    Then the to-do list should hold 2 tasks reading "Buy bread"
    And the older "Buy bread" should still be shown as not done

  # Only somebody going around the screen can send this, because the screen's field
  # cannot. A new task is never born done, whatever it claims.
  @req:CR-2609-823a/R-1
  Scenario: A task sent as already done is still saved as not done
    Given the to-do list is empty
    When somebody adds the task "Already finished", sent as if it were already done
    Then the task should be saved
    And the task "Already finished" should be shown as not done

  # What a task's text may be.

  @req:CR-2609-823a/R-2
  Scenario: Spaces between the words of a task are kept as typed
    Given the to-do list is empty
    When somebody adds the task "Buy  two   lamps"
    Then the task should be saved
    And the stored text should be exactly "Buy  two   lamps", with its two and three spaces

  # A line break inside a task is refused, but one after the last word is trimmed
  # away like a trailing space, because the ends are trimmed before anything is
  # judged.
  @req:CR-2609-823a/R-2
  Scenario: A line break after the last word is trimmed, not refused
    Given the to-do list is empty
    When somebody adds the task "Buy bread" with a line break after it
    Then the task should be saved
    And the stored text should be exactly "Buy bread"

  # One list, one order: newest first, and nothing a person does to a task moves it.

  @req:CR-2609-823a/R-3
  Scenario: The list shows the newest task at the top
    Given the to-do list holds the tasks "First", "Second" and "Third", added in that order
    When the to-do list is displayed
    Then it should read "Third", "Second", "First"

  # The list is read whole. A list handed out a piece at a time would lose the
  # oldest task without a word, and a hundred and one is one more than any piece.
  @req:CR-2609-823a/R-3
  Scenario: A hundred and one tasks are all shown on one list
    Given 101 tasks have been added, "Task 001" first and "Task 101" last
    When the to-do list is displayed
    Then all 101 tasks should be shown at once
    And "Task 101" should be at the top and "Task 001" at the bottom

  @req:CR-2609-823a/R-3
  Scenario: Marking a task done leaves it where it was
    Given the to-do list holds the tasks "First", "Second" and "Third", added in that order
    When somebody marks "Second" as done
    Then the list should still read "Third", "Second", "First"

  # "Newest" means the moment a task was added, never the moment it was last changed.
  @req:CR-2609-823a/R-3
  Scenario: Correcting a task's text leaves it where it was
    Given the to-do list holds the tasks "First", "Second" and "Third", added in that order
    When somebody changes the text of "Second" to "Second, corrected"
    Then the list should read "Third", "Second, corrected", "First"

  # The list belongs to the application, not to one visitor: what one person adds,
  # the next person to read the list sees.
  @req:CR-2609-823a/R-3
  Scenario: A task somebody else added appears after a reload
    Given somebody has the to-do list open, showing the task "First"
    When somebody else adds the task "From the other window"
    And the first person reloads the list
    Then "From the other window" should be at the top of their list

  # Marking a task done, and back.

  @req:CR-2609-823a/R-4
  Scenario: A task marked done stays done after a reload
    Given the to-do list holds the task "Buy bread", not done
    When somebody marks "Buy bread" as done
    And the list is reloaded
    Then "Buy bread" should be shown as done
    And its text should still be "Buy bread"

  @req:CR-2609-823a/R-4
  Scenario: A task marked done by mistake goes back to not done
    Given the to-do list holds the task "Buy bread", done
    When somebody marks "Buy bread" as not done
    And the list is reloaded
    Then "Buy bread" should be shown as not done

  # Marking sets the state the person chose; it never flips whatever is stored. Two
  # people who both chose done must both end with the task done.
  @req:CR-2609-823a/R-4
  Scenario: Marking done a task that is already done leaves it done
    Given the to-do list holds the task "Buy bread", not done
    And somebody else has marked it done while this person's screen still shows it not done
    When this person marks "Buy bread" as done
    Then the task should be saved
    And "Buy bread" should be shown as done

  @req:CR-2609-823a/R-4
  Scenario: Marking not done a task that is already not done leaves it not done
    Given the to-do list holds the task "Buy bread", done
    And somebody else has marked it not done while this person's screen still shows it done
    When this person marks "Buy bread" as not done
    Then the task should be saved
    And "Buy bread" should be shown as not done

  # Correcting a task's text.

  @req:CR-2609-823a/R-6
  Scenario: Correcting a typo in a task
    Given the to-do list holds the task "Buy bred", not done
    When somebody changes its text to "Buy bread"
    Then the task should be saved
    And the list should show "Buy bread" in its place
    And "Buy bread" should be shown as not done

  @req:CR-2609-823a/R-6
  Scenario: Editing a done task keeps it done and where it was
    Given the to-do list holds the tasks "Call the plumber" and "Buy bread", added in that order
    And "Call the plumber" is done
    When somebody changes the text of "Call the plumber" to "Call the plumber again"
    Then the list should read "Buy bread", "Call the plumber again"
    And "Call the plumber again" should be shown as done

  # Deleting a task. On the screen a deletion is asked about first; here the
  # question has already been answered, so "deletes and confirms" is one deletion.

  @req:CR-2609-823a/R-7
  Scenario: Deleting one task leaves the others and does not come back
    Given the to-do list holds the tasks "Alpha", "Beta" and "Gamma"
    When somebody deletes "Beta" and confirms
    And the list is reloaded
    Then the to-do list should hold 2 tasks
    And there should be no task "Beta" on the list
    And "Alpha" and "Gamma" should be unchanged

  # A task that no longer exists. A change aimed at it is refused, and nothing
  # brings it back -- not a marking, not a correction, not a second deletion.

  @req:CR-2609-823a/R-8
  Scenario: Marking done a task that somebody else deleted
    Given the to-do list holds the task "Buy bread"
    And somebody else has deleted it while this person's screen still shows it
    When this person marks "Buy bread" as done
    Then the change should be refused as being about a task that no longer exists
    And after a reload there should be no task "Buy bread" on the list

  @req:CR-2609-823a/R-8
  Scenario: Editing a task that somebody else deleted creates nothing
    Given the to-do list holds the task "Buy bread"
    And somebody else has deleted it while this person's screen still shows it
    When this person changes the text of "Buy bread" to "Buy rye bread"
    Then the change should be refused as being about a task that no longer exists
    And there should be no task "Buy rye bread" on the list
    And the to-do list should hold 0 tasks

  @req:CR-2609-823a/R-8
  Scenario: Deleting the same task twice
    Given the to-do list holds the task "Buy bread"
    When somebody deletes "Buy bread" and confirms
    And somebody deletes that task again
    Then the operation should be refused as being about a task that no longer exists

  # Two people changing one task at the same moment. Both changes are sent before
  # either is answered. A correction and a tick touch different things, so both are
  # kept; two ticks that chose done leave the task done. From outside the
  # application nobody can make the two meet at exactly the same instant, so these
  # catch the defect on the runs where they do meet and pass on a correct
  # application every time.

  @req:CR-2609-823a/R-9
  Scenario: An edit and a tick sent at the same moment are both kept
    Given the to-do list holds the task "Buy bread", not done
    When somebody changes its text to "Buy rye bread" and somebody else marks it done, both before either is answered
    Then the task should read "Buy rye bread"
    And it should be shown as done

  @req:CR-2609-823a/R-9
  Scenario: Two people marking the same task done at the same moment leave it done
    Given the to-do list holds the task "Buy bread", not done
    When two people both mark it done, both before either is answered
    Then "Buy bread" should be shown as done
