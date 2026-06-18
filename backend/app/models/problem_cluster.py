import uuid
from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

class ProblemCluster(Base):
    __tablename__ = "problem_clusters"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    cluster_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    problem_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"), 
        unique=True, 
        nullable=False
    )

    # Relationship to Problem
    problem: Mapped["Problem"] = relationship(back_populates="cluster_rel")
