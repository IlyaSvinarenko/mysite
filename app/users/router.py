from fastapi import APIRouter, Response, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import List
from app.exceptions import UserAlreadyExistsException, IncorrectEmailOrPasswordException, PasswordMismatchException
from app.users.auth import get_password_hash, authenticate_user, create_access_token
from app.users.dao import UsersDAO
from app.users.schemas import SUserRegister, SUserAuth, SUserRead
from app.users.dependencies import get_current_user
from app.users.models import User

router = APIRouter(prefix='/auth', tags=['Auth'])
templates = Jinja2Templates(directory='app/templates')


@router.get("/", response_class=HTMLResponse, summary="Страница авторизации")
async def get_auth_page(request: Request, message: str = None, message_type: str = None):
    return templates.TemplateResponse("auth.html", {
        "request": request,
        "message": message,
        "message_type": message_type
    })


# Форма регистрации
@router.post("/register/")
async def register_user_form(
        request: Request,
        email: str = Form(...),
        name: str = Form(...),
        password: str = Form(...),
        password_check: str = Form(...)
):
    try:
        # Проверяем существование пользователя
        user = await UsersDAO.find_one_or_none(email=email)
        if user:
            return templates.TemplateResponse("auth.html", {
                "request": request,
                "message": "Пользователь с таким email уже существует",
                "message_type": "error"
            })

        # Проверяем совпадение паролей
        if password != password_check:
            return templates.TemplateResponse("auth.html", {
                "request": request,
                "message": "Пароли не совпадают",
                "message_type": "error"
            })

        # Хэшируем пароль и создаем пользователя
        hashed_password = get_password_hash(password)
        await UsersDAO.add(
            name=name,
            email=email,
            hashed_password=hashed_password
        )

        return templates.TemplateResponse("auth.html", {
            "request": request,
            "message": "Вы успешно зарегистрированы! Теперь можете войти.",
            "message_type": "success"
        })

    except Exception as e:
        return templates.TemplateResponse("auth.html", {
            "request": request,
            "message": f"Ошибка регистрации: {str(e)}",
            "message_type": "error"
        })


# Форма авторизации
@router.post("/login/")
async def auth_user_form(
        request: Request,
        response: Response,
        email: str = Form(...),
        password: str = Form(...)
):
    try:
        user = await authenticate_user(email=email, password=password)
        if not user:
            return templates.TemplateResponse("auth.html", {
                "request": request,
                "message": "Неверный email или пароль",
                "message_type": "error"
            })

        access_token = create_access_token({"sub": str(user.id)})
        # Перенаправляем на чат после успешного входа
        response = RedirectResponse(url="/chat/", status_code=status.HTTP_302_FOUND)
        response.set_cookie(key="users_access_token", value=access_token, httponly=True)
        return response

    except Exception as e:
        return templates.TemplateResponse("auth.html", {
            "request": request,
            "message": f"Ошибка авторизации: {str(e)}",
            "message_type": "error"
        })


# JSON API для Swagger (оставляем для обратной совместимости)
@router.post("/api/register/")
async def register_user_api(user_data: SUserRegister) -> dict:
    user = await UsersDAO.find_one_or_none(email=user_data.email)
    if user:
        raise UserAlreadyExistsException

    if user_data.password != user_data.password_check:
        raise PasswordMismatchException("Пароли не совпадают")
    hashed_password = get_password_hash(user_data.password)
    await UsersDAO.add(
        name=user_data.name,
        email=user_data.email,
        hashed_password=hashed_password
    )

    return {'message': 'Вы успешно зарегистрированы!'}


@router.post("/api/login/")
async def auth_user_api(response: Response, user_data: SUserAuth):
    check = await authenticate_user(email=user_data.email, password=user_data.password)
    if check is None:
        raise IncorrectEmailOrPasswordException
    access_token = create_access_token({"sub": str(check.id)})
    response.set_cookie(key="users_access_token", value=access_token, httponly=True)
    return {'ok': True, 'access_token': access_token, 'refresh_token': None, 'message': 'Авторизация успешна!'}


@router.post("/logout/")
async def logout_user(response: Response):
    response = RedirectResponse(url="/auth/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="users_access_token")
    return response


@router.get("/users", response_model=List[SUserRead])
async def get_users(current_user: User = Depends(get_current_user)):
    users_all = await UsersDAO.find_all()
    return [{'id': user.id, 'name': user.name} for user in users_all]