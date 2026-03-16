from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, comments_scraper, analysis, group_scraper, company_scraper, people_scraper

app = FastAPI(
    title="LinkedIn Scraper API",
    description="Refactored, production-ready LinkedIn scraper backend",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(comments_scraper.router)
app.include_router(analysis.router)
app.include_router(group_scraper.router)
app.include_router(company_scraper.router)
app.include_router(people_scraper.router)

@app.get("/")
async def root():
    return {
        "message": "LinkedIn Scraper API is running",
        "docs": "/docs",
        "endpoints": ["/auth/login", "/scraper/comments"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
