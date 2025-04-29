import math
from typing import Tuple

# Earth's radius in meters
EARTH_RADIUS = 6371000

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the distance between two points using the Haversine formula.
    
    Args:
        lat1, lon1: Coordinates of the first point in degrees
        lat2, lon2: Coordinates of the second point in degrees
        
    Returns:
        Distance in meters
    """
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return EARTH_RADIUS * c

def calculate_heading(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the heading (bearing) between two points in degrees.
    
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

def lat_lon_to_meters(lat: float, lon: float) -> Tuple[float, float]:
    """
    Convert latitude/longitude coordinates to meters using the Haversine formula.
    This provides a good approximation for small distances.
    
    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees
        
    Returns:
        Tuple of (x, y) coordinates in meters relative to the reference point
    """
    # Convert to radians
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    
    # Calculate x and y in meters
    x = EARTH_RADIUS * math.cos(lat_rad) * math.cos(lon_rad)
    y = EARTH_RADIUS * math.cos(lat_rad) * math.sin(lon_rad)
    
    return (x, y)

def distance_to_segment(position: Tuple[float, float], 
                       segment_start: Tuple[float, float], 
                       segment_end: Tuple[float, float]) -> float:
    """
    Calculate the perpendicular distance from a point to a line segment.
    
    Args:
        position: The point to measure from (latitude, longitude)
        segment_start: Start of the segment (latitude, longitude)
        segment_end: End of the segment (latitude, longitude)
        
    Returns:
        Perpendicular distance in meters
    """
    # Convert all coordinates to meters
    pos_meters = lat_lon_to_meters(position[0], position[1])
    start_meters = lat_lon_to_meters(segment_start[0], segment_start[1])
    end_meters = lat_lon_to_meters(segment_end[0], segment_end[1])
    
    # Calculate segment vector
    segment_vector = (end_meters[0] - start_meters[0], 
                     end_meters[1] - start_meters[1])
    
    # Calculate vector from start to position
    position_vector = (pos_meters[0] - start_meters[0],
                      pos_meters[1] - start_meters[1])
    
    # Calculate projection parameter
    segment_length_squared = segment_vector[0]**2 + segment_vector[1]**2
    if segment_length_squared == 0:
        return float('inf')
        
    projection = (position_vector[0] * segment_vector[0] + 
                 position_vector[1] * segment_vector[1]) / segment_length_squared
    
    # Clamp projection to segment
    projection = max(0, min(1, projection))
    
    # Calculate projected point
    projected_point = (start_meters[0] + projection * segment_vector[0],
                      start_meters[1] + projection * segment_vector[1])
    
    # Calculate distance to projected point
    return ((pos_meters[0] - projected_point[0])**2 + 
            (pos_meters[1] - projected_point[1])**2)**0.5 