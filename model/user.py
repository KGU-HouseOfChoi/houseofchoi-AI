from sqlalchemy import String, BigInteger, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum as PyEnum
from model.base import BaseLongIdEntity
from model.schedule import Schedule


class Role(PyEnum):
    SENIOR = "부모"
    GUARDIAN = "자식"

class User(BaseLongIdEntity):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    birth: Mapped[str] = mapped_column(String(20), nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    role: Mapped[Role | None] = mapped_column(Enum(Role, native_enum=False), nullable=True)
    personality_tag: Mapped[str | None] = mapped_column("personality_tag", String(255))
    user_code: Mapped[str] = mapped_column("user_code", String(255), nullable=False, unique=True)
    related_user: Mapped[int | None] = mapped_column("related_user", BigInteger)

    schedules: Mapped[list["Schedule"]] = relationship("Schedule", back_populates="user")