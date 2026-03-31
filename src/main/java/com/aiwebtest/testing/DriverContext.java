package com.aiwebtest.testing;

import org.openqa.selenium.WebDriver;

/**
 * Minimal placeholder for DriverContext. Adjust as needed for your framework.
 */
public class DriverContext {
    private static WebDriver driver;

    public static WebDriver getDriver() {
        return driver;
    }

    public static void setDriver(WebDriver webDriver) {
        driver = webDriver;
    }

    public static void clear() {
        driver = null;
    }
}
