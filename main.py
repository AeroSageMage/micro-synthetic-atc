import tkinter as tk
from airport_manager import AirportManager
from atc_state_manager import ATCController
from radio_display import RadioDisplay
import threading
import time
import signal
import sys
from position_detector import PositionDetector

# Global variables for signal handler
atc_controller = None
position_detector = None
root = None

def signal_handler(sig, frame):
    print("\nShutting down...")
    global atc_controller, position_detector, root
    if atc_controller:
        atc_controller.stop()
    if position_detector:
        position_detector.udp_receiver.stop()
    if root:
        root.quit()
    sys.exit(0)

def main():
    global atc_controller, position_detector, root
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize airport manager
        airport_manager = AirportManager("./airport_data/lowg_airport.json")
        
        # Create ATC controller
        atc_controller = ATCController(airport_manager)
        
        # Create root window
        root = tk.Tk()
        
        # Create radio display with both required arguments
        radio_display = RadioDisplay(
            root,
            atc_controller.state_manager
        )
        
        # Connect radio display to message sender
        atc_controller.state_manager.message_sender.set_radio_display(radio_display)
        
        # Create position detector and connect it to ATC state manager
        position_detector = PositionDetector(airport_manager, atc_controller.state_manager)
        atc_controller.state_manager.set_position_detector(position_detector)
        
        # Print initial state
        print(f"Initial state: {atc_controller.state_manager.current_state}")
        print(f"Initial status: {atc_controller.state_manager.aircraft_status}")
        print(f"Initial frequency: {atc_controller.state_manager.get_current_frequency().frequency} MHz")
        print("\nATC system is running. Press Ctrl+C to stop.")
        
        # Start UDP receiver first
        position_detector.udp_receiver.start_receiving()
        
        # Start position detection in a separate thread
        position_detector_thread = threading.Thread(target=position_detector.run)
        position_detector_thread.daemon = True
        position_detector_thread.start()
        
        # Run the UI
        root.mainloop()
        
    except KeyboardInterrupt:
        print("\nShutting down...")
        if atc_controller:
            atc_controller.stop()
        if position_detector:
            position_detector.udp_receiver.stop()
        if root:
            root.quit()
    except Exception as e:
        print(f"Error: {e}")
        if atc_controller:
            atc_controller.stop()
        if position_detector:
            position_detector.udp_receiver.stop()
        if root:
            root.quit()
        sys.exit(1)

if __name__ == "__main__":
    main() 