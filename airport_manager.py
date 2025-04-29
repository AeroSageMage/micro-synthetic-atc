import json
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
from pathlib import Path
import math
from utils.geo_utils import calculate_heading, lat_lon_to_meters, distance_to_segment, haversine_distance

@dataclass
class Runway:
    name: str
    threshold1_coords: Tuple[float, float]
    threshold2_coords: Tuple[float, float]
    width: float
    length: float
    _heading: Optional[float] = None

    def __init__(self, name: str, threshold1_coords: List[float], threshold2_coords: List[float], 
                 width: float, length: float, heading: Optional[float] = None):
        self.name = name
        self.threshold1_coords = tuple(threshold1_coords)
        self.threshold2_coords = tuple(threshold2_coords)
        self.width = width
        self.length = length
        self._heading = heading

    @property
    def heading(self) -> float:
        if self._heading is not None:
            return self._heading
        # Calculate heading from threshold coordinates
        lat1, lon1 = self.threshold1_coords
        lat2, lon2 = self.threshold2_coords
        return calculate_heading(lat1, lon1, lat2, lon2)

    def distance_to_center(self, position: Tuple[float, float]) -> float:
        """Calculate the perpendicular distance from the given position to the runway center line."""
        # Convert all coordinates to meters
        pos_meters = lat_lon_to_meters(position[0], position[1])
        threshold1_meters = lat_lon_to_meters(self.threshold1_coords[0], self.threshold1_coords[1])
        threshold2_meters = lat_lon_to_meters(self.threshold2_coords[0], self.threshold2_coords[1])
        
        # Calculate runway center line vector
        runway_vector = (threshold2_meters[0] - threshold1_meters[0], 
                        threshold2_meters[1] - threshold1_meters[1])
        
        # Calculate vector from threshold1 to aircraft
        aircraft_vector = (pos_meters[0] - threshold1_meters[0],
                         pos_meters[1] - threshold1_meters[1])
        
        # Calculate projection parameter
        runway_length_squared = runway_vector[0]**2 + runway_vector[1]**2
        if runway_length_squared == 0:
            return float('inf')
            
        projection = (aircraft_vector[0] * runway_vector[0] + aircraft_vector[1] * runway_vector[1]) / runway_length_squared
        
        # Calculate perpendicular distance to center line
        projected_point = (threshold1_meters[0] + projection * runway_vector[0],
                         threshold1_meters[1] + projection * runway_vector[1])
        
        distance_to_center = ((pos_meters[0] - projected_point[0])**2 + 
                            (pos_meters[1] - projected_point[1])**2)**0.5
        
        return distance_to_center

@dataclass
class TaxiwaySegment:
    start: Tuple[float, float]
    end: Tuple[float, float]
    width: float

@dataclass
class Taxiway:
    name: str
    segments: List[TaxiwaySegment]

    def distance_to(self, position: Tuple[float, float]) -> float:
        """Calculate the perpendicular distance from the given position to the nearest taxiway segment."""
        min_distance = float('inf')
        
        for segment in self.segments:
            distance = distance_to_segment(position, segment.start, segment.end)
            if distance < min_distance:
                min_distance = distance
        
        return min_distance

@dataclass
class ParkingPosition:
    name: str
    coords: Tuple[float, float]
    type: str
    elevation: float
    heading: float
    size: float
    
    def __init__(self, name: str, coords: List[float], type: str, elevation: float, heading: float, size: float):
        self.name = name
        self.coords = tuple(coords)
        self.type = type
        self.elevation = elevation
        self.heading = heading
        self.size = size
    
    def distance_to(self, position: Tuple[float, float]) -> float:
        """Calculate the distance to another position in meters."""
        return haversine_distance(
            self.coords[0], self.coords[1],
            position[0], position[1]
        )

@dataclass
class HoldingPoint:
    name: str
    coords: Tuple[float, float]
    associated_with: str

    def __init__(self, name: str, coords: List[float], associated_with: str):
        self.name = name
        self.coords = tuple(coords)
        self.associated_with = associated_with

    def distance_to(self, position: Tuple[float, float]) -> float:
        """Calculate the distance to another position in meters."""
        return haversine_distance(
            self.coords[0], self.coords[1],
            position[0], position[1]
        )

class AirportManager:
    def __init__(self, layout_file: str = "airport_layout.json"):
        self.layout_file = Path(layout_file)
        self.name: str = ""
        self.icao: str = ""
        self.runways: List[Runway] = []
        self.taxiways: List[Taxiway] = []
        self.parking_positions: List[ParkingPosition] = []
        self.holding_points: List[HoldingPoint] = []
        self.load_layout()
    
    def load_layout(self) -> None:
        """Load the airport layout from the JSON file."""
        try:
            with open(self.layout_file, 'r') as f:
                data = json.load(f)
            
            self.name = data.get('name', '')
            self.icao = data.get('icao', '')
            
            # Load runways
            self.runways = []
            for runway_data in data.get('runways', []):
                runway = Runway(
                    name=runway_data['name'],
                    threshold1_coords=runway_data['threshold1_coords'],
                    threshold2_coords=runway_data['threshold2_coords'],
                    width=runway_data['width'],
                    length=runway_data['length']
                )
                self.runways.append(runway)
            
            # Load taxiways
            self.taxiways = []
            for taxiway_data in data.get('taxiways', []):
                segments = []
                for segment_data in taxiway_data['segments']:
                    segment = TaxiwaySegment(
                        start=tuple(segment_data['start']),
                        end=tuple(segment_data['end']),
                        width=segment_data['width']
                    )
                    segments.append(segment)
                taxiway = Taxiway(
                    name=taxiway_data['name'],
                    segments=segments
                )
                self.taxiways.append(taxiway)
            
            # Load parking positions
            self.parking_positions = []
            for parking_data in data.get('parking_positions', []):
                parking = ParkingPosition(
                    name=parking_data['name'],
                    coords=tuple(parking_data['coords']),
                    type=parking_data['type'],
                    elevation=parking_data['elevation'],
                    heading=parking_data['heading'],
                    size=parking_data['size']
                )
                self.parking_positions.append(parking)
            
            # Load holding points
            self.holding_points = []
            for holding_data in data.get('holding_points', []):
                holding = HoldingPoint(
                    name=holding_data['name'],
                    coords=tuple(holding_data['coords']),
                    associated_with=holding_data['associated_with']
                )
                self.holding_points.append(holding)
            
        except Exception as e:
            raise ValueError(f"Error loading airport layout: {str(e)}")
    
    def get_nearest_parking(self, position: Tuple[float, float], threshold: float = 0.0002) -> Optional[ParkingPosition]:
        """Find the nearest parking position to the given coordinates."""
        if not self.parking_positions:
            return None
            
        nearest = min(self.parking_positions, key=lambda p: p.distance_to(position))
        dist = nearest.distance_to(position)
        if dist <= threshold:
            print(f"DEBUG: Nearest parking {nearest.name} detected")
            return nearest
        return None
    
    def get_active_runway(self, wind_direction: float) -> Optional[Runway]:
        """Determine the active runway based on wind direction."""
        if not self.runways:
            return None
            
        # Simple logic: choose runway with heading closest to wind direction
        active_runway = min(self.runways, key=lambda r: abs((r.heading - wind_direction) % 360))
        print(f"DEBUG: Active runway: {active_runway.name} (heading: {active_runway.heading})")
        return active_runway
    
    def get_taxi_route(self, start: Tuple[float, float], end: Tuple[float, float]) -> List[str]:
        """Generate a taxi route between two points using the taxiway network."""
        if not self.taxiways:
            return []
            
        # Find the nearest taxiway segments to start and end points
        start_segment = self._find_nearest_taxiway_segment(start)
        end_segment = self._find_nearest_taxiway_segment(end)
        
        if not start_segment or not end_segment:
            return []
            
        # Simple pathfinding: find a path through connected taxiways
        route = []
        current_taxiway = start_segment[0]  # (taxiway_name, segment_index)
        end_taxiway = end_segment[0]
        
        # If we're already on the same taxiway as the destination
        if current_taxiway[0] == end_taxiway[0]:
            return [current_taxiway[0]]
            
        # Try to find a path through connected taxiways
        visited = set()
        queue = [(current_taxiway[0], [current_taxiway[0]])]
        
        while queue:
            current, path = queue.pop(0)
            if current == end_taxiway[0]:
                return path
                
            if current in visited:
                continue
                
            visited.add(current)
            
            # Find connected taxiways
            for taxiway in self.taxiways:
                if taxiway.name != current and self._are_taxiways_connected(current, taxiway.name):
                    queue.append((taxiway.name, path + [taxiway.name]))
        
        return []
    
    def _find_nearest_taxiway_segment(self, position: Tuple[float, float]) -> Optional[Tuple[Tuple[str, int], float]]:
        """Find the nearest taxiway segment to a position."""
        nearest = None
        min_distance = float('inf')
        
        for taxiway in self.taxiways:
            for i, segment in enumerate(taxiway.segments):
                # Calculate distance to segment
                distance = distance_to_segment(position, segment.start, segment.end)
                if distance < min_distance:
                    min_distance = distance
                    nearest = ((taxiway.name, i), distance)
        
        return nearest
    
    def _are_taxiways_connected(self, taxiway1: str, taxiway2: str) -> bool:
        """Check if two taxiways are connected."""
        # Find the taxiways
        tw1 = next((t for t in self.taxiways if t.name == taxiway1), None)
        tw2 = next((t for t in self.taxiways if t.name == taxiway2), None)
        
        if not tw1 or not tw2:
            return False
            
        # Check if any segments of taxiway1 connect to any segments of taxiway2
        for seg1 in tw1.segments:
            for seg2 in tw2.segments:
                # Check if segments share an endpoint
                if (seg1.start == seg2.start or seg1.start == seg2.end or
                    seg1.end == seg2.start or seg1.end == seg2.end):
                    return True
                    
        return False
    
    def is_at_holding_point(self, position: Tuple[float, float], threshold: float = 0.002) -> Optional[HoldingPoint]:
        """Check if the aircraft is at a holding point."""
        for hp in self.holding_points:
            if hp.distance_to(position) <= threshold:
                print(f"DEBUG: Holding point {hp.name} detected")
                return hp
        return None
    
    def is_on_runway(self, position, runway, threshold=0.002):
        """Check if the aircraft is on the runway by determining if it's between the thresholds
        and within the runway width."""
        if not runway:
            return False
            
        # Convert all coordinates to meters
        pos_meters = lat_lon_to_meters(position[0], position[1])
        threshold1_meters = lat_lon_to_meters(runway.threshold1_coords[0], runway.threshold1_coords[1])
        threshold2_meters = lat_lon_to_meters(runway.threshold2_coords[0], runway.threshold2_coords[1])
        
        # Calculate runway center line vector
        runway_vector = (threshold2_meters[0] - threshold1_meters[0], 
                        threshold2_meters[1] - threshold1_meters[1])
        
        # Calculate vector from threshold1 to aircraft
        aircraft_vector = (pos_meters[0] - threshold1_meters[0],
                         pos_meters[1] - threshold1_meters[1])
        
        # Calculate projection parameter
        runway_length_squared = runway_vector[0]**2 + runway_vector[1]**2
        if runway_length_squared == 0:
            return False
            
        projection = (aircraft_vector[0] * runway_vector[0] + aircraft_vector[1] * runway_vector[1]) / runway_length_squared
        
        # Check if aircraft is between thresholds
        if projection < 0 or projection > 1:
            return False
            
        # Calculate perpendicular distance to center line
        projected_point = (threshold1_meters[0] + projection * runway_vector[0],
                         threshold1_meters[1] + projection * runway_vector[1])
        
        distance_to_center = ((pos_meters[0] - projected_point[0])**2 + 
                            (pos_meters[1] - projected_point[1])**2)**0.5
        
        # Convert runway width from meters to degrees (approximate)
        # 1 degree ≈ 111,000 meters at the equator
        width_in_degrees = runway.width / 111000
        
        # Use the larger of the default threshold or half the runway width
        effective_threshold = max(threshold, width_in_degrees / 2)
        
        # Convert distance to degrees for comparison
        distance_in_degrees = distance_to_center / 111000
        
        # Check if aircraft is within runway width
        is_on_runway = distance_in_degrees <= effective_threshold
        if is_on_runway:
            print(f"DEBUG: Aircraft is on runway {runway.name}")
        
        return is_on_runway

    def get_nearest_taxiway(self, position: Tuple[float, float], threshold: float = 0.0002) -> Optional[Taxiway]:
        """Find the nearest taxiway to the given coordinates."""
        if not self.taxiways:
            return None
            
        nearest_taxiway = None
        min_distance = float('inf')
        
        for taxiway in self.taxiways:
            for segment in taxiway.segments:
                distance = distance_to_segment(position, segment.start, segment.end)
                if distance < min_distance:
                    min_distance = distance
                    nearest_taxiway = taxiway
        
        # Convert taxiway width from meters to degrees (approximate)
        # 1 degree ≈ 111,000 meters at the equator
        width_in_degrees = nearest_taxiway.segments[0].width / 111000 if nearest_taxiway else 0
        
        # Convert the distance from meters to degrees
        distance_in_degrees = min_distance / 111000
        
        # Use the larger of the default threshold or half the taxiway width
        effective_threshold = max(threshold, width_in_degrees / 2)
        
        if distance_in_degrees <= effective_threshold:
            print(f"DEBUG: Aircraft is on taxiway {nearest_taxiway.name} (distance: {min_distance:.1f}m)")
            return nearest_taxiway
            
        return None