import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from fastapi import HTTPException

def login_to_linkedin(driver, email, password):

    driver.get("https://www.linkedin.com/login")
    
    try:
        if "feed" in driver.current_url:
            return True

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )

        email_field = driver.find_element(By.ID, "username")
        email_field.clear()
        email_field.send_keys(email)

        password_field = driver.find_element(By.ID, "password")
        password_field.clear()
        password_field.send_keys(password)

        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()

        WebDriverWait(driver, 20).until(
            lambda d: "feed" in d.current_url or "checkpoint" in d.current_url or d.find_elements(By.ID, "input__phone_verification_pin")
        )

        if "checkpoint" in driver.current_url or driver.find_elements(By.ID, "input__phone_verification_pin"):
            raise HTTPException(
                status_code=401,
                detail="Security checkpoint triggered. Please complete verification manually."
            )

        return True
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")
