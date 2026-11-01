Feature: Antrag erstellen mit Testdatenbank

  @db
  Scenario: joe erstellt einen Antrag der in der Liste erscheint
    Given the following users are registered:
      | name | email        | password  | group      |
      | joe  | joe@test.com | JoePass1! | user_group |
    And the following observatories exist:
      | name              | site         |
      | Testobservatorium | Teststandort |
    When I login as "joe@test.com" with password "JoePass1!"
    And I create the following Antraege:
      | requester_name | date       | type | remark      |
      | Joe Tester     | 2026-12-01 | B    | Test Antrag |
    Then the orders list contains:
      | name       |
      | Joe Tester |
    And the observatory_reservation table contains:
      | date       |
      | 2026-12-01 |

  @db
  Scenario: joe kann ohne Datum keinen Antrag erstellen
    Given the following users are registered:
      | name | email        | password  | group      |
      | joe  | joe@test.com | JoePass1! | user_group |
    And the following observatories exist:
      | name              | site         |
      | Testobservatorium | Teststandort |
    When I login as "joe@test.com" with password "JoePass1!"
    And I create an Antrag without a date
    Then the Antrag form is shown again with a date hint
    And no Antrag was created
