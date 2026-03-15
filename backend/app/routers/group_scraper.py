from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional
from app.schemas.group_scraper import GroupScrapeResponse
from app.services.group_scraper_service import scrape_group_members_logic
from app.services.auth_service import login_to_linkedin
from app.core.driver import get_driver
from app.utils.csv_generator import generate_csv_stream

router = APIRouter(prefix="/scraper", tags=["Group Scraper"])

@router.get("/group-members", response_model=GroupScrapeResponse)
async def get_group_members(
    group_url: str = Query(..., description="The LinkedIn group URL"),
    email: str = Query(..., description="LinkedIn Email"),
    password: str = Query(..., description="LinkedIn Password"),
    search: Optional[str] = Query(None, description="Optional search term to filter members")
):
    with get_driver() as driver:
        try:
            login_to_linkedin(driver, email, password)
            members = scrape_group_members_logic(driver, group_url, search=search)
            return GroupScrapeResponse(status="success", members_scraped=len(members), members=members)
        except Exception as e:
            if isinstance(e, HTTPException): raise e
            raise HTTPException(status_code=500, detail=f"Group scraping failed: {str(e)}")

@router.get("/group-members/download")
async def download_group_members_csv(
    group_url: str = Query(..., description="The LinkedIn group URL"),
    email: str = Query(..., description="LinkedIn Email"),
    password: str = Query(..., description="LinkedIn Password"),
    search: Optional[str] = Query(None, description="Optional search term to filter members")
):
    with get_driver() as driver:
        try:
            login_to_linkedin(driver, email, password)
            members = scrape_group_members_logic(driver, group_url, search=search)
            
            data = [m.dict() for m in members]
            csv_stream = generate_csv_stream(data)
            
            return StreamingResponse(
                csv_stream,
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=group_members.csv"}
            )
        except Exception as e:
            if isinstance(e, HTTPException): raise e
            raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")
