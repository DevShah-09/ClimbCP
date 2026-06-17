import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class PlatformAccount(Base):
    __tablename__ = "platform_accounts"

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

    current_rating: Mapped[int | None] = mapped_column(nullable=True)

    max_rating: Mapped[int | None] = mapped_column(nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="platform_accounts")
