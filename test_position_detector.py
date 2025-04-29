import unittest
import threading
import time
import socket
import json
import sys
import os

# Add tools directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

from position_detector import PositionDetector, AircraftArea
from position_detector_gui import PositionDetectorGUI
from airport_manager import AirportManager
from read_my_csv import extract_gps_from_csv

class TestPositionDetector(unittest.TestCase):
    def setUp(self):
        # Load airport data
        self.airport_manager = AirportManager("lowg_airport.json")
        self.detector = PositionDetector(self.airport_manager)
        
        # Setup UDP socket for testing
        self.udp_ip = "127.0.0.1"
        self.udp_port = 49002
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Load test data
        self.test_data, _, _ = extract_gps_from_csv("tools/output_recorder/output_GPS_DATA.csv")
        
        # Expected test results based on actual airport layout positions
        self.expected_results = {
            "parking": {
                "area": AircraftArea.AT_PARKING,
                "speed_threshold": 0.5,
                "altitude_threshold": 5.0,
                "coordinates": (46.998795, 15.443520)  # Parking0 position
            },
            "taxiway": {
                "area": AircraftArea.ON_TAXIWAY,
                "taxiway_name": "D",
                "speed_threshold": 0.5,
                "distance_threshold": 5.0,
                "coordinates": (46.9944148, 15.4427199)  # Middle of taxiway D
            },
            "holding_point": {
                "area": AircraftArea.AT_HOLDING_POINT,
                "runway": "16C",
                "speed_threshold": 0.5,
                "coordinates": (47.004069, 15.438067)  # H1 holding point
            },
            "runway": {
                "area": AircraftArea.ON_RUNWAY,
                "runway": "16C",
                "heading_tolerance": 45.0,
                "coordinates": (46.991, 15.439)  # Middle of runway 16C
            }
        }
    
    def send_udp_data(self, data):
        """Send UDP data to the position detector following Aerofly UDP protocol"""
        simulator_name = "Aerofly FS 4"
        icao_address = "TEST01"
        callsign = "TEST"
        
        # Send aircraft info message
        aircraft_info = f"XAIRCRAFT{simulator_name},TEST01,{icao_address},C172,N12345,{callsign},"
        self.sock.sendto(bytes(aircraft_info, "utf-8"), (self.udp_ip, self.udp_port))
        
        # Send GPS data message
        gps_message = f"XGPS{simulator_name},{data[0]},{data[1]},{data[2]},{data[3]},{data[4]}"
        self.sock.sendto(bytes(gps_message, "utf-8"), (self.udp_ip, self.udp_port))
        
        # Send attitude data message
        attitude_message = f"XATT{simulator_name},{data[5]},{data[6]},{data[7]}"
        self.sock.sendto(bytes(attitude_message, "utf-8"), (self.udp_ip, self.udp_port))
    
    def test_parking_position(self):
        """Test detection of aircraft at parking position"""
        # Use the parking position coordinates
        lat, lon = self.expected_results["parking"]["coordinates"]
        heading = 167  # Parking0 heading
        
        # Create test data with parking position
        test_data = [lon, lat, 336.0, 0.1, 167.0, 167.0, 0.0, 0.0]
        self.send_udp_data(test_data)
        
        # Test position detection
        position_info = self.detector.detect_position((lat, lon), heading)
        
        # Verify results
        self.assertEqual(position_info.area, self.expected_results["parking"]["area"])
        self.assertIsNotNone(position_info.specific_location)
        self.assertLess(0.1, self.expected_results["parking"]["speed_threshold"])
        self.assertLess(abs(336.0), self.expected_results["parking"]["altitude_threshold"])
    
    def test_taxiway_movement(self):
        """Test detection of aircraft on taxiway"""
        # Use the taxiway position coordinates
        lat, lon = self.expected_results["taxiway"]["coordinates"]
        heading = 170  # Approximate taxiway heading
        
        # Create test data with taxiway position
        test_data = [lon, lat, 337.0, 5.0, 170.0, 170.0, 0.0, 0.0]
        self.send_udp_data(test_data)
        
        # Test position detection
        position_info = self.detector.detect_position((lat, lon), heading)
        
        # Verify results
        self.assertEqual(position_info.area, self.expected_results["taxiway"]["area"])
        self.assertEqual(position_info.taxiway, self.expected_results["taxiway"]["taxiway_name"])
        self.assertLess(position_info.distance_to_center, self.expected_results["taxiway"]["distance_threshold"])
    
    def test_holding_point(self):
        """Test detection of aircraft at holding point"""
        # Use the holding point coordinates
        lat, lon = self.expected_results["holding_point"]["coordinates"]
        heading = 170  # Approximate holding point heading
        
        # Create test data with holding point position
        test_data = [lon, lat, 337.0, 0.1, 170.0, 170.0, 0.0, 0.0]
        self.send_udp_data(test_data)
        
        # Test position detection
        position_info = self.detector.detect_position((lat, lon), heading)
        
        # Verify results
        self.assertEqual(position_info.area, self.expected_results["holding_point"]["area"])
        self.assertIsNotNone(position_info.specific_location)
        self.assertEqual(position_info.runway, self.expected_results["holding_point"]["runway"])
    
    def test_runway_position(self):
        """Test detection of aircraft on runway"""
        # Use the runway position coordinates
        lat, lon = self.expected_results["runway"]["coordinates"]
        heading = 170  # Runway 16C heading
        
        # Create test data with runway position
        test_data = [lon, lat, 337.0, 25.0, 170.0, 170.0, 0.0, 0.0]
        self.send_udp_data(test_data)
        
        # Test position detection
        position_info = self.detector.detect_position((lat, lon), heading)
        
        # Verify results
        self.assertEqual(position_info.area, self.expected_results["runway"]["area"])
        self.assertEqual(position_info.runway, self.expected_results["runway"]["runway"])
        
        # Check heading alignment with runway
        runway_heading = self.airport_manager.get_runway_heading(position_info.runway)
        heading_diff = abs(heading - runway_heading)
        self.assertLess(heading_diff, self.expected_results["runway"]["heading_tolerance"])
    
    def tearDown(self):
        self.sock.close()

if __name__ == "__main__":
    unittest.main() 