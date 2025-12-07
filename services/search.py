from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import sys
import os
from app.database import get_db, Comment

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

app = FastAPI()

class SearchRequest(BaseModel):
    keyword: str
    limit: Optional[int] = 50

class CommentResponse(BaseModel):
    id: int
    author: str
    text: str
    timestamp: str
    likes: int
    session_id: str

@app.get("/search", response_model=List[CommentResponse])
async def search_comments(keyword: str, limit: int = 50):
    db = next(get_db())
    try:
        comments = db.query(Comment).filter(
            Comment.cleaned_text.ilike(f"%{keyword}%")
        ).limit(limit).all()

        return [
            CommentResponse(
                id=c.id,
                author=c.author,
                text=c.cleaned_text,
                timestamp=c.timestamp,
                likes=0,  # No likes field in database
                session_id=c.session_id
            ) for c in comments
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    db = next(get_db())
    try:
        total_comments = db.query(Comment).count()
        total_sessions = db.query(Comment.session_id).distinct().count()

        return {
            "total_comments": total_comments,
            "total_sessions": total_sessions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))