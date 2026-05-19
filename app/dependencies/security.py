from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.jwt import JwtService
from app.repositories.user_repository import UserRepository

security = HTTPBearer(auto_error=False)

async def get_request_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = None
    if credentials:
        token = credentials.credentials
    else:
        token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(detail="Token is missing.", status_code=status.HTTP_401_UNAUTHORIZED)
    verified = JwtService().verify_jwt(token=token, token_type="access")
    user_id = verified.payload["user_id"]
    user = await UserRepository().get_user(user_id)
    if not user:
        raise HTTPException(detail="Authenticate Failed.", status_code=status.HTTP_401_UNAUTHORIZED)
    return user
