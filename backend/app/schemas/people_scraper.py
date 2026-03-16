from pydantic import BaseModel
from typing import List, Optional

class CandidateOut(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    location: Optional[str] = None
    profile_url: str

class PeopleScrapeResponse(BaseModel):
    status: str
    people_scraped: int
    data: List[CandidateOut]
