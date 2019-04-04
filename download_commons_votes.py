from selenium import webdriver
from selenium.webdriver.common.by import By


with webdriver.Firefox() as driver:
    driver.get("https://commonsvotes.digiminster.com/")
    for i in range(0, 665):
        driver.get(f"https://commonsvotes.digiminster.com/Divisions/Details/{i}")
        src = driver.page_source
        # print(src)
        if "This system has suffered an error" in src:
            print('skip')
            continue
        download_button_1 = driver.find_element(By.XPATH, '/html/body/div/div/div[2]/div[3]/div/div[1]/div/div[4]/div/div/a')
        download_button_1.click()
        
        input("next")
