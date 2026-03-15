from pydantic import BaseModel, HttpUrl
from typing import List, Optional

class CommentsScrapeRequest(BaseModel):
    email: str
    password: str
    profile_url: str
    max_comments: Optional[int] = 50
    max_scroll: Optional[int] = 20

class CommentOut(BaseModel):
    author: str
    timestamp: str
    original_text: str
    cleaned_text: str
    text_length: int

class CommentsScrapeResponse(BaseModel):
    status: str
    comments_scraped: int
    comments: List[CommentOut]
