from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

opts = webdriver.FirefoxOptions()
opts.add_argument('-headless')

with webdriver.Firefox(options=opts) as driver:
    driver.set_window_size(1920, 1080)
    driver.get('https://dotesthere.com/')
    wait = WebDriverWait(driver, 15)
    link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "aside nav a[href='#add-remove']")))
    driver.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});", link)
    driver.execute_script("arguments[0].click();", link)
    add_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Add Element')]")))
    print('initial', len(driver.find_elements(By.CSS_SELECTOR, '#elements-container .delete-btn')))
    for _ in range(3):
        add_btn.click()
    print('after_add', len(driver.find_elements(By.CSS_SELECTOR, '#elements-container .delete-btn')))
    delete_btns = driver.find_elements(By.CSS_SELECTOR, '#elements-container .delete-btn')
    import time
    if delete_btns:
        delete_btns[0].click()
        time.sleep(1)
    print('after_delete', len(driver.find_elements(By.CSS_SELECTOR, '#elements-container .delete-btn')))
