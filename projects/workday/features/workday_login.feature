Feature: Workday login smoke regression
  As a Workday user
  I want to sign in and bypass the remember device prompt
  So that I can reach the home page without interruptions

  @project:workday
  Scenario: Successful login with device skip
    Given the user launches the Workday portal
    When the user authenticates with valid Workday credentials
    And the user dismisses the remember device overlay
    Then the Workday landing page should be displayed
