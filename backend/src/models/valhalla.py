from pydantic import BaseModel
from typing import List, Optional, Any


class ExitTowardElement(BaseModel):
    text: str
    consecutive_count: Optional[int] = None


class Sign(BaseModel):
    exit_toward_elements: Optional[List[ExitTowardElement]] = None


class Maneuver(BaseModel):
    type: int
    instruction: str
    time: float
    length: float
    cost: float
    begin_shape_index: int
    end_shape_index: int
    travel_mode: str
    travel_type: str

    verbal_succinct_transition_instruction: Optional[str] = None
    verbal_pre_transition_instruction: Optional[str] = None
    verbal_post_transition_instruction: Optional[str] = None
    verbal_transition_alert_instruction: Optional[str] = None
    street_names: Optional[List[str]] = None
    bearing_before: Optional[float] = None
    bearing_after: Optional[float] = None
    sign: Optional[Sign] = None
    verbal_multi_cue: Optional[bool] = None


class Summary(BaseModel):
    has_time_restrictions: bool
    has_toll: bool
    has_highway: bool
    has_ferry: bool
    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float
    time: float
    length: float
    cost: float


class Leg(BaseModel):
    maneuvers: List[Maneuver]
    summary: Summary
    shape: str


class TripLocation(BaseModel):
    type: str
    lat: float
    lon: float
    original_index: int
    side_of_street: Optional[str] = None


class Trip(BaseModel):
    locations: List[TripLocation]
    legs: List[Leg]
    summary: Summary
    status_message: str
    status: int
    units: str
    language: str
