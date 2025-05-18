from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Dict, Set
import threading
import queue
from datetime import datetime
import socket
import json
import time
import signal
import sys

class ResponseType(Enum):
    READBACK = "READBACK"  # Simple readback of instructions
    ACKNOWLEDGE = "ACKNOWLEDGE"  # Wilco/roger acknowledgment
    READY_REPORT = "READY_REPORT"  # Report when ready
    NO_RESPONSE = "NO_RESPONSE"  # No response expected

@dataclass
class ExpectedResponse:
    type: ResponseType
    requires_readback: bool
    requires_acknowledgment: bool
    requires_ready_report: bool
    action: str  # The action to report ready for

class ATCState(Enum):
    GROUND = "GROUND"
    TOWER = "TOWER"
    DEPARTURE = "DEPARTURE"
    APPROACH = "APPROACH"
    CENTER = "CENTER"
    WAITING = "WAITING"

class AircraftStatus(Enum):
    AT_GATE = "AT_GATE"
    PUSHBACK = "PUSHBACK"
    TAXIING = "TAXIING"
    HOLDING_SHORT = "HOLDING_SHORT"
    LINED_UP = "LINED_UP"
    TAKEOFF = "TAKEOFF"
    CLIMBING = "CLIMBING"
    CRUISING = "CRUISING"
    DESCENDING = "DESCENDING"
    APPROACHING = "APPROACHING"
    LANDING = "LANDING"
    LANDED = "LANDED"

@dataclass
class RadioFrequency:
    name: str
    frequency: str
    description: str

class RadioFrequencies:
    def __init__(self, airport_data: dict):
        # Load frequencies from airport data
        self.frequencies = {
            ATCState.GROUND: RadioFrequency(
                name=airport_data["radio_frequencies"]["ground"]["name"],
                frequency=airport_data["radio_frequencies"]["ground"]["frequency"],
                description=airport_data["radio_frequencies"]["ground"]["description"]
            ),
            ATCState.TOWER: RadioFrequency(
                name=airport_data["radio_frequencies"]["tower"]["name"],
                frequency=airport_data["radio_frequencies"]["tower"]["frequency"],
                description=airport_data["radio_frequencies"]["tower"]["description"]
            ),
            ATCState.DEPARTURE: RadioFrequency(
                name=airport_data["radio_frequencies"]["departure"]["name"],
                frequency=airport_data["radio_frequencies"]["departure"]["frequency"],
                description=airport_data["radio_frequencies"]["departure"]["description"]
            ),
            ATCState.APPROACH: RadioFrequency(
                name=airport_data["radio_frequencies"]["approach"]["name"],
                frequency=airport_data["radio_frequencies"]["approach"]["frequency"],
                description=airport_data["radio_frequencies"]["approach"]["description"]
            ),
            ATCState.CENTER: RadioFrequency(
                name=airport_data["radio_frequencies"]["center"]["name"],
                frequency=airport_data["radio_frequencies"]["center"]["frequency"],
                description=airport_data["radio_frequencies"]["center"]["description"]
            )
        }
    
    def get_frequency(self, state: ATCState) -> RadioFrequency:
        return self.frequencies.get(state)

@dataclass
class ATCTransition:
    from_state: ATCState
    to_state: ATCState
    required_status: Set[AircraftStatus]
    trigger_message: str
    expected_response: str
    next_actions: List[str]
    response_type: ResponseType
    action: str  # The action to report ready for

class ATCMessageSender:
    """Handles sending ATC messages to the radio display"""
    def __init__(self, port: int = 49003):
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.radio_display = None  # Reference to RadioDisplay instance
        
    def set_radio_display(self, radio_display):
        """Set the radio display instance for direct message display"""
        self.radio_display = radio_display
        
    def send_message(self, message: str, state: ATCState, frequency: str):
        """Send a message to the radio display"""
        try:
            # If we have a direct reference to the radio display, use it
            if self.radio_display:
                self.radio_display.display_atc_message(message)
            else:
                # Fall back to UDP for backward compatibility
                data = {
                    'timestamp': time.strftime('%H:%M:%S'),
                    'message': message,
                    'state': state.value,
                    'frequency': frequency
                }
                self.socket.sendto(json.dumps(data).encode('utf-8'), ('127.0.0.1', self.port))
        except Exception as e:
            print(f"Error sending ATC message: {e}")
            
    def close(self):
        """Close the UDP socket"""
        self.socket.close()

class ATCStateManager:
    def __init__(self, airport_manager):
        self.airport_manager = airport_manager
        self.current_state = ATCState.GROUND
        self.aircraft_status = AircraftStatus.AT_GATE
        self.transitions: Dict[str, ATCTransition] = {}
        self.message_queue = queue.Queue()
        self.state_lock = threading.Lock()
        self.callsign = "aabbcc"  # Default callsign
        
        # Initialize message sender
        self.message_sender = ATCMessageSender()
        
        # Load airport data and initialize frequencies
        with open(airport_manager.layout_file, 'r') as f:
            airport_data = json.load(f)
        self.radio_frequencies = RadioFrequencies(airport_data)
        
        self._setup_transitions()
        
    def _setup_transitions(self):
        # Get frequencies for messages
        ground_freq = self.radio_frequencies.get_frequency(ATCState.GROUND).frequency
        tower_freq = self.radio_frequencies.get_frequency(ATCState.TOWER).frequency
        departure_freq = self.radio_frequencies.get_frequency(ATCState.DEPARTURE).frequency
        
        # Get tower name from frequencies
        tower_name = self.radio_frequencies.get_frequency(ATCState.TOWER).name
        
        # Define all possible state transitions with their required conditions
        self.transitions = {
            # Ground Control Phase
            "REQUEST_PUSHBACK": ATCTransition(
                from_state=ATCState.GROUND,
                to_state=ATCState.GROUND,
                required_status={AircraftStatus.AT_GATE},
                trigger_message=f"Ground: {self.callsign}, request pushback",
                expected_response=f"Requesting pushback, {self.callsign}",
                next_actions=[f"Ground: {self.callsign}, pushback approved, face east"],
                response_type=ResponseType.READBACK,
                action="pushback"
            ),
            "PUSHBACK_APPROVED": ATCTransition(
                from_state=ATCState.GROUND,
                to_state=ATCState.GROUND,
                required_status={AircraftStatus.PUSHBACK},
                trigger_message=f"Ground: {self.callsign}, pushback approved, face east",
                expected_response=f"Pushback approved, face east, {self.callsign}",
                next_actions=[f"Ground: {self.callsign}, report when ready to taxi"],
                response_type=ResponseType.READBACK,
                action="pushback"
            ),
            "READY_TO_TAXI": ATCTransition(
                from_state=ATCState.GROUND,
                to_state=ATCState.GROUND,
                required_status={AircraftStatus.PUSHBACK},
                trigger_message=f"Ground: {self.callsign}, report when ready to taxi",
                expected_response=f"Ready to taxi, {self.callsign}",
                next_actions=[f"Ground: {self.callsign}, taxi to Runway 16C via Alpha, Bravo"],
                response_type=ResponseType.READY_REPORT,
                action="taxi"
            ),
            "TAXI_CLEARANCE": ATCTransition(
                from_state=ATCState.GROUND,
                to_state=ATCState.GROUND,
                required_status={AircraftStatus.PUSHBACK, AircraftStatus.TAXIING},
                trigger_message=f"Ground: {self.callsign}, taxi to Runway 16C via Alpha, Bravo",
                expected_response=f"Taxi to Runway 16C via Alpha, Bravo, {self.callsign}",
                next_actions=[f"Ground: {self.callsign}, hold short Runway 16C"],
                response_type=ResponseType.READBACK,
                action="taxi"
            ),
            "HOLD_SHORT": ATCTransition(
                from_state=ATCState.GROUND,
                to_state=ATCState.GROUND,
                required_status={AircraftStatus.TAXIING},
                trigger_message=f"Ground: {self.callsign}, hold short Runway 16C",
                expected_response=f"Hold short Runway 16C, {self.callsign}",
                next_actions=[f"Ground: {self.callsign}, contact {tower_name} {tower_freq}"],
                response_type=ResponseType.READBACK,
                action="hold short"
            ),
            "CROSS_RUNWAY": ATCTransition(
                from_state=ATCState.GROUND,
                to_state=ATCState.GROUND,
                required_status={AircraftStatus.TAXIING},
                trigger_message=f"Ground: {self.callsign}, cross Runway 16C",
                expected_response=f"Cross Runway 16C, {self.callsign}",
                next_actions=[f"Ground: {self.callsign}, continue taxi via Bravo"],
                response_type=ResponseType.READBACK,
                action="cross runway"
            ),
            "CONTINUE_TAXI": ATCTransition(
                from_state=ATCState.GROUND,
                to_state=ATCState.GROUND,
                required_status={AircraftStatus.TAXIING},
                trigger_message=f"Ground: {self.callsign}, continue taxi via Bravo",
                expected_response=f"Continue taxi via Bravo, {self.callsign}",
                next_actions=[f"Ground: {self.callsign}, hold short Runway 16C"],
                response_type=ResponseType.READBACK,
                action="taxi"
            ),
            
            # Ground to Tower Handoff
            "GROUND_TO_TOWER": ATCTransition(
                from_state=ATCState.GROUND,
                to_state=ATCState.TOWER,
                required_status={AircraftStatus.HOLDING_SHORT},
                trigger_message=f"Ground: {self.callsign}, contact {tower_name} {tower_freq}",
                expected_response=f"Contacting {tower_name} {tower_freq}, {self.callsign}",
                next_actions=[f"{tower_name}: {self.callsign}, hold short Runway 16C"],
                response_type=ResponseType.READBACK,
                action="contact tower"
            ),
            
            # Tower Phase
            "TOWER_HOLD_SHORT": ATCTransition(
                from_state=ATCState.TOWER,
                to_state=ATCState.TOWER,
                required_status={AircraftStatus.HOLDING_SHORT},
                trigger_message=f"{tower_name}: {self.callsign}, hold short Runway 16C",
                expected_response=f"Hold short Runway 16C, {self.callsign}",
                next_actions=[f"{tower_name}: {self.callsign}, line up and wait Runway 16C"],
                response_type=ResponseType.READBACK,
                action="hold short"
            ),
            "TOWER_LINE_UP": ATCTransition(
                from_state=ATCState.TOWER,
                to_state=ATCState.TOWER,
                required_status={AircraftStatus.HOLDING_SHORT},
                trigger_message=f"{tower_name}: {self.callsign}, line up and wait Runway 16C",
                expected_response=f"Line up and wait Runway 16C, {self.callsign}",
                next_actions=[f"{tower_name}: {self.callsign}, cleared for takeoff Runway 16C"],
                response_type=ResponseType.READBACK,
                action="line up"
            ),
            "TOWER_TAKEOFF": ATCTransition(
                from_state=ATCState.TOWER,
                to_state=ATCState.TOWER,
                required_status={AircraftStatus.LINED_UP},
                trigger_message=f"{tower_name}: {self.callsign}, cleared for takeoff Runway 16C",
                expected_response=f"Cleared for takeoff Runway 16C, {self.callsign}",
                next_actions=[f"{tower_name}: {self.callsign}, contact Departure {departure_freq}"],
                response_type=ResponseType.READBACK,
                action="takeoff"
            ),
            "TOWER_TO_DEPARTURE": ATCTransition(
                from_state=ATCState.TOWER,
                to_state=ATCState.DEPARTURE,
                required_status={AircraftStatus.TAKEOFF, AircraftStatus.CLIMBING},
                trigger_message=f"{tower_name}: {self.callsign}, contact Departure {departure_freq}",
                expected_response=f"Contacting Departure {departure_freq}, {self.callsign}",
                next_actions=[f"Departure: {self.callsign}, climb and maintain 5,000"],
                response_type=ResponseType.READBACK,
                action="climb"
            ),
        }
    
    def get_expected_response(self) -> Optional[ExpectedResponse]:
        """Get the expected response type for the current state"""
        with self.state_lock:
            # Find applicable transitions
            applicable_transitions = [
                t for t in self.transitions.values()
                if t.from_state == self.current_state and 
                self.aircraft_status in t.required_status
            ]
            
            if not applicable_transitions:
                return None
                
            # For now, just use the first applicable transition
            transition = applicable_transitions[0]
            
            return ExpectedResponse(
                type=transition.response_type,
                requires_readback=transition.response_type == ResponseType.READBACK,
                requires_acknowledgment=transition.response_type == ResponseType.ACKNOWLEDGE,
                requires_ready_report=transition.response_type == ResponseType.READY_REPORT,
                action=transition.action
            )
    
    def get_next_message(self) -> Optional[str]:
        """Get the next message to send based on current state and aircraft status"""
        with self.state_lock:
            # Find applicable transitions
            applicable_transitions = [
                t for t in self.transitions.values()
                if t.from_state == self.current_state and 
                self.aircraft_status in t.required_status
            ]
            
            if not applicable_transitions:
                return None
                
            # For now, just use the first applicable transition
            transition = applicable_transitions[0]
            return transition.trigger_message
    
    def process_response(self, response: str, current_frequency: str = None) -> bool:
        """Process a pilot response and update state if valid"""
        with self.state_lock:
            print("\n=== Processing ATC Response ===")
            print(f"Current ATC State: {self.current_state.value}")
            print(f"Current Aircraft Status: {self.aircraft_status.value}")
            print(f"Current Callsign: {self.callsign}")
            print(f"Received Response: '{response}'")
            if current_frequency:
                print(f"Current Frequency: {current_frequency}")
            
            # Find applicable transitions
            applicable_transitions = [
                t for t in self.transitions.values()
                if t.from_state == self.current_state and 
                self.aircraft_status in t.required_status
            ]
            
            print(f"\nFound {len(applicable_transitions)} applicable transitions:")
            for t in applicable_transitions:
                print(f"- Expected Response: '{t.expected_response}'")
                print(f"  Required Status: {[s.value for s in t.required_status]}")
                print(f"  From State: {t.from_state.value} -> To State: {t.to_state.value}")
                print(f"  Using Callsign: {self.callsign}")
            
            if not applicable_transitions:
                print("\nNo applicable transitions found!")
                return False
                
            # Check if response matches expected
            for transition in applicable_transitions:
                print(f"\nComparing responses:")
                print(f"Received: '{response.strip().lower()}'")
                print(f"Expected: '{transition.expected_response.lower()}'")
                if response.strip().lower() == transition.expected_response.lower():
                    # Check if frequency matches for tower/departure transitions
                    if transition.to_state in [ATCState.TOWER, ATCState.DEPARTURE]:
                        expected_freq = self.radio_frequencies.get_frequency(transition.to_state).frequency
                        if current_frequency and current_frequency != expected_freq:
                            print(f"\nFrequency mismatch! Expected {expected_freq}, got {current_frequency}")
                            return False
                    
                    print(f"\nFound matching transition!")
                    # Update state
                    old_state = self.current_state
                    self.current_state = transition.to_state
                    
                    # Update aircraft status based on the transition
                    old_status = self.aircraft_status
                    if "pushback" in response.lower():
                        self.aircraft_status = AircraftStatus.PUSHBACK
                    elif "taxi" in response.lower():
                        self.aircraft_status = AircraftStatus.TAXIING
                    elif "hold short" in response.lower():
                        self.aircraft_status = AircraftStatus.HOLDING_SHORT
                    
                    print(f"State Change: {old_state.value} -> {self.current_state.value}")
                    print(f"Status Change: {old_status.value} -> {self.aircraft_status.value}")
                    
                    # Send next action message to radio display
                    if transition.next_actions:
                        next_action = transition.next_actions[0]
                        print(f"\nSending next action: '{next_action}'")
                        self.message_sender.send_message(next_action, self.current_state, self.radio_frequencies.get_frequency(self.current_state).frequency)
                        # Clear the message queue to prevent old messages from being sent
                        while not self.message_queue.empty():
                            try:
                                self.message_queue.get_nowait()
                            except queue.Empty:
                                break
                    
                    print("=== Response Processing Complete ===\n")
                    return True
                    
            print("\nNo matching transition found for response!")
            print("=== Response Processing Complete ===\n")
            return False

    def handle_pilot_message(self, message: str, current_frequency: str = None, callsign: str = None) -> None:
        """Handle incoming pilot messages and process them"""
        # Update callsign if provided and not empty
        if callsign and callsign.strip():
            print(f"Updating callsign from '{self.callsign}' to '{callsign}'")
            self.callsign = callsign.strip()
            # Rebuild transitions with new callsign
            self._setup_transitions()
            
        # Process the message and update state if needed
        if self.process_response(message, current_frequency):
            print(f"Successfully processed pilot message: {message}")
        else:
            print(f"Could not process pilot message: {message}")
            # Send a standby message if we can't process the message
            self.message_sender.send_message(f"{self.callsign}, standby", self.current_state, self.radio_frequencies.get_frequency(self.current_state).frequency)

    def update_aircraft_status(self, new_status: AircraftStatus):
        """Update the aircraft's current status"""
        with self.state_lock:
            self.aircraft_status = new_status
    
    def get_current_frequency(self) -> RadioFrequency:
        """Get the current radio frequency"""
        return self.radio_frequencies.get_frequency(self.current_state)

    def __del__(self):
        """Cleanup when the object is destroyed"""
        if hasattr(self, 'message_sender'):
            self.message_sender.close()

class ATCController:
    def __init__(self, airport_manager):
        self.state_manager = ATCStateManager(airport_manager)
        self.message_queue = queue.Queue()
        self.running = False
        self.controller_thread = None
        
        # Initialize UDP socket for receiving pilot messages
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('127.0.0.1', 49004))  # Port for receiving pilot messages
        self.socket.settimeout(0.1)  # Non-blocking socket with 100ms timeout
    
    def start(self):
        """Start the ATC controller thread"""
        self.running = True
        self.controller_thread = threading.Thread(target=self._controller_loop)
        self.controller_thread.start()
    
    def stop(self):
        """Stop the ATC controller thread"""
        self.running = False
        if self.controller_thread:
            self.controller_thread.join()
        self.socket.close()
    
    def _controller_loop(self):
        """Main controller loop that processes messages and updates state"""
        while self.running:
            try:
                # Check for next message to send
                next_message = self.state_manager.get_next_message()
                if next_message:
                    self.message_queue.put(next_message)
                
                # Check for incoming pilot messages
                try:
                    data, addr = self.socket.recvfrom(1024)
                    message_data = json.loads(data.decode('utf-8'))
                    
                    # Process the pilot message
                    self.state_manager.handle_pilot_message(
                        message_data['message'],
                        message_data.get('frequency'),
                        message_data.get('callsign')
                    )
                    
                except socket.timeout:
                    continue
                except json.JSONDecodeError:
                    print("Error decoding pilot message")
                    continue
                    
            except Exception as e:
                print(f"Error in controller loop: {e}")

# Example usage
if __name__ == "__main__":
    def signal_handler(sig, frame):
        print("\nShutting down ATC controller...")
        atc_controller.stop()
        sys.exit(0)
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize
        from airport_manager import AirportManager
        airport_manager = AirportManager("./airport_data/lowg_airport.json")
        atc_controller = ATCController(airport_manager)

        # Start the controller
        print("Starting ATC controller...")
        atc_controller.start()
        
        # Print initial state
        print(f"Initial state: {atc_controller.state_manager.current_state}")
        print(f"Initial status: {atc_controller.state_manager.aircraft_status}")
        print(f"Initial frequency: {atc_controller.state_manager.get_current_frequency().frequency} MHz")
        print("\nATC controller is running. Press Ctrl+C to stop.")
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down ATC controller...")
        atc_controller.stop()
    except Exception as e:
        print(f"Error: {e}")
        if 'atc_controller' in locals():
            atc_controller.stop()
        sys.exit(1) 