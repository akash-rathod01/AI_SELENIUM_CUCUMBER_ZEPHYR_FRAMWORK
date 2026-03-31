package com.aiwebtest.demoqa.elements.buttons;

import com.aiwebtest.testing.DriverContext;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.interactions.Actions;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.testng.Assert;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.time.Duration;

public class ButtonsTest {
    private WebDriver driver;

    @BeforeClass
    public void setUp() {
        driver = new ChromeDriver();
        DriverContext.setDriver(driver);
        driver.manage().window().maximize();
        driver.get("https://demoqa.com/buttons");
    }

    @Test
    public void testDoubleClickButton() {
        WebElement doubleClickBtn = driver.findElement(By.id("doubleClickBtn"));
        new Actions(driver).doubleClick(doubleClickBtn).perform();

        WebElement message = new WebDriverWait(driver, Duration.ofSeconds(10))
                .until(ExpectedConditions.visibilityOfElementLocated(By.id("doubleClickMessage")));
        Assert.assertTrue(message.getText().contains("You have done a double click"));
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
