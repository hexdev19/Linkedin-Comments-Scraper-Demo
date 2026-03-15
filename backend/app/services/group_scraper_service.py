import time
import random
from typing import List
from urllib.parse import urljoin
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from app.schemas.group_scraper import MemberOut

def scroll_to_load_all_members(driver):
    prev_height = 0
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(0.5, 1.0))
        
        try:
            show_more_btn = driver.find_element(By.XPATH, "//button[contains(., 'Show more results') or contains(., 'Afficher plus de résultats')]")
            if show_more_btn:
                show_more_btn.click()
                time.sleep(random.uniform(1.5, 2.5))
        except:
            pass
            
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == prev_height:
            break
        prev_height = new_height

def get_group_members_urls(driver, group_url: str, search: str = None) -> List[str]:
    driver.get(group_url)
    time.sleep(2)
    
    try:
        join_btn = driver.find_elements(By.XPATH, "//button[.//span[contains(@class, 'a11y-text') and (contains(., 'Rejoindre le groupe') or contains(., 'Join group'))]]")
        if join_btn:
            join_btn[0].click()
            time.sleep(1)
            cont_btn = driver.find_elements(By.XPATH, "//button[contains(., 'Continue') or contains(., 'Continuer')]")
            if cont_btn:
                cont_btn[0].click()
                time.sleep(2)
    except:
        pass
        
    members_activity_url = urljoin(group_url.rstrip('/') + '/', "members/")
    driver.get(members_activity_url)
    time.sleep(2)
    
    if search:
        try:
            search_input = driver.find_element(By.XPATH, "//input[@placeholder='Search members' or @placeholder='Chercher des membres']")
            search_input.send_keys(search)
            search_input.send_keys(Keys.ENTER)
            time.sleep(2)
        except:
            pass
            
    scroll_to_load_all_members(driver)
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    members_urls = []
    
    list_container = soup.select_one('ul.artdeco-list.groups-members-list__results-list')
    if list_container:
        for item in list_container.find_all('li', recursive=False):
            link_elem = item.find('a', class_='ui-entity-action-row__link')
            if link_elem and 'href' in link_elem.attrs:
                url = urljoin("https://www.linkedin.com/", link_elem['href'])
                if url not in members_urls:
                    members_urls.append(url)
                    
    return members_urls

def get_members_infos(driver, urls: List[str]) -> List[MemberOut]:
    members = []
    for url in urls:
        try:
            driver.get(url)
            time.sleep(2)
            
            name = None
            name_elem = driver.find_elements(By.CSS_SELECTOR, "h1.inline.t-24.v-align-middle.break-words") or \
                        driver.find_elements(By.XPATH, "//h1[contains(@class, 'inline t-24')]")
            if name_elem:
                name = name_elem[0].text.strip()
                
            headline = None
            headline_elem = driver.find_elements(By.CSS_SELECTOR, "div.text-body-medium.break-words")
            if headline_elem:
                headline = headline_elem[0].text.strip()
                
            country = None
            country_elem = driver.find_elements(By.CSS_SELECTOR, "span.text-body-small.inline.t-black--light.break-words")
            if country_elem:
                country = country_elem[0].text.strip()
                
            members.append(MemberOut(
                name=name,
                headline=headline,
                country=country,
                profile_url=url
            ))
        except:
            continue
    return members

def scrape_group_members_logic(driver, group_url: str, search: str = None) -> List[MemberOut]:
    urls = get_group_members_urls(driver, group_url, search)
    if not urls:
        return []
    return get_members_infos(driver, urls)
