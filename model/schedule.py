from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from model.base import BaseLongIdEntity

class Schedule(BaseLongIdEntity):
    __tablename__ = "schedule"

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    program_id: Mapped[int] = mapped_column(ForeignKey("program.id"), nullable=False)
    center_id: Mapped[int] = mapped_column(ForeignKey("center.id"), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="schedules")
    program: Mapped["Program"] = relationship("Program", back_populates="schedules")
    center: Mapped["Center"] = relationship("Center", back_populates="schedules")