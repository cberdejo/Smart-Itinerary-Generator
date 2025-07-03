
from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    PrimaryKeyConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from app_config.postgres import Base
class Intangible(Base):
    __tablename__ = "intangible_assets"

    municipality_ine = Column(String, ForeignKey("towns.municipality_ine"))
    name = Column(String)
    scope = Column(String)
    typology = Column(String)
    description = Column(String)
    date = Column(String)

    __table_args__ = (PrimaryKeyConstraint("municipality_ine", "name"),)

    town = relationship("Town", back_populates="intangible_assets")
