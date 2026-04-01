Feature: DoTestHere smoke coverage

  Background:
    Given the application is prepared

  Scenario: Home page responds successfully
    When Ensure the page at https://dotesthere.com/ responds with HTTP 200 and displays the title 'DoTestHere.com - Free Automation Testing Practice Hub | Selenium, Playwright, API Testing'.
    Then the expected outcome should be verified

  Scenario: API Testing page responds successfully
    When Ensure the page at https://dotesthere.com/api-testing responds with HTTP 200 and displays the title 'API Testing Practice Hub - DoTestHere.com | Free REST API Testing Environment'.
    Then the expected outcome should be verified

  Scenario: Manual Testing Lab responds successfully
    When Ensure the page at https://dotesthere.com/manual-testing-lab responds with HTTP 200 and displays the title 'Manual Testing Practice Lab - DoTestHere.com | Free Testing Practice Environment'.
    Then the expected outcome should be verified

  Scenario: Author page responds successfully
    When Ensure the page at https://dotesthere.com/author responds with HTTP 200 and displays the title 'About Ankur Malviya - QA Automation Engineer | DoTestHere.com'.
    Then the expected outcome should be verified

  Scenario: Manual Testing Lab pricing calculator
    When I complete the manual lab pricing calculator form
    Then the expected outcome should be verified

  Scenario: Manual Testing Lab blur effects
    When I configure manual lab blur controls
    Then the expected outcome should be verified

  Scenario: Manual Testing Lab format validation
    When I validate manual lab format inputs
    Then the expected outcome should be verified

    Then the manual lab inputs should reflect the entered data

  Scenario: Primary navigation links are reachable
    When I capture the primary navigation links
    Then each captured navigation link should respond with HTTP 200
