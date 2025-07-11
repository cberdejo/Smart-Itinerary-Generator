from sqlalchemy import (
    Column,
    String,
    JSON,
    ForeignKey,
    PrimaryKeyConstraint,
)
from sqlalchemy.orm import relationship

from app_config.postgres import Base


class RealEstate(Base):
    __tablename__ = "real_estate_assets"

    municipality_ine = Column(String, ForeignKey("towns.municipality_ine"))
    name = Column(String)
    description = Column(String)
    typologies = Column(JSON)
    characterization = Column(String)

    __table_args__ = (PrimaryKeyConstraint("municipality_ine", "name"),)

    town = relationship("Town", back_populates="real_estate_assets")
