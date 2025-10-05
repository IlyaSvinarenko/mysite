from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class ChatCreate(BaseModel):
    name: Optional[str] = Field(None, description="Название чата")
    participant_ids: List[int] = Field(..., description="ID участников чата")


class ChatRead(BaseModel):
    id: int = Field(..., description="ID чата")
    name: Optional[str] = Field(None, description="Название чата")
    created_at: datetime = Field(..., description="Время создания чата")
    participant_count: int = Field(..., description="Количество участников")


class MessageRead(BaseModel):
    id: int = Field(..., description="Уникальный идентификатор сообщения")
    chat_id: int = Field(..., description="ID чата")
    sender_id: int = Field(..., description="ID отправителя сообщения")
    sender_name: str = Field(..., description="Имя отправителя")
    content: str = Field(..., description="Содержимое сообщения")
    created_at: datetime = Field(..., description="Время отправки сообщения")


class MessageCreate(BaseModel):
    chat_id: int = Field(..., description="ID чата")
    content: str = Field(..., description="Содержимое сообщения")