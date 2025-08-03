from enum import Enum, auto

class AircraftArea(Enum):
    NOT_DETECTED = auto()
    AT_PARKING = auto()
    ON_TAXIWAY = auto()
    AT_HOLDING_POINT = auto()
    ON_RUNWAY = auto()
    IN_FLIGHT = auto() 