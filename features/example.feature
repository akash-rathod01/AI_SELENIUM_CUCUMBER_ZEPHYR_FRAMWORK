Feature: Workday Login
  Scenario: Successful login and skip Remember Me
    Given the user is on the Workday login page
    When the user enters valid credentials
    When the user skips the Remember Device prompt
    Then the user should be on the Workday home page
