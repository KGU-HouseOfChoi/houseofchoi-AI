from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped, mapped_column

from model.base import BaseLongIdEntity

if TYPE_CHECKING:
    from model.user import User

class ChatLog(BaseLongIdEntity):
    __tablename__ = "chat_logs"

    user_message: Mapped[str] = mapped_column(String(500), nullable=False)
    assistant_response: Mapped[str] = mapped_column(String(1000), nullable=False)
    recommended_program: Mapped[str | None] = mapped_column(String(500), nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)  # User 테이블과 관계 설정

    # 관계 설정 (Lazy load)
    user: Mapped["User"] = relationship("User", back_populates="chat_logs")