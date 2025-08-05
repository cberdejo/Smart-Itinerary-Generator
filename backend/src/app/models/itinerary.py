from models.valhalla import Trip
from pydantic import BaseModel
from models.municiaplity import TownOut
from models.valhalla import Trip

class Itinerary(BaseModel):
    trip: Trip | None = None
    towns: list[TownOut]
