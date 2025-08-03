from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Dict, Set, Tuple
import threading
import queue
from datetime import datetime
import socket
import json
import time
import signal
import sys
from shared_enums import AircraftArea
from utils.geo_utils import calculate_heading

@dataclass
class AircraftInfo:
    """Class to store aircraft information"""
    callsign: str
    type: str  # ICAO code
    name: str  # Full name
    cruise_speed: int  # in knots
    approach_speed: int  # in knots
    cruise_altitude: int  # in feet
    max_range: int  # in nautical miles
    tags: List[str]
    has_radio_nav: bool = True
    runway_takeoff: Optional[int] = None
    runway_landing: Optional[int] = None

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
        print(f"=== Sending ATC Message ===")
        print(f"Message: {message}")
        print(f"State: {state.value}")
        print(f"Frequency: {frequency}")
        print(f"Radio display set: {self.radio_display is not None}")
        
        try:
            # If we have a direct reference to the radio display, use it
            if self.radio_display:
                print("Using direct radio display reference")
                self.radio_display.display_atc_message(message)
                print("Message sent to radio display")
            else:
                print("Using UDP fallback")
                # Fall back to UDP for backward compatibility
                data = {
                    'timestamp': time.strftime('%H:%M:%S'),
                    'message': message,
                    'state': state.value,
                    'frequency': frequency
                }
                self.socket.sendto(json.dumps(data).encode('utf-8'), ('127.0.0.1', self.port))
                print("Message sent via UDP")
        except Exception as e:
            print(f"Error sending ATC message: {e}")
            import traceback
            traceback.print_exc()
            
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
        
        # Initialize aircraft info
        self.aircraft_info = None
        self.current_position = None  # (lat, lon)
        self.current_heading = None
        
        # Initialize message sender
        self.message_sender = ATCMessageSender()
        
        # Initialize position detector reference
        self.position_detector = None
        
        # Load airport data and initialize frequencies
        with open(airport_manager.layout_file, 'r') as f:
            airport_data = json.load(f)
        self.radio_frequencies = RadioFrequencies(airport_data)
        
        self._setup_transitions()
        
    def set_position_detector(self, position_detector):
        """Set the position detector instance"""
        self.position_detector = position_detector

    def update_position(self, position: Tuple[float, float], heading: float):
        """Update the current aircraft position and heading"""
        # Quick update of position data with minimal lock time
        print(f"[LOCK] update_position requesting state_lock...")
        with self.state_lock:
            print(f"[LOCK] update_position acquired state_lock")
            print(f"\n=== Position Update ===")
            print(f"New position: {position[0]:.6f}, {position[1]:.6f}")
            print(f"New heading: {heading:.1f}°")
            print(f"Previous position: {self.current_position}")
            
            # Check if this is the first position update
            first_position = self.current_position is None
            
            self.current_position = position
            self.current_heading = heading
            
            # Quick status update based on position detector
            if self.position_detector:
                info = self.position_detector.detect_position(position, heading)
                print(f"Position detector result: {info.area.value}")
                
                if info.area == AircraftArea.AT_PARKING:
                    self.aircraft_status = AircraftStatus.AT_GATE
                    print(f"Status updated to: {self.aircraft_status.value}")
                elif info.area == AircraftArea.ON_TAXIWAY:
                    self.aircraft_status = AircraftStatus.TAXIING
                    print(f"Status updated to: {self.aircraft_status.value}")
                elif info.area == AircraftArea.AT_HOLDING_POINT:
                    self.aircraft_status = AircraftStatus.HOLDING_SHORT
                    print(f"Status updated to: {self.aircraft_status.value}")
                elif info.area == AircraftArea.ON_RUNWAY:
                    if self.aircraft_status == AircraftStatus.HOLDING_SHORT:
                        self.aircraft_status = AircraftStatus.LINED_UP
                        print(f"Status updated to: {self.aircraft_status.value}")
                    elif self.aircraft_status == AircraftStatus.LINED_UP:
                        self.aircraft_status = AircraftStatus.TAKEOFF
                        print(f"Status updated to: {self.aircraft_status.value}")
                elif info.area == AircraftArea.IN_FLIGHT:
                    if self.aircraft_status == AircraftStatus.TAKEOFF:
                        self.aircraft_status = AircraftStatus.CLIMBING
                        print(f"Status updated to: {self.aircraft_status.value}")
                    elif self.aircraft_status == AircraftStatus.CLIMBING:
                        self.aircraft_status = AircraftStatus.CRUISING
                        print(f"Status updated to: {self.aircraft_status.value}")
            
            print(f"=== Position Update Complete ===\n")
            print(f"[LOCK] update_position releasing state_lock")
        
        # Do expensive operations outside the lock
        if first_position and position is not None:
            # Run transition setup in background to avoid blocking
            import threading
            def setup_transitions_background():
                try:
                    self.update_transitions_for_callsign()
                except Exception as e:
                    print(f"Error setting up transitions in background: {e}")
            
            transition_thread = threading.Thread(target=setup_transitions_background)
            transition_thread.daemon = True
            transition_thread.start()

    def _get_pushback_direction(self) -> str:
        """Get the pushback direction based on current position and nearest taxiway"""
        if not self.current_position:
            return "east"  # Default if no position available
            
        # Find nearest taxiway
        nearest_taxiway = self.airport_manager.get_nearest_taxiway(self.current_position)
        if not nearest_taxiway:
            return "east"  # Default if no taxiway found
            
        # Get the first segment of the taxiway
        first_segment = nearest_taxiway.segments[0]
        
        # Calculate heading to taxiway
        taxiway_heading = calculate_heading(
            self.current_position[0], self.current_position[1],
            first_segment.start[0], first_segment.start[1]
        )
        
        # Convert heading to cardinal direction
        if 45 <= taxiway_heading < 135:
            return "east"
        elif 135 <= taxiway_heading < 225:
            return "south"
        elif 225 <= taxiway_heading < 315:
            return "west"
        else:
            return "north"

    def _get_taxi_route_to_runway(self, runway_name: str) -> str:
        """Get the taxi route to a specific runway"""
        # Throttle calculations to prevent GUI freezing
        current_time = time.time()
        if hasattr(self, '_last_taxi_calc') and current_time - self._last_taxi_calc < 1.0:
            # Return cached result if called too frequently
            return getattr(self, '_cached_taxi_route', "via Alpha, Bravo")
        
        self._last_taxi_calc = current_time
        
        print(f"\nCalculating taxi route to {runway_name}")
        print(f"Current position: {self.current_position}")
        
        if not self.current_position:
            print("No current position available, using default route")
            self._cached_taxi_route = "via Alpha, Bravo"
            return self._cached_taxi_route  # Default if no position available
            
        # Find the runway
        target_runway = next((r for r in self.airport_manager.runways if r.name == runway_name), None)
        if not target_runway:
            print(f"Runway {runway_name} not found in airport layout")
            print(f"Available runways: {[r.name for r in self.airport_manager.runways]}")
            self._cached_taxi_route = "via Alpha, Bravo"
            return self._cached_taxi_route  # Default if runway not found
            
        print(f"Found runway {runway_name} at threshold: {target_runway.threshold1_coords}")
        
        # Use runway threshold as destination
        destination = target_runway.threshold1_coords
        
        # Get taxi route
        route = self.airport_manager.get_taxi_route(self.current_position, destination)
        if not route:
            print("No taxi route found, using default route")
            print(f"Available taxiways: {[t.name for t in self.airport_manager.taxiways]}")
            self._cached_taxi_route = "via Alpha, Bravo"
            return self._cached_taxi_route  # Default if no route found
            
        print(f"Calculated route: {route}")
        
        # Format route as "via A, B, C" with hold short instructions
        formatted_parts = []
        for item in route:
            if item.startswith("HOLD_SHORT_"):
                # Extract runway name from HOLD_SHORT_16C format
                runway_name = item.replace("HOLD_SHORT_", "")
                formatted_parts.append(f"hold short {runway_name}")
            else:
                formatted_parts.append(item)
        
        self._cached_taxi_route = "via " + ", ".join(formatted_parts)
        return self._cached_taxi_route

    def _setup_transitions(self):
        # Throttle transition setup to prevent excessive calls
        current_time = time.time()
        if hasattr(self, '_last_transition_setup') and current_time - self._last_transition_setup < 2.0:
            print("Transition setup throttled - skipping")
            return
        
        self._last_transition_setup = current_time
        
        print("Starting transition setup...")
        print(f"Current callsign: {self.callsign}")
        
        # Get frequencies for messages
        ground_freq = self.radio_frequencies.get_frequency(ATCState.GROUND).frequency
        tower_freq = self.radio_frequencies.get_frequency(ATCState.TOWER).frequency
        departure_freq = self.radio_frequencies.get_frequency(ATCState.DEPARTURE).frequency
        
        # Get tower name from frequencies
        tower_name = self.radio_frequencies.get_frequency(ATCState.TOWER).name
        
        print("Setting up ground control transitions...")
        # Define all possible state transitions with their required conditions
        # Use dynamic message generation instead of pre-calculated routes
        self.transitions = {
            # Ground Control Phase
            "REQUEST_PUSHBACK": ATCTransition(
                from_state=ATCState.GROUND,
                to_state=ATCState.GROUND,
                required_status={AircraftStatus.AT_GATE},
                trigger_message=f"Ground: {self.callsign}, request pushback",
                expected_response=f"Requesting pushback, {self.callsign}",
                next_actions=[f"Ground: {self.callsign}, pushback approved, face [DIRECTION]"],  # Dynamic direction
                response_type=ResponseType.READBACK,
                action="pushback"
            ),
            "PUSHBACK_APPROVED": ATCTransition(
                from_state=ATCState.GROUND,
                to_state=ATCState.GROUND,
                required_status={AircraftStatus.PUSHBACK},
                trigger_message=f"Ground: {self.callsign}, pushback approved, face [DIRECTION]",  # Dynamic direction
                expected_response=f"Pushback approved, face [DIRECTION], {self.callsign}",
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
                next_actions=[f"Ground: {self.callsign}, taxi to Runway 16C [ROUTE]"],  # Dynamic route
                response_type=ResponseType.READY_REPORT,
                action="taxi"
            ),
            "TAXI_CLEARANCE": ATCTransition(
                from_state=ATCState.GROUND,
                to_state=ATCState.GROUND,
                required_status={AircraftStatus.PUSHBACK, AircraftStatus.TAXIING},
                trigger_message=f"Ground: {self.callsign}, taxi to Runway 16C [ROUTE]",  # Dynamic route
                expected_response=f"Taxi to Runway 16C [ROUTE], {self.callsign}",
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
        print(f"Transition setup complete. Created {len(self.transitions)} transitions.")

    def _get_dynamic_message(self, transition_key: str) -> str:
        """Get a dynamic message with real calculations only when needed"""
        if not hasattr(self, 'transitions') or transition_key not in self.transitions:
            return ""
            
        transition = self.transitions[transition_key]
        message = transition.trigger_message
        
        # Only do expensive calculations when actually needed
        if "[DIRECTION]" in message and self.current_position:
            direction = self._get_pushback_direction()
            message = message.replace("[DIRECTION]", direction)
        elif "[ROUTE]" in message and self.current_position:
            # Only calculate route when user actually requests taxi
            route = self._get_taxi_route_to_runway('16C')
            message = message.replace("[ROUTE]", route)
        elif "[ROUTE]" in message:
            # Use default if no position available
            message = message.replace("[ROUTE]", "via Alpha, Bravo")
        elif "[DIRECTION]" in message:
            # Use default if no position available
            message = message.replace("[DIRECTION]", "east")
            
        return message

    def set_aircraft(self, aircraft_info: AircraftInfo):
        """Set the current aircraft information (like filing a flight plan)"""
        print(f"Setting aircraft: {aircraft_info.callsign} ({aircraft_info.type})")
        
        # Simple assignment - no lock needed for this one-time operation
        self.aircraft_info = aircraft_info
        self.callsign = aircraft_info.callsign
        print(f"Aircraft data updated: {self.callsign} ({aircraft_info.type})")
        print("Flight plan filed - transitions will be updated when position data is available")
        print("set_aircraft() completed")

    def update_transitions_for_callsign(self):
        """Update transitions with current callsign - called when position data becomes available"""
        if not self.callsign:
            return
            
        print(f"Updating transitions for callsign: {self.callsign}")
        import time
        start_time = time.time()
        
        # Don't acquire state_lock here since it's already held by the caller
        # Rebuild transitions with current callsign
        self._setup_transitions()
        elapsed = time.time() - start_time
        print(f"Transitions updated successfully in {elapsed:.2f} seconds")

    def get_controller_name(self, state: ATCState) -> str:
        """Get the controller name for the current state from airport data"""
        try:
            # Get the frequency info for this state
            freq_info = self.radio_frequencies.get_frequency(state)
            if freq_info and hasattr(freq_info, 'name'):
                return freq_info.name
            else:
                # Fallback to state name if no specific name found
                return state.value.title()
        except Exception as e:
            print(f"Error getting controller name: {e}")
            return state.value.title()

    def get_aircraft_info(self) -> Optional[AircraftInfo]:
        """Get the current aircraft information"""
        return self.aircraft_info

    def get_expected_response(self) -> Optional[ExpectedResponse]:
        """Get the expected response type for the current state"""
        # No lock needed for UI updates - just read current state
        print("Getting expected response for UI (no lock needed)")
        
        # Find applicable transitions
        applicable_transitions = [
            t for t in self.transitions.values()
            if t.from_state == self.current_state and 
            self.aircraft_status in t.required_status
        ]
        
        if not applicable_transitions:
            print("No applicable transitions found for UI")
            return None
            
        # For now, just use the first applicable transition
        transition = applicable_transitions[0]
        
        # Only do expensive calculations if we actually need them
        # For UI updates, we can use a simplified version
        expected_response = transition.expected_response
        
        # Replace placeholders with defaults for UI purposes
        if "[DIRECTION]" in expected_response:
            expected_response = expected_response.replace("[DIRECTION]", "east")
        elif "[ROUTE]" in expected_response:
            expected_response = expected_response.replace("[ROUTE]", "PATHFINDING_ERROR")
        
        result = ExpectedResponse(
            type=transition.response_type,
            requires_readback=transition.response_type == ResponseType.READBACK,
            requires_acknowledgment=transition.response_type == ResponseType.ACKNOWLEDGE,
            requires_ready_report=transition.response_type == ResponseType.READY_REPORT,
            action=transition.action
        )
        print("Expected response for UI calculated")
        return result

    def get_actual_expected_response(self) -> Optional[str]:
        """Get the actual expected response with real calculations - only call when needed"""
        # Don't acquire state_lock here since it's already held by the caller
        print("Getting actual expected response (lock already held by caller)")
        
        # Find applicable transitions
        applicable_transitions = [
            t for t in self.transitions.values()
            if t.from_state == self.current_state and 
            self.aircraft_status in t.required_status
        ]
        
        if not applicable_transitions:
            print("No applicable transitions found")
            return None
            
        # For now, just use the first applicable transition
        transition = applicable_transitions[0]
        
        # Get dynamic expected response with real calculations
        expected_response = transition.expected_response
        print(f"Base expected response: {expected_response}")
        
        if "[DIRECTION]" in expected_response and self.current_position:
            print("Calculating real direction...")
            direction = self._get_pushback_direction()
            expected_response = expected_response.replace("[DIRECTION]", direction)
            print(f"Replaced [DIRECTION] with {direction}")
        elif "[DIRECTION]" in expected_response:
            expected_response = expected_response.replace("[DIRECTION]", "east")
            print("Replaced [DIRECTION] with east (default)")
        elif "[ROUTE]" in expected_response and self.current_position:
            print("Calculating real route...")
            route = self._get_taxi_route_to_runway('16C')
            expected_response = expected_response.replace("[ROUTE]", route)
            print(f"Replaced [ROUTE] with {route}")
        elif "[ROUTE]" in expected_response:
            expected_response = expected_response.replace("[ROUTE]", "via Alpha, Bravo")
            print("Replaced [ROUTE] with via Alpha, Bravo (default)")
        
        print(f"Final expected response: {expected_response}")
        return expected_response
    
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
            
            # Get the key for this transition
            transition_key = next(k for k, v in self.transitions.items() if v == transition)
            
            # Return dynamic message with real calculations
            return self._get_dynamic_message(transition_key)
    
    def process_response(self, response: str, current_frequency: str = None) -> bool:
        """Process a pilot response and update state if valid"""
        print(f"\n=== Processing Pilot Response ===")
        print(f"Response: '{response}'")
        print(f"Current State: {self.current_state.value}")
        print(f"Current Status: {self.aircraft_status.value}")
        print(f"Current Callsign: {self.callsign}")
        
        # Use current callsign directly for response matching
        current_callsign = self.callsign
        
        # Define expected responses based on current state and status
        if self.current_state == ATCState.GROUND and self.aircraft_status == AircraftStatus.AT_GATE:
            controller_name = self.get_controller_name(self.current_state)
            expected_response = f"{controller_name}, requesting pushback, {current_callsign}"
            if response.strip().lower() == expected_response.lower():
                print("MATCH FOUND! Processing pushback request...")
                
                # Update state
                self.current_state = ATCState.GROUND  # Stay in GROUND
                self.aircraft_status = AircraftStatus.PUSHBACK
                
                print(f"Status: AT_GATE -> PUSHBACK")
                
                # Send next ATC message
                next_message = f"{current_callsign}, pushback approved, face east"
                print(f"Sending ATC message: '{next_message}'")
                self.message_sender.send_message(
                    next_message, 
                    self.current_state, 
                    self.radio_frequencies.get_frequency(self.current_state).frequency
                )
                
                print("=== Response Processing Complete ===")
                return True
        
        # Handle readback after pushback approval
        elif self.current_state == ATCState.GROUND and self.aircraft_status == AircraftStatus.PUSHBACK:
            # Check for readback of pushback approval
            expected_readback = f"Pushback approved, face east, {current_callsign}"
            if response.strip().lower() == expected_readback.lower():
                print("MATCH FOUND! Processing pushback readback...")
                
                # Update state - pilot can now start pushback
                self.aircraft_status = AircraftStatus.TAXIING
                
                print(f"Status: PUSHBACK -> TAXIING")
                
                # Send acknowledgment
                ack_message = f"Roger, {current_callsign}. Contact ground when ready for taxi."
                print(f"Sending ATC message: '{ack_message}'")
                self.message_sender.send_message(
                    ack_message, 
                    self.current_state, 
                    self.radio_frequencies.get_frequency(self.current_state).frequency
                )
                
                print("=== Response Processing Complete ===")
                return True
        
        # Handle taxi-related responses
        elif self.current_state == ATCState.GROUND and self.aircraft_status == AircraftStatus.TAXIING:
            # Check for acknowledgment of the taxi instruction
            expected_ack = f"Contact ground when ready for taxi, {current_callsign}"
            if response.strip().lower() == expected_ack.lower():
                print("MATCH FOUND! Processing taxi acknowledgment...")
                
                # Send acknowledgment and frequency change
                ack_message = f"Roger, {current_callsign}. Contact ground on 121.700 when ready."
                print(f"Sending ATC message: '{ack_message}'")
                self.message_sender.send_message(
                    ack_message, 
                    self.current_state, 
                    self.radio_frequencies.get_frequency(self.current_state).frequency
                )
                
                print("=== Response Processing Complete ===")
                return True
            
            # Check for "ready for taxi" request
            expected_taxi_request = f"Ground, ready for taxi, {current_callsign}"
            if response.strip().lower() == expected_taxi_request.lower():
                print("MATCH FOUND! Processing taxi request...")
                
                # Send taxi clearance
                # Get the active runway or default to first available
                active_runway = self.airport_manager.get_active_runway(0)  # 0 = no wind data
                if not active_runway and self.airport_manager.runways:
                    active_runway = self.airport_manager.runways[0]  # Use first runway as fallback
                
                if active_runway:
                    route = self._get_taxi_route_to_runway(active_runway.name)
                    taxi_message = f"{current_callsign}, taxi to Runway {active_runway.name} {route}"
                else:
                    taxi_message = f"{current_callsign}, taxi to runway PATHFINDING_ERROR"
                
                print(f"Sending ATC message: '{taxi_message}'")
                self.message_sender.send_message(
                    taxi_message, 
                    self.current_state, 
                    self.radio_frequencies.get_frequency(self.current_state).frequency
                )
                
                print("=== Response Processing Complete ===")
                return True
        
        print("No matching transition found")
        print("=== Response Processing Complete ===")
        return False

    def handle_pilot_message(self, message: str, current_frequency: str = None, callsign: str = None) -> None:
        """Handle incoming pilot messages and process them"""
        print(f"=== Handling Pilot Message ===")
        print(f"Message: {message}")
        print(f"Callsign: {callsign}")
        print(f"Frequency: {current_frequency}")
        
        # Update callsign if provided and not empty
        if callsign and callsign.strip() and callsign.strip() != self.callsign:
            print(f"Updating callsign from '{self.callsign}' to '{callsign}'")
            self.callsign = callsign.strip()
            # Force transition update when callsign changes (bypass throttling)
            print("Forcing transition update for new callsign...")
            self._last_transition_setup = 0  # Reset throttle
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
    
    def get_actual_pushback_direction(self) -> str:
        """Get the actual pushback direction with real calculations - only call when pilot starts pushback"""
        if not self.current_position:
            return "east"  # Default if no position available
            
        print("Calculating real pushback direction...")
        direction = self._get_pushback_direction()
        print(f"Real pushback direction: {direction}")
        return direction

    def get_current_frequency(self) -> RadioFrequency:
        """Get the current frequency for the current state"""
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