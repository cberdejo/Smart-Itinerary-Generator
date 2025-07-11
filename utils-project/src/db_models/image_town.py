from sqlalchemy import (
    Column,
    PrimaryKeyConstraint,
    String,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from app_config.postgres import Base


class ImageTown(Base):
    __tablename__ = "images"

    url = Column(String, nullable=False)
    municipality_ine = Column(
        String, ForeignKey("towns.municipality_ine"), nullable=False
    )

    __table_args__ = (
        PrimaryKeyConstraint(
            "municipality_ine", "url", name="pk_image_municipality_url"
        ),
    )

    town = relationship("Town", back_populates="images")
