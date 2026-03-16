from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from app.schemas.people_scraper import PeopleScrapeResponse
from app.services.people_scraper_service import scrape_people_logic
from app.services.auth_service import login_to_linkedin
from app.core.driver import get_driver
from app.utils.csv_generator import generate_csv_stream

router = APIRouter(prefix="/scraper", tags=["People Scraper"])

@router.get("/people", response_model=PeopleScrapeResponse)
async def get_people(
    keywords: str = Query(..., description="Search keywords"),
    email: str = Query(..., description="LinkedIn Email"),
    password: str = Query(..., description="LinkedIn Password"),
    max_pages: int = Query(2, ge=1, le=10)
):
    with get_driver() as driver:
        try:
            login_to_linkedin(driver, email, password)
            data = scrape_people_logic(driver, keywords, max_pages)
            return PeopleScrapeResponse(status="success", people_scraped=len(data), data=data)
        except Exception as e:
            if isinstance(e, HTTPException): raise e
            raise HTTPException(status_code=500, detail=f"People scraping failed: {str(e)}")

@router.get("/people/download")
async def download_people_csv(
    keywords: str = Query(..., description="Search keywords"),
    email: str = Query(..., description="LinkedIn Email"),
    password: str = Query(..., description="LinkedIn Password"),
    max_pages: int = Query(2, ge=1, le=10)
):
    with get_driver() as driver:
        try:
            login_to_linkedin(driver, email, password)
            data = scrape_people_logic(driver, keywords, max_pages)
            
            flattened_data = [item.dict() for item in data]
            csv_stream = generate_csv_stream(flattened_data)
            
            return StreamingResponse(
                csv_stream,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=linkedin_people_{keywords.replace(' ', '_')}.csv"}
            )
        except Exception as e:
            if isinstance(e, HTTPException): raise e
            raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")
