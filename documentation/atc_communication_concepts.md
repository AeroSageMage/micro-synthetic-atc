# ATC Communication and State Management Concepts

## Cross-Reference Guide

| Concept | ATC Communication Concepts | ATC Communication Patterns | Implementation Notes |
|---------|---------------------------|---------------------------|---------------------|
| **State Management** | State machine, transitions, waiting points | Pilot procedures for state changes | UI for state awareness |
| **Frequency Changes** | Handoff procedures, frequency protocols | Pilot frequency management, readbacks | Radio frequency UI |
| **Transponder Operations** | State-based transponder requirements | Detailed transponder procedures | Transponder panel UI |
| **Communication Structure** | ATC hierarchy and responsibilities | Standard message formats, acknowledgments | Message display system |
| **Emergency Procedures** | Emergency state handling | Emergency communication protocols | Emergency UI indicators |
| **TCAS Integration** | TCAS state requirements | TCAS operation procedures | TCAS display integration |
| **Pilot Procedures** | State transition requirements | Detailed pilot checklists | Pilot interface design |
| **Clearance Types** | State-specific clearances | Clearance communication patterns | Clearance display format |
| **Position Reporting** | State-based reporting requirements | Position report formats | Position tracking system |
| **Error Handling** | State transition rules | Error communication procedures | Error notification system |

**Document Relationships:**
- **ATC Communication Concepts**: Defines the theoretical framework and state management
- **ATC Communication Patterns**: Provides practical implementation details
- **Implementation**: Focuses on technical realization and UI design

**Usage Guide:**
1. Start with Concepts for understanding the system structure
2. Use Patterns for specific communication procedures
3. Refer to Implementation for technical details

## 1. ATC Hierarchy and Control Responsibilities

**ATC Control Hierarchy:**
1. **Ground Control**
   - Controls all movements on the ramp/apron
   - Manages pushback and taxiway movements
   - Handles gate assignments and ground vehicle movements
   - Frequency typically ends with "Ground" (e.g., "Boston Ground")

2. **Tower Control**
   - Controls all runway operations
   - Manages takeoffs and landings
   - Controls aircraft in the immediate airport vicinity
   - Frequency typically ends with "Tower" (e.g., "Boston Tower")

3. **Departure Control**
   - Manages aircraft after takeoff
   - Provides initial climb instructions
   - Handles aircraft until they reach cruising altitude
   - Frequency typically includes "Departure" (e.g., "Boston Departure")

4. **Approach Control**
   - Manages arriving aircraft
   - Provides descent and approach vectors
   - Coordinates with Tower for landing sequence
   - Frequency typically includes "Approach" (e.g., "Boston Approach")

## 2. ATC State Machine Concept

**State Machine Representation:**
```
[Ground] → [Tower] → [Departure] → [Center]
    ↓          ↓          ↓           ↓
[Wait]     [Wait]     [Wait]      [Wait]
```

**State Transitions and Waiting Points:**

1. **Ground → Tower Transition**
   - Wait Point: Holding short of runway
   - Trigger: Clearance to enter runway
   - Example: "Delta 123, hold short Runway 22L" → "Delta 123, line up and wait Runway 22L"

2. **Tower → Departure Transition**
   - Wait Point: Initial climb altitude
   - Trigger: Reaching specified altitude/point
   - Example: "Delta 123, climb and maintain 5,000" → "Delta 123, contact Departure 125.8"

3. **Departure → Center Transition**
   - Wait Point: Airspace boundary
   - Trigger: Reaching enroute altitude/airspace boundary
   - Example: "Delta 123, climb and maintain 10,000" → "Delta 123, contact Center 132.55"

**Waiting State Characteristics:**
1. **Ground Wait States**
   - At gate (waiting for pushback)
   - At taxiway intersection
   - Holding short of runway
   - At runway entry point

2. **Tower Wait States**
   - Line up and wait
   - In traffic pattern
   - Holding for landing clearance
   - After landing, waiting for taxi clearance

3. **Departure Wait States**
   - At initial climb altitude
   - At vector points
   - At airspace boundary
   - During altitude restrictions

4. **Center Wait States**
   - At cruise altitude
   - At waypoints
   - During route changes
   - At airspace boundaries

**State Machine Rules:**
1. Each state has specific responsibilities
2. Transitions require explicit clearance
3. Waiting states maintain current clearance
4. No movement between states without authorization
5. Each state has its own communication protocol
6. Controllers coordinate state transitions

### Transponder State Management

**Transponder States by ATC Facility:**
1. **Ground Control State**
   - Initial squawk assignment
   - Mode: ON or ALT
   - TCAS: STBY or OFF
   - Common codes: Assigned departure code

2. **Tower Control State**
   - Mode: ALT (for altitude reporting)
   - TCAS: TA/RA (if in busy airspace)
   - Code verification before takeoff
   - Monitoring for emergency codes

3. **Departure/Approach State**
   - Mode: ALT
   - TCAS: TA/RA
   - Code changes for approach sequence
   - Traffic conflict monitoring

4. **Center/Enroute State**
   - Mode: ALT
   - TCAS: TA/RA
   - Code changes for sector transitions
   - Long-range traffic monitoring

**Transponder State Transitions:**
1. **Ground → Tower**
   - Verify squawk code is correct
   - Set Mode C (ALT)
   - Activate TCAS if required
   - Monitor for emergency codes

2. **Tower → Departure**
   - Maintain Mode C
   - Ensure TCAS is active
   - Monitor for traffic alerts
   - Be prepared for code changes

3. **Departure → Center**
   - Maintain Mode C
   - Keep TCAS active
   - Expect code changes
   - Monitor for traffic

**Emergency State Handling:**
1. **Radio Failure (7600)**
   - Maintain last assigned code
   - Follow last received clearance
   - Monitor appropriate frequency
   - Land at nearest suitable airport

2. **Emergency (7700)**
   - Set emergency code
   - Declare emergency
   - Follow ATC instructions
   - Maintain communication

3. **Security (7500)**
   - Set security code
   - Maintain normal operations
   - Follow security procedures
   - Await further instructions

**Transponder Integration Rules:**
1. Each ATC state has specific transponder requirements
2. Transponder state changes require verification
3. Emergency codes override normal operations
4. TCAS operations must be coordinated with ATC
5. Code changes must be acknowledged
6. Mode changes must be appropriate for phase of flight

## 3. Handoff Procedures and Frequency Changes

**Standard Handoff Process:**

1. **Initiation by Current Controller**
   - Controller identifies aircraft ready for handoff
   - Provides new frequency and any transition instructions
   - Example: "Delta 123, contact Tower 118.7, expect Runway 22L"

2. **Pilot Acknowledgment**
   - Must read back frequency and any instructions
   - Example: "Contacting Tower 118.7, expect Runway 22L, Delta 123"

3. **Frequency Change**
   - Pilot switches to new frequency
   - Establishes contact with new controller
   - Example: "Boston Tower, Delta 123 with you, taxiing to Runway 22L"

4. **New Controller Acknowledgment**
   - Confirms contact and provides new instructions
   - Example: "Delta 123, Boston Tower, continue taxi to Runway 22L"

**Frequency Change Protocol:**
1. Wait for explicit instruction to change frequency
2. Read back the frequency and any associated instructions
3. Switch to new frequency
4. Establish contact with new controller
5. Maintain current clearance until new instructions received

**Common Handoff Scenarios:**

1. **Ground to Tower**
   - Trigger: Approaching runway entry point
   - Ground: "Delta 123, contact Tower 118.7"
   - Pilot: "Contacting Tower 118.7, Delta 123"
   - Pilot (on Tower freq): "Boston Tower, Delta 123 with you, holding short Runway 22L"

2. **Tower to Departure**
   - Trigger: After takeoff, reaching specified altitude
   - Tower: "Delta 123, contact Departure 125.8"
   - Pilot: "Contacting Departure 125.8, Delta 123"
   - Pilot (on Departure freq): "Boston Departure, Delta 123 with you, climbing through 2,000"

3. **Departure to Center**
   - Trigger: Reaching enroute altitude or airspace boundary
   - Departure: "Delta 123, contact Boston Center 132.55"
   - Pilot: "Contacting Boston Center 132.55, Delta 123"
   - Pilot (on Center freq): "Boston Center, Delta 123 with you, level at 10,000"

**Important Handoff Rules:**
- Never change frequency without explicit instruction
- Always read back frequency changes
- Include current position/altitude when checking in with new controller
- Maintain current clearance until new instructions received
- If no response from new controller, return to previous frequency
- Report any issues or concerns during handoff 

from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Dict, Set
import threading
import queue
from datetime import datetime

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
class ATCTransition:
    from_state: ATCState
    to_state: ATCState
    required_status: Set[AircraftStatus]
    trigger_message: str
    expected_response: str
    next_actions: List[str]

class ATCStateManager:
    def __init__(self, airport_manager):
        self.airport_manager = airport_manager
        self.current_state = ATCState.GROUND
        self.aircraft_status = AircraftStatus.AT_GATE
        self.transitions: Dict[str, ATCTransition] = {}
        self.message_queue = queue.Queue()
        self.state_lock = threading.Lock()
        self._setup_transitions()
        
    def _setup_transitions(self):
        # Define all possible state transitions with their required conditions
        self.transitions = {
            "GROUND_TO_TOWER": ATCTransition(
                from_state=ATCState.GROUND,
                to_state=ATCState.TOWER,
                required_status={AircraftStatus.HOLDING_SHORT},
                trigger_message="Delta 123, contact Tower 118.7",
                expected_response="Contacting Tower 118.7, Delta 123",
                next_actions=["Tower: Delta 123, hold short Runway 22L"]
            ),
            "TOWER_TO_DEPARTURE": ATCTransition(
                from_state=ATCState.TOWER,
                to_state=ATCState.DEPARTURE,
                required_status={AircraftStatus.TAKEOFF, AircraftStatus.CLIMBING},
                trigger_message="Delta 123, contact Departure 125.8",
                expected_response="Contacting Departure 125.8, Delta 123",
                next_actions=["Departure: Delta 123, climb and maintain 5,000"]
            ),
            # Add more transitions...
        }
    
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
    
    def process_response(self, response: str) -> bool:
        """Process a pilot response and update state if valid"""
        with self.state_lock:
            # Find applicable transitions
            applicable_transitions = [
                t for t in self.transitions.values()
                if t.from_state == self.current_state and 
                self.aircraft_status in t.required_status
            ]
            
            if not applicable_transitions:
                return False
                
            # Check if response matches expected
            for transition in applicable_transitions:
                if response.strip() == transition.expected_response:
                    self.current_state = transition.to_state
                    return True
                    
            return False
    
    def update_aircraft_status(self, new_status: AircraftStatus):
        """Update the aircraft's current status"""
        with self.state_lock:
            self.aircraft_status = new_status

class ATCController:
    def __init__(self, airport_manager):
        self.state_manager = ATCStateManager(airport_manager)
        self.message_queue = queue.Queue()
        self.running = False
        self.controller_thread = None
    
    def start(self):
        """Start the ATC controller thread"""
        self.running = True
        self.controller_thread = threading.Thread(target=self._controller_loop)
        self.controller_thread.start()
    
    def _controller_loop(self):
        """Main controller loop that processes messages and updates state"""
        while self.running:
            try:
                # Check for next message to send
                next_message = self.state_manager.get_next_message()
                if next_message:
                    self.message_queue.put(next_message)
                
                # Process any responses
                try:
                    response = self.message_queue.get(timeout=1.0)
                    self.state_manager.process_response(response)
                except queue.Empty:
                    continue
                    
            except Exception as e:
                print(f"Error in controller loop: {e}")
    
    def stop(self):
        """Stop the ATC controller thread"""
        self.running = False
        if self.controller_thread:
            self.controller_thread.join()

# Initialize
airport_manager = AirportManager("airport_layout.json")
atc_controller = ATCController(airport_manager)

# Start the controller
atc_controller.start()

# Update aircraft status (e.g., from position detector)
atc_controller.state_manager.update_aircraft_status(AircraftStatus.HOLDING_SHORT)

# Get next message to send
next_message = atc_controller.state_manager.get_next_message()
if next_message:
    print(f"ATC: {next_message}")

# Process pilot response
response = "Contacting Tower 118.7, Delta 123"
if atc_controller.state_manager.process_response(response):
    print("State transition successful")

# Ground Phase:
# ATC: "Delta 123, taxi to Runway 22L via Alpha, Bravo"
# Pilot: "Taxi to Runway 22L via Alpha, Bravo, Delta 123"
# [Aircraft moves to HOLDING_SHORT]
# ATC: "Delta 123, contact Tower 118.7"
# Pilot: "Contacting Tower 118.7, Delta 123"
# [State changes to TOWER] 