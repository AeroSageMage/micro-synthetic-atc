# Basic ATC Communication Patterns for Micro-Synthetic ATC

## 1. Core Communication Structure

### Standard Message Format
```
[Controller]: "[Callsign], [Facility]"
[Pilot]: "[Facility], [Callsign], [Position/Status]"
```

### Common Responses
- Acknowledgment: "Roger"
- Readback: "[Instruction], [Callsign]"
- Unable: "Unable, [Callsign]"
- Request: "[Callsign], request [request]"

### Acknowledgment Words and Their Meanings
1. **"Roger"**
   - Meaning: "I have received all of your last transmission"
   - Usage: When acknowledging information-only messages
   - Examples:
     - "Delta 123, wind 270 at 10" → "Roger, Delta 123"
     - "Delta 123, traffic 2 o'clock, 5 miles" → "Roger, Delta 123"
     - "Delta 123, expect vectors for ILS approach" → "Roger, Delta 123"
   - Important: Does NOT mean agreement or compliance
   - Common Mistake: Using "Roger" instead of a required readback
   - Regional Note: Some regions prefer "Copy" instead of "Roger"

2. **"Wilco"**
   - Meaning: "I have received your message, understand it, and will comply with it"
   - Usage: When acknowledging and agreeing to comply with an instruction
   - Examples:
     - "Delta 123, turn left heading 270" → "Wilco, Delta 123"
     - "Delta 123, maintain 5,000 feet" → "Wilco, Delta 123"
   - Note: Rarely used in modern aviation, usually replaced by readback
   - Common Mistake: Using "Wilco" when a specific readback is required
   - Regional Note: More common in military communications

3. **"Affirmative"**
   - Meaning: "Yes"
   - Usage: When answering yes/no questions
   - Examples:
     - "Delta 123, do you have the ATIS?" → "Affirmative, Delta 123"
     - "Delta 123, can you accept Runway 22L?" → "Affirmative, Delta 123"
     - "Delta 123, are you ready for pushback?" → "Affirmative, Delta 123"
   - Common Mistake: Using "Yes" instead of "Affirmative"
   - Regional Note: Some regions use "Affirm" as a shorter form

4. **"Negative"**
   - Meaning: "No"
   - Usage: When answering yes/no questions
   - Examples:
     - "Delta 123, can you accept Runway 22L?" → "Negative, Delta 123"
     - "Delta 123, do you have the weather?" → "Negative, Delta 123"
     - "Delta 123, are you ready for departure?" → "Negative, Delta 123"
   - Common Mistake: Using "No" instead of "Negative"
   - Regional Note: Consistent usage across all regions

5. **"Confirm"**
   - Meaning: "Please verify that what I heard is correct"
   - Usage: When seeking verification of information
   - Examples:
     - "Delta 123, confirm you are holding short Runway 22L" → "Affirmative, holding short Runway 22L, Delta 123"
     - "Delta 123, confirm you are at 5,000 feet" → "Affirmative, level at 5,000, Delta 123"
     - "Delta 123, confirm you have information Charlie" → "Affirmative, information Charlie, Delta 123"
   - Common Mistake: Using "Confirm" when you mean "Verify"
   - Regional Note: Some regions use "Verify" more frequently

6. **"Verify"**
   - Meaning: "Please check and confirm"
   - Usage: When asking for confirmation of specific information
   - Examples:
     - "Delta 123, verify you are at 5,000 feet" → "Affirmative, level at 5,000, Delta 123"
     - "Delta 123, verify you are on frequency 118.7" → "Affirmative, on 118.7, Delta 123"
     - "Delta 123, verify you are cleared for takeoff" → "Affirmative, cleared for takeoff Runway 22L, Delta 123"
   - Common Mistake: Using "Verify" when you mean "Confirm"
   - Regional Note: More common in US communications

7. **"Standby"**
   - Meaning: "Please wait, I will get back to you"
   - Usage: When needing time to process a request
   - Examples:
     - "Delta 123, request higher altitude" → "Delta 123, standby"
     - "Delta 123, request runway change" → "Delta 123, standby"
     - "Delta 123, request delay vectors" → "Delta 123, standby"
   - Common Mistake: Not responding after "Standby"
   - Regional Note: Some regions use "Wait" instead

8. **"Say Again"**
   - Meaning: "Please repeat your last transmission"
   - Usage: When message was not understood
   - Examples:
     - "Delta 123, say again your altitude" → "Level at 5,000, Delta 123"
     - "Delta 123, say again your position" → "Holding short Runway 22L, Delta 123"
     - "Delta 123, say again your request" → "Request higher to 7,000, Delta 123"
   - Common Mistake: Using "Repeat" instead of "Say Again"
   - Regional Note: Consistent usage across all regions

### Quick Reference Table
| Word        | Meaning                                    | When to Use                    | When NOT to Use               |
|-------------|--------------------------------------------|--------------------------------|-------------------------------|
| Roger       | Message received                           | Information-only messages      | Clearances, instructions      |
| Wilco       | Will comply                                | Simple instructions            | When readback required        |
| Affirmative | Yes                                        | Yes/no questions               | General acknowledgments       |
| Negative    | No                                         | Yes/no questions               | General acknowledgments       |
| Confirm     | Verify information                         | Checking specific information  | When you mean "Verify"        |
| Verify      | Check and confirm                          | Verifying status               | When you mean "Confirm"       |
| Standby     | Wait for response                          | Processing requests            | As a final response           |
| Say Again   | Repeat transmission                        | Unclear messages               | Instead of proper readback    |

### Common Mistakes to Avoid
1. Using "Roger" for clearances that require readback
2. Using "Yes" or "No" instead of "Affirmative" or "Negative"
3. Using "Confirm" and "Verify" interchangeably
4. Not responding after receiving "Standby"
5. Using "Repeat" instead of "Say Again"
6. Using "Wilco" when a specific readback is required
7. Using abbreviated acknowledgments when full readback is needed

### Regional Variations
1. **North America**
   - More frequent use of "Verify"
   - "Copy" sometimes used instead of "Roger"
   - Strict adherence to readback requirements

2. **Europe**
   - More frequent use of "Confirm"
   - "Wait" sometimes used instead of "Standby"
   - Slightly more flexible with readbacks

3. **Asia/Pacific**
   - More formal communication style
   - Frequent use of full readbacks
   - Clear distinction between "Confirm" and "Verify"

4. **Military Operations**
   - More frequent use of "Wilco"
   - "Affirm" used instead of "Affirmative"
   - More abbreviated communications

Important Rules:
- Never use "Roger" when a readback is required
- Always use proper readback for clearances and instructions
- Use "Affirmative" or "Negative" instead of "Yes" or "No"
- "Roger" does not imply compliance with instructions
- When in doubt, use a full readback
- Be aware of regional variations in phraseology
- Always use the most appropriate acknowledgment for the situation

### Callsign Usage and Structure
1. **Standard Airline Callsigns**
   - Major Airlines: Use company name + flight number
     - Example: "Delta 123", "United 456", "American 789"
   - Regional Airlines: Use company name + flight number
     - Example: "SkyWest 1234", "Republic 5678"

2. **General Aviation Callsigns**
   - Registered Aircraft: Use full registration
     - Example: "N123AB"
   - Private Aircraft: Use aircraft type + last 3 digits
     - Example: "Cessna 123"

3. **Military Callsigns**
   - Use specific military designators
     - Example: "Reach 123", "Navy 456"

4. **Callsign Rules**
   - Always use full callsign on initial contact
   - After established contact, can use abbreviated form
   - Never abbreviate similar-sounding callsigns
   - Always use full callsign when changing frequencies

### Phonetic Alphabet Usage
1. **When to Use Phonetic Alphabet**
   - Spelling out registration numbers
   - Clarifying similar-sounding callsigns
   - Reading back taxiway/runway identifiers
   - Confirming frequency numbers
   - Any time clarity is needed

2. **Standard Phonetic Alphabet**
   ```
   A - Alpha      B - Bravo     C - Charlie    D - Delta
   E - Echo       F - Foxtrot   G - Golf       H - Hotel
   I - India      J - Juliet    K - Kilo       L - Lima
   M - Mike       N - November  O - Oscar      P - Papa
   Q - Quebec     R - Romeo     S - Sierra     T - Tango
   U - Uniform    V - Victor    W - Whiskey    X - X-ray
   Y - Yankee     Z - Zulu
   ```

3. **Common Usage Examples**
   - Registration: "November One Two Three Alpha Bravo"
   - Taxiway: "Taxi via Alpha, Bravo, Charlie"
   - Frequency: "Contact Tower One One Eight Point Seven"
   - Similar Callsigns: "Delta One Two Three, not Delta One Two Four"

4. **Numbers Pronunciation**
   - 0 - Zero
   - 1 - One
   - 2 - Two
   - 3 - Tree
   - 4 - Fower
   - 5 - Fife
   - 6 - Six
   - 7 - Seven
   - 8 - Eight
   - 9 - Niner

## 2. Essential Communication Cases

### Ground Phase
1. **Initial Contact**
   - Ground: "Delta 123, Boston Ground"
   - Pilot: "Boston Ground, Delta 123 at Gate A5"

2. **Pushback**
   - Ground: "Delta 123, pushback approved, face east"
   - Pilot: "Pushback approved, face east, Delta 123"

3. **Taxi Instructions**
   - Ground: "Delta 123, taxi to Runway 22L via Alpha, Bravo"
   - Pilot: "Taxi to Runway 22L via Alpha, Bravo, Delta 123"

4. **Hold Short**
   - Ground: "Delta 123, hold short Runway 22L"
   - Pilot: "Hold short Runway 22L, Delta 123"

### Tower Phase
1. **Line Up**
   - Tower: "Delta 123, line up and wait Runway 22L"
   - Pilot: "Line up and wait Runway 22L, Delta 123"

2. **Takeoff Clearance**
   - Tower: "Delta 123, cleared for takeoff Runway 22L"
   - Pilot: "Cleared for takeoff Runway 22L, Delta 123"

3. **Landing Clearance**
   - Tower: "Delta 123, cleared to land Runway 22L"
   - Pilot: "Cleared to land Runway 22L, Delta 123"

### Departure/Approach Phase
1. **Initial Climb**
   - Departure: "Delta 123, climb and maintain 5,000"
   - Pilot: "Climb and maintain 5,000, Delta 123"

2. **Heading Change**
   - Departure: "Delta 123, turn left heading 270"
   - Pilot: "Turn left heading 270, Delta 123"

3. **Frequency Change**
   - Departure: "Delta 123, contact Boston Center 132.55"
   - Pilot: "Contacting Boston Center 132.55, Delta 123"

## 3. Common State Transitions

### Ground → Tower
1. Ground: "Delta 123, contact Tower 118.7"
2. Pilot: "Contacting Tower 118.7, Delta 123"
3. Pilot (on Tower): "Boston Tower, Delta 123 with you, holding short Runway 22L"

### Tower → Departure
1. Tower: "Delta 123, contact Departure 125.8"
2. Pilot: "Contacting Departure 125.8, Delta 123"
3. Pilot (on Departure): "Boston Departure, Delta 123 with you, climbing through 2,000"

## 4. Implementation Notes

### Key States to Track
1. **Aircraft State**
   - Position (gate/taxiway/runway)
   - Altitude
   - Heading
   - Speed

2. **Communication State**
   - Current frequency
   - Last instruction
   - Pending clearances
   - Next expected action

### Required Validations
1. **Clearance Checks**
   - Verify aircraft position matches clearance
   - Confirm altitude restrictions
   - Validate heading changes
   - Check runway assignments

2. **Response Requirements**
   - Mandatory readbacks for:
     - Takeoff clearances
     - Landing clearances
     - Altitude changes
     - Frequency changes
     - Runway crossings

## 5. Common Error Cases

### Pilot Errors
1. **Incorrect Readback**
   - Pilot: "Cleared to land Runway 22R, Delta 123"
   - Tower: "Negative, cleared to land Runway 22L, Delta 123"

2. **Missed Instruction**
   - Tower: "Delta 123, turn left heading 270"
   - Pilot: "Say again, Delta 123"

### System Errors
1. **Frequency Congestion**
   - Pilot: "Boston Tower, Delta 123, unable to contact"
   - Tower: "Delta 123, standby"

2. **Clearance Conflict**
   - System should detect and prevent:
     - Multiple aircraft on same runway
     - Conflicting altitude assignments
     - Intersecting taxi routes 

## 6. Pilot Communication Procedures

### Frequency Management
1. **Frequency Changes**
   - Monitor current frequency until explicitly told to change
   - Write down new frequency before changing
   - Verify frequency is correctly set
   - Listen briefly before transmitting
   - Make initial contact with new facility

2. **Frequency Change Protocol**
   ```
   1. Receive instruction: "Delta 123, contact Tower 118.7"
   2. Read back: "Contacting Tower 118.7, Delta 123"
   3. Set new frequency
   4. Listen briefly
   5. Initial contact: "Boston Tower, Delta 123 with you, [position/status]"
   ```

3. **Common Frequency Change Scenarios**
   - Ground → Tower: When approaching runway
   - Tower → Departure: After takeoff
   - Departure → Center: When reaching enroute altitude
   - Approach → Tower: When established on approach
   - Tower → Ground: After landing

### Pilot Readback Requirements
1. **Mandatory Readbacks**
   - Clearance to takeoff
   - Clearance to land
   - Runway crossing clearances
   - Altitude assignments
   - Heading assignments
   - Speed assignments
   - Frequency changes

2. **Readback Format**
   ```
   [Instruction], [Callsign]
   Example: "Cleared for takeoff Runway 22L, Delta 123"
   ```

### Pilot Edge Cases

1. **Frequency Congestion**
   - If unable to contact new frequency:
     - Return to previous frequency
     - Report: "Unable to contact [facility], Delta 123"
     - Wait for further instructions

2. **Missed Instructions**
   - If instruction unclear:
     - Request: "Say again, Delta 123"
     - If still unclear: "Unable [instruction], Delta 123"

3. **Unable to Comply**
   - If unable to comply with instruction:
     - Report immediately: "Unable [instruction], Delta 123"
     - Provide reason if possible
     - Wait for amended instructions

4. **Lost Communication**
   - If radio failure:
     - Squawk 7600
     - Follow last received clearance
     - Monitor appropriate frequency
     - Land at nearest suitable airport

5. **Emergency Communications**
   - Use "Mayday" or "Pan-Pan" as appropriate
   - State nature of emergency
   - Follow ATC instructions
   - Maintain communication priority

### Common Pilot Mistakes

1. **Frequency Management**
   - Changing frequency too early
   - Not listening before transmitting
   - Incorrect frequency setting
   - Forgetting to monitor previous frequency

2. **Readback Errors**
   - Incomplete readbacks
   - Incorrect information
   - Missing mandatory readbacks
   - Using "Roger" instead of readback

3. **Communication Timing**
   - Transmitting during other communications
   - Not waiting for appropriate pause
   - Interrupting ongoing communications
   - Delayed responses

4. **Position Reporting**
   - Inaccurate position reports
   - Missing required information
   - Unclear position descriptions
   - Late position reports

### Pilot Best Practices

1. **Preparation**
   - Have frequencies ready before needed
   - Know expected communication points
   - Prepare position reports in advance
   - Anticipate next frequency change

2. **Communication**
   - Listen before transmitting
   - Use standard phraseology
   - Be concise but complete
   - Maintain professional tone

3. **Situational Awareness**
   - Monitor other aircraft communications
   - Be aware of traffic situation
   - Anticipate ATC instructions
   - Maintain position awareness

4. **Error Prevention**
   - Double-check frequency changes
   - Verify readbacks before transmitting
   - Confirm understanding of instructions
   - Ask for clarification when needed

### Pilot Communication Checklist

1. **Before Frequency Change**
   - [ ] Have new frequency ready
   - [ ] Know current position
   - [ ] Understand next expected action
   - [ ] Prepare initial contact message

2. **During Communication**
   - [ ] Listen before transmitting
   - [ ] Use proper phraseology
   - [ ] Include all required information
   - [ ] Verify readback accuracy

3. **After Communication**
   - [ ] Confirm understanding
   - [ ] Monitor for further instructions
   - [ ] Update position awareness
   - [ ] Prepare for next expected action

4. **Emergency Preparedness**
   - [ ] Know emergency frequencies
   - [ ] Understand emergency procedures
   - [ ] Have backup communication methods
   - [ ] Know diversion procedures

### Handling Non-Compliance

1. **ATC Response to Non-Compliance**
   - Immediate recognition of deviation
   - Clear communication of the issue
   - Provision of corrective instructions
   - Monitoring of compliance
   - Escalation if necessary

2. **Common Non-Compliance Scenarios**

   a) **Altitude Deviations**
   - ATC: "Delta 123, verify maintaining 5,000"
   - If no response: "Delta 123, say altitude"
   - If still non-compliant: "Delta 123, climb/descend immediately to 5,000"
   - If continues: "Delta 123, state intentions"

   b) **Heading Deviations**
   - ATC: "Delta 123, verify heading 270"
   - If no response: "Delta 123, say heading"
   - If still non-compliant: "Delta 123, turn immediately to heading 270"
   - If continues: "Delta 123, state intentions"

   c) **Speed Deviations**
   - ATC: "Delta 123, verify speed 250 knots"
   - If no response: "Delta 123, say speed"
   - If still non-compliant: "Delta 123, reduce/increase speed to 250 knots"
   - If continues: "Delta 123, state intentions"

   d) **Clearance Violations**
   - ATC: "Delta 123, verify cleared to land Runway 22L"
   - If no response: "Delta 123, say intentions"
   - If still non-compliant: "Delta 123, go around"
   - If continues: "Delta 123, state intentions"

3. **Escalation Protocol**

   a) **First Level - Verification**
   - Ask for verification of current state
   - Example: "Delta 123, verify maintaining 5,000"
   - Purpose: Confirm if pilot is aware of deviation

   b) **Second Level - Direct Instruction**
   - Provide clear corrective action
   - Example: "Delta 123, climb immediately to 5,000"
   - Purpose: Get immediate compliance

   c) **Third Level - Intentions**
   - Ask for pilot's intentions
   - Example: "Delta 123, state intentions"
   - Purpose: Understand pilot's situation

   d) **Fourth Level - Emergency**
   - Declare emergency if necessary
   - Example: "Delta 123, do you require assistance?"
   - Purpose: Ensure safety of flight

4. **Simulation-Specific Considerations**

   a) **UI Feedback**
   - Visual indicators of non-compliance
   - Warning messages
   - Corrective action suggestions
   - Status updates

   b) **Automated Responses**
   - Automatic verification requests
   - Progressive escalation
   - Safety net implementations
   - Recovery procedures

   c) **Learning Opportunities**
   - Explain why instruction wasn't followed
   - Provide correct procedure
   - Show potential consequences
   - Offer practice scenarios

5. **Recovery Procedures**

   a) **After Non-Compliance**
   - Acknowledge the issue
   - Provide clear recovery instructions
   - Monitor compliance
   - Reinstate normal operations

   b) **Communication Reset**
   - Re-establish communication
   - Verify understanding
   - Confirm new instructions
   - Resume normal procedures

6. **Prevention Strategies**

   a) **Clear Communication**
   - Use standard phraseology
   - Ensure understanding
   - Request readbacks
   - Verify compliance

   b) **Proactive Monitoring**
   - Track aircraft parameters
   - Identify potential issues
   - Provide early warnings
   - Offer assistance

   c) **Education**
   - Explain procedures
   - Provide context
   - Show consequences
   - Offer guidance

7. **Simulation Implementation Guidelines**

   a) **Grading System**
   - Track compliance
   - Score performance
   - Provide feedback
   - Suggest improvements

   b) **Assistance Levels**
   - Full guidance
   - Partial assistance
   - Minimal support
   - No assistance

   c) **Feedback Mechanisms**
   - Immediate corrections
   - Post-flight analysis
   - Performance metrics
   - Learning resources

## 7. Transponder Operations and TCAS

### Transponder Modes and Functions
1. **Mode Selection**
   - OFF: Transponder is off
   - STBY (Standby): Transponder is on but not transmitting
   - ON: Normal operation, responding to interrogations
   - ALT (Altitude): Transmitting altitude information (Mode C)
   - TA/RA: Traffic Advisory/Resolution Advisory (TCAS)

2. **Common Squawk Codes**
   - 1200: VFR flight in US
   - 2000: IFR flight in Europe
   - 7000: VFR flight in Europe
   - 7500: Hijacking
   - 7600: Radio failure
   - 7700: Emergency

### Transponder Communication Protocol
1. **Initial Squawk Assignment**
   - ATC: "Delta 123, squawk 4321"
   - Pilot: "Squawking 4321, Delta 123"
   - Verify code is correctly set
   - Confirm ATC acknowledgment

2. **Code Changes**
   - ATC: "Delta 123, squawk 1234"
   - Pilot: "Squawking 1234, Delta 123"
   - Verify change
   - Wait for ATC acknowledgment

3. **Ident Function**
   - ATC: "Delta 123, ident"
   - Pilot: "Ident, Delta 123"
   - Press IDENT button
   - Wait for ATC acknowledgment

### TCAS Operations
1. **TCAS Modes**
   - TA ONLY: Traffic Advisory only
   - TA/RA: Traffic and Resolution Advisories
   - STBY: Standby mode

2. **TCAS Alerts**
   - Traffic Advisory (TA): Yellow traffic symbol
   - Resolution Advisory (RA): Red traffic symbol with climb/descend commands

3. **TCAS Response Protocol**
   - Follow RA commands immediately
   - Notify ATC: "Delta 123, TCAS RA"
   - After RA: "Delta 123, clear of conflict"
   - Resume normal operations

### Emergency Squawk Codes
1. **7500 - Hijacking**
   - Set code immediately
   - Maintain normal radio communications if possible
   - Follow ATC instructions
   - Do not discuss situation on frequency

2. **7600 - Radio Failure**
   - Set code immediately
   - Follow last received clearance
   - Monitor appropriate frequency
   - Land at nearest suitable airport

3. **7700 - Emergency**
   - Set code immediately
   - Declare emergency on frequency
   - State nature of emergency
   - Follow ATC instructions

### Common Transponder Scenarios
1. **Departure**
   - Set assigned squawk before taxi
   - Verify code is correct
   - Monitor for code changes
   - Activate TCAS as required

2. **Enroute**
   - Monitor for code changes
   - Respond to TCAS alerts
   - Verify code periodically
   - Report any transponder issues

3. **Approach/Landing**
   - Monitor for code changes
   - Be prepared for final code change
   - Deactivate TCAS as required
   - Verify code is correct

### Transponder Best Practices
1. **Pre-flight**
   - Verify transponder operation
   - Check TCAS functionality
   - Have emergency codes memorized
   - Review transponder procedures

2. **In-flight**
   - Monitor for code changes
   - Verify code entries
   - Respond to TCAS alerts
   - Report any issues immediately

3. **Emergency Situations**
   - Set appropriate code immediately
   - Follow emergency procedures
   - Maintain communication if possible
   - Follow ATC instructions

### Common Transponder Errors
1. **Code Entry Errors**
   - Incorrect code entry
   - Partial code entry
   - Mode selection errors
   - Failure to verify code

2. **TCAS Errors**
   - Late response to RA
   - Incorrect RA interpretation
   - Failure to notify ATC
   - Improper TCAS mode selection

3. **Emergency Code Errors**
   - Delayed code setting
   - Incorrect code selection
   - Failure to follow procedures
   - Improper communication

### Transponder Checklist
1. **Pre-flight**
   - [ ] Verify transponder operation
   - [ ] Check TCAS functionality
   - [ ] Review emergency codes
   - [ ] Set initial code if known

2. **Before Taxi**
   - [ ] Set assigned squawk code
   - [ ] Verify code is correct
   - [ ] Set appropriate mode
   - [ ] Activate TCAS if required

3. **In-flight**
   - [ ] Monitor for code changes
   - [ ] Verify code entries
   - [ ] Respond to TCAS alerts
   - [ ] Report any issues

4. **Emergency**
   - [ ] Set appropriate emergency code
   - [ ] Follow emergency procedures
   - [ ] Maintain communication
   - [ ] Follow ATC instructions 