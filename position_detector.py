from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict
import json
import time
from enum import Enum, auto
from airport_manager import AirportManager, Runway, Taxiway, ParkingPosition, HoldingPoint
from Inspiration.rewinger import UDPReceiver, GPSData, AttitudeData
import sys
import logging
from datetime import datetime
import math

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
    def __init__(self, airport_manager: AirportManager):
        self.airport_manager = airport_manager
        self.udp_receiver = UDPReceiver()
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
        print(f"Starting position detection for {self.airport_manager.name} ({self.airport_manager.icao})")
        self.udp_receiver.start_receiving()
        
    def detect_position(self, coords: Tuple[float, float], heading: float) -> Dict:
        """Detect the aircraft's position and return detailed information."""
        position_info = {
            'position': 'Unknown',
            'nearest_runway': None,
            'distance_to_center': float('inf'),
            'nearest_taxiway': None,
            'distance_to_taxiway': float('inf'),
            'nearest_parking': None,
            'parking_type': None,
            'parking_elevation': None,
            'parking_heading': None,
            'parking_size': None,
            'nearest_holding_point': None,
            'holding_point_association': None
        }
        
        # Check if we're on a runway
        for runway in self.airport_manager.runways:
            distance = runway.distance_to(coords)
            if distance < 50:  # Within 50 meters of runway centerline
                position_info['position'] = 'On Runway'
                position_info['nearest_runway'] = runway.name
                position_info['distance_to_center'] = distance
                break
        
        # Check if we're on a taxiway
        if position_info['position'] == 'Unknown':
            for taxiway in self.airport_manager.taxiways:
                distance = taxiway.distance_to(coords)
                if distance < taxiway.width / 2:  # Within taxiway width
                    position_info['position'] = 'On Taxiway'
                    position_info['nearest_taxiway'] = taxiway.name
                    position_info['distance_to_taxiway'] = distance
                    break
        
        # Check if we're at a parking position
        if position_info['position'] == 'Unknown':
            for parking in self.airport_manager.parking_positions:
                distance = parking.distance_to(coords)
                if distance < 10:  # Within 10 meters of parking position
                    position_info['position'] = 'At Parking'
                    position_info['nearest_parking'] = parking.name
                    position_info['parking_type'] = parking.type
                    position_info['parking_elevation'] = parking.elevation
                    position_info['parking_heading'] = parking.heading
                    position_info['parking_size'] = parking.size
                    break
        
        # Check if we're at a holding point
        if position_info['position'] == 'Unknown':
            for holding_point in self.airport_manager.holding_points:
                distance = holding_point.distance_to(coords)
                if distance < 10:  # Within 10 meters of holding point
                    position_info['position'] = 'At Holding Point'
                    position_info['nearest_holding_point'] = holding_point.name
                    position_info['holding_point_association'] = holding_point.associated_with
                    break
        
        # If still unknown, find nearest features
        if position_info['position'] == 'Unknown':
            # Find nearest runway
            min_distance = float('inf')
            nearest_runway = None
            for runway in self.airport_manager.runways:
                distance = runway.distance_to(coords)
                if distance < min_distance:
                    min_distance = distance
                    nearest_runway = runway
            if nearest_runway:
                position_info['nearest_runway'] = nearest_runway.name
                position_info['distance_to_center'] = min_distance
            
            # Find nearest taxiway
            min_distance = float('inf')
            nearest_taxiway = None
            for taxiway in self.airport_manager.taxiways:
                distance = taxiway.distance_to(coords)
                if distance < min_distance:
                    min_distance = distance
                    nearest_taxiway = taxiway
            if nearest_taxiway:
                position_info['nearest_taxiway'] = nearest_taxiway.name
                position_info['distance_to_taxiway'] = min_distance
            
            # Find nearest parking
            min_distance = float('inf')
            nearest_parking = None
            for parking in self.airport_manager.parking_positions:
                distance = parking.distance_to(coords)
                if distance < min_distance:
                    min_distance = distance
                    nearest_parking = parking
            if nearest_parking:
                position_info['nearest_parking'] = nearest_parking.name
                position_info['parking_type'] = nearest_parking.type
                position_info['parking_elevation'] = nearest_parking.elevation
                position_info['parking_heading'] = nearest_parking.heading
                position_info['parking_size'] = nearest_parking.size
            
            # Find nearest holding point
            min_distance = float('inf')
            nearest_holding_point = None
            for holding_point in self.airport_manager.holding_points:
                distance = holding_point.distance_to(coords)
                if distance < min_distance:
                    min_distance = distance
                    nearest_holding_point = holding_point
            if nearest_holding_point:
                position_info['nearest_holding_point'] = nearest_holding_point.name
                position_info['holding_point_association'] = nearest_holding_point.associated_with
        
        return position_info
        
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
        self.start()  # Start the UDP receiver
        
        try:
            while True:
                data = self.udp_receiver.get_latest_data()
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
                        parking = self.airport_manager.get_nearest_parking(position)
                        if parking and parking.distance_to(position) < 0.00005:  # Within 5 meters
                            info.area = AircraftArea.AT_PARKING
                            info.specific_location = parking.name
                            return info
                            
                    # 3. Check if on taxiway (if moving)
                    if gps.ground_speed > 0.5:
                        taxiway = self.airport_manager.get_nearest_taxiway(position)
                        if taxiway:
                            distance = taxiway.distance_to(position)
                            if distance < 0.00005:  # Within 5 meters
                                info.area = AircraftArea.ON_TAXIWAY
                                info.taxiway = taxiway.name
                                info.distance_to_center = distance
                                return info
                                
                    # 4. Check if at holding point (if moving)
                    if gps.ground_speed > 0.5:
                        holding_point = self.airport_manager.is_at_holding_point(position)
                        if holding_point:
                            info.area = AircraftArea.AT_HOLDING_POINT
                            info.specific_location = holding_point.name
                            info.runway = holding_point.runway
                            return info
                            
                    # 5. Check if on runway (most restrictive criteria)
                    if gps.ground_speed > 0.5:
                        for runway in self.airport_manager.runways:
                            # First check if between thresholds
                            is_between_thresholds = self.airport_manager.is_on_runway(position, runway)
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
                else:
                    self.logger.debug("No GPS or Attitude data received")
                    time.sleep(1)
                
        except KeyboardInterrupt:
            print("\nStopping position detection...")
            self.udp_receiver.stop()

if __name__ == "__main__":
    layout_file = sys.argv[1] if len(sys.argv) > 1 else "airport_layout.json"
    airport_manager = AirportManager(layout_file)
    detector = PositionDetector(airport_manager)
    detector.run() 