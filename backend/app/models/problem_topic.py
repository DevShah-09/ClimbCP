import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.database.base import Base


class ProblemTopic(Base):
    __tablename__ = "problem_topics"

    problem_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("problems.id"),
        primary_key=True
    )

    topic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topics.id"),
        primary_key=True
    )