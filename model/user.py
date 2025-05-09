from sqlalchemy import String, BigInteger, Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from model.base import BaseLongIdEntity

if TYPE_CHECKING:
    from model.schedule import Schedule
    from model.chat_log import ChatLog
    from model.personality import Personality

class Role(PyEnum):
    SENIOR = "부모"
    GUARDIAN = "자식"

class User(BaseLongIdEntity):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    birth: Mapped[str] = mapped_column(String(20), nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    role: Mapped[Role | None] = mapped_column(SqlEnum(Role, native_enum=False), nullable=True)
    user_code: Mapped[str] = mapped_column("user_code", String(255), nullable=False, unique=True)
    related_user: Mapped[int | None] = mapped_column("related_user", BigInteger)

    schedules: Mapped[list["Schedule"]] = relationship("Schedule", back_populates="user")
    chat_logs: Mapped[list["ChatLog"]] = relationship("ChatLog", back_populates="user")
    personality: Mapped["Personality"] = relationship(
        "Personality",
        back_populates="user",
        uselist=False  # 1:1 관계임을 명시
    )
