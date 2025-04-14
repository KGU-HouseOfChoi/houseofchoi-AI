from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from model.base import BaseLongIdEntity
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from model.user import User

class Personality(BaseLongIdEntity):
    __tablename__ = "personality"

    tag: Mapped[str] = mapped_column("personality_tags", String(255), nullable=False)
    ei: Mapped[str | None] = mapped_column(String(10))
    sn: Mapped[str | None] = mapped_column(String(10))
    tf: Mapped[str | None] = mapped_column(String(10))
    pj: Mapped[str | None] = mapped_column(String(10))

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)
    user: Mapped["User"] = relationship("User", back_populates="personality")
