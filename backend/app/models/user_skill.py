import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float
from sqlalchemy import ForeignKey

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.topic import Topic


class UserSkill(Base):
    __tablename__ = "user_skills"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id")
    )

    topic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topics.id")
    )

    score: Mapped[float] = mapped_column()

    confidence: Mapped[float] = mapped_column()

    # Relationships
    user: Mapped["User"] = relationship(back_populates="skills")
    topic: Mapped["Topic"] = relationship(back_populates="user_skills")