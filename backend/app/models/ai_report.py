import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Text, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.cf_user import CFUser
    from app.models.contest import Contest


class AIReport(Base):
    __tablename__ = "ai_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cf_users.id")
    )

    contest_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("contests.id"),
        nullable=True
    )

    summary: Mapped[str] = mapped_column(Text)

    strengths: Mapped[str] = mapped_column(Text)

    weaknesses: Mapped[str] = mapped_column(Text)

    recommendations: Mapped[str] = mapped_column(Text)

    # Full JSON blob returned by the LLM (serialised as text)
    generated_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Unique cache key: "<report_type>:<user_id>:<contest_code|none>"
    cache_key: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True
    )

    report_type: Mapped[str] = mapped_column(String(50), default="contest_review")

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now()
    )

    # Relationships
    user: Mapped["CFUser"] = relationship(back_populates="reports")
    contest: Mapped["Contest | None"] = relationship(back_populates="reports")