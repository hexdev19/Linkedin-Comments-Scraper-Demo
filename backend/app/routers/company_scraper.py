from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import List, Optional
from app.schemas.company_scraper import CompanyScrapeResponse
from app.services.company_scraper_service import scrape_companies_logic
from app.services.auth_service import login_to_linkedin
from app.core.driver import get_driver
from app.utils.csv_generator import generate_csv_stream

router = APIRouter(prefix="/scraper", tags=["Company Scraper"])

@router.get("/companies", response_model=CompanyScrapeResponse)
async def get_companies(
    keywords: str = Query(..., description="Search keywords"),
    geo_id: str = Query(..., description="HQ Geography ID"),
    size_code: str = Query(..., description="Company Size Code"),
    industry_id: str = Query(..., description="Industry Vertical ID"),
    email: str = Query(..., description="LinkedIn Email"),
    password: str = Query(..., description="LinkedIn Password"),
    max_pages: int = Query(2, ge=1, le=10)
):
    with get_driver() as driver:
        try:
            login_to_linkedin(driver, email, password)
            data = scrape_companies_logic(driver, keywords, geo_id, size_code, industry_id, max_pages)
            return CompanyScrapeResponse(status="success", companies_scraped=len(data), data=data)
        except Exception as e:
            if isinstance(e, HTTPException): raise e
            raise HTTPException(status_code=500, detail=f"Company scraping failed: {str(e)}")

@router.get("/companies/download")
async def download_companies_csv(
    keywords: str = Query(..., description="Search keywords"),
    geo_id: str = Query(..., description="HQ Geography ID"),
    size_code: str = Query(..., description="Company Size Code"),
    industry_id: str = Query(..., description="Industry Vertical ID"),
    email: str = Query(..., description="LinkedIn Email"),
    password: str = Query(..., description="LinkedIn Password"),
    max_pages: int = Query(2, ge=1, le=10)
):
    with get_driver() as driver:
        try:
            login_to_linkedin(driver, email, password)
            data = scrape_companies_logic(driver, keywords, geo_id, size_code, industry_id, max_pages)
            
            flattened_data = []
            for company in data:
                base_info = company.dict()
                members = base_info.pop("members", [])
                if not members:
                    flattened_data.append({**base_info, "member_name": "", "member_title": ""})
                else:
                    for member in members:
                        flattened_data.append({**base_info, "member_name": member["name"], "member_title": member["title"]})
            
            csv_stream = generate_csv_stream(flattened_data)
            return StreamingResponse(
                csv_stream,
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=linkedin_companies.csv"}
            )
        except Exception as e:
            if isinstance(e, HTTPException): raise e
            raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")
