package com.aiwebtest.demoqa.elements.text_box;

import com.aiwebtest.testing.DriverContext;
import org.openqa.selenium.By;
import org.openqa.selenium.ElementClickInterceptedException;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.testng.Assert;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.time.Duration;

public class TextBoxTest {
    private WebDriver driver;

    @BeforeClass
    public void setUp() {
        driver = new ChromeDriver();
        DriverContext.setDriver(driver);
        driver.manage().window().maximize();
        driver.get("https://demoqa.com/text-box");
    }

    @Test
    public void testTextBoxInput() {
        WebElement fullName = driver.findElement(By.id("userName"));
        WebElement email = driver.findElement(By.id("userEmail"));
        WebElement currentAddress = driver.findElement(By.id("currentAddress"));
        WebElement permanentAddress = driver.findElement(By.id("permanentAddress"));
        WebElement submitBtn = driver.findElement(By.id("submit"));

        fullName.sendKeys("John Doe");
        email.sendKeys("john.doe@example.com");
        currentAddress.sendKeys("123 Main St");
        permanentAddress.sendKeys("456 Secondary St");

    dismissAds();
    ((JavascriptExecutor) driver).executeScript("arguments[0].scrollIntoView({block: 'center'});", submitBtn);
    WebElement clickableSubmit = new WebDriverWait(driver, Duration.ofSeconds(10))
        .until(ExpectedConditions.elementToBeClickable(submitBtn));
    try {
        clickableSubmit.click();
    } catch (ElementClickInterceptedException intercepted) {
        ((JavascriptExecutor) driver).executeScript("arguments[0].click();", clickableSubmit);
    }

        WebElement nameOutput = driver.findElement(By.id("name"));
        WebElement emailOutput = driver.findElement(By.id("email"));
        Assert.assertTrue(nameOutput.getText().contains("John Doe"));
        Assert.assertTrue(emailOutput.getText().contains("john.doe@example.com"));
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

    private void dismissAds() {
        if (driver instanceof JavascriptExecutor) {
        String script = "const selectors = ['#adplus-anchor', '#fixedban', '.modal', 'div[id*=\\\"google_ads\\\"]', '[style*=\\\"position: fixed\\\"]'];"
            + "selectors.forEach(sel => document.querySelectorAll(sel).forEach(el => el.remove()));";
            ((JavascriptExecutor) driver).executeScript(script);
        }
    }
}
