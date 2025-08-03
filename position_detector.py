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
    def __init__(self, airport_manager: AirportManager, atc_state_manager: Optional["ATCStateManager"] = None):
        self.airport_manager = airport_manager
        self.atc_state_manager = atc_state_manager
        self.udp_receiver = UDPReceiver()
        self.last_position = None
        self.last_update = None
        
        # Setup logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        self.logger = logging.getLogger(__name__)
        
    def set_atc_state_manager(self, atc_state_manager: "ATCStateManager"):
        """Set the ATC state manager to update with position information"""
        self.atc_state_manager = atc_state_manager

    def start(self):
        """Start the position detection system."""
        print(f"Starting position detection for {self.airport_manager.name} ({self.airport_manager.icao})")
        self.udp_receiver.start_receiving()
        
    def detect_position(self, coordinates: Tuple[float, float], heading: float) -> PositionInfo:
        """Detect the aircraft's position and provide detailed information."""
        lat, lon = coordinates
        
        # Update ATC state manager if available
        if self.atc_state_manager:
            self.atc_state_manager.update_position(coordinates, heading)
        
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
            if distance < min_distance:
                min_distance = distance
                nearest_holding = holding
                
        if nearest_holding:
            info.specific_location = nearest_holding.name
            info.runway = nearest_holding.associated_with
            
        # Determine area based on position and conditions
        if info.specific_location and info.specific_location.startswith("Parking"):
            info.area = AircraftArea.AT_PARKING
        elif info.taxiway:
            info.area = AircraftArea.ON_TAXIWAY
        elif info.specific_location and info.specific_location.startswith("H"):
            info.area = AircraftArea.AT_HOLDING_POINT
        elif info.runway and info.distance_to_center and info.distance_to_center < 22.5:  # Half of runway width
            info.area = AircraftArea.ON_RUNWAY
            
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
        print(f"Starting position detection for {self.airport_manager.name} ({self.airport_manager.icao})")
        # Don't call self.start() here since we're calling run() directly
        
        try:
            while True:
                data = self.udp_receiver.get_latest_data()
                print(f"UDP data received: {data}")  # Debug: see what data we're getting
                
                if data['gps'] and data['attitude']:
                    gps = data['gps']
                    attitude = data['attitude']
                    position = (gps.latitude, gps.longitude)
                    
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
                time.sleep(2.0)  # Changed from 1.0 to 2.0 seconds
                
        except KeyboardInterrupt:
            print("\nStopping position detection...")
            self.udp_receiver.stop()

if __name__ == "__main__":
    layout_file = sys.argv[1] if len(sys.argv) > 1 else "airport_layout.json"
    airport_manager = AirportManager(layout_file)
    detector = PositionDetector(airport_manager)
    detector.run() 