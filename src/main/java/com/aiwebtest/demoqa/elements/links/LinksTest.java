package com.aiwebtest.demoqa.elements.links;

import com.aiwebtest.testing.DriverContext;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.Assert;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

public class LinksTest {
    private WebDriver driver;

    @BeforeClass
    public void setUp() {
        driver = new ChromeDriver();
        DriverContext.setDriver(driver);
        driver.manage().window().maximize();
        driver.get("https://demoqa.com/links");
    }

    @Test
    public void testHomeLink() {
        WebElement homeLink = driver.findElement(By.id("simpleLink"));
        homeLink.click();
        // Switch to new tab and verify URL
        for (String handle : driver.getWindowHandles()) {
            driver.switchTo().window(handle);
        }
        Assert.assertTrue(driver.getCurrentUrl().contains("demoqa.com"));
    }

    @AfterClass
    public void tearDown() {
        try {
            if (driver != null) {
                driver.quit();
            }
        } finally {
            DriverContext.clear();
        }
    }
}
