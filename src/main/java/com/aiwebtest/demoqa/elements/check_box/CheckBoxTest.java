package com.aiwebtest.demoqa.elements.check_box;

import com.aiwebtest.testing.DriverContext;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.Assert;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

public class CheckBoxTest {
    private WebDriver driver;

    @BeforeClass
    public void setUp() {
        driver = new ChromeDriver();
        DriverContext.setDriver(driver);
        driver.manage().window().maximize();
        driver.get("https://demoqa.com/checkbox");
    }

    @Test
    public void testCheckBox() {
        WebElement expandAll = driver.findElement(By.cssSelector("button[title='Expand all']"));
        expandAll.click();
        WebElement homeCheckBox = driver.findElement(By.cssSelector("span.rct-checkbox"));
        homeCheckBox.click();
        WebElement result = driver.findElement(By.id("result"));
        Assert.assertTrue(result.getText().contains("home"));
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
