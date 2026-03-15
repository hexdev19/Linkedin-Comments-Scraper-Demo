import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from contextlib import contextmanager
from app.core.config import settings

class DriverManager:
    @staticmethod
    def create_driver():
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--start-maximized")
        
        profile_path = os.path.abspath(settings.chrome_profile_path)
        chrome_options.add_argument(f"--user-data-dir={profile_path}")

        driver = webdriver.Chrome(options=chrome_options)
        
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        })
        
        return driver

@contextmanager
def get_driver():
    driver = DriverManager.create_driver()
    try:
        yield driver
    finally:
        driver.quit()
