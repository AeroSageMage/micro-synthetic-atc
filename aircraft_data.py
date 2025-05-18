from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class AircraftType:
    name: str
    name_full: str
    icao_code: str
    aerofly_code: str
    cruise_speed_kts: int
    approach_airspeed_kts: int
    cruise_altitude_ft: int
    maximum_range_nm: int
    tags: List[str]
    has_radio_nav: bool
    runway_takeoff: Optional[int]
    runway_landing: Optional[int]

class AircraftData:
    """Class to manage aircraft data from AeroflyAircraft.ts"""
    
    def __init__(self):
        self.aircraft_types: Dict[str, AircraftType] = {}
        self._load_aircraft_data()
    
    def _load_aircraft_data(self):
        """Load aircraft data from AeroflyAircraft.ts"""
        self.aircraft_types = {
            'A319': AircraftType(
                name='A319',
                name_full='Airbus A319-115',
                icao_code='A319',
                aerofly_code='a319',
                cruise_speed_kts=453,
                approach_airspeed_kts=142,
                cruise_altitude_ft=32000,
                maximum_range_nm=3747,
                tags=['airliner', 'jet'],
                has_radio_nav=True,
                runway_takeoff=8000,
                runway_landing=6000
            ),
            'A320': AircraftType(
                name='A320',
                name_full='Airbus A320-214',
                icao_code='A320',
                aerofly_code='a320',
                cruise_speed_kts=453,
                approach_airspeed_kts=142,
                cruise_altitude_ft=32000,
                maximum_range_nm=3321,
                tags=['airliner', 'jet'],
                has_radio_nav=True,
                runway_takeoff=7186,
                runway_landing=4725
            ),
            'A321': AircraftType(
                name='A321',
                name_full='Airbus A321-213',
                icao_code='A321',
                aerofly_code='a321',
                cruise_speed_kts=453,
                approach_airspeed_kts=145,
                cruise_altitude_ft=32000,
                maximum_range_nm=3186,
                tags=['airliner', 'jet'],
                has_radio_nav=True,
                runway_takeoff=8000,
                runway_landing=6000
            ),
            'A380': AircraftType(
                name='A380',
                name_full='Airbus A380-800',
                icao_code='A388',
                aerofly_code='a380',
                cruise_speed_kts=517,
                approach_airspeed_kts=142,
                cruise_altitude_ft=36000,
                maximum_range_nm=8207,
                tags=['airliner', 'jet', 'widebody'],
                has_radio_nav=True,
                runway_takeoff=8000,
                runway_landing=6000
            ),
            'B735': AircraftType(
                name='B737-500',
                name_full='Boeing 737-500',
                icao_code='B735',
                aerofly_code='b737',
                cruise_speed_kts=490,
                approach_airspeed_kts=125,
                cruise_altitude_ft=33000,
                maximum_range_nm=2808,
                tags=['airliner', 'jet'],
                has_radio_nav=True,
                runway_takeoff=8000,
                runway_landing=6000
            ),
            'B739': AircraftType(
                name='B737-900ER',
                name_full='Boeing 737-900ER',
                icao_code='B739',
                aerofly_code='b737_900',
                cruise_speed_kts=453,
                approach_airspeed_kts=144,
                cruise_altitude_ft=37000,
                maximum_range_nm=2948,
                tags=['airliner', 'jet'],
                has_radio_nav=True,
                runway_takeoff=8000,
                runway_landing=6000
            ),
            'B39M': AircraftType(
                name='B737 MAX 9',
                name_full='Boeing 737 MAX 9',
                icao_code='B39M',
                aerofly_code='b737_max9',
                cruise_speed_kts=453,
                approach_airspeed_kts=144,
                cruise_altitude_ft=37000,
                maximum_range_nm=3548,
                tags=['airliner', 'jet'],
                has_radio_nav=True,
                runway_takeoff=8000,
                runway_landing=6000
            ),
            'B744': AircraftType(
                name='B747-400',
                name_full='Boeing 747-400',
                icao_code='B744',
                aerofly_code='b747',
                cruise_speed_kts=492,
                approach_airspeed_kts=145,
                cruise_altitude_ft=34000,
                maximum_range_nm=7262,
                tags=['airliner', 'jet', 'widebody'],
                has_radio_nav=True,
                runway_takeoff=8000,
                runway_landing=6000
            ),
            'B77F': AircraftType(
                name='B777F',
                name_full='Boeing 777F',
                icao_code='B77F',
                aerofly_code='b777f',
                cruise_speed_kts=482,
                approach_airspeed_kts=147,
                cruise_altitude_ft=41000,
                maximum_range_nm=9750,
                tags=['airliner', 'jet', 'widebody'],
                has_radio_nav=True,
                runway_takeoff=8000,
                runway_landing=6000
            ),
            'B77W': AircraftType(
                name='B777-300ER',
                name_full='Boeing 777-300ER',
                icao_code='B77W',
                aerofly_code='b777_300er',
                cruise_speed_kts=482,
                approach_airspeed_kts=145,
                cruise_altitude_ft=41000,
                maximum_range_nm=7370,
                tags=['airliner', 'jet', 'widebody'],
                has_radio_nav=True,
                runway_takeoff=8000,
                runway_landing=6000
            ),
            'B78X': AircraftType(
                name='B787-10',
                name_full='Boeing 787-10 Dreamliner',
                icao_code='B78X',
                aerofly_code='b787',
                cruise_speed_kts=482,
                approach_airspeed_kts=150,
                cruise_altitude_ft=40000,
                maximum_range_nm=6425,
                tags=['airliner', 'jet', 'widebody'],
                has_radio_nav=True,
                runway_takeoff=8000,
                runway_landing=6000
            ),
            'C172': AircraftType(
                name='C172',
                name_full='Cessna 172 SP Skyhawk',
                icao_code='C172',
                aerofly_code='c172',
                cruise_speed_kts=130,
                approach_airspeed_kts=62,
                cruise_altitude_ft=8000,
                maximum_range_nm=1031,
                tags=['general_aviation', 'trainer', 'piston'],
                has_radio_nav=True,
                runway_takeoff=960,
                runway_landing=575
            ),
            'BE9L': AircraftType(
                name='King Air',
                name_full='Beechcraft King Air C90 GTx',
                icao_code='BE9L',
                aerofly_code='c90gtx',
                cruise_speed_kts=272,
                approach_airspeed_kts=100,
                cruise_altitude_ft=18000,
                maximum_range_nm=1192,
                tags=['general_aviation', 'executive', 'turboprop'],
                has_radio_nav=True,
                runway_takeoff=2557,
                runway_landing=3417
            ),
            'CRJ9': AircraftType(
                name='CRJ-900LR',
                name_full='Bombardier CRJ-900LR',
                icao_code='CRJ9',
                aerofly_code='crj900',
                cruise_speed_kts=470,
                approach_airspeed_kts=125,
                cruise_altitude_ft=38000,
                maximum_range_nm=1550,
                tags=['airliner', 'regional', 'jet'],
                has_radio_nav=True,
                runway_takeoff=8000,
                runway_landing=6000
            ),
            'DH8D': AircraftType(
                name='Q400',
                name_full='Bombardier Dash-8 Q400',
                icao_code='DH8D',
                aerofly_code='q400',
                cruise_speed_kts=286,
                approach_airspeed_kts=135,
                cruise_altitude_ft=24000,
                maximum_range_nm=2808,
                tags=['airliner', 'regional', 'turboprop'],
                has_radio_nav=True,
                runway_takeoff=8000,
                runway_landing=6000
            ),
            'LJ45': AircraftType(
                name='Learjet 45',
                name_full='Bombardier Learjet 45',
                icao_code='LJ45',
                aerofly_code='lj45',
                cruise_speed_kts=486,
                approach_airspeed_kts=120,
                cruise_altitude_ft=41000,
                maximum_range_nm=1710,
                tags=['general_aviation', 'executive', 'jet'],
                has_radio_nav=True,
                runway_takeoff=4348,
                runway_landing=2658
            )
        }
    
    def get_aircraft_type(self, icao_code: str) -> Optional[AircraftType]:
        """Get aircraft type by ICAO code"""
        return self.aircraft_types.get(icao_code)
    
    def get_all_aircraft_types(self) -> List[AircraftType]:
        """Get all available aircraft types"""
        return list(self.aircraft_types.values())
    
    def get_aircraft_by_tag(self, tag: str) -> List[AircraftType]:
        """Get all aircraft types with a specific tag"""
        return [a for a in self.aircraft_types.values() if tag in a.tags]
    
    def get_aircraft_by_type(self, aircraft_type: str) -> List[AircraftType]:
        """Get all aircraft types of a specific type (e.g., 'airliner', 'jet')"""
        return [a for a in self.aircraft_types.values() if aircraft_type in a.tags]

# Create a singleton instance
aircraft_data = AircraftData() 