from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from app.database import get_db, Comment, init_db
from app.driver_manager import get_driver
from urllib.parse import urljoin
import time
import re
import uuid

app = FastAPI()

class ScrapeRequest(BaseModel):
    email: str
    password: str
    profile_url: str
    max_comments: int = 50
    max_scroll: int = 20

def clean_text(text):
    if not text:
        return ""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002700-\U000027BF"
        "\U0001f926-\U0001f937"
        "\U00010000-\U0010ffff"
        "\u2640-\u2642"
        "\u2600-\u2B55"
        "\u200d\u23cf\u23e9\u231a\ufe0f\u3030"
        "]+",
        flags=re.UNICODE
    )
    text = emoji_pattern.sub('', text)
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    return re.sub(r'\s+', ' ', text.lower().strip())

def login_to_linkedin(driver, email, password):
    driver.get("https://www.linkedin.com/login")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    if driver.find_elements(By.ID, "username") or driver.find_elements(By.ID, "session_key"):
        try:
            email_field = driver.find_element(By.ID, "username") if driver.find_elements(By.ID, "username") else driver.find_element(By.ID, "session_key")
            current_value = email_field.get_attribute("value")
            if current_value:
                email_field.send_keys(Keys.CONTROL + "a")
                email_field.send_keys(Keys.DELETE)
                time.sleep(0.3)
            email_field.send_keys(email)

            time.sleep(1)

            password_field = driver.find_element(By.ID, "password") if driver.find_elements(By.ID, "password") else driver.find_element(By.ID, "session_password")
            current_value = password_field.get_attribute("value")
            if current_value:
                password_field.send_keys(Keys.CONTROL + "a")
                password_field.send_keys(Keys.DELETE)
                time.sleep(0.3)
            password_field.send_keys(password)

            time.sleep(2)

            login_button = driver.find_element(By.XPATH, "//button[@type='submit' and (contains(text(), 'Sign in') or contains(text(), \"S'identifier\"))]")
            login_button.click()

            WebDriverWait(driver, 50).until(EC.url_contains("feed"))
            return True

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")
    else:
        return True

@app.on_event("startup")
async def startup():
    init_db()

@app.post("/scrape")
async def scrape(req: ScrapeRequest, db: Session = Depends(get_db)):
    session_id = str(uuid.uuid4())

    with get_driver() as driver:
        try:
            login_to_linkedin(driver, req.email, req.password)
        except Exception as e:
            if "checkpoint" in driver.current_url or driver.find_elements(By.ID, "input__phone_verification_pin"):
                raise HTTPException(
                    status_code=401,
                    detail="Phone verification required. Please complete verification manually and try again."
                )
            raise e

        # Navigate directly to the comments activity page (same as working script)
        comments_url = urljoin(req.profile_url.rstrip('/') + '/', "recent-activity/comments/")
        print(f"Going to: {comments_url}")
        driver.get(comments_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        print("At comments activity page")

        time.sleep(2)

        comments = []
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_count = 0

        # Scroll and collect comments (exactly as in working script)
        while len(comments) < req.max_comments and scroll_count < req.max_scroll:
            print(f"Scroll {scroll_count + 1}")

            # Use the exact same XPath from the working script
            comment_containers = driver.find_elements(By.XPATH,
                "//div[contains(@class, 'comments-comment-item')] | "
                "//div[contains(@class, 'comment-item')] | "
                "//article[contains(@class, 'comment')] | "
                "//div[contains(@class, 'feed-shared-comment-item')]"
            )
            print(f"Found {len(comment_containers)} comment containers")

            for container in comment_containers:
                if len(comments) >= req.max_comments:
                    break
                try:
                    # Extract author using the exact same selectors as working script
                    author_selectors = [
                        ".//span[contains(@class, 'comments-comment-meta__name')]",
                        ".//a[contains(@class, 'comments-comment-meta__name')]",
                        ".//span[contains(@class, 'comment-author-text')]",
                        ".//a[contains(@class, 'comment-author-text')]",
                        ".//span[contains(@class, 'feed-shared-actor__name')]",
                        ".//a[contains(@class, 'feed-shared-actor__name')]",
                        ".//span[contains(@class, 'actor-name')]",
                        ".//a[contains(@class, 'actor-name')]",
                        ".//div[contains(@class, 'comments-comment-meta')]//span[1]",
                        ".//div[contains(@class, 'comments-comment-meta')]//a[1]"
                    ]

                    author_name = ""
                    for selector in author_selectors:
                        try:
                            author_elem = container.find_element(By.XPATH, selector)
                            author_name = author_elem.text.strip()
                            if author_name and len(author_name) > 1:
                                break
                        except:
                            continue

                    # Extract timestamp using the exact same selectors as working script
                    time_selectors = [
                        ".//time", 
                        ".//span[contains(@class, 'time')]",
                        ".//span[contains(@class, 'timestamp')]",
                        ".//span[contains(@class, 'feed-shared-actor__sub-description')]"
                    ]

                    timestamp = ""
                    for selector in time_selectors:
                        try:
                            time_elem = container.find_element(By.XPATH, selector)
                            datetime_attr = time_elem.get_attribute("datetime")
                            if datetime_attr:
                                timestamp = datetime_attr
                                break
                            text_content = time_elem.text.strip()
                            if text_content:
                                timestamp = text_content
                        except:
                            continue

                    if not timestamp:
                        try:
                            datetime_elem = container.find_element(By.XPATH, ".//*[@datetime]")
                            timestamp = datetime_elem.get_attribute("datetime")
                        except:
                            pass

                    # Extract comment text using the exact same selectors as working script
                    text_selectors = [
                        ".//span[contains(@class, 'comment-text')]",
                        ".//span[contains(@class, 'break-words')]",
                        ".//div[contains(@class, 'feed-shared-update-v2__commentary')]//span[@dir='ltr']",
                        ".//div[contains(@class, 'update-components-text')]//span",
                        ".//div[contains(@class, 'comment-item__content')]//span",
                        ".//div[contains(@class, 'feed-shared-comment-item__content')]//span"
                    ]

                    comment_text = ""
                    for selector in text_selectors:
                        try:
                            text_elem = container.find_element(By.XPATH, selector)
                            comment_text = text_elem.text.strip()
                            if comment_text:
                                break
                        except:
                            continue

                    cleaned_text = clean_text(comment_text)

                    # Only add if cleaned text is valid and unique
                    if cleaned_text and len(cleaned_text) > 1:
                        if not any(c["cleaned_text"] == cleaned_text for c in comments):
                            comments.append({
                                'author': author_name,
                                'timestamp': timestamp,
                                'original_text': comment_text,
                                'cleaned_text': cleaned_text,
                                'text_length': len(cleaned_text)
                            })
                            print(f"Collected comment {len(comments)}: {cleaned_text[:50]}...")

                except Exception as e:
                    print(f"Error processing comment container: {e}")
                    continue

            # Scroll down
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

            # Check if we've reached the bottom
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("No more content to load")
                break
            last_height = new_height
            scroll_count += 1

        print(f"Total comments collected: {len(comments)}")

        for comment_data in comments:
            comment = Comment(
                session_id=session_id,
                author=comment_data["author"],
                timestamp=comment_data["timestamp"],
                original_text=comment_data["original_text"],
                cleaned_text=comment_data["cleaned_text"],
                text_length=comment_data["text_length"]
            )
            db.add(comment)

        db.commit()

        print(f"Debug: Successfully scraped {len(comments)} comments")

        return {
            "status": "success",
            "session_id": session_id,
            "comments_scraped": len(comments),
            "comments": comments
        }

@app.get("/health")
async def health():
    return {"status": "ok"}
