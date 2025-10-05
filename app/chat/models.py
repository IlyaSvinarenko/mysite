from sqlalchemy import Integer, Text, ForeignKey, DateTime, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base
from typing import List

# Таблица для связи многие-ко-многим между пользователями и чатами
chat_participants = Table(
    'chat_participants',
    Base.metadata,
    Column('chat_id', Integer, ForeignKey('chats.id')),
    Column('user_id', Integer, ForeignKey('users.id'))
)


class Chat(Base):
    __tablename__ = 'chats'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(Text, nullable=True)  # Название чата (опционально)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Связи
    participants: Mapped[List["User"]] = relationship(  # type: ignore
        "User",
        secondary=chat_participants,
        back_populates="chats"
    )
    messages: Mapped[List["Message"]] = relationship(  # type: ignore
        "Message",
        back_populates="chat",
        cascade="all, delete-orphan"
    )


class Message(Base):
    __tablename__ = 'messages'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey("chats.id"))
    sender_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Связи
    chat: Mapped["Chat"] = relationship("Chat", back_populates="messages")  # type: ignore
    sender: Mapped["User"] = relationship("User")  # type: ignore