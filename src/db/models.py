from typing import List

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class UserModel(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)

    chats: Mapped[List["ChatModel"]] = relationship(back_populates="user")

class ChatModel(Base):
    __tablename__ = 'chats'

    chat_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    message_history: Mapped[JSONB] = mapped_column(JSONB, default=list, nullable=True)

    user: Mapped["UserModel"] = relationship(back_populates="chats")

