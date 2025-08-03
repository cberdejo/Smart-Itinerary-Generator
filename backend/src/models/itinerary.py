from typing import List, Optional
from models.municiaplity import TownOut
from models.valhalla import Trip
from pydantic import BaseModel


class Itinerary(BaseModel):
    trip: Optional[Trip] = None
    towns: List[TownOut]
