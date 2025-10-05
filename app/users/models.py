from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from typing import List


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)

    # created_at и updated_at уже есть в Base, не переопределяем

    # Связь с чатами
    chats: Mapped[List["Chat"]] = relationship(  # type: ignore
        "Chat",
        secondary="chat_participants",
        back_populates="participants"
    )