from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import List, Dict
from app.chat.dao import ChatsDAO, MessagesDAO
from app.chat.schemas import ChatCreate, ChatRead, MessageRead, MessageCreate
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

    async def broadcast_to_chat(self, chat_id: int, message: dict, exclude_user_id: int = None):
        """Отправить сообщение всем участникам чата"""
        chat = await ChatsDAO.find_one_or_none_by_id(chat_id)
        if not chat:
            return

        for user in chat.participants:
            if user.id != exclude_user_id and user.id in self.active_connections:
                await self.send_personal_message(message, user.id)


manager = ConnectionManager()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)

                if message_data.get('type') == 'message':
                    chat_id = message_data.get('chat_id')
                    content = message_data.get('content')

                    if chat_id and content:
                        # Сохраняем сообщение в БД
                        message = await MessagesDAO.add_message(
                            chat_id=chat_id,
                            sender_id=user_id,
                            content=content
                        )

                        # Получаем информацию об отправителе
                        sender = await UsersDAO.find_one_or_none_by_id(user_id)

                        # Отправляем сообщение всем участникам чата
                        response_data = {
                            'type': 'message',
                            'id': message.id,
                            'chat_id': chat_id,
                            'sender_id': user_id,
                            'sender_name': sender.name if sender else f"User{user_id}",
                            'content': content,
                            'created_at': message.created_at.isoformat()
                        }

                        await manager.broadcast_to_chat(chat_id, response_data, exclude_user_id=user_id)
                        # Также отправляем обратно отправителю для подтверждения
                        await manager.send_personal_message(user_id, response_data)

            except json.JSONDecodeError:
                await websocket.send_json({'error': 'Invalid JSON'})

    except WebSocketDisconnect:
        manager.disconnect(user_id)


@router.get("/", response_class=HTMLResponse, summary="Chat Page")
async def get_chat_page(request: Request, current_user: User = Depends(get_current_user)):
    # Получаем чаты пользователя и всех пользователей для создания новых чатов
    user_chats = await ChatsDAO.get_user_chats(current_user.id)
    all_users = await UsersDAO.find_all()

    # Исключаем текущего пользователя из списка
    other_users = [user for user in all_users if user.id != current_user.id]

    return templates.TemplateResponse("chat.html", {
        "request": request,
        "current_user": current_user,
        "user_chats": user_chats,
        "all_users": other_users
    })


@router.post("/create", response_class=JSONResponse)
async def create_chat(
        request: Request,
        chat_name: str = Form(None),
        participant_ids: str = Form(...),
        current_user: User = Depends(get_current_user)
):
    """Создать новый чат через форму"""
    try:
        # Парсим ID участников
        participant_id_list = [int(pid.strip()) for pid in participant_ids.split(',') if pid.strip()]

        # Добавляем текущего пользователя в участники
        if current_user.id not in participant_id_list:
            participant_id_list.append(current_user.id)

        # Создаем чат
        new_chat = await ChatsDAO.create_chat(
            name=chat_name,
            participant_ids=participant_id_list
        )

        return JSONResponse({
            "success": True,
            "chat_id": new_chat.id,
            "message": "Чат успешно создан"
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=400)


@router.get("/chats", response_model=List[ChatRead])
async def get_user_chats(current_user: User = Depends(get_current_user)):
    """Получить все чаты пользователя"""
    chats = await ChatsDAO.get_user_chats(current_user.id)
    return [{
        "id": chat.id,
        "name": chat.name,
        "created_at": chat.created_at,
        "participant_count": len(chat.participants)
    } for chat in chats]


@router.get("/messages/{chat_id}", response_model=List[MessageRead])
async def get_chat_messages(chat_id: int, current_user: User = Depends(get_current_user)):
    """Получить сообщения чата"""
    # Проверяем, что пользователь является участником чата
    chat = await ChatsDAO.find_one_or_none_by_id(chat_id)
    if not chat or current_user not in chat.participants:
        raise HTTPException(status_code=404, detail="Chat not found")

    messages = await MessagesDAO.get_chat_messages(chat_id)
    return [{
        "id": message.id,
        "chat_id": message.chat_id,
        "sender_id": message.sender_id,
        "sender_name": message.sender.name,
        "content": message.content,
        "created_at": message.created_at
    } for message in messages]


@router.post("/messages", response_model=MessageRead)
async def send_message(message: MessageCreate, current_user: User = Depends(get_current_user)):
    """Отправить сообщение в чат"""
    # Проверяем, что пользователь является участником чата
    chat = await ChatsDAO.find_one_or_none_by_id(message.chat_id)
    if not chat or current_user not in chat.participants:
        raise HTTPException(status_code=404, detail="Chat not found")

    new_message = await MessagesDAO.add_message(
        chat_id=message.chat_id,
        sender_id=current_user.id,
        content=message.content
    )

    # Отправляем через WebSocket
    sender = await UsersDAO.find_one_or_none_by_id(current_user.id)
    message_data = {
        'type': 'message',
        'id': new_message.id,
        'chat_id': message.chat_id,
        'sender_id': current_user.id,
        'sender_name': sender.name if sender else f"User{current_user.id}",
        'content': message.content,
        'created_at': new_message.created_at.isoformat()
    }

    await manager.broadcast_to_chat(message.chat_id, message_data, exclude_user_id=current_user.id)

    return {
        "id": new_message.id,
        "chat_id": new_message.chat_id,
        "sender_id": new_message.sender_id,
        "sender_name": sender.name if sender else f"User{current_user.id}",
        "content": new_message.content,
        "created_at": new_message.created_at
    }