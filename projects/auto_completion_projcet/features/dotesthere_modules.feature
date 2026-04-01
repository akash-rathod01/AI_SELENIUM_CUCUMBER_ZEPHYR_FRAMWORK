Feature: DoTestHere.com - Complete Module Testing Coverage
  Comprehensive automation coverage for all dotesthere.com practice modules

  Background:
    Given the application is prepared

  # Smoke Tests
  Scenario: Verify dotesthere.com home page accessibility
    When Ensure the page at https://dotesthere.com/ responds with HTTP 200 and displays the title 'DoTestHere.com - Free Automation Testing Practice Hub | Selenium, Playwright, API Testing'.
    Then the expected outcome should be verified

  # A/B Testing Module
  Scenario: Test A/B version switching functionality
    Given the user navigates to AB Testing module
    When the user clicks Switch Version button
    Then the heading text should change between Version A and Version B

  # Add/Remove Elements Module
  Scenario: Add and remove dynamic elements
    Given the user navigates to Add/Remove Elements module
    When the user clicks Add Element button 3 times
    Then 3 delete buttons should be present
    When the user clicks first delete button
    Then 2 delete buttons should be present

  # Basic Auth Module
  Scenario: Trigger basic authentication simulation
    Given the user navigates to Basic Auth module
    When the user clicks Authenticate button
    Then auth result should display success message

  # Broken Images Module
  Scenario: Detect broken images on page
    Given the user navigates to Broken Images module
    When the page loads all images
    Then broken images should be identified

  # Challenging DOM Module
  Scenario: Interact with dynamic table actions
    Given the user navigates to Challenging DOM module
    When the user clicks Edit button for first row
    Then the action should be captured
    When the user clicks Delete button for first row
    Then the action should be captured

  # Checkboxes Module
  Scenario: Toggle checkbox states
    Given the user navigates to Checkboxes module
    When the user toggles checkbox1
    Then checkbox1 state should change
    When the user toggles checkbox2
    Then checkbox2 state should change

  # Context Menu Module
  Scenario: Right-click context menu interaction
    Given the user navigates to Context Menu module
    When the user right-clicks on hot-spot element
    Then context menu alert should appear
    When the user accepts the alert
    Then alert should be dismissed

  # Disappearing Elements Module
  Scenario: Verify gallery link visibility toggle
    Given the user navigates to Disappearing Elements module
    When the page loads navigation elements
    Then gallery link visibility should be verified

  # Drag and Drop Module
  Scenario: Drag column A to column B
    Given the user navigates to Drag and Drop module
    When the user drags column-a to column-b
    Then drag status should show successful swap

  # Dropdown Module
  Scenario: Select dropdown options
    Given the user navigates to Dropdown module
    When the user selects Option 1 from dropdown
    Then selected option should be Option 1
    When the user selects Option 2 from dropdown
    Then selected option should be Option 2

  # Dynamic Content Module
  Scenario: Refresh dynamic content
    Given the user navigates to Dynamic Content module
    When the user clicks Refresh Content button
    Then content area should update with new text

  # Dynamic Controls Module
  Scenario: Toggle dynamic checkbox visibility
    Given the user navigates to Dynamic Controls module
    When the user clicks Add/Remove button
    Then checkbox presence should toggle

  Scenario: Enable/Disable dynamic input
    Given the user navigates to Dynamic Controls module
    When the user clicks Enable/Disable button
    Then input field enabled state should toggle

  # Dynamic Loading Module
  Scenario: Wait for loading spinner completion
    Given the user navigates to Dynamic Loading module
    When the user clicks Start button
    Then loading spinner should appear and disappear
    And finish text should be displayed

  # File Download Module
  Scenario: Download sample file
    Given the user navigates to File Download module
    When the user clicks download link
    Then file should be downloaded successfully

  # File Upload Module
  Scenario: Upload file via input
    Given the user navigates to File Upload module
    When the user selects a file and clicks upload
    Then upload result should confirm success

  # Form Authentication Module
  Scenario: Login with valid credentials
    Given the user navigates to Form Authentication module
    When the user enters username tomsmith
    And the user enters password SuperSecretPassword!
    And the user clicks login button
    Then flash message should display success

  # Frames Module
  Scenario: Switch between iframe contexts
    Given the user navigates to Frames module
    When the user switches to frame1
    Then frame1 content should be accessible
    When the user switches back to default content
    And the user switches to frame2
    Then frame2 content should be accessible

  # Horizontal Slider Module
  Scenario: Adjust slider value
    Given the user navigates to Horizontal Slider module
    When the user moves slider to position 5
    Then slider value should display 5

  # Hovers Module
  Scenario: Hover over figure elements
    Given the user navigates to Hovers module
    When the user hovers over figure 1
    Then caption for user1 should appear
    When the user hovers over figure 2
    Then caption for user2 should appear

  # JavaScript Alerts Module
  Scenario: Handle JS Alert
    Given the user navigates to JavaScript Alerts module
    When the user clicks JS Alert button
    Then alert with message should appear
    When the user accepts the alert
    Then alert should be dismissed

  Scenario: Handle JS Confirm - Accept
    Given the user navigates to JavaScript Alerts module
    When the user clicks JS Confirm button
    And the user accepts the confirm
    Then result should show OK

  Scenario: Handle JS Confirm - Dismiss
    Given the user navigates to JavaScript Alerts module
    When the user clicks JS Confirm button
    And the user dismisses the confirm
    Then result should show Cancel

  Scenario: Handle JS Prompt with input
    Given the user navigates to JavaScript Alerts module
    When the user clicks JS Prompt button
    And the user enters Test Input in prompt
    And the user accepts the prompt
    Then result should show Test Input

  # Key Presses Module
  Scenario: Capture key press events
    Given the user navigates to Key Presses module
    When the user focuses on target input
    And the user presses ENTER key
    Then key result should display ENTER
    When the user presses TAB key
    Then key result should display TAB

  # Multiple Windows Module
  Scenario: Open and switch to new window
    Given the user navigates to Multiple Windows module
    When the user clicks Click Here button
    Then new window should open
    When the user switches to new window
    Then new window content should be verified
    When the user closes new window and switches back
    Then original window should be active

  # Shadow DOM Module
  Scenario: Access shadow DOM elements
    Given the user navigates to Shadow DOM module
    When the page loads shadow host
    Then shadow root content should be accessible

  # Sortable Tables Module
  Scenario: Sort table by Last Name
    Given the user navigates to Sortable Tables module
    When the user clicks Last Name header
    Then table should be sorted by Last Name

  Scenario: Sort table by First Name
    Given the user navigates to Sortable Tables module
    When the user clicks First Name header
    Then table should be sorted by First Name

  # WYSIWYG Editor Module
  Scenario: Edit content in TinyMCE editor
    Given the user navigates to WYSIWYG Editor module
    When the user switches to editor iframe
    And the user types Sample Test Content
    And the user switches back to default content
    Then editor should contain Sample Test Content

  # Manual Testing Lab - Pricing Calculator
  Scenario: Calculate total with pricing inputs
    When I complete the manual lab pricing calculator form
    Then the expected outcome should be verified

  # Manual Testing Lab - Blur Effects
  Scenario: Apply blur effects to text
    When I configure manual lab blur controls
    Then the expected outcome should be verified

  # Manual Testing Lab - Format Validation
  Scenario: Validate input formats
    When I validate manual lab format inputs
    Then the expected outcome should be verified

  # Manual Testing Lab - Layout Testing
  Scenario: Apply grid layout settings
    When I configure manual lab grid layout
    Then the expected outcome should be verified

  # Manual Testing Lab - Visual Testing
  Scenario: Apply visual theme settings
    When I configure manual lab visual theme
    Then the expected outcome should be verified
