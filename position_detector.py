from dataclasses import dataclass
from typing import Optional, Tuple, List
import json
import time
from enum import Enum, auto
from airport_manager import AirportManager
from Inspiration.rewinger import UDPReceiver, GPSData, AttitudeData
import sys
import logging
from datetime import datetime

class AircraftArea(Enum):
    NOT_DETECTED = auto()
    AT_PARKING = auto()
    ON_TAXIWAY = auto()
    AT_HOLDING_POINT = auto()
    ON_RUNWAY = auto()
    IN_FLIGHT = auto()

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
    def __init__(self, layout_file: str = "airport_layout.json"):
        self.udp_receiver = UDPReceiver()
        self.airport = AirportManager(layout_file)
        self.last_position = None
        self.last_update = None
        
        # Setup logging
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"position_detector_{timestamp}.log"
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def start(self):
        """Start the position detection system."""
        print(f"Starting position detection for {self.airport.name} ({self.airport.icao})")
        self.udp_receiver.start_receiving()
        
    def detect_position(self) -> PositionInfo:
        """Detect the aircraft's current position and return a PositionInfo object."""
        data = self.udp_receiver.get_latest_data()
        
        if not data['gps'] or not data['attitude']:
            self.logger.debug("No GPS or Attitude data received")
            return PositionInfo(area=AircraftArea.NOT_DETECTED)
            
        gps = data['gps']
        attitude = data['attitude']
        position = (gps.latitude, gps.longitude)
        
        # Debug GPS data
        self.logger.debug(f"GPS Data - Altitude: {gps.altitude}, Ground Speed: {gps.ground_speed}")
        self.logger.debug(f"Position - Lat: {position[0]}, Lon: {position[1]}")
        
        # Update position tracking
        self.last_position = position
        self.last_update = time.time()
        
        # Initialize with default NOT_DETECTED area
        info = PositionInfo(
            area=AircraftArea.NOT_DETECTED,
            heading=attitude.true_heading,
            speed=gps.ground_speed
        )
        
        # 1. Check if in flight (most restrictive criteria)
        is_in_flight = (
            gps.altitude > 500 and  # Above 500 meters
            gps.ground_speed > 50  # Moving faster than taxi speed
        )
        
        self.logger.debug(f"In Flight Check - Altitude > 500: {gps.altitude > 500}, Speed > 50: {gps.ground_speed > 50}")
        
        if is_in_flight:
            info.area = AircraftArea.IN_FLIGHT
            return info
            
        # 2. Check if stationary (ground speed < 0.5 m/s)
        if gps.ground_speed < 0.5:
            # Check parking first when stationary
            parking = self.airport.get_nearest_parking(position)
            if parking and parking.distance_to(position) < 0.00005:  # Within 5 meters
                info.area = AircraftArea.AT_PARKING
                info.specific_location = parking.name
                return info
                
        # 3. Check if on taxiway (if moving)
        if gps.ground_speed > 0.5:
            taxiway = self.airport.get_nearest_taxiway(position)
            if taxiway:
                distance = taxiway.distance_to(position)
                if distance < 0.00005:  # Within 5 meters
                    info.area = AircraftArea.ON_TAXIWAY
                    info.taxiway = taxiway.name
                    info.distance_to_center = distance
                    return info
                    
        # 4. Check if at holding point (if moving)
        if gps.ground_speed > 0.5:
            holding_point = self.airport.is_at_holding_point(position)
            if holding_point:
                info.area = AircraftArea.AT_HOLDING_POINT
                info.specific_location = holding_point.name
                info.runway = holding_point.runway
                return info
                
        # 5. Check if on runway (most restrictive criteria)
        if gps.ground_speed > 0.5:
            for runway in self.airport.runways:
                # First check if between thresholds
                is_between_thresholds = self.airport.is_on_runway(position, runway)
                if is_between_thresholds:
                    # Then check distance to center line
                    distance_to_center = runway.distance_to_center(position)
                    if distance_to_center < runway.width / 2:  # Within runway width
                        # Additional check: must be moving in runway direction
                        heading_diff = abs((attitude.true_heading - runway.heading) % 360)
                        if heading_diff < 45 or heading_diff > 315:  # Within 45 degrees of runway heading
                            info.area = AircraftArea.ON_RUNWAY
                            info.runway = runway.name
                            info.distance_to_center = distance_to_center
                            return info
                
        self.logger.debug("\nAircraft not detected in any area")
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
        print(f"Starting position detection for {self.airport.name} ({self.airport.icao})")
        self.start()  # Start the UDP receiver
        
        try:
            while True:
                info = self.detect_position()
                print(
                    f"Area: {info.area.name.replace('_', ' ').title()} | "
                    f"Location: {info.specific_location or 'N/A'} | "
                    f"Taxiway: {info.taxiway or 'N/A'} | "
                    f"Runway: {info.runway or 'N/A'} | "
                    f"Heading: {info.heading if info.heading is not None else 'N/A'}° | "
                    f"Speed: {info.speed if info.speed is not None else 'N/A'} m/s"
                )
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\nStopping position detection...")
            self.udp_receiver.stop()

if __name__ == "__main__":
    layout_file = sys.argv[1] if len(sys.argv) > 1 else "airport_layout.json"
    detector = PositionDetector(layout_file)
    detector.run() 