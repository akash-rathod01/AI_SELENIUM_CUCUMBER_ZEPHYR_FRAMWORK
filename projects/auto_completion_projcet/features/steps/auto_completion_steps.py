from behave import given, when, then


@given("the Auto Completion application is reachable")
def step_app_reachable(context):
    """Verify the home page loads successfully."""
    assert context.driver.current_url, "Driver not initialized"
    assert "dotesthere" in context.driver.current_url.lower()


@when("I initialise the automation context")
def step_initialise_context(context):
    """Context is already initialized by environment hooks."""
    assert hasattr(context, "driver")
    assert hasattr(context, "page")


@then("I should replace this scenario with a real end-to-end flow")
def step_replace_with_real_flow(context):
    """Verify page object is accessible."""
    title = context.page.driver.title
    assert "DoTestHere" in title or len(title) > 0
