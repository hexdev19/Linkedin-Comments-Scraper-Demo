import time
import re
from typing import List
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin
from app.schemas.comments_scraper import CommentOut

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text.strip())
    return text

def scrape_comments_logic(driver, profile_url: str, max_comments: int = 50, max_scroll: int = 20) -> List[CommentOut]:

    comments_url = urljoin(profile_url.rstrip('/') + '/', "recent-activity/comments/")
    driver.get(comments_url)
    
    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except:
        return []

    time.sleep(2)
    comments = []
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_count = 0

    while len(comments) < max_comments and scroll_count < max_scroll:
        comment_containers = driver.find_elements(By.XPATH,
            "//div[contains(@class, 'comments-comment-item')] | "
            "//div[contains(@class, 'comment-item')] | "
            "//article[contains(@class, 'comment')] | "
            "//div[contains(@class, 'feed-shared-comment-item')]"
        )

        for container in comment_containers:
            if len(comments) >= max_comments:
                break
            
            try:
                author_name = "Anonymous"
                author_selectors = [
                    ".//span[contains(@class, 'comments-comment-meta__name')]",
                    ".//a[contains(@class, 'comments-comment-meta__name')]",
                    ".//span[contains(@class, 'comment-author-text')]"
                ]
                for selector in author_selectors:
                    try:
                        elem = container.find_element(By.XPATH, selector)
                        author_name = elem.text.strip()
                        if author_name: break
                    except: continue

                timestamp = "Recent"
                try:
                    time_elem = container.find_element(By.XPATH, ".//time")
                    timestamp = time_elem.get_attribute("datetime") or time_elem.text.strip()
                except: pass

                text_selectors = [
                    ".//span[contains(@class, 'comment-text')]",
                    ".//span[contains(@class, 'break-words')]",
                    ".//div[contains(@class, 'feed-shared-main-content')]//span"
                ]
                content_text = ""
                for selector in text_selectors:
                    try:
                        elem = container.find_element(By.XPATH, selector)
                        content_text = elem.text.strip()
                        if content_text: break
                    except: continue

                if not content_text:
                    continue

                cleaned = clean_text(content_text)
                
                if not any(c.original_text == content_text for c in comments):
                    comments.append(CommentOut(
                        author=author_name,
                        timestamp=timestamp,
                        original_text=content_text,
                        cleaned_text=cleaned,
                        text_length=len(cleaned)
                    ))

            except Exception:
                continue

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
        scroll_count += 1

    return comments[:max_comments]
