package com.aiwebtest.demoqa.elements.web_tables;

import com.aiwebtest.testing.DriverContext;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.Assert;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

public class WebTablesTest {
    private WebDriver driver;

    @BeforeClass
    public void setUp() {
        driver = new ChromeDriver();
        DriverContext.setDriver(driver);
        driver.manage().window().maximize();
        driver.get("https://demoqa.com/webtables");
    }

    @Test
    public void testWebTables() {
        WebElement addButton = driver.findElement(By.id("addNewRecordButton"));
        addButton.click();
        driver.findElement(By.id("firstName")).sendKeys("Alice");
        driver.findElement(By.id("lastName")).sendKeys("Smith");
        driver.findElement(By.id("userEmail")).sendKeys("alice.smith@example.com");
        driver.findElement(By.id("age")).sendKeys("30");
        driver.findElement(By.id("salary")).sendKeys("50000");
        driver.findElement(By.id("department")).sendKeys("QA");
        driver.findElement(By.id("submit")).click();
        WebElement table = driver.findElement(By.className("rt-table"));
        Assert.assertTrue(table.getText().contains("Alice"));
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
