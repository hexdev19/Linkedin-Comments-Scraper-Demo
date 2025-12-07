import uvicorn
from app.api import app

if __name__ == "__main__":
    print("\n" + "="*60)
    print("LinkedIn Scraper API - FastAPI Microservices")
    print("="*60)
    print("\nServices Available:")
    print("  → Scraper: http://localhost:8000/scraper")
    print("  → Search:  http://localhost:8000/search")
    print("\nAPI Docs:    http://localhost:8000/docs")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
