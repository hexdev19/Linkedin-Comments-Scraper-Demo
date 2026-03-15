from pydantic import BaseModel
from typing import List, Optional

class MemberOut(BaseModel):
    name: Optional[str] = None
    headline: Optional[str] = None
    country: Optional[str] = None
    profile_url: str

class GroupScrapeResponse(BaseModel):
    status: str
    members_scraped: int
    members: List[MemberOut]
