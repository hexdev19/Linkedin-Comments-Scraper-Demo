import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

sys.path.append(os.path.dirname(__file__))

import services.scraper as scraper
import services.search as search

app = FastAPI(title="LinkedIn Scraper API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/scraper", scraper.app)
app.mount("/search", search.app)

@app.get("/")
async def root():
    return {
        "services": {
            "scraper": "/scraper",
            "search": "/search"
        },
        "docs": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
