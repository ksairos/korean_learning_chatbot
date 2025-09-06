from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4, UUID
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from sqlalchemy import DateTime, ForeignKey, LargeBinary, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(unique=True, nullable=True)
    first_name: Mapped[str]
    last_name: Mapped[Optional[str]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    chat_id: Mapped[int] = mapped_column(BigInteger, unique=True)

    # Relationship to raw message blobs
    messages: Mapped[list["MessageBlobModel"]] = relationship(
        "MessageBlobModel",
        back_populates="user",
        lazy="dynamic"
    )


# class ChatModel(Base):
#     __tablename__ = "chats"
#
#     id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
#     created_at: Mapped[datetime] = mapped_column(
#         DateTime(timezone=True),
#         nullable=False,
#         default=lambda: datetime.now(timezone.utc)
#     )
#
#     user: Mapped["UserModel"] = relationship(
#         "UserModel",
#         back_populates="chat",
#         uselist=False
#     )


class MessageBlobModel(Base):
    __tablename__ = "message_blobs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    
    user: Mapped['UserModel'] = relationship(
        'UserModel',
        back_populates='messages'
    )
