Feature: Saucedemo checkout smoke
  As a Swag Labs shopper
  I want to complete a purchase with multiple items
  So that I can validate the end-to-end checkout flow

  @project:saucedemo
  Scenario: Complete checkout with four inventory items
    Given a Saucedemo user opens the login page
    When the user signs in with standard credentials
    And the user adds the following items to the cart:
      | item                     |
      | Sauce Labs Backpack      |
      | Sauce Labs Bolt T-Shirt  |
      | Sauce Labs Onesie        |
      | Sauce Labs Bike Light    |
  Then the cart badge should display "4"
    And the user opens the cart
    And the user proceeds to checkout
    And the user submits checkout information:
      | first_name | last_name | postal_code |
      | Akash      | Rathod    | 445303      |
    Then the order should complete successfully
