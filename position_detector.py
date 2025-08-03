from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict, TYPE_CHECKING
import json
import time
from enum import Enum, auto
from airport_manager import AirportManager, Runway, Taxiway, ParkingPosition, HoldingPoint
from tools.rewinger import UDPReceiver, GPSData, AttitudeData
import sys
import logging
from datetime import datetime
import math
from utils.geo_utils import haversine_distance, calculate_heading, distance_to_segment
from shared_enums import AircraftArea

if TYPE_CHECKING:
    from atc_state_manager import ATCStateManager

@dataclass
class PositionInfo:
    area: AircraftArea
    specific_location: Optional[str] = None
    taxiway: Optional[str] = None
    runway: Optional[str] = None
    distance_to_center: Optional[float] = None
    heading: Optional[float] = None
    speed: Optional[float] = None

class PositionDetector:
    def __init__(self, airport_manager: AirportManager, atc_state_manager: Optional["ATCStateManager"] = None, debug: bool = False):
        self.airport_manager = airport_manager
        self.atc_state_manager = atc_state_manager
        self.udp_receiver = UDPReceiver()
        self.last_position = None
        self.last_update = 0
        self.debug = debug  # Debug flag to control output
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        
    def set_atc_state_manager(self, atc_state_manager: "ATCStateManager"):
        """Set the ATC state manager to update with position information"""
        self.atc_state_manager = atc_state_manager

    def start(self):
        """Start the position detection system."""
        print(f"Starting position detection for {self.airport_manager.name} ({self.airport_manager.icao})")
        self.udp_receiver.start_receiving()
        
    def detect_position(self, coordinates: Tuple[float, float], heading: float) -> PositionInfo:
        """Detect the aircraft's current position and area"""
        if self.debug:
            print(f"🔍 Position detector called: {coordinates}, heading: {heading}")
            print(f"🔍 ATC state manager connected: {self.atc_state_manager is not None}")
        
        lat, lon = coordinates
        
        # Initialize with default NOT_DETECTED area
        info = PositionInfo(
            area=AircraftArea.NOT_DETECTED,
            heading=heading
        )
        
        # Find nearest runway
        nearest_runway = None
        min_distance = float('inf')
        
        for runway in self.airport_manager.runways:
            distance = runway.distance_to_center((lat, lon))
            if distance < min_distance:
                min_distance = distance
                nearest_runway = runway
                
        if nearest_runway:
            info.runway = nearest_runway.name
            info.distance_to_center = min_distance
            
        # Find nearest taxiway
        nearest_taxiway = None
        min_distance = float('inf')
        
        for taxiway in self.airport_manager.taxiways:
            distance = taxiway.distance_to((lat, lon))
            if distance < min_distance:
                min_distance = distance
                nearest_taxiway = taxiway
                
        if nearest_taxiway:
            info.taxiway = nearest_taxiway.name
            
        # Find nearest parking position
        nearest_parking = None
        min_distance = float('inf')
        
        for parking in self.airport_manager.parking_positions:
            distance = parking.distance_to((lat, lon))
            if distance < min_distance:
                min_distance = distance
                nearest_parking = parking
                
        if nearest_parking:
            info.specific_location = nearest_parking.name
            
        # Find nearest holding point
        nearest_holding = None
        min_distance = float('inf')
        
        for holding in self.airport_manager.holding_points:
            distance = holding.distance_to((lat, lon))
            if self.debug:
                print(f"DEBUG: Holding point {holding.name} at {holding.coords} - distance: {distance:.6f} meters")
            if distance < min_distance:
                min_distance = distance
                nearest_holding = holding
                
        if nearest_holding:
            if self.debug:
                print(f"DEBUG: Nearest holding point: {nearest_holding.name} (distance: {min_distance:.6f} meters)")
                # Convert meters to degrees for comparison (1 degree ≈ 111,000 meters)
                distance_in_degrees = min_distance / 111000
                print(f"DEBUG: Distance in degrees: {distance_in_degrees:.6f}")
                print(f"DEBUG: Threshold for detection: 0.002 degrees")
                print(f"DEBUG: Within threshold: {distance_in_degrees <= 0.002}")
            info.specific_location = nearest_holding.name
            info.runway = nearest_holding.associated_with
        else:
            if self.debug:
                print("DEBUG: No holding points found")
            
        # Determine area based on position and conditions
        if self.debug:
            print(f"DEBUG: Determining area - specific_location: {info.specific_location}")
            print(f"DEBUG: Determining area - starts with 'H': {info.specific_location and info.specific_location.startswith('H')}")
        
        if info.specific_location and info.specific_location.startswith("Parking"):
            info.area = AircraftArea.AT_PARKING
            if self.debug:
                print("DEBUG: Area = AT_PARKING")
        elif nearest_holding:  # Check holding points FIRST (before taxiways)
            info.area = AircraftArea.AT_HOLDING_POINT
            if self.debug:
                print("DEBUG: Area = AT_HOLDING_POINT")
            # Don't update ATC state manager here - let the caller handle it
            if self.debug:
                print(f"🛫 Aircraft at holding point: {info.specific_location or nearest_holding.name or 'unnamed'}")
        elif info.taxiway:  # Check taxiways AFTER holding points
            info.area = AircraftArea.ON_TAXIWAY
            if self.debug:
                print("DEBUG: Area = ON_TAXIWAY")
        elif info.runway and info.distance_to_center and info.distance_to_center < 22.5:  # Half of runway width
            info.area = AircraftArea.ON_RUNWAY
            if self.debug:
                print("DEBUG: Area = ON_RUNWAY")
        else:
            info.area = AircraftArea.NOT_DETECTED
            if self.debug:
                print("DEBUG: Area = NOT_DETECTED")
        
        return info
        
    def format_position_info(self, info: PositionInfo) -> str:
        """Format the position information into a readable string."""
        if info.area == AircraftArea.NOT_DETECTED:
            return "Aircraft position not detected"
            
        status = []
        status.append(f"Area: {info.area.name.replace('_', ' ').title()}")
        
        if info.specific_location:
            status.append(f"Location: {info.specific_location}")
        if info.taxiway:
            status.append(f"Taxiway: {info.taxiway}")
        if info.runway:
            status.append(f"Runway: {info.runway}")
        if info.distance_to_center is not None:
            status.append(f"Distance to center: {info.distance_to_center:.2f} meters")
        if info.heading is not None:
            status.append(f"Heading: {info.heading:.1f}°")
        if info.speed is not None:
            status.append(f"Speed: {info.speed:.1f} m/s")
            
        return " | ".join(status)
        
    def run(self):
        """Run the position detector."""
        print(f"🚀 Starting position detection for {self.airport_manager.name} ({self.airport_manager.icao})")
        print(f"🚀 Position detector thread started")
        # Don't call self.start() here since we're calling run() directly
        
        try:
            while True:
                print(f"🔄 Position detector loop iteration")
                data = self.udp_receiver.get_latest_data()
                print(f"📡 UDP data received: {data}")  # Debug: see what data we're getting
                
                if data['gps'] and data['attitude']:
                    gps = data['gps']
                    attitude = data['attitude']
                    position = (gps.latitude, gps.longitude)
                    
                    print(f"📡 Processing GPS data: {position}, heading: {attitude.true_heading}")
                    
                    # Debug GPS data
                    self.logger.debug(f"GPS Data - Altitude: {gps.altitude}, Ground Speed: {gps.ground_speed}")
                    self.logger.debug(f"Position - Lat: {position[0]}, Lon: {position[1]}")
                    
                    # Update position tracking
                    self.last_position = position
                    self.last_update = time.time()
                    
                    # Call detect_position to update ATC state manager
                    info = self.detect_position(position, attitude.true_heading)
                    
                    # Print position info for debugging
                    print(f"Position detected: {info.area.value} at {position[0]:.6f}, {position[1]:.6f}")
                    if info.specific_location:
                        print(f"  Location: {info.specific_location}")
                    if info.taxiway:
                        print(f"  Taxiway: {info.taxiway}")
                    if info.runway:
                        print(f"  Runway: {info.runway}")
                    
                else:
                    print("No GPS or Attitude data received from UDP")  # Debug: see when no data
                    self.logger.debug("No GPS or Attitude data received")
                
                # Sleep longer to prevent GUI freezing
                time.sleep(2.0)  # Back to 2.0 seconds - the beachball was caused by UI calling position detector
                
        except KeyboardInterrupt:
            print("\nStopping position detection...")
            self.udp_receiver.stop()
        except Exception as e:
            print(f"❌ Position detector thread crashed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python3 position_detector.py <airport_json> <latitude> <longitude> [heading]")
        print("Example: python3 position_detector.py airport_data/lowg_airport.json 47.004 15.4381 308.6")
        sys.exit(1)
    
    layout_file = sys.argv[1]
    lat = float(sys.argv[2])
    lon = float(sys.argv[3])
    heading = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
    
    print(f"Testing position detection:")
    print(f"  Airport: {layout_file}")
    print(f"  Position: ({lat}, {lon})")
    print(f"  Heading: {heading}")
    print()
    
    airport_manager = AirportManager(layout_file)
    detector = PositionDetector(airport_manager)
    
    # Test the position detection
    info = detector.detect_position((lat, lon), heading)
    
    print(f"\nResults:")
    print(f"  Area: {info.area.value}")
    print(f"  Location: {info.specific_location}")
    print(f"  Taxiway: {info.taxiway}")
    print(f"  Runway: {info.runway}")
    print(f"  Distance to center: {info.distance_to_center}")
    print(f"  Formatted: {detector.format_position_info(info)}") 