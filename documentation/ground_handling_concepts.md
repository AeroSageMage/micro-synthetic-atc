# Airport Ground Handling Concepts

## 1. Lifecycle State Diagram (Ground Handling)

**Lifecycle States:**

1. **Arriving Aircraft**
    - Landing Roll (on runway, decelerating)
    - Runway Exit (turns off onto taxiway)
    - Taxi to Stand (follows taxi route to parking/gate)
    - At Stand (engines off, ground services, passengers disembark)
2. **Turnaround (At Stand)**
    - Ground Services (fuel, catering, cleaning, boarding, etc.)
    - Pushback/Engine Start (if required)
3. **Departing Aircraft**
    - Pushback (if required)
    - Taxi to Runway (follows taxi route to assigned runway)
    - Holding Point (waits for clearance to enter runway)
    - Line Up & Wait (on runway, waiting for takeoff clearance)
    - Takeoff Roll (accelerating on runway)
    - Departure (airborne)

**Text State Diagram:**

```
[Landing Roll] 
    ↓ (exit runway)
[Taxi to Stand]
    ↓ (arrive at stand)
[At Stand]
    ↓ (services complete, ready for departure)
[Pushback/Engine Start]
    ↓ (pushback complete)
[Taxi to Runway]
    ↓ (arrive at holding point)
[Holding Point]
    ↓ (cleared to line up)
[Line Up & Wait]
    ↓ (takeoff clearance)
[Takeoff Roll]
    ↓ (airborne)
[Departure]
```

## 2. Typical Ground Clearances and Their Triggers

| **Clearance**         | **When/Why Given**                                                                 |
|-----------------------|------------------------------------------------------------------------------------|
| **Taxi to Stand**     | After landing, cleared to taxi from runway exit to assigned stand/gate             |
| **Taxi to Runway**    | After pushback/engine start, cleared to taxi from stand to holding point/runway    |
| **Pushback**          | When ready to leave stand, if pushback is required                                 |
| **Hold Short**        | Instructed to stop before entering a runway or crossing another taxiway/runway     |
| **Cross Runway**      | Allowed to cross a runway while taxiing                                            |
| **Line Up & Wait**    | Cleared to enter runway and wait for takeoff clearance                             |
| **Takeoff Clearance** | Cleared to begin takeoff roll                                                      |
| **Continue Taxi**     | After holding, allowed to continue taxiing                                         |

**Triggers:**
- Aircraft reaches a specific location (e.g., holding point, stand, runway entry)
- Previous clearance completed (e.g., pushback complete, taxi complete)
- No conflicting traffic (runway/taxiway is clear)
- Ground services completed

## 3. Data Structures for Tracking Aircraft on the Ground

### Aircraft State Object
```python
class GroundAircraftState:
    callsign: str
    position: Tuple[float, float]  # (lat, lon)
    heading: float
    speed: float
    current_state: Enum  # e.g., AT_STAND, TAXIING, HOLDING, ON_RUNWAY, etc.
    assigned_stand: str
    assigned_runway: str
    taxi_route: List[str]  # List of taxiway/segment names
    taxi_route_index: int  # Where they are on the route
    clearance: str  # Current clearance (e.g., 'Taxi to Runway', 'Hold Short')
    last_update: float  # Timestamp
```

### Airport Map/Graph
- Nodes: stands, intersections, holding points, runway entries
- Edges: taxiways, runways (with allowed directions, restrictions)

### Ground Services Queue
- List of pending services per aircraft
- Log of completed services and their times

### Conflict Matrix
- Which segments are occupied, reserved, or free

## Summary Table

| **Concept**         | **Example**                                                                 |
|---------------------|-----------------------------------------------------------------------------|
| State Machine       | AT_STAND → PUSHBACK → TAXIING → HOLDING → ON_RUNWAY → AIRBORNE              |
| Ground Clearances   | Taxi, Pushback, Hold Short, Line Up, Takeoff, Cross Runway                  |
| Data Structures     | Aircraft state, airport map/graph, service log, segment occupancy tracker   |
``` 