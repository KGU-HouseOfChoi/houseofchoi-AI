from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from model.base import BaseLongIdEntity
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from model.user import User
    from model.program import Program
    from model.center import Center

class Schedule(BaseLongIdEntity):
    __tablename__ = "schedule"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    program_id: Mapped[int] = mapped_column(ForeignKey("program.id"), nullable=False)
    center_id: Mapped[int] = mapped_column(ForeignKey("center.id"), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="schedules")
    program: Mapped["Program"] = relationship("Program", back_populates="schedules")
    center: Mapped["Center"] = relationship("Center", back_populates="schedules")
