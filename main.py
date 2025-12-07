import os
import csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
from dotenv import load_dotenv

load_dotenv()

def clean_text(text):
    """Clean and format text"""
    if not text:
        return ""
    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text.strip())
    return text

def login_to_linkedin(driver, email, password):
    """Login to LinkedIn"""
    driver.get("https://www.linkedin.com/login")

    # Wait for email field
    email_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "username"))
    )
    email_field.send_keys(email)

    # Password field
    password_field = driver.find_element(By.ID, "password")
    password_field.send_keys(password)

    # Click login
    login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    login_button.click()

    # Wait for login to complete
    WebDriverWait(driver, 10).until(
        EC.url_contains("linkedin.com/feed")
    )

    print("Logged in successfully")

def scrape_comments(driver, profile_url, max_comments=50):
    """Scrape comments from LinkedIn profile"""
    driver.get(profile_url)

    # Wait for page to load
    time.sleep(3)

    comments = []
    scroll_count = 0
    max_scrolls = 10

    while len(comments) < max_comments and scroll_count < max_scrolls:
        # Scroll down to load more comments
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # Find comment elements
        comment_elements = driver.find_elements(By.CSS_SELECTOR, "[data-testid='feed-comment']")

        for element in comment_elements[len(comments):]:
            try:
                # Extract author
                author_elem = element.find_element(By.CSS_SELECTOR, ".comments-comment-item__post-meta .comments-post-meta__name-text")
                author = clean_text(author_elem.text)

                # Extract comment text
                text_elem = element.find_element(By.CSS_SELECTOR, ".comments-comment-item__main-content .comments-comment-item__comment-content")
                text = clean_text(text_elem.text)

                # Extract timestamp
                time_elem = element.find_element(By.CSS_SELECTOR, ".comments-comment-item__post-meta time")
                timestamp = time_elem.get_attribute("datetime") or time_elem.text

                # Extract likes
                likes = 0
                try:
                    likes_elem = element.find_element(By.CSS_SELECTOR, "[data-testid='social-counts-reactions']")
                    likes_text = likes_elem.text
                    likes = int(re.search(r'\d+', likes_text).group()) if re.search(r'\d+', likes_text) else 0
                except:
                    pass

                if author and text:
                    comments.append({
                        'author': author,
                        'text': text,
                        'timestamp': timestamp,
                        'likes': likes
                    })

                if len(comments) >= max_comments:
                    break

            except Exception as e:
                continue

        scroll_count += 1

    return comments[:max_comments]

def main():
    # Configuration
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")
    profile_url = os.getenv("LINKEDIN_PROFILE_URL", "https://www.linkedin.com/in/yourprofile/")
    max_comments = 100

    if not email or not password:
        print("Please set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in .env file")
        return

    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # Use existing profile if available
    profile_path = os.path.join(os.getcwd(), "chrome_profile")
    if os.path.exists(profile_path):
        chrome_options.add_argument(f"--user-data-dir={profile_path}")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Login
        login_to_linkedin(driver, email, password)

        # Scrape comments
        comments = scrape_comments(driver, profile_url, max_comments)

        # Save to CSV
        os.makedirs("data", exist_ok=True)
        csv_path = "data/linkedin_comments.csv"

        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['author', 'text', 'timestamp', 'likes']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(comments)

        print(f"Scraped {len(comments)} comments and saved to {csv_path}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()