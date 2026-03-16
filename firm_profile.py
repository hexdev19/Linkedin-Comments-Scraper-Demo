import logging
import time
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.parsing import clean_text

logger = logging.getLogger(__name__)

PAGE_LOAD_TIMEOUT = 10
PAGE_LOAD_DELAY = 2


def scrape_firm_profiles(driver: WebDriver, companies: list[dict]) -> list[dict]:
    enriched = []
    total = len(companies)
    
    for idx, company in enumerate(companies, 1):
        linkedin_url = company.get("linkedin_url", "")
        if not linkedin_url:
            continue
        
        logger.info(f"Scraping {idx}/{total}: {linkedin_url}")
        firm_data = scrape_single_profile(driver, linkedin_url, company)
        enriched.append(firm_data)
    
    logger.info(f"Completed scraping {len(enriched)} firm profiles")
    return enriched


def scrape_single_profile(driver: WebDriver, linkedin_url: str, company: dict) -> dict:
    try:
        about_url = linkedin_url.rstrip("/") + "/about/"
        driver.get(about_url)
        time.sleep(PAGE_LOAD_DELAY)
        
        if not wait_for_page_load(driver):
            logger.warning(f"Page load timeout for {linkedin_url}")
            return create_empty_profile(linkedin_url, company)
        
        return extract_firm_data(driver, linkedin_url)
        
    except Exception as e:
        logger.warning(f"Failed to scrape {linkedin_url}: {e}")
        return create_empty_profile(linkedin_url, company)


def wait_for_page_load(driver: WebDriver) -> bool:
    wait = WebDriverWait(driver, PAGE_LOAD_TIMEOUT)
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "main")))
        return True
    except Exception:
        return False


def create_empty_profile(linkedin_url: str, company: dict) -> dict:
    return {
        "firm_name": company.get("firm_name", ""),
        "linkedin_url": linkedin_url,
        "website_url": "",
        "hq_location": "",
        "industry": "",
        "about_text": ""
    }


def extract_firm_data(driver: WebDriver, linkedin_url: str) -> dict:
    return {
        "firm_name": clean_text(extract_firm_name(driver)),
        "linkedin_url": linkedin_url,
        "website_url": clean_text(extract_website_url(driver)),
        "hq_location": clean_text(extract_hq_location(driver)),
        "industry": clean_text(extract_industry(driver)),
        "about_text": clean_text(extract_about_text(driver))
    }


def extract_firm_name(driver: WebDriver) -> str:
    selectors = [
        "h1.org-top-card-summary__title",
        "h1[title]",
        "h1"
    ]
    return find_text_by_selectors(driver, selectors)


def extract_website_url(driver: WebDriver) -> str:
    try:
        visit_button = driver.find_element(
            By.CSS_SELECTOR,
            "a[data-control-name='visit_website'], a.org-top-card-primary-actions__action"
        )
        href = visit_button.get_attribute("href")
        if href and "linkedin.com" not in href:
            return href
    except Exception:
        pass
    
    try:
        dt_elements = driver.find_elements(By.CSS_SELECTOR, "dt")
        for dt in dt_elements:
            label = dt.text.lower()
            if "website" in label:
                dd = dt.find_element(By.XPATH, "following-sibling::dd[1]")
                link = dd.find_element(By.CSS_SELECTOR, "a")
                href = link.get_attribute("href")
                if href and "linkedin.com" not in href:
                    return href
    except Exception:
        pass
    
    link_selectors = [
        ".org-page-details-module__container a[href^='http']",
        "a[data-test-id='about-us-link']",
        ".org-about-company-module a[href^='http']"
    ]
    
    for selector in link_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                href = el.get_attribute("href")
                if href and "linkedin.com" not in href:
                    return href
        except Exception:
            continue
    
    return ""


def extract_hq_location(driver: WebDriver) -> str:
    try:
        dt_elements = driver.find_elements(By.CSS_SELECTOR, "dt")
        for dt in dt_elements:
            label = dt.text.lower()
            if "headquarters" in label or "location" in label:
                dd = dt.find_element(By.XPATH, "following-sibling::dd[1]")
                return dd.text
    except Exception:
        pass
    
    location_selectors = [
        ".org-top-card-summary-info-list__info-item",
        ".org-page-details__definition-text",
        "[data-test-id='headquarters-value']"
    ]
    
    for selector in location_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                text = el.text.strip()
                if is_location_text(text):
                    return text
        except Exception:
            continue
    
    return ""


def is_location_text(text: str) -> bool:
    location_indicators = ["nc", "north carolina", "charlotte", ",", "united states"]
    text_lower = text.lower()
    return any(indicator in text_lower for indicator in location_indicators)


def extract_industry(driver: WebDriver) -> str:
    try:
        dt_elements = driver.find_elements(By.CSS_SELECTOR, "dt")
        for dt in dt_elements:
            if "industry" in dt.text.lower():
                dd = dt.find_element(By.XPATH, "following-sibling::dd[1]")
                return dd.text
    except Exception:
        pass
    
    industry_selectors = [
        ".org-top-card-summary-info-list__info-item",
        "[data-test-id='industry-value']",
        ".org-page-details__definition-text"
    ]
    
    pe_keywords = ["private equity", "investment", "capital", "venture", "financial"]
    
    for selector in industry_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                text = el.text.strip()
                if any(kw in text.lower() for kw in pe_keywords):
                    return text
        except Exception:
            continue
    
    return ""


def extract_about_text(driver: WebDriver) -> str:
    about_selectors = [
        "section.org-about-module p",
        ".org-about-us-organization-description__text",
        "[data-test-id='about-us__description']",
        ".org-page-details__definition-text",
        ".org-about-company-module__description",
        "p.break-words"
    ]
    return find_text_by_selectors(driver, about_selectors)


def find_text_by_selectors(driver: WebDriver, selectors: list[str]) -> str:
    for selector in selectors:
        try:
            element = driver.find_element(By.CSS_SELECTOR, selector)
            text = element.text.strip()
            if text:
                return text
        except Exception:
            continue
    return ""