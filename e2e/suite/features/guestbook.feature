Feature: Guestbook

  # The four operations this application can perform, described in the language a
  # non-technical person uses about them. This file is read instead of the code when
  # somebody asks "what does this application actually do" -- which is why there is
  # not one HTTP code, not one column name and not one path in it.
  #
  # Every scenario starts from an empty guestbook: the world is cleaned before each
  # of them (e2e/suite/conftest.py), so the numbers below are this scenario's
  # numbers rather than the sum of what earlier ones left behind.

  @req:CR-2609-9b1e/R-1
  Scenario: Leaving the first entry
    Given the guestbook is empty
    When a guest leaves an entry signed "Anna" with the message "Good morning!"
    Then the entry should be saved
    And the guestbook should hold 1 entry

  @req:CR-2609-9b1e/R-2
  Scenario: An entry with no signature is not saved
    Given the guestbook is empty
    When a guest tries to leave an entry with no signature
    Then the entry should be refused
    And the guestbook should hold 0 entries

  @req:CR-2609-9b1e/R-2
  Scenario: An entry with no message is not saved
    Given the guestbook is empty
    When a guest tries to leave an entry with no message
    Then the entry should be refused
    And the guestbook should hold 0 entries

  # The order is a promise made in the specification (BR-04) rather than an accident
  # of write order -- which is why it is a scenario and not a comment.
  @req:CR-2609-9b1e/R-3
  Scenario: The list shows the newest entry at the top
    Given the guestbook holds entries signed "first", "second" and "third"
    When the guestbook is displayed
    Then the entry signed "third" should be at the top of the list
    And the guestbook should hold 3 entries

  @req:CR-2609-9b1e/R-4
  Scenario: Amending an entry's message
    Given the guestbook holds an entry signed "Anna" with the message "first version"
    When the author amends that entry's message to "second version"
    Then the entry should be saved
    And that entry should have the message "second version"
    And that entry should be marked as edited
    And the guestbook should hold 1 entry

  # The date it was written survives every later amendment -- this is the half of
  # BR-02 nobody sees until somebody breaks it.
  @req:CR-2609-9b1e/R-4
  Scenario: An amendment does not change the date the entry was written
    Given the guestbook holds an entry signed "Anna" with the message "first version"
    When the author amends that entry's message to "second version"
    Then the date that entry was written should not change

  @req:CR-2609-9b1e/R-4
  Scenario: Amending an entry that is not there
    Given the guestbook is empty
    When somebody tries to amend an entry that is not there
    Then the operation should be refused as being about an entry that does not exist

  @req:CR-2609-9b1e/R-5
  Scenario: Deleting an entry
    Given the guestbook holds an entry signed "Anna" with the message "to be deleted"
    When the author deletes that entry
    Then the guestbook should hold 0 entries

  # Deletion is permanent (BR-03), so a second deletion of the same entry has to
  # refuse rather than report the success of something it did not do.
  @req:CR-2609-9b1e/R-5
  Scenario: Deleting the same entry twice
    Given the guestbook holds an entry signed "Anna" with the message "to be deleted"
    When the author deletes that entry
    And the author deletes that entry again
    Then the operation should be refused as being about an entry that does not exist

  @req:CR-2609-9b1e/R-5
  Scenario: Deleting one entry leaves the rest
    Given the guestbook holds entries signed "first", "second" and "third"
    When the author deletes the entry signed "second"
    Then the guestbook should hold 2 entries
    And there should be no entry signed "second" in the guestbook

  # The scenarios below take their data from the reference corpus instead of
  # inventing it. The case names are sentences, because this file is read by
  # somebody who does not write code; the steps find them in the corpus by that
  # sentence and by nothing else.

  @req:CR-2609-9b1e/R-3
  Scenario: The guestbook shows everything the guests left
    Given the guests have already left their entries
    When the guestbook is displayed
    Then the guestbook should show every entry that was left
    And they should be ordered newest first

  @req:CR-2609-9b1e/R-1
  Scenario: Characters outside ASCII survive a write and a read
    Given the guests have already left their entries
    When the entry with non-ASCII characters is looked up
    Then its message should come back unchanged

  @req:CR-2609-9b1e/R-2
  Scenario Outline: An entry at the boundary size is accepted
    Given the guestbook is empty
    When a guest leaves an entry in which <case>
    Then the entry should be saved
    And the stored message should be exactly what was sent

    Examples:
      | case |
      | the signature is at the maximum permitted length |
      | the message is at the maximum permitted length |
      | the signature and the message are one character each |
      | the signature is padded with spaces and is at the maximum length after trimming |
      | the signature is emoji and at the maximum permitted length |

  @req:CR-2609-9b1e/R-2
  Scenario Outline: An entry breaking a rule is not saved
    Given the guestbook is empty
    When a guest tries to leave an entry in which <case>
    Then the entry should be refused
    And the guestbook should hold 0 entries

    Examples:
      | case |
      | the signature was not given at all |
      | the signature is all spaces |
      | the signature is all whitespace |
      | the message was not given at all |
      | the message is all whitespace |
      | the signature is one character too long |
      | the message is one character too long |
      | the signature is emoji and one code point too long |

  # Search, order and paging (BR-05). A guestbook that has grown stops fitting on
  # one screen: a guest has to be able to find an entry and view the rest a piece at
  # a time, and how many entries match is a different number from how many are shown.

  @req:CR-2609-9b1e/R-6
  Scenario: A guest finds an entry by its signature
    Given the guestbook holds entries signed "first", "second" and "third"
    When a guest searches for entries containing "second"
    Then they should find 1 matching entry
    And the entry signed "second" should be at the top of the list

  # Searching the signature alone would lose half the matches, and lose them in a way
  # that looks like there being no entries.
  @req:CR-2609-9b1e/R-6
  Scenario: A guest finds an entry by its message, not only by its signature
    Given the guestbook holds an entry signed "Anna" with the message "greetings from Lisbon"
    When a guest searches for entries containing "Lisbon"
    Then they should find 1 matching entry

  @req:CR-2609-9b1e/R-6
  Scenario: Searching ignores case
    Given the guestbook holds an entry signed "Anna" with the message "anything"
    When a guest searches for entries containing "anna"
    Then they should find 1 matching entry

  # "Nothing matches" and "the guestbook is empty" are two different sentences, and
  # the screen can only tell them apart when it is given both numbers.
  @req:CR-2609-9b1e/R-7
  Scenario: A search that finds nothing does not empty the guestbook
    Given the guestbook holds entries signed "first", "second" and "third"
    When a guest searches for entries nobody wrote
    Then they should find 0 matching entries
    And the guestbook should hold 3 entries

  @req:CR-2609-9b1e/R-3
  Scenario: The guestbook can be read oldest first
    Given the guestbook holds entries signed "first", "second" and "third"
    When the guestbook is displayed oldest first
    Then the entry signed "first" should be at the top of the list

  # How many entries the whole guestbook holds is the one number a piece cannot tell
  # about itself -- and without it "show more" cannot be written.
  @req:CR-2609-9b1e/R-7
  Scenario: A piece of the guestbook says how many entries there are in total
    Given the guests have already left their entries
    When a guest views the first 2 entries
    Then they should see 2 entries
    And they should be told how many entries the whole guestbook holds

  @req:CR-2609-9b1e/R-7
  Scenario: Viewing the guestbook a piece at a time shows every entry exactly once
    Given the guests have already left their entries
    When a guest views the guestbook 2 entries at a time, to the end
    Then they should see every entry exactly once
