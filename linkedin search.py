import logging
import time
from urllib.parse import urlencode
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from utils.parsing import clean_text

logger = logging.getLogger(__name__)

MAX_PAGES = 10
MAX_SCROLLS_PER_PAGE = 5
SCROLL_PAUSE = 2
PAGE_LOAD_TIMEOUT = 20

SEARCH_QUERIES = [
    "private equity Charlotte",
    "investment firm Charlotte NC",
    "venture capital Charlotte",
    "private equity North Carolina",
    "investment management Charlotte"
]


def search_companies(driver: WebDriver, query: str) -> list[dict]:
    all_companies = []
    seen_urls: set[str] = set()
    
    queries = [query] if query not in SEARCH_QUERIES else SEARCH_QUERIES
    
    for q in queries:
        logger.info(f"Searching for: {q}")
        companies = search_single_query(driver, q, seen_urls)
        

        all_companies.extend(companies)
        
        logger.info(f"Total companies so far: {len(all_companies)}")
        
        if len(all_companies) >= 50:
            break
    
    logger.info(f"Found {len(all_companies)} unique companies total")
    return all_companies


def search_single_query(driver: WebDriver, query: str, seen_urls: set[str]) -> list[dict]:
    search_url = build_search_url(query)
    logger.info(f"Search URL: {search_url}")
    
    driver.get(search_url)
    time.sleep(5)
    
    logger.info(f"Current URL: {driver.current_url}")
    
    if not wait_for_results(driver):
        logger.warning("No search results container found, trying search bar approach")
        companies = search_via_search_bar(driver, query, seen_urls)
        if companies:
            return companies
        debug_page_structure(driver)
        return []
    
    return collect_all_results(driver, seen_urls)


def search_via_search_bar(driver: WebDriver, query: str, seen_urls: set[str]) -> list[dict]:
    try:
        driver.get("https://www.linkedin.com/feed/")
        time.sleep(2)
        
        search_box = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='Search'], input[aria-label*='Search']")
        search_box.clear()
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        time.sleep(3)
        
        try:
            companies_filter = driver.find_element(By.CSS_SELECTOR, "button[aria-label*='Companies'], button:has-text('Companies')")
            companies_filter.click()
            time.sleep(3)
        except Exception:
            driver.get(driver.current_url + "&f_ST=C")
            time.sleep(3)
        
        if wait_for_results(driver):
            return collect_all_results(driver, seen_urls)
        
    except Exception as e:
        logger.warning(f"Search bar approach failed: {e}")
    
    return []


def build_search_url(query: str) -> str:
    params = {
        "keywords": query,
        "origin": "SWITCH_SEARCH_VERTICAL"
    }
    base_url = "https://www.linkedin.com/search/results/companies/"
    return f"{base_url}?{urlencode(params)}"


def wait_for_results(driver: WebDriver) -> bool:
    time.sleep(3)
    
    wait = WebDriverWait(driver, PAGE_LOAD_TIMEOUT)
    
    selectors_to_try = [
        "div.search-results-container",
        "ul.reusable-search__entity-result-list",
        ".reusable-search__entity-result-list",
        "main[aria-label]",
        "div[data-view-name='search-entity-result-universal-template']",
        "li[class*='result']",
        "div[class*='search-result']"
    ]
    
    for selector in selectors_to_try:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                logger.info(f"Found results container with selector: {selector}")
                return True
        except Exception:
            continue
    
    try:
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "main")))
        return True
    except Exception:
        return False


def debug_page_structure(driver: WebDriver) -> None:
    logger.info("=== DEBUG: Analyzing page structure ===")
    
    all_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/company/']")
    logger.info(f"Found {len(all_links)} links containing '/company/'")
    
    for i, link in enumerate(all_links[:5]):
        href = link.get_attribute("href")
        text = link.text[:50] if link.text else "(no text)"
        logger.info(f"  Link {i+1}: {href} - {text}")
    
    lists = driver.find_elements(By.CSS_SELECTOR, "ul")
    logger.info(f"Found {len(lists)} <ul> elements")
    
    divs_with_class = driver.find_elements(By.CSS_SELECTOR, "div[class*='search']")
    logger.info(f"Found {len(divs_with_class)} divs with 'search' in class")


def collect_all_results(driver: WebDriver, seen_urls: set[str]) -> list[dict]:
    companies = []
    page_count = 0
    
    while page_count < MAX_PAGES:
        page_count += 1
        logger.info(f"Processing page {page_count}")
        
        scroll_and_load_results(driver)
        
        new_companies = extract_companies_from_page(driver, seen_urls)
        logger.info(f"Extracted {len(new_companies)} companies from page {page_count}")
        
        if not new_companies:
            logger.info("No new companies found on this page")
            if page_count == 1:
                debug_page_structure(driver)
            break
        
        companies.extend(new_companies)
        for c in new_companies:
            seen_urls.add(c["linkedin_url"])
        
        if not go_to_next_page(driver):
            break
    
    return companies


def scroll_and_load_results(driver: WebDriver) -> None:
    for _ in range(MAX_SCROLLS_PER_PAGE):
        last_height = driver.execute_script("return document.body.scrollHeight")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE)
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        if new_height == last_height:
            break


def extract_companies_from_page(driver: WebDriver, seen_urls: set[str]) -> list[dict]:
    companies = []
    
    card_selectors = [
        "li.reusable-search__result-container",
        "div.reusable-search__result-container",
        "li[class*='reusable-search']",
        "div[data-view-name='search-entity-result-universal-template']",
        "li.artdeco-list__item",
        "div.entity-result"
    ]
    
    cards = []
    used_selector = ""
    for selector in card_selectors:
        cards = driver.find_elements(By.CSS_SELECTOR, selector)
        if cards:
            used_selector = selector
            logger.info(f"Found {len(cards)} cards with selector: {selector}")
            break
    
    if cards:
        for i, card in enumerate(cards):
            company = extract_company_from_card(card)
            if company and company["linkedin_url"] not in seen_urls:
                companies.append(company)
                logger.debug(f"Card {i+1}: {company['firm_name']} -> {company['linkedin_url']}")
            else:
                logger.debug(f"Card {i+1}: skipped (no data or duplicate)")
    
    # If card-based extraction got nothing, try link-based as fallback
    if not companies:
        logger.info("Card extraction found nothing, trying link-based extraction")
        companies = extract_companies_from_links(driver, seen_urls)
    
    return companies


def extract_companies_from_links(driver: WebDriver, seen_urls: set[str]) -> list[dict]:
    companies = []
    
    links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/company/']")
    logger.info(f"Link-based extraction: found {len(links)} company links")
    
    for link in links:
        try:
            href = link.get_attribute("href")
            if not href or "/company/" not in href:
                continue
            
            clean_url = href.split("?")[0].rstrip("/")
            
            if clean_url in seen_urls:
                continue
            
            # Extract company slug
            slug = clean_url.split("/company/")[1].split("/")[0] if "/company/" in clean_url else ""
            
            if slug.lower() == "linkedin":
                continue
            
            # Try to get text from link
            text = link.text.strip()
            
            # If no text, try child spans
            if not text:
                try:
                    spans = link.find_elements(By.CSS_SELECTOR, "span")
                    for span in spans:
                        span_text = span.text.strip()
                        if span_text and len(span_text) > 1:
                            text = span_text
                            break
                except Exception:
                    pass
            
            # If still no text, try parent element for nearby text
            if not text:
                try:
                    parent = link.find_element(By.XPATH, "..")
                    # Look for sibling spans with name
                    sibling_spans = parent.find_elements(By.CSS_SELECTOR, "span[aria-hidden='true']")
                    for span in sibling_spans:
                        span_text = span.text.strip()
                        if span_text and len(span_text) > 1:
                            text = span_text
                            break
                except Exception:
                    pass
            
            # Last resort: derive name from URL slug
            if not text and slug:
                text = slug.replace("-", " ").replace("_", " ").title()
            
            if text and len(text) > 1:
                companies.append({
                    "firm_name": clean_text(text),
                    "linkedin_url": clean_url
                })
                seen_urls.add(clean_url)
                logger.debug(f"Extracted via link: {text} -> {clean_url}")
                
        except Exception as e:
            logger.debug(f"Error processing link: {e}")
            continue
    
    logger.info(f"Link-based extraction yielded {len(companies)} companies")
    return companies


def extract_company_from_card(card) -> dict | None:
    try:
        link_element = find_company_link(card)
        if not link_element:
            logger.debug("No company link found in card")
            return None
        
        linkedin_url = extract_clean_url(link_element)
        if not linkedin_url:
            logger.debug(f"Could not extract clean URL from link")
            return None
        
        firm_name = extract_firm_name(card)
        
        # If no name found, extract from URL slug as last resort
        if not firm_name:
            try:
                slug = linkedin_url.split("/company/")[1].split("/")[0]
                if slug and slug.lower() != "linkedin":
                    firm_name = slug.replace("-", " ").replace("_", " ").title()
                    logger.debug(f"Using URL-derived name: {firm_name}")
            except Exception:
                pass
        
        # Only skip if still no name AND url looks like linkedin's own page
        if not firm_name and "linkedin" in linkedin_url.lower().split("/company/")[1]:
            logger.debug(f"Skipping LinkedIn's own company page")
            return None
        
        # Return company even with URL-derived name
        return {
            "firm_name": firm_name if firm_name else "Unknown Company",
            "linkedin_url": linkedin_url
        }
    except Exception as e:
        logger.debug(f"Error extracting company from card: {e}")
        return None


def find_company_link(card):
    link_selectors = [
        "a[href*='/company/']",
        "a.app-aware-link[href*='/company/']",
        ".entity-result__title-text a",
        "div[data-view-name*='entity'] a[href*='/company/']",
        "span.entity-result__title-text a"
    ]
    
    for selector in link_selectors:
        try:
            elements = card.find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                href = el.get_attribute("href")
                if href and "/company/" in href and "/company/linkedin" not in href.lower():
                    return el
        except Exception:
            continue
    
    return None


def extract_clean_url(link_element) -> str:
    href = link_element.get_attribute("href")
    if not href or "/company/" not in href:
        return ""
    return href.split("?")[0].rstrip("/")


def extract_firm_name(card) -> str:
    
    try:
        # Look for the title/name area - usually has visually-hidden + visible span pattern
        spans = card.find_elements(By.CSS_SELECTOR, "span")
        for span in spans:
            try:
                # Skip visually-hidden spans
                classes = span.get_attribute("class") or ""
                if "visually-hidden" in classes:
                    continue
                
                # Skip empty spans
                text = span.text.strip()
                if not text or len(text) < 2:
                    continue
                
                # Skip spans that are just numbers, descriptions, or common non-name text
                if text.isdigit():
                    continue
                if text.lower() in ["follow", "following", "company", "view", "see all"]:
                    continue
                    
                # Look for aria-hidden="true" which usually contains the visible name
                aria_hidden = span.get_attribute("aria-hidden")
                if aria_hidden == "true":
                    logger.debug(f"Found name via aria-hidden span: {text}")
                    return clean_text(text)
                    
            except Exception:
                continue
    except Exception as e:
        logger.debug(f"Error finding spans: {e}")
    
    # Try specific selectors for company name
    name_selectors = [
        "span[aria-hidden='true']",  # Most common pattern
        "span[dir='ltr']",
        ".entity-result__title-text span",
        ".entity-result__title-line span",
        ".org-company-card__title",
        "h3",
        "h4",
        "[data-anonymize='company-name']"
    ]
    
    for selector in name_selectors:
        try:
            elements = card.find_elements(By.CSS_SELECTOR, selector)
            for element in elements:
                text = element.text.strip()
                if text and len(text) > 1 and not text.isdigit():
                    # Filter out common non-name patterns
                    if text.lower() not in ["follow", "following", "company", "view"]:
                        logger.debug(f"Found name via selector {selector}: {text}")
                        return clean_text(text)
        except Exception:
            continue
    
    # Last resort: try to extract name from URL
    try:
        link = card.find_element(By.CSS_SELECTOR, "a[href*='/company/']")
        href = link.get_attribute("href")
        if href and "/company/" in href:
            # Extract company slug from URL and format it
            slug = href.split("/company/")[1].split("/")[0].split("?")[0]
            if slug and slug != "linkedin":
                # Convert slug to readable name (e.g., "acme-corp" -> "Acme Corp")
                name = slug.replace("-", " ").replace("_", " ").title()
                logger.debug(f"Extracted name from URL slug: {name}")
                return name
    except Exception:
        pass
    
    return ""


def go_to_next_page(driver: WebDriver) -> bool:
    try:
        next_button = driver.find_element(
            By.CSS_SELECTOR,
            "button.artdeco-pagination__button--next:not([disabled])"
        )
        driver.execute_script("arguments[0].scrollIntoView();", next_button)
        time.sleep(0.5)
        next_button.click()
        time.sleep(SCROLL_PAUSE)
        return wait_for_results(driver)
    except Exception:
        return False


def deduplicate_by_url(companies: list[dict]) -> list[dict]:
    seen: set[str] = set()
    unique = []
    
    for company in companies:
        url = company.get("linkedin_url", "")
        if url and url not in seen:
            seen.add(url)
            unique.append(company)
    
    return unique