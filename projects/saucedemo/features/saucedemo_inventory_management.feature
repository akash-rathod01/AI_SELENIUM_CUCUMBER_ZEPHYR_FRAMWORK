Feature: Saucedemo inventory management enhancements
  As a Swag Labs quality engineer
  I want coverage for cart adjustments and catalog sorting
  So that I can demonstrate reliable automation flows beyond checkout

  @project:saucedemo @cart
  Scenario: Removing an item updates the cart badge
    Given a Saucedemo user opens the login page
    When the user signs in with standard credentials
    And the user adds the following items to the cart:
      | item                    |
      | Sauce Labs Backpack     |
      | Sauce Labs Bike Light   |
    And the user removes "Sauce Labs Bike Light" from the catalog
    Then the cart badge should display "1"

  @project:saucedemo @sorting
  Scenario: Sorting by price surfaces the lowest-cost item first
    Given a Saucedemo user opens the login page
    When the user signs in with standard credentials
    And the user sorts the inventory by "Price (low to high)"
    Then the first inventory item should display price "$7.99"
    And the inventory should list "Sauce Labs Onesie" first
