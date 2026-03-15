from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from app.schemas.comments_scraper import CommentsScrapeResponse
from app.services.comments_scraper_service import scrape_comments_logic
from app.services.auth_service import login_to_linkedin
from app.core.driver import get_driver
from app.utils.csv_generator import generate_csv_stream

router = APIRouter(prefix="/scraper", tags=["Scraper"])

@router.get("/comments", response_model=CommentsScrapeResponse)
async def get_comments(
    profile_url: str = Query(..., description="The LinkedIn profile or post URL"),
    email: str = Query(..., description="LinkedIn Email"),
    password: str = Query(..., description="LinkedIn Password"),
    max_comments: int = Query(50, ge=1, le=200),
    max_scroll: int = Query(20, ge=1, le=100)
):
    with get_driver() as driver:
        try:
            login_to_linkedin(driver, email, password)
            comments = scrape_comments_logic(driver, profile_url, max_comments, max_scroll)
            return CommentsScrapeResponse(status="success", comments_scraped=len(comments), comments=comments)
        except Exception as e:
            if isinstance(e, HTTPException): raise e
            raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

@router.get("/comments/download")
async def download_comments_csv(
    profile_url: str = Query(..., description="The LinkedIn profile or post URL"),
    email: str = Query(..., description="LinkedIn Email"),
    password: str = Query(..., description="LinkedIn Password"),
    max_comments: int = Query(50, ge=1, le=200),
    max_scroll: int = Query(20, ge=1, le=100)
):
    with get_driver() as driver:
        try:
            login_to_linkedin(driver, email, password)
            comments = scrape_comments_logic(driver, profile_url, max_comments, max_scroll)
            
            data = [c.dict() for c in comments]
            csv_stream = generate_csv_stream(data)
            
            return StreamingResponse(
                csv_stream,
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=linkedin_comments.csv"}
            )
        except Exception as e:
            if isinstance(e, HTTPException): raise e
            raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")
