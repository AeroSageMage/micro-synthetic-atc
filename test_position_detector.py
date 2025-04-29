import unittest
import threading
import time
import socket
import json
from position_detector import PositionDetector, AircraftArea
from position_detector_gui import PositionDetectorGUI
from airport_manager import AirportManager
from read_my_csv import extract_gps_from_csv

class TestPositionDetector(unittest.TestCase):
    def setUp(self):
        # Load airport data
        self.airport_manager = AirportManager("airport_data/LIRF.json")
        self.detector = PositionDetector(self.airport_manager)
        
        # Setup UDP socket for testing
        self.udp_ip = "127.0.0.1"
        self.udp_port = 49002
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Load test data
        self.test_data, _, _ = extract_gps_from_csv("Inspiration/output_recorder/output_GPS_DATA.csv")
        
        # Expected test results
        self.expected_results = {
            "parking": {
                "area": AircraftArea.AT_PARKING,
                "speed_threshold": 0.5,
                "altitude_threshold": 5.0
            },
            "taxiway": {
                "area": AircraftArea.ON_TAXIWAY,
                "taxiway_name": "D",
                "speed_threshold": 0.5,
                "distance_threshold": 5.0
            },
            "holding_point": {
                "area": AircraftArea.AT_HOLDING_POINT,
                "runway": "16C",
                "speed_threshold": 0.5
            },
            "runway": {
                "area": AircraftArea.ON_RUNWAY,
                "runway": "16C",
                "heading_tolerance": 45.0
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
        # XGPS<simulator_name>,<longitude>,<latitude>,<altitude_msl>,<track_true_north>,<groundspeed_m/s>
        gps_message = f"XGPS{simulator_name},{data[0]},{data[1]},{data[2]},{data[3]},{data[4]}"
        self.sock.sendto(bytes(gps_message, "utf-8"), (self.udp_ip, self.udp_port))
        
        # Send attitude data message
        # XATT<simulator_name>,<true_heading>,<pitch>,<roll>
        attitude_message = f"XATT{simulator_name},{data[5]},{data[6]},{data[7]}"
        self.sock.sendto(bytes(attitude_message, "utf-8"), (self.udp_ip, self.udp_port))
        
        # Log the messages for debugging
        print(f"Sent messages:")
        print(f"GPS: {gps_message}")
        print(f"ATT: {attitude_message}")
        print(f"AIRCRAFT: {aircraft_info}")
    
    def test_parking_position(self):
        """Test detection of aircraft at parking position"""
        # Find parking position data (low speed, ground level)
        parking_data = next((d for d in self.test_data if d[4] < self.expected_results["parking"]["speed_threshold"]), None)
        self.assertIsNotNone(parking_data, "No parking position data found")
        
        # Send data
        self.send_udp_data(parking_data)
        time.sleep(0.1)  # Allow for processing
        
        # Get position info
        info = self.detector.detect_position((parking_data[1], parking_data[0]), parking_data[5])
        
        # Verify results
        self.assertEqual(info.area, self.expected_results["parking"]["area"])
        self.assertLess(info.speed, self.expected_results["parking"]["speed_threshold"])
        self.assertLess(info.distance_to_center, self.expected_results["parking"]["altitude_threshold"])
    
    def test_taxiway_movement(self):
        """Test detection of aircraft on taxiway"""
        # Find taxiway data (moving but not too fast)
        taxiway_data = next((d for d in self.test_data 
                           if self.expected_results["taxiway"]["speed_threshold"] < d[4] < 10.0), None)
        self.assertIsNotNone(taxiway_data, "No taxiway movement data found")
        
        # Send data
        self.send_udp_data(taxiway_data)
        time.sleep(0.1)
        
        # Get position info
        info = self.detector.detect_position((taxiway_data[1], taxiway_data[0]), taxiway_data[5])
        
        # Verify results
        self.assertEqual(info.area, self.expected_results["taxiway"]["area"])
        self.assertEqual(info.taxiway, self.expected_results["taxiway"]["taxiway_name"])
        self.assertGreater(info.speed, self.expected_results["taxiway"]["speed_threshold"])
        self.assertLess(info.distance_to_center, self.expected_results["taxiway"]["distance_threshold"])
    
    def test_holding_point(self):
        """Test detection of aircraft at holding point"""
        # Find holding point data (low speed, near runway)
        holding_data = next((d for d in self.test_data 
                           if d[4] < self.expected_results["holding_point"]["speed_threshold"]), None)
        self.assertIsNotNone(holding_data, "No holding point data found")
        
        # Send data
        self.send_udp_data(holding_data)
        time.sleep(0.1)
        
        # Get position info
        info = self.detector.detect_position((holding_data[1], holding_data[0]), holding_data[5])
        
        # Verify results
        self.assertEqual(info.area, self.expected_results["holding_point"]["area"])
        self.assertEqual(info.runway, self.expected_results["holding_point"]["runway"])
        self.assertLess(info.speed, self.expected_results["holding_point"]["speed_threshold"])
    
    def test_runway_position(self):
        """Test detection of aircraft on runway"""
        # Find runway data (higher speed, aligned with runway)
        runway_data = next((d for d in self.test_data if d[4] > 20.0), None)
        self.assertIsNotNone(runway_data, "No runway position data found")
        
        # Send data
        self.send_udp_data(runway_data)
        time.sleep(0.1)
        
        # Get position info
        info = self.detector.detect_position((runway_data[1], runway_data[0]), runway_data[5])
        
        # Verify results
        self.assertEqual(info.area, self.expected_results["runway"]["area"])
        self.assertEqual(info.runway, self.expected_results["runway"]["runway"])
        
        # Check heading alignment with runway
        runway = next((r for r in self.airport_manager.runways if r.name == "16C"), None)
        self.assertIsNotNone(runway)
        heading_diff = abs((info.heading - runway.heading) % 360)
        self.assertLess(heading_diff, self.expected_results["runway"]["heading_tolerance"])
    
    def tearDown(self):
        self.sock.close()

if __name__ == "__main__":
    unittest.main() 