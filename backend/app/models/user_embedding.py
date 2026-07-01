import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.cf_user import CFUser


class UserEmbedding(Base):
    __tablename__ = "user_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cf_users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    embedding: Mapped[list[float]] = mapped_column(Vector(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationship to CFUser
    user: Mapped["CFUser"] = relationship(back_populates="embedding_rel")
