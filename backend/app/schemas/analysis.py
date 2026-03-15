from pydantic import BaseModel
from typing import List
from app.schemas.comments_scraper import CommentOut

class AnalysisRequest(BaseModel):
    comments: List[CommentOut]

class AnalysisResponse(BaseModel):
    analysis: str
