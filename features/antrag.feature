Feature: Antrag erstellen mit Testdatenbank

  @db
  Scenario: joe erstellt einen Antrag der in der Liste erscheint
    Given the following users are registered:
      | name | firstname | surname | email        | password  | group      |
      | joe  | Joe       | Tester  | joe@test.com | JoePass1! | user_group |
    And the following observatories exist:
      | name              | site         |
      | Testobservatorium | Teststandort |
    When I login as "joe@test.com" with password "JoePass1!"
    And I create the following Antraege:
      | date       | type | remark      |
      | 2026-12-01 | B    | Test Antrag |
    Then the orders list contains:
      | name       |
      | Joe Tester |
    And the observatory_reservation table contains:
      | date       |
      | 2026-12-01 |

  @db
  Scenario: joe kann ohne Datum keinen Antrag erstellen
    Given the following users are registered:
      | name | firstname | surname | email        | password  | group      |
      | joe  | Joe       | Tester  | joe@test.com | JoePass1! | user_group |
    And the following observatories exist:
      | name              | site         |
      | Testobservatorium | Teststandort |
    When I login as "joe@test.com" with password "JoePass1!"
    And I create an Antrag without a date
    Then the Antrag form is shown again with a date hint
    And no Antrag was created

  @db
  Scenario: joe sieht beim neuen Antrag Kopfdaten und Aufnahmezeilen auf einer Seite
    Given the following users are registered:
      | name | firstname | surname | email        | password  | group      |
      | joe  | Joe       | Tester  | joe@test.com | JoePass1! | user_group |
    And the following observatories exist:
      | name              | site         |
      | Testobservatorium | Teststandort |
    When I login as "joe@test.com" with password "JoePass1!"
    And I open the form for a new Antrag
    Then the new Antrag form shows head and positions
