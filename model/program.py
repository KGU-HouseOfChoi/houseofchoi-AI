# models/program.py

from sqlalchemy import String, BigInteger, ForeignKey, Table, Time, Column, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from model.base import BaseLongIdEntity
from model.center import Center
from model.schedule import Schedule
from model.tag import Tag

# 중간 테이블 정의
program_tag = Table(
    "program_tag",
    BaseLongIdEntity.metadata,
    Column("program_id", ForeignKey("program.id"), primary_key=True, type_=Integer),
    Column("tag_id", ForeignKey("tag.id"), primary_key=True, type_=Integer)
)

class Program(BaseLongIdEntity):
    __tablename__ = "program"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    fir_day: Mapped[str] = mapped_column(String(20), nullable=False)
    sec_day: Mapped[str | None] = mapped_column(String(20))
    thr_day: Mapped[str | None] = mapped_column(String(20))
    fou_day: Mapped[str | None] = mapped_column(String(20))
    fiv_day: Mapped[str | None] = mapped_column(String(20))

    start_time: Mapped[str] = mapped_column(Time, nullable=False)
    end_time: Mapped[str] = mapped_column(Time, nullable=False)
    price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    main_category: Mapped[str] = mapped_column(String(100), nullable=False)
    sub_category: Mapped[str] = mapped_column(String(100), nullable=False)
    headcount: Mapped[str] = mapped_column(String(100), nullable=False)

    center_id: Mapped[int] = mapped_column(ForeignKey("center.id"), nullable=False)
    center: Mapped[Center] = relationship(back_populates="programs")

    tags: Mapped[list[Tag]] = relationship(
        secondary=program_tag,
        back_populates="programs"
    )

    schedules: Mapped[list["Schedule"]] = relationship("Schedule", back_populates="program")