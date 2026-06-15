import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class CPProfile(Base):
    __tablename__ = "cp_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id")
    )

    platform: Mapped[str] = mapped_column(
        String(30)
    )

    handle: Mapped[str] = mapped_column(
        String(100)
    )

    current_rating: Mapped[int | None] = mapped_column()

    max_rating: Mapped[int | None] = mapped_column()

    # Relationships
    user: Mapped["User"] = relationship(back_populates="cp_profiles")