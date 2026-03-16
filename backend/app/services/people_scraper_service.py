import time
import logging
from typing import List
from urllib.parse import urlencode
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app.utils.parsing import clean_text
from app.schemas.people_scraper import CandidateOut

logger = logging.getLogger(__name__)

MAX_SCROLLS_PER_PAGE = 5
SCROLL_PAUSE = 2
PAGE_LOAD_TIMEOUT = 20

def scrape_people_logic(driver: WebDriver, keywords: str, max_pages: int = 2) -> List[CandidateOut]:
    all_people = []
    seen_urls = set()
    
    base_url = "https://www.linkedin.com/search/results/people/"
    params = {"keywords": keywords, "origin": "SWITCH_SEARCH_VERTICAL"}
    search_url = f"{base_url}?{urlencode(params)}"
    
    for page in range(1, max_pages + 1):
        url = f"{search_url}&page={page}"
        logger.info(f"Scraping page {page}: {url}")
        driver.get(url)
        time.sleep(5)
        
        if not wait_for_results(driver):
            logger.warning(f"No results found on page {page}")
            break
            
        scroll_and_load_results(driver)
        new_people = extract_people_from_page(driver, seen_urls)
        
        if not new_people:
            break
            
        all_people.extend(new_people)
        if not go_to_next_page(driver):
            break
            
    return all_people

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

def extract_people_from_page(driver: WebDriver, seen_urls: set) -> List[CandidateOut]:
    people = []
    card_selectors = [
        "li.reusable-search__result-container",
        ".entity-result"
    ]
    
    cards = []
    for selector in card_selectors:
        cards = driver.find_elements(By.CSS_SELECTOR, selector)
        if cards: break
        
    for card in cards:
        try:
            link_elem = card.find_element(By.CSS_SELECTOR, ".entity-result__title-text a")
            href = link_elem.get_attribute("href").split('?')[0].rstrip('/')
            
            if href in seen_urls: continue
            
            name = clean_text(link_elem.find_element(By.CSS_SELECTOR, "span[aria-hidden='true']").text)
            title = ""
            try:
                title = clean_text(card.find_element(By.CSS_SELECTOR, ".entity-result__primary-subtitle").text)
            except: pass
            
            location = ""
            try:
                location = clean_text(card.find_element(By.CSS_SELECTOR, ".entity-result__secondary-subtitle").text)
            except: pass
            
            if name and href:
                people.append(CandidateOut(
                    name=name,
                    title=title,
                    location=location,
                    profile_url=href
                ))
                seen_urls.add(href)
        except: continue
        
    return people

def go_to_next_page(driver: WebDriver) -> bool:
    try:
        next_button = driver.find_element(By.CSS_SELECTOR, "button.artdeco-pagination__button--next:not([disabled])")
        next_button.click()
        return True
    except:
        return False
