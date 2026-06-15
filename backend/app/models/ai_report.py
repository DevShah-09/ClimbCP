import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Text
from sqlalchemy import String
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy.sql import func

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.contest import Contest


class AIReport(Base):
    __tablename__ = "ai_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id")
    )

    contest_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("contests.id"),
        nullable=True
    )

    summary: Mapped[str] = mapped_column(
        Text
    )

    strengths: Mapped[str] = mapped_column(
        Text
    )

    weaknesses: Mapped[str] = mapped_column(
        Text
    )

    recommendations: Mapped[str] = mapped_column(
        Text
    )

    report_type: Mapped[str] = mapped_column(
        String(50),
        default="contest_review"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="reports")
    contest: Mapped["Contest | None"] = relationship(back_populates="reports")