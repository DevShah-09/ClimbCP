import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.cf_user import CFUser
    from app.models.topic import Topic
    from app.models.problem import Problem


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cf_users.id")
    )

    topic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topics.id")
    )

    problem_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("problems.id"),
        nullable=True
    )

    priority: Mapped[int] = mapped_column()

    reason: Mapped[str] = mapped_column(String(500))

    status: Mapped[str] = mapped_column(String(30), default="active")

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now()
    )

    # Relationships
    user: Mapped["CFUser"] = relationship(back_populates="recommendations")
    topic: Mapped["Topic"] = relationship(back_populates="recommendations")
    problem: Mapped["Problem | None"] = relationship(back_populates="recommendations")