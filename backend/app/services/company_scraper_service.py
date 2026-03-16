import time
import logging
from typing import List
from urllib.parse import urlencode
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app.utils.parsing import clean_text
from app.schemas.company_scraper import CompanyOut, CompanyMemberOut

logger = logging.getLogger(__name__)

MAX_SCROLLS_PER_PAGE = 5
SCROLL_PAUSE = 2
PAGE_LOAD_TIMEOUT = 20

def scrape_companies_logic(driver: WebDriver, keywords: str, max_pages: int = 1) -> List[CompanyOut]:
    company_previews = search_companies(driver, keywords, max_pages)
    enriched_companies = []
    
    for preview in company_previews:
        try:
            full_data = scrape_single_company(driver, preview["profile_url"])
            if full_data:
                enriched_companies.append(full_data)
            else:
                enriched_companies.append(CompanyOut(**preview, members=[]))
        except Exception as e:
            logger.warning(f"Failed to enrich {preview['profile_url']}: {e}")
            enriched_companies.append(CompanyOut(**preview, members=[]))
            
    return enriched_companies

def search_companies(driver: WebDriver, query: str, max_pages: int) -> List[dict]:
    all_companies = []
    seen_urls = set()
    
    base_url = "https://www.linkedin.com/search/results/companies/"
    params = {"keywords": query, "origin": "SWITCH_SEARCH_VERTICAL"}
    search_url = f"{base_url}?{urlencode(params)}"
    
    for page in range(1, max_pages + 1):
        url = f"{search_url}&page={page}"
        driver.get(url)
        time.sleep(5)
        
        if not wait_for_results(driver): break
        
        scroll_and_load_results(driver)
        new_companies = extract_companies_from_page(driver, seen_urls)
        if not new_companies: break
        
        all_companies.extend(new_companies)
        if not go_to_next_page(driver): break
        
    return all_companies

def wait_for_results(driver: WebDriver) -> bool:
    try:
        WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".reusable-search__entity-result-list, .search-results-container"))
        )
        return True
    except:
        return False

def scroll_and_load_results(driver: WebDriver) -> None:
    for _ in range(MAX_SCROLLS_PER_PAGE):
        last_height = driver.execute_script("return document.body.scrollHeight")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE)
        if driver.execute_script("return document.body.scrollHeight") == last_height:
            break

def extract_companies_from_page(driver: WebDriver, seen_urls: set) -> List[dict]:
    companies = []
    cards = driver.find_elements(By.CSS_SELECTOR, "li.reusable-search__result-container, .entity-result")
    
    for card in cards:
        try:
            link_elem = card.find_element(By.CSS_SELECTOR, "a[href*='/company/']")
            href = link_elem.get_attribute("href").split('?')[0].rstrip('/')
            
            if href in seen_urls or "/company/linkedin" in href.lower(): continue
            
            name = ""
            try:
                name = clean_text(card.find_element(By.CSS_SELECTOR, "span[aria-hidden='true']").text)
            except:
                slug = href.split("/company/")[1].split("/")[0]
                name = slug.replace("-", " ").replace("_", " ").title()
                
            if name and href:
                companies.append({"name": name, "profile_url": href})
                seen_urls.add(href)
        except: continue
        
    return companies

def scrape_single_company(driver: WebDriver, url: str) -> CompanyOut:
    about_url = url.rstrip("/") + "/about/"
    driver.get(about_url)
    time.sleep(3)
    
    data = {"profile_url": url, "members": []}
    
    try:
        data["name"] = clean_text(driver.find_element(By.CSS_SELECTOR, "h1.org-top-card-summary__title, h1").text)
    except: pass
    
    try:
        sections = driver.find_elements(By.CSS_SELECTOR, "section.org-about-module, .org-grid__core-rail--no-margins section")
        for section in sections:
            try:
                header = section.find_element(By.TAG_NAME, "h2").text.lower()
                if "about" in header:
                    data["description"] = clean_text(section.find_element(By.TAG_NAME, "p").text)
            except: pass
            
        dt_elements = driver.find_elements(By.CSS_SELECTOR, "dt")
        for dt in dt_elements:
            try:
                label = dt.text.lower()
                dd = dt.find_element(By.XPATH, "following-sibling::dd[1]")
                val = clean_text(dd.text)
                if "website" in label: data["website"] = dd.find_element(By.TAG_NAME, "a").get_attribute("href")
                elif "industry" in label: data["industry"] = val
                elif "size" in label: data["size"] = val
                elif "headquarters" in label: data["headquarters"] = val
            except: pass
    except: pass
    
    people_url = url.rstrip("/") + "/people/"
    driver.get(people_url)
    time.sleep(3)
    
    try:
        member_cards = driver.find_elements(By.CSS_SELECTOR, "li.org-people-profile-card__profile-card")
        for card in member_cards:
            try:
                m_name = clean_text(card.find_element(By.CSS_SELECTOR, ".artdeco-entity-lockup__title").text)
                m_title = clean_text(card.find_element(By.CSS_SELECTOR, ".artdeco-entity-lockup__subtitle").text)
                if m_name:
                    data["members"].append(CompanyMemberOut(name=m_name, title=m_title))
            except: continue
    except: pass
    
    return CompanyOut(**data)

def go_to_next_page(driver: WebDriver) -> bool:
    try:
        next_button = driver.find_element(By.CSS_SELECTOR, "button.artdeco-pagination__button--next:not([disabled])")
        next_button.click()
        return True
    except:
        return False
