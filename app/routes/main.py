from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import verify_token

router = APIRouter()
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Зависимость для получения текущего пользователя из JWT токена"""
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный или просроченный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload

@router.get("/")
async def root():
    return {"message": "Hello World"}

@router.get("/protected")
async def protected_route(user: dict = Depends(get_current_user)):
    """Пример защищенного маршрута"""
    return {"message": f"Привет, {user['sub']}! Это защищенный маршрут."}