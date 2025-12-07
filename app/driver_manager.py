import os
from selenium import webdriver
from contextlib import contextmanager

class DriverManager:
    def __init__(self):
        self.profile_path = os.path.join(os.getcwd(), "chrome_profile")
        self.ext_path = os.path.join(os.getcwd(), "data", "ext.crx")
        self.auto_select = [{"pattern": "https://www.linkedin.com","filter": {"SUBJECT": {"CN": "PRONTOGOV PRODUTOS E SERVICOS LTDA:23090165000105"}}}]
    
    def create_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-plugins")
        options.add_argument(f"--user-data-dir={self.profile_path}")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--start-maximized")
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option('prefs', {
            'intl.accept_languages': 'en,en_US',
            'AutoSelectCertificateForUrls': self.auto_select
        })
        if os.path.exists(self.ext_path):
            options.add_extension(self.ext_path)
        
        driver = webdriver.Chrome(options=options)
        driver.execute_cdp_cmd('Security.setIgnoreCertificateErrors', {'ignore': True})
        return driver

@contextmanager
def get_driver():
    manager = DriverManager()
    driver = manager.create_driver()
    try:
        yield driver
    finally:
        driver.quit()
