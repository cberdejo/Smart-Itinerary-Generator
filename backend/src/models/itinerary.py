from models.valhalla import Trip
from pydantic import BaseModel
from models.municiaplity import TownOut


class Itinerary(BaseModel):
    trip: Trip | None = None
    towns: list[TownOut]
