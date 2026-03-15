import time
from typing import List
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app.schemas.company_scraper import CompanyOut, CompanyMemberOut

def get_company_profile_urls(driver, keywords: str, geo_id: str, size_code: str, industry_id: str, max_pages: int = 5) -> List[str]:
    base_search_url = f"https://www.linkedin.com/search/results/companies/?keywords={keywords}&origin=FACETED_SEARCH&companyHqGeo=%5B\"{geo_id}\"%5D&companySize=%5B\"{size_code}\"%5D&industryCompanyVertical=%5B\"{industry_id}\"%5D"
    
    company_urls = []
    for page in range(1, max_pages + 1):
        driver.get(f"{base_search_url}&page={page}")
        time.sleep(3)
        
        container_xpath = "/html/body/div/div[2]/div[2]/div[2]/main/div/div/div/div[1]/div/div/div/div[1]/div[1]"
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, container_xpath)))
            cards = driver.find_elements(By.XPATH, f"{container_xpath}/div")
            if not cards: break
            
            for card in cards:
                try:
                    link_elem = card.find_element(By.CSS_SELECTOR, "a.app-aware-link")
                    url = link_elem.get_attribute("href").split('?')[0]
                    if url not in company_urls:
                        company_urls.append(url)
                except: continue
        except: break
    return company_urls

def scrape_company_details(driver, url: str) -> CompanyOut:
    driver.get(url)
    time.sleep(3)
    
    details = {"profile_url": url, "members": []}
    
    try:
        details["name"] = driver.find_element(By.CSS_SELECTOR, "h1.org-top-card-summary__title").text.strip()
    except: pass
    
    try:
        about_section = driver.find_element(By.CSS_SELECTOR, "section.org-about-company")
        details["description"] = about_section.find_element(By.CSS_SELECTOR, "p.break-words").text.strip()
        
        fields = about_section.find_elements(By.CSS_SELECTOR, "dl.org-about-company__info > div")
        for field in fields:
            label = field.find_element(By.TAG_NAME, "dt").text.strip().lower()
            value = field.find_element(By.TAG_NAME, "dd").text.strip()
            if "industry" in label: details["industry"] = value
            elif "size" in label: details["size"] = value
            elif "headquarters" in label: details["headquarters"] = value
            elif "website" in label: details["website"] = value
    except: pass
    
    people_url = f"{url.rstrip('/')}/people/"
    driver.get(people_url)
    time.sleep(3)
    
    try:
        member_cards = driver.find_elements(By.CSS_SELECTOR, "li.org-people-profile-card__profile-card")
        for card in member_cards:
            try:
                name = card.find_element(By.CSS_SELECTOR, "div.artdeco-entity-lockup__title").text.strip()
                title = card.find_element(By.CSS_SELECTOR, "div.artdeco-entity-lockup__subtitle").text.strip()
                details["members"].append(CompanyMemberOut(name=name, title=title))
            except: continue
    except: pass
    
    return CompanyOut(**details)

def scrape_companies_logic(driver, keywords: str, geo_id: str, size_code: str, industry_id: str, max_pages: int = 2) -> List[CompanyOut]:
    urls = get_company_profile_urls(driver, keywords, geo_id, size_code, industry_id, max_pages)
    results = []
    for url in urls:
        results.append(scrape_company_details(driver, url))
    return results
