import json
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
from pathlib import Path
import math

def calculate_heading(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the heading (bearing) between two points in degrees.
    Uses the Haversine formula for accurate calculations.
    
    Args:
        lat1, lon1: Coordinates of the first point in degrees
        lat2, lon2: Coordinates of the second point in degrees
        
    Returns:
        Heading in degrees from 0 to 360
    """
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Calculate differences
    dlon = lon2 - lon1
    
    # Calculate heading using the formula
    y = math.sin(dlon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    
    # Calculate heading in degrees
    heading = math.degrees(math.atan2(y, x))
    
    # Normalize to 0-360
    heading = (heading + 360) % 360
    
    return heading

@dataclass
class Runway:
    name: str
    threshold_coords: List[float]
    length: float
    width: float
    _heading: Optional[float] = None

    def __init__(self, name: str, threshold_coords: List[float], length: float, width: float, heading: Optional[float] = None):
        self.name = name
        self.length = length
        self.width = width
        self._heading = heading
        
        # Handle both single threshold point and dual threshold point cases
        if len(threshold_coords) == 2:
            # Single threshold point provided, calculate second point based on heading and length
            lat1, lon1 = threshold_coords
            # Convert length to degrees (approximate)
            length_deg = length / 111000  # 1 degree ≈ 111km
            # Calculate second point based on heading
            lat2 = lat1 + length_deg * math.cos(math.radians(heading))
            lon2 = lon1 + length_deg * math.sin(math.radians(heading))
            self.threshold_coords = [lat1, lon1, lat2, lon2]
        else:
            # Dual threshold points provided
            self.threshold_coords = threshold_coords

    @property
    def heading(self) -> float:
        if self._heading is not None:
            return self._heading
        # Calculate heading from threshold coordinates
        lat1, lon1 = self.threshold_coords[:2]
        lat2, lon2 = self.threshold_coords[2:]
        return calculate_heading(lat1, lon1, lat2, lon2)

    def _lat_lon_to_meters(self, lat, lon):
        """
        Convert latitude/longitude coordinates to meters using the Haversine formula.
        This provides a good approximation for small distances.
        
        Args:
            lat (float or str): Latitude in degrees
            lon (float or str): Longitude in degrees
            
        Returns:
            tuple: (x, y) coordinates in meters relative to the reference point
        """
        # Convert strings to floats if necessary
        lat = float(lat) if isinstance(lat, str) else lat
        lon = float(lon) if isinstance(lon, str) else lon
        
        # Earth's radius in meters
        R = 6371000
        
        # Convert to radians
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)
        
        # Calculate x and y in meters
        x = R * math.cos(lat_rad) * math.cos(lon_rad)
        y = R * math.cos(lat_rad) * math.sin(lon_rad)
        
        return (x, y)

    def distance_to_center(self, position: Tuple[float, float]) -> float:
        """Calculate the perpendicular distance from the given position to the runway center line.
        
        Args:
            position: The aircraft's current position (latitude, longitude)
            
        Returns:
            The perpendicular distance in meters
        """
        # Convert all coordinates to meters for accurate distance calculations
        pos_meters = self._lat_lon_to_meters(float(position[0]), float(position[1]))
        threshold1_meters = self._lat_lon_to_meters(float(self.threshold_coords[0]), float(self.threshold_coords[1]))
        threshold2_meters = self._lat_lon_to_meters(float(self.threshold_coords[2]), float(self.threshold_coords[3]))
        
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

    def _lat_lon_to_meters(self, lat, lon):
        """
        Convert latitude/longitude coordinates to meters using the Haversine formula.
        This provides a good approximation for small distances.
        
        Args:
            lat (float or str): Latitude in degrees
            lon (float or str): Longitude in degrees
            
        Returns:
            tuple: (x, y) coordinates in meters relative to the reference point
        """
        # Convert strings to floats if necessary
        lat = float(lat) if isinstance(lat, str) else lat
        lon = float(lon) if isinstance(lon, str) else lon
        
        # Earth's radius in meters
        R = 6371000
        
        # Convert to radians
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)
        
        # Calculate x and y in meters
        x = R * math.cos(lat_rad) * math.cos(lon_rad)
        y = R * math.cos(lat_rad) * math.sin(lon_rad)
        
        return (x, y)

    def distance_to(self, position: Tuple[float, float]) -> float:
        """Calculate the perpendicular distance from the given position to the nearest taxiway segment.
        
        Args:
            position: The aircraft's current position (latitude, longitude)
            
        Returns:
            The perpendicular distance in meters
        """
        min_distance = float('inf')
        
        for segment in self.segments:
            # Convert all coordinates to meters for accurate distance calculations
            pos_meters = self._lat_lon_to_meters(float(position[0]), float(position[1]))
            start_meters = self._lat_lon_to_meters(float(segment.start[0]), float(segment.start[1]))
            end_meters = self._lat_lon_to_meters(float(segment.end[0]), float(segment.end[1]))
            
            # Calculate segment vector
            segment_vector = (end_meters[0] - start_meters[0], 
                            end_meters[1] - start_meters[1])
            
            # Calculate vector from start to aircraft
            aircraft_vector = (pos_meters[0] - start_meters[0],
                             pos_meters[1] - start_meters[1])
            
            # Calculate projection parameter
            segment_length_squared = segment_vector[0]**2 + segment_vector[1]**2
            if segment_length_squared == 0:
                continue
                
            projection = (aircraft_vector[0] * segment_vector[0] + aircraft_vector[1] * segment_vector[1]) / segment_length_squared
            
            # Clamp projection to segment
            projection = max(0, min(1, projection))
            
            # Calculate perpendicular distance to segment
            projected_point = (start_meters[0] + projection * segment_vector[0],
                             start_meters[1] + projection * segment_vector[1])
            
            distance = ((pos_meters[0] - projected_point[0])**2 + 
                       (pos_meters[1] - projected_point[1])**2)**0.5
            
            if distance < min_distance:
                min_distance = distance
        
        return min_distance

@dataclass
class ParkingPosition:
    name: str
    coords: Tuple[float, float]
    type: str
    
    def distance_to(self, position: Tuple[float, float]) -> float:
        """Calculate the distance to another position in degrees."""
        return ((self.coords[0] - position[0])**2 + 
                (self.coords[1] - position[1])**2)**0.5

@dataclass
class HoldingPoint:
    name: str
    coords: Tuple[float, float]
    type: str
    runway: Optional[str] = None
    taxiway: Optional[str] = None

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
            
            self.name = data['name']
            self.icao = data['icao']
            
            # Load runways
            self.runways = []
            for r in data['runways']:
                # Handle both threshold_coords and threshold1_coords/threshold2_coords formats
                if 'threshold_coords' in r:
                    threshold_coords = r['threshold_coords']
                else:
                    # Combine threshold1 and threshold2 coordinates
                    threshold_coords = r['threshold1_coords'] + r['threshold2_coords']
                
                self.runways.append(
                    Runway(
                        name=r['name'],
                        threshold_coords=threshold_coords,
                        length=r['length'],
                        width=r['width'],
                        heading=r.get('heading')  # Optional heading
                    )
                )
            
            # Load taxiways
            self.taxiways = []
            for t in data['taxiways']:
                print(f"DEBUG: Processing taxiway {t['name']}")
                print(f"DEBUG: Segments: {t['segments']}")
                segments = []
                points = t['segments']
                width = t.get('width', 23)  # Default width if not specified
                
                # Handle both segment formats
                if isinstance(points[0], dict) and 'start' in points[0]:
                    # Format 1: Explicit start/end points
                    for segment in points:
                        segments.append(
                            TaxiwaySegment(
                                start=tuple(segment['start']),
                                end=tuple(segment['end']),
                                width=segment.get('width', width)
                            )
                        )
                else:
                    # Format 2: List of points
                    for i in range(len(points) - 1):
                        print(f"DEBUG: Creating segment from {points[i]} to {points[i + 1]}")
                        segments.append(
                            TaxiwaySegment(
                                start=tuple(points[i]),
                                end=tuple(points[i + 1]),
                                width=width
                            )
                        )
                
                self.taxiways.append(
                    Taxiway(
                        name=t['name'],
                        segments=segments
                    )
                )
            
            # Load parking positions
            self.parking_positions = []
            for p in data['parking_positions']:
                self.parking_positions.append(
                    ParkingPosition(
                        name=p['name'],
                        coords=tuple(p['coords']),
                        type=p['type']
                    )
                )
            
            # Load holding points
            self.holding_points = []
            for h in data['holding_points']:
                self.holding_points.append(
                    HoldingPoint(
                        name=h['name'],
                        coords=tuple(h['coords']),
                        type='Runway',  # Default type
                        runway=h.get('associated_with')  # Optional runway association
                    )
                )
            
        except Exception as e:
            print(f"Error loading airport layout: {e}")
            print("Please check the format of your airport layout file.")
            print("Expected formats:")
            print("1. Taxiway segments:")
            print("   [[lat, lon], [lat, lon], ...] with optional \"width\" field")
            print("2. Parking positions:")
            print("   {\"name\": name, \"coords\": [lat, lon], \"type\": type}")
            print("3. Holding points:")
            print("   {\"name\": name, \"coords\": [lat, lon], \"associated_with\": runway}")
            raise
    
    def get_nearest_parking(self, position: Tuple[float, float], threshold: float = 0.0002) -> Optional[ParkingPosition]:
        """Find the nearest parking position to the given coordinates.
        
        Args:
            position: The aircraft's current position (latitude, longitude)
            threshold: Maximum distance in degrees to consider the aircraft at the parking position
                      (default 0.0002 degrees ≈ 22 meters at the equator)
            
        Returns:
            The nearest parking position if within threshold, None otherwise
        """
        if not self.parking_positions:
            return None
            
        def distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
            return ((float(p1[0]) - float(p2[0]))**2 + 
                   (float(p1[1]) - float(p2[1]))**2)**0.5
            
        nearest = min(self.parking_positions, key=lambda p: distance(p.coords, position))
        dist = distance(nearest.coords, position)
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
        """Generate a taxi route between two points using the taxiway network.
        
        Args:
            start: Starting position (latitude, longitude)
            end: Destination position (latitude, longitude)
            
        Returns:
            List of taxiway names to follow in order
        """
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
        """Find the nearest taxiway segment to a position.
        
        Args:
            position: Position to find nearest segment to (latitude, longitude)
            
        Returns:
            Tuple of ((taxiway_name, segment_index), distance) or None if no segment found
        """
        nearest = None
        min_distance = float('inf')
        
        for taxiway in self.taxiways:
            for i, segment in enumerate(taxiway.segments):
                # Calculate distance to segment
                distance = self._distance_to_segment(position, segment)
                if distance < min_distance:
                    min_distance = distance
                    nearest = ((taxiway.name, i), distance)
        
        return nearest
    
    def _distance_to_segment(self, position: Tuple[float, float], segment: TaxiwaySegment) -> float:
        """Calculate the distance from a position to a taxiway segment."""
        # Convert to meters for accurate distance calculation
        pos_meters = self._lat_lon_to_meters(float(position[0]), float(position[1]))
        start_meters = self._lat_lon_to_meters(float(segment.start[0]), float(segment.start[1]))
        end_meters = self._lat_lon_to_meters(float(segment.end[0]), float(segment.end[1]))
        
        # Calculate vector from start to end
        segment_vector = (end_meters[0] - start_meters[0], end_meters[1] - start_meters[1])
        
        # Calculate vector from start to position
        position_vector = (pos_meters[0] - start_meters[0],
                         pos_meters[1] - start_meters[1])
        
        # Calculate projection parameter
        segment_length_squared = segment_vector[0]**2 + segment_vector[1]**2
        if segment_length_squared == 0:
            return float('inf')
            
        projection = (position_vector[0] * segment_vector[0] + position_vector[1] * segment_vector[1]) / segment_length_squared
        
        # Clamp projection to segment
        projection = max(0, min(1, projection))
        
        # Calculate projected point
        projected_point = (start_meters[0] + projection * segment_vector[0],
                         start_meters[1] + projection * segment_vector[1])
        
        # Calculate distance to projected point
        return ((pos_meters[0] - projected_point[0])**2 + 
                (pos_meters[1] - projected_point[1])**2)**0.5
    
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
        """Check if the aircraft is at a holding point.
        
        Args:
            position: The aircraft's current position (latitude, longitude)
            threshold: Maximum distance in degrees to consider the aircraft at the holding point
                      (default 0.002 degrees ≈ 220 meters at the equator)
        """
        for hp in self.holding_points:
            lat_diff = abs(float(hp.coords[0]) - float(position[0]))
            lon_diff = abs(float(hp.coords[1]) - float(position[1]))
            if lat_diff <= threshold and lon_diff <= threshold:
                print(f"DEBUG: Holding point {hp.name} detected")
                return hp
        return None
    
    def is_on_runway(self, position, runway, threshold=0.002):
        """Check if the aircraft is on the runway by determining if it's between the thresholds
        and within the runway width.
        
        Args:
            position: The aircraft's current position (latitude, longitude)
            runway: The runway to check against
            threshold: Maximum distance in degrees to consider the aircraft on the runway
                      (default 0.002 degrees ≈ 220 meters at the equator)
        """
        if not runway:
            return False
            
        # Convert all coordinates to meters for accurate distance calculations
        pos_meters = self._lat_lon_to_meters(float(position[0]), float(position[1]))
        threshold1_meters = self._lat_lon_to_meters(float(runway.threshold_coords[0]), float(runway.threshold_coords[1]))
        threshold2_meters = self._lat_lon_to_meters(float(runway.threshold_coords[2]), float(runway.threshold_coords[3]))
        
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

    def _lat_lon_to_meters(self, lat, lon):
        """
        Convert latitude/longitude coordinates to meters using the Haversine formula.
        This provides a good approximation for small distances.
        
        Args:
            lat (float or str): Latitude in degrees
            lon (float or str): Longitude in degrees
            
        Returns:
            tuple: (x, y) coordinates in meters relative to the reference point
        """
        # Convert strings to floats if necessary
        lat = float(lat) if isinstance(lat, str) else lat
        lon = float(lon) if isinstance(lon, str) else lon
        
        # Earth's radius in meters
        R = 6371000
        
        # Convert to radians
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)
        
        # Calculate x and y in meters
        x = R * math.cos(lat_rad) * math.cos(lon_rad)
        y = R * math.cos(lat_rad) * math.sin(lon_rad)
        
        return (x, y)

    def get_nearest_taxiway(self, position: Tuple[float, float], threshold: float = 0.0002) -> Optional[Taxiway]:
        """Find the nearest taxiway to the given coordinates.
        
        Args:
            position: The aircraft's current position (latitude, longitude)
            threshold: Maximum distance in degrees to consider the aircraft on the taxiway
                      (default 0.0002 degrees ≈ 22 meters at the equator)
            
        Returns:
            The nearest taxiway if within threshold, None otherwise
        """
        if not self.taxiways:
            return None
            
        nearest_taxiway = None
        min_distance = float('inf')
        
        for taxiway in self.taxiways:
            for segment in taxiway.segments:
                distance = self._distance_to_segment(position, segment)
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