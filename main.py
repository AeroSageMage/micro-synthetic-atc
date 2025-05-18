import tkinter as tk
from airport_manager import AirportManager
from atc_state_manager import ATCController
from radio_display import RadioDisplay
import threading
import time
import signal
import sys

def signal_handler(sig, frame):
    print("\nShutting down...")
    if 'atc_controller' in globals():
        atc_controller.stop()
    if 'root' in globals():
        root.quit()
    sys.exit(0)

def main():
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize airport manager
        airport_manager = AirportManager("./airport_data/lowg_airport.json")
        
        # Initialize ATC controller
        atc_controller = ATCController(airport_manager)
        atc_controller.start()
        
        # Create and run the UI
        root = tk.Tk()
        app = RadioDisplay(root, atc_controller.state_manager)
        
        # Connect the radio display to the message sender
        atc_controller.state_manager.message_sender.set_radio_display(app)
        
        # Print initial state
        print(f"Initial state: {atc_controller.state_manager.current_state}")
        print(f"Initial status: {atc_controller.state_manager.aircraft_status}")
        print(f"Initial frequency: {atc_controller.state_manager.get_current_frequency().frequency} MHz")
        print("\nATC system is running. Press Ctrl+C to stop.")
        
        # Start the UI main loop
        root.mainloop()
        
    except KeyboardInterrupt:
        print("\nShutting down...")
        atc_controller.stop()
        root.quit()
    except Exception as e:
        print(f"Error: {e}")
        if 'atc_controller' in locals():
            atc_controller.stop()
        if 'root' in locals():
            root.quit()
        sys.exit(1)

if __name__ == "__main__":
    main() 