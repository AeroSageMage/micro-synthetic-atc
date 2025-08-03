import tkinter as tk
from airport_manager import AirportManager
from atc_state_manager import ATCController, ATCState, AircraftStatus
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

def reload_atc_system():
    """Reload ATC system while preserving current state"""
    global atc_controller, position_detector
    
    print("\n🔄 Reloading ATC system...")
    
    # Save current state
    current_state = atc_controller.state_manager.current_state
    current_status = atc_controller.state_manager.aircraft_status
    current_callsign = atc_controller.state_manager.callsign
    current_position = atc_controller.state_manager.current_position
    
    print(f"💾 Preserving state: {current_state.value}, {current_status.value}, {current_callsign}")
    
    # Stop current system
    if atc_controller:
        atc_controller.stop()
    if position_detector:
        position_detector.udp_receiver.stop()
    
    # Reinitialize airport manager
    airport_manager = AirportManager("./airport_data/lowg_airport.json")
    
    # Create new ATC controller
    atc_controller = ATCController(airport_manager, debug=False)
    
    # Restore state
    atc_controller.state_manager.current_state = current_state
    atc_controller.state_manager.aircraft_status = current_status
    atc_controller.state_manager.callsign = current_callsign
    atc_controller.state_manager.current_position = current_position
    
    # Reconnect to radio display
    radio_display = root.winfo_children()[0].winfo_children()[0]  # Get the RadioDisplay
    atc_controller.state_manager.message_sender.set_radio_display(radio_display)
    
    # Recreate position detector
    position_detector = PositionDetector(airport_manager, atc_controller.state_manager, debug=False)
    atc_controller.state_manager.set_position_detector(position_detector)
    
    # Restart UDP receiver
    position_detector.udp_receiver.start_receiving()
    
    # Restart position detection thread
    position_detector_thread = threading.Thread(target=position_detector.run)
    position_detector_thread.daemon = True
    position_detector_thread.start()
    
    print(f"✅ ATC system reloaded! State restored: {current_state.value}, {current_status.value}, {current_callsign}")

def on_reload_key(event):
    """Handle reload key press"""
    reload_atc_system()

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
        atc_controller = ATCController(airport_manager, debug=False)
        
        # Create root window
        root = tk.Tk()
        
        # Bind reload key (Ctrl+R)
        root.bind('<Control-r>', on_reload_key)
        root.bind('<Control-R>', on_reload_key)
        
        # Create radio display with both required arguments
        radio_display = RadioDisplay(
            root,
            atc_controller.state_manager
        )
        
        # Connect radio display to message sender
        atc_controller.state_manager.message_sender.set_radio_display(radio_display)
        
        # Create position detector and connect it to ATC state manager
        position_detector = PositionDetector(airport_manager, atc_controller.state_manager, debug=False)
        atc_controller.state_manager.set_position_detector(position_detector)
        
        # Print initial state
        print(f"Initial state: {atc_controller.state_manager.current_state}")
        print(f"Initial status: {atc_controller.state_manager.aircraft_status}")
        print(f"Initial frequency: {atc_controller.state_manager.get_current_frequency().frequency} MHz")
        print("\nATC system is running. Press Ctrl+C to stop.")
        
        # Start UDP receiver with position callback
        position_detector.udp_receiver.start_receiving()
        print(f"🔧 UDP receiver started")
        
        # Set up position callback to call ATC state manager directly
        def position_callback(position, heading):
            """Callback function called when new position data is received"""
            # Debug: Check if debug attribute exists
            if hasattr(atc_controller.state_manager, 'debug'):
                if atc_controller.state_manager.debug:
                    print(f"📍 Position callback: {position}, heading: {heading}")
            else:
                print(f"⚠️  WARNING: ATCStateManager has no debug attribute!")
            atc_controller.state_manager.update_position(position, heading)
        
        position_detector.udp_receiver.set_position_callback(position_callback)
        print(f"🔧 Position callback set up")
        
        # Debug: Check ATCStateManager attributes
        print(f"🔍 ATCStateManager attributes: {dir(atc_controller.state_manager)}")
        print(f"🔍 ATCStateManager has debug: {hasattr(atc_controller.state_manager, 'debug')}")
        
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