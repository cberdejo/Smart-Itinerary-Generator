from .town import Town
from .intangible import Intangible
from .real_estate import RealEstate
from .image_town import ImageTown

from app_config.postgres import Base

__all__ = [
    "Town",
    "Intangible",
    "RealEstate",
    "ImageTown",
    "Base",
]
