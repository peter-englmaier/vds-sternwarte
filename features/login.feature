Feature: Login to webpage

  Scenario: login to website
    Given I am on the home page
    When I click on the "Anmelden" Link
    And I enter the admin credentials
    Then I am logged in

  Scenario: Successful login with existing user
    Given the following users are registered:
      | name     | email            | password  |
      | testuser | test@example.com | TestPass1 |
    When I post login with email "test@example.com" and password "TestPass1"
    Then I am redirected to home
    And the response contains "Abmelden"

  Scenario: Login fails with wrong password
    Given the following users are registered:
      | name     | email            | password  |
      | testuser | test@example.com | TestPass1 |
    When I post login with email "test@example.com" and password "WrongPass9"
    Then the response contains "Login nicht erfolgreich"

