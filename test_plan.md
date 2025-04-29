# Position Detector Test Plan

## Test Environment Setup
- Airport: LIRF (Rome Fiumicino)
- Runway: 16C (17C in real world)
- Taxiway: D
- Test Data Source: Recorded UDP data from Aerofly FS 4
- UDP Protocol: Aerofly UDP format (XAIRCRAFT, XGPS, XATT messages)

## Test Cases

### 1. Initial Position (Parking)
**Test Data**: First few seconds of recording when aircraft is stationary
**Expected Results**:
- Area: AT_PARKING
- Specific Location: Parking spot identifier
- Ground Speed: < 0.5 m/s
- Altitude: Ground level
- Distance to Center: Within 5 meters of parking position

### 2. Taxiway Movement
**Test Data**: Middle section of recording during taxi
**Expected Results**:
- Area: ON_TAXIWAY
- Taxiway: D
- Ground Speed: > 0.5 m/s but < 10 m/s
- Altitude: Ground level
- Distance to Center: Within 5 meters of taxiway centerline

### 3. Holding Point
**Test Data**: Section where aircraft stops before runway
**Expected Results**:
- Area: AT_HOLDING_POINT
- Specific Location: Holding point identifier
- Runway: 16C
- Ground Speed: < 0.5 m/s
- Altitude: Ground level

### 4. Runway Entry and Takeoff
**Test Data**: Final section of recording during takeoff
**Expected Results**:
- Area: ON_RUNWAY
- Runway: 16C
- Ground Speed: Increasing from taxi speed to takeoff speed
- Distance to Center: Within runway width
- Heading: Aligned with runway heading (within 45 degrees)

### 5. Transition Points
**Test Data**: Points between different areas
**Expected Results**:
- Smooth transitions between areas
- No false detections during transitions
- Correct area detection at boundary points

### 6. Position Formatting
**Test Data**: Various position scenarios
**Expected Results**:
- Correctly formatted position information
- Accurate distance calculations
- Proper heading calculations

## Test Procedure
1. Load recorded data from `output_GPS_DATA.csv`
2. Process data through `GUI_send_GPS_data.py` in GPS mode
3. Send UDP messages in Aerofly format:
   - XAIRCRAFT message with aircraft info
   - XGPS message with position data
   - XATT message with attitude data
4. Monitor position detector output
5. Compare detected positions with expected results

## Success Criteria
- All test cases pass with expected results
- No false detections in any area
- Accurate distance calculations
- Proper heading alignment
- Smooth transitions between areas

## Notes
- Runway 16C in simulator corresponds to 17C in real world
- Distance thresholds:
  - Parking: 5 meters
  - Taxiway: 5 meters
  - Runway: Within runway width
- Speed thresholds:
  - Stationary: < 0.5 m/s
  - Taxiing: 0.5 - 10 m/s
  - Takeoff: > 10 m/s
- Heading alignment tolerance: ±45 degrees
- UDP messages follow Aerofly FS 4 protocol format
- Test data should be recorded in GPS mode (not traffic mode) 