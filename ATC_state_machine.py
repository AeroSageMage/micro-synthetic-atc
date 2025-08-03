from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Dict, Set

class ATCState(Enum):
    """Represents the different ATC positions/states"""
    GROUND = "GROUND"
    TOWER = "TOWER"
    DEPARTURE = "DEPARTURE"
    APPROACH = "APPROACH"
    CENTER = "CENTER"

class AircraftStatus(Enum):
    """Represents the different states an aircraft can be in"""
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
class ATCTransition:
    """Represents a possible state transition in the ATC system"""
    from_state: ATCState
    to_state: ATCState
    required_status: Set[AircraftStatus]
    trigger_message: str
    expected_response: str
    next_actions: List[str]

class ATCStateMachine:
    """A simplified state machine for handling ATC communications"""
    
    def __init__(self, callsign: str = "TEST123"):
        self.callsign = callsign
        self.current_state = ATCState.GROUND
        self.aircraft_status = AircraftStatus.AT_GATE
        self.transitions: Dict[str, ATCTransition] = {}
        self._setup_transitions()
    
    def _setup_transitions(self):
        """Set up all possible state transitions"""
        self.transitions = {
            # Ground Control Phase
            "REQUEST_PUSHBACK": ATCTransition(
                from_state=ATCState.GROUND,
                to_state=ATCState.GROUND,
                required_status={AircraftStatus.AT_GATE},
                trigger_message=f"Ground: {self.callsign}, request pushback",
                expected_response=f"Requesting pushback, {self.callsign}",
                next_actions=[f"Ground: {self.callsign}, pushback approved, face east"]
            ),
            "PUSHBACK_APPROVED": ATCTransition(
                from_state=ATCState.GROUND,
                to_state=ATCState.GROUND,
                required_status={AircraftStatus.PUSHBACK},
                trigger_message=f"Ground: {self.callsign}, pushback approved, face east",
                expected_response=f"Pushback approved, face east, {self.callsign}",
                next_actions=[f"Ground: {self.callsign}, report when ready to taxi"]
            ),
            "READY_TO_TAXI": ATCTransition(
                from_state=ATCState.GROUND,
                to_state=ATCState.GROUND,
                required_status={AircraftStatus.PUSHBACK},
                trigger_message=f"Ground: {self.callsign}, report when ready to taxi",
                expected_response=f"Ready to taxi, {self.callsign}",
                next_actions=[f"Ground: {self.callsign}, taxi to Runway 16C via Alpha, Bravo"]
            ),
            "TAXI_CLEARANCE": ATCTransition(
                from_state=ATCState.GROUND,
                to_state=ATCState.GROUND,
                required_status={AircraftStatus.PUSHBACK, AircraftStatus.TAXIING},
                trigger_message=f"Ground: {self.callsign}, taxi to Runway 16C via Alpha, Bravo",
                expected_response=f"Taxi to Runway 16C via Alpha, Bravo, {self.callsign}",
                next_actions=[f"Ground: {self.callsign}, hold short Runway 16C"]
            ),
            "HOLD_SHORT": ATCTransition(
                from_state=ATCState.GROUND,
                to_state=ATCState.GROUND,
                required_status={AircraftStatus.TAXIING},
                trigger_message=f"Ground: {self.callsign}, hold short Runway 16C",
                expected_response=f"Hold short Runway 16C, {self.callsign}",
                next_actions=[f"Ground: {self.callsign}, contact Tower 118.1"]
            ),
            
            # Ground to Tower Handoff
            "GROUND_TO_TOWER": ATCTransition(
                from_state=ATCState.GROUND,
                to_state=ATCState.TOWER,
                required_status={AircraftStatus.HOLDING_SHORT},
                trigger_message=f"Ground: {self.callsign}, contact Tower 118.1",
                expected_response=f"Contacting Tower 118.1, {self.callsign}",
                next_actions=[f"Tower: {self.callsign}, hold short Runway 16C"]
            ),
            
            # Tower Phase
            "TOWER_HOLD_SHORT": ATCTransition(
                from_state=ATCState.TOWER,
                to_state=ATCState.TOWER,
                required_status={AircraftStatus.HOLDING_SHORT},
                trigger_message=f"Tower: {self.callsign}, hold short Runway 16C",
                expected_response=f"Hold short Runway 16C, {self.callsign}",
                next_actions=[f"Tower: {self.callsign}, line up and wait Runway 16C"]
            ),
            "TOWER_LINE_UP": ATCTransition(
                from_state=ATCState.TOWER,
                to_state=ATCState.TOWER,
                required_status={AircraftStatus.HOLDING_SHORT},
                trigger_message=f"Tower: {self.callsign}, line up and wait Runway 16C",
                expected_response=f"Line up and wait Runway 16C, {self.callsign}",
                next_actions=[f"Tower: {self.callsign}, cleared for takeoff Runway 16C"]
            ),
            "TOWER_TAKEOFF": ATCTransition(
                from_state=ATCState.TOWER,
                to_state=ATCState.TOWER,
                required_status={AircraftStatus.LINED_UP},
                trigger_message=f"Tower: {self.callsign}, cleared for takeoff Runway 16C",
                expected_response=f"Cleared for takeoff Runway 16C, {self.callsign}",
                next_actions=[f"Tower: {self.callsign}, contact Departure 119.1"]
            ),
            "TOWER_TO_DEPARTURE": ATCTransition(
                from_state=ATCState.TOWER,
                to_state=ATCState.DEPARTURE,
                required_status={AircraftStatus.TAKEOFF, AircraftStatus.CLIMBING},
                trigger_message=f"Tower: {self.callsign}, contact Departure 119.1",
                expected_response=f"Contacting Departure 119.1, {self.callsign}",
                next_actions=[f"Departure: {self.callsign}, climb and maintain 5,000"]
            ),
        }
    
    def get_next_message(self) -> Optional[str]:
        """Get the next message to send based on current state and aircraft status"""
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
    
    def process_response(self, response: str) -> bool:
        """Process a pilot response and update state if valid"""
        print(f"\nProcessing response: '{response}'")
        print(f"Current state: {self.current_state.value}")
        print(f"Current status: {self.aircraft_status.value}")
        
        # Find applicable transitions
        applicable_transitions = [
            t for t in self.transitions.values()
            if t.from_state == self.current_state and 
            self.aircraft_status in t.required_status
        ]
        
        if not applicable_transitions:
            print("No applicable transitions found!")
            return False
            
        # Check if response matches expected
        for transition in applicable_transitions:
            if response.strip().lower() == transition.expected_response.lower():
                # Update state
                self.current_state = transition.to_state
                
                # Update aircraft status based on the response
                if "pushback" in response.lower():
                    self.aircraft_status = AircraftStatus.PUSHBACK
                elif "taxi" in response.lower():
                    self.aircraft_status = AircraftStatus.TAXIING
                elif "hold short" in response.lower():
                    self.aircraft_status = AircraftStatus.HOLDING_SHORT
                elif "line up" in response.lower():
                    self.aircraft_status = AircraftStatus.LINED_UP
                elif "takeoff" in response.lower():
                    self.aircraft_status = AircraftStatus.TAKEOFF
                elif "climb" in response.lower():
                    self.aircraft_status = AircraftStatus.CLIMBING
                
                print(f"State updated to: {self.current_state.value}")
                print(f"Status updated to: {self.aircraft_status.value}")
                return True
                
        print("No matching transition found for response!")
        return False
    
    def update_aircraft_status(self, new_status: AircraftStatus):
        """Update the aircraft's current status"""
        self.aircraft_status = new_status
        print(f"Aircraft status updated to: {new_status.value}")

# Example usage
if __name__ == "__main__":
    # Create a new state machine
    atc = ATCStateMachine(callsign="TEST123")
    
    # Example sequence of interactions
    print("\n=== Starting ATC Sequence ===")
    
    # Initial state
    print(f"\nInitial state: {atc.current_state.value}")
    print(f"Initial status: {atc.aircraft_status.value}")
    
    # Get first message
    first_message = atc.get_next_message()
    print(f"\nFirst message to send: {first_message}")
    
    # Process a response
    response = "Requesting pushback, TEST123"
    print(f"\nProcessing response: {response}")
    atc.process_response(response)
    
    # Get next message
    next_message = atc.get_next_message()
    print(f"\nNext message to send: {next_message}")
    
    print("\n=== ATC Sequence Complete ===") 