from sqlalchemy import String, Table, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from model.base import BaseLongIdEntity
from model.program import Program


class Tag(BaseLongIdEntity):
    __tablename__ = "tag"

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    programs: Mapped[list["Program"]] = relationship(
        secondary="program_tag",
        back_populates="tags"
    )
