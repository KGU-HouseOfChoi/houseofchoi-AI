from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from model.base import BaseLongIdEntity

if TYPE_CHECKING:
    from model.program import Program

class Tag(BaseLongIdEntity):
    __tablename__ = "tag"

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    programs: Mapped[list["Program"]] = relationship(
        secondary="program_tag",
        back_populates="tags"
    )
