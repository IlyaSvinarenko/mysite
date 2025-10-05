from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List, Dict
from app.chat.dao import MessagesDAO
from app.chat.schemas import MessageRead, MessageCreate
from app.users.dao import UsersDAO
from app.users.dependencies import get_current_user
from app.users.models import User
import json
import logging

router = APIRouter(prefix='/chat', tags=['Chat'])
templates = Jinja2Templates(directory='app/templates')

# Активные WebSocket-подключения: {user_id: websocket}
active_connections: Dict[int, WebSocket] = {}


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logging.info(f"User {user_id} connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logging.info(f"User {user_id} disconnected. Active connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except Exception as e:
                logging.error(f"Error sending message to user {user_id}: {e}")
                self.disconnect(user_id)

    async def broadcast(self, message: dict):
        for user_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except Exception as e:
                logging.error(f"Error broadcasting to user {user_id}: {e}")
                self.disconnect(user_id)


manager = ConnectionManager()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                # Обработка входящих сообщений
                if message_data.get('type') == 'message':
                    recipient_id = message_data.get('recipient_id')
                    content = message_data.get('content')

                    if recipient_id and content:
                        # Сохраняем сообщение в БД
                        message = await MessagesDAO.add(
                            sender_id=user_id,
                            recipient_id=recipient_id,
                            content=content
                        )

                        # Отправляем сообщение получателю
                        response_data = {
                            'type': 'message',
                            'id': message.id,
                            'sender_id': user_id,
                            'sender_name': await get_username(user_id),
                            'recipient_id': recipient_id,
                            'content': content,
                            'created_at': message.created_at.isoformat()
                        }

                        await manager.send_personal_message(response_data, recipient_id)
                        # Также отправляем обратно отправителю для подтверждения
                        await manager.send_personal_message(response_data, user_id)

            except json.JSONDecodeError:
                await websocket.send_json({'error': 'Invalid JSON'})

    except WebSocketDisconnect:
        manager.disconnect(user_id)


async def get_username(user_id: int) -> str:
    """Получить имя пользователя по ID"""
    user = await UsersDAO.find_one_or_none_by_id(user_id)
    return user.name if user else f"User{user_id}"


@router.get("/", response_class=HTMLResponse, summary="Chat Page")
async def get_chat_page(request: Request, current_user: User = Depends(get_current_user)):
    users_all = await UsersDAO.find_all()
    # Исключаем текущего пользователя из списка
    other_users = [user for user in users_all if user.id != current_user.id]
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "current_user": current_user,
        "users_all": other_users
    })


@router.get("/messages/{user_id}", response_model=List[MessageRead])
async def get_messages(user_id: int, current_user: User = Depends(get_current_user)):
    """Получить историю сообщений с конкретным пользователем"""
    messages = await MessagesDAO.get_messages_between_users(
        user_id_1=user_id,
        user_id_2=current_user.id
    )
    return messages or []


@router.get("/users", response_model=List[dict])
async def get_chat_users(current_user: User = Depends(get_current_user)):
    """Получить список пользователей для чата"""
    users_all = await UsersDAO.find_all()
    other_users = [{"id": user.id, "name": user.name} for user in users_all if user.id != current_user.id]
    return other_users