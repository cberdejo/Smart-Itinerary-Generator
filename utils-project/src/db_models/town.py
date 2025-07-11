from sqlalchemy import (
    Column,
    String,
    Float,
    Boolean,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from app_config.postgres import Base


class Town(Base):
    __tablename__ = "towns"

    municipality_ine = Column(String, primary_key=True)
    municipality_name = Column(String)
    description = Column(String)
    history = Column(String)
    capital_city = Column(Boolean)
    latitude = Column(Float)
    longitude = Column(Float)
    province_identifier = Column(String)
    province_name = Column(String)
    has_beach = Column(Boolean, default=False)
    embeddings = Column(ARRAY(Float))

    intangible_assets = relationship(
        "Intangible", back_populates="town", cascade="all, delete-orphan"
    )
    real_estate_assets = relationship(
        "RealEstate", back_populates="town", cascade="all, delete-orphan"
    )
    images = relationship(
        "ImageTown", back_populates="town", cascade="all, delete-orphan"
    )
    