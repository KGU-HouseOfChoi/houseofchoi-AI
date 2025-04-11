from sqlalchemy import String, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from model.base import BaseLongIdEntity

if TYPE_CHECKING:
    from model.program import Program
    from model.schedule import Schedule

class Center(BaseLongIdEntity):
    __tablename__ = "center"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[float] = mapped_column(nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    tel: Mapped[str] = mapped_column(String(30), nullable=False)

    programs: Mapped[list["Program"]] = relationship("Program", back_populates="center", cascade="all, delete-orphan")

    schedules: Mapped[list["Schedule"]] = relationship("Schedule", back_populates="center")
