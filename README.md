# LinkedIn Scraper

Automated LinkedIn comment scraper with FastAPI.

## Setup

```bash
pip install -r requirements.txt
```

Create `.env`:
```
LINKEDIN_EMAIL=your@email.com
LINKEDIN_PASSWORD=yourpassword
LINKEDIN_PROFILE_URL=https://www.linkedin.com/in/yourprofile/
```
## Usage

### Run API
```bash
python run.py
```
API at `http://localhost:8000` | Docs at `/docs`

**Endpoints:**
- `POST /scraper/scrape` - Login + scrape comments in one call
- `GET /search/search?keyword=text` - Search comments
- `GET /search/stats` - Get scraping statistics

### Run Script (CSV Export)
```bash
python main.py
```
Outputs to `data/linkedin_comments.csv`

## API Examples

**Scrape Comments:**
```bash
curl -X POST http://localhost:8000/scraper/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email.com",
    "password": "yourpass",
    "profile_url": "https://linkedin.com/in/yourprofile",
    "max_comments": 50
  }'
```

**Search Comments:**
```bash
curl "http://localhost:8000/search/search?keyword=python"
```

**Get Stats:**
```bash
curl "http://localhost:8000/search/stats"
```

SQLite: `data/linkedin.db`
