from pydantic import BaseModel, HttpUrl
from typing import List, Optional

class CompanyMemberOut(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None

class CompanyOut(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    headquarters: Optional[str] = None
    website: Optional[str] = None
    profile_url: str
    members: List[CompanyMemberOut] = []

class CompanyScrapeResponse(BaseModel):
    status: str
    companies_scraped: int
    data: List[CompanyOut]
