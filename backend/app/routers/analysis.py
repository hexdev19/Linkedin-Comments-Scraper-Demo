from fastapi import APIRouter, HTTPException
from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.services.analysis_service import analyze_comments_logic

router = APIRouter(prefix="/scraper", tags=["Analysis"])

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_comments(req: AnalysisRequest):
    try:
        analysis = analyze_comments_logic(req.comments)
        return AnalysisResponse(analysis=analysis)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
