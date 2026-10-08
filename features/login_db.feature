Feature: Login with in-memory test database

  @db
  Scenario: Successful login with fixture user
    Given the following users are registered:
      | name     | email            | password  |
      | testuser | test@example.com | TestPass1 |
    When I post login with email "test@example.com" and password "TestPass1"
    Then I am redirected to home
    And the response contains "Abmelden"

  @db
  Scenario: Login fails with wrong password
    Given the following users are registered:
      | name     | email            | password  |
      | testuser | test@example.com | TestPass1 |
    When I post login with email "test@example.com" and password "WrongPass9"
    Then the response contains "Login nicht erfolgreich"

  @db
  Scenario: Successful login with a weak password requires an update
    Given the following users are registered:
      | name     | email            | password |
      | testuser | test@example.com | weakpass |
    When I post login with email "test@example.com" and password "weakpass"
    Then I am redirected to the profile page
    And the response contains "Ihr Passwort muss aktualisiert werden"

  @db
  Scenario: Weak password is accepted when configured
    Given weak passwords are allowed by configuration
    And the following users are registered:
      | name     | email            | password |
      | testuser | test@example.com | weakpass |
    When I post login with email "test@example.com" and password "weakpass"
    Then I am redirected to home
    And the response contains "Abmelden"

  @db
  Scenario: Weak password change is rejected when weak passwords are disabled
    Given the following users are registered:
      | name     | email            | password  |
      | testuser | test@example.com | TestPass1 |
    When I post login with email "test@example.com" and password "TestPass1"
    And I change my password from "TestPass1" to "weakpass"
    Then I am redirected to the profile page
    And the response contains "Das Passwort muss mindestens 8 Zeichen lang sein"

  @db
  Scenario: Weak password change is accepted when weak passwords are configured
    Given weak passwords are allowed by configuration
    And the following users are registered:
      | name     | email            | password  |
      | testuser | test@example.com | TestPass1 |
    When I post login with email "test@example.com" and password "TestPass1"
    And I change my password from "TestPass1" to "weakpass"
    Then I am redirected to the password changed page
    And the response contains "Ihr Passwort wurde aktualisiert"

  @db
  Scenario: Weak password is accepted during registration when configured
    Given weak passwords are allowed by configuration
    When I register user "weakuser" with password "weakpass"
    Then I am redirected to login
    And the response contains "Ihr Benutzer ist registriert!"
