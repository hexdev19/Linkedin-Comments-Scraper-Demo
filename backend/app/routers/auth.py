from fastapi import APIRouter, Depends, HTTPException
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth_service import login_to_linkedin
from app.core.driver import get_driver

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):

    with get_driver() as driver:
        try:
            success = login_to_linkedin(driver, req.email, req.password)
            if success:
                return LoginResponse(success=True, message="Successfully logged into LinkedIn")
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    return LoginResponse(success=False, message="Login failed")
