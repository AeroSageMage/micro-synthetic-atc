import simpy
import random
from enum import Enum

class AircraftState(Enum):
    APPROACHING = "APPROACHING"
    LANDING = "LANDING"
    TAXIING = "TAXIING"
    AT_GATE = "AT_GATE"
    PUSHBACK = "PUSHBACK"
    TAKEOFF = "TAKEOFF"
    CLIMBING = "CLIMBING"

class Aircraft:
    def __init__(self, env, name, is_arrival=True):
        self.env = env
        self.name = name
        self.is_arrival = is_arrival
        self.state = AircraftState.APPROACHING if is_arrival else AircraftState.AT_GATE
        self.process = env.process(self.run())

    def run(self):
        if self.is_arrival:
            yield from self.arrival_sequence()
        else:
            yield from self.departure_sequence()

    def arrival_sequence(self):
        # Approaching
        print(f'{self.env.now:.1f}: {self.name} is approaching')
        yield self.env.timeout(random.uniform(1, 2))
        
        # Landing
        self.state = AircraftState.LANDING
        print(f'{self.env.now:.1f}: {self.name} is landing')
        yield self.env.timeout(1)
        
        # Taxiing to gate
        self.state = AircraftState.TAXIING
        print(f'{self.env.now:.1f}: {self.name} is taxiing to gate')
        yield self.env.timeout(random.uniform(2, 3))
        
        # At gate
        self.state = AircraftState.AT_GATE
        print(f'{self.env.now:.1f}: {self.name} has arrived at gate')

    def departure_sequence(self):
        # At gate
        print(f'{self.env.now:.1f}: {self.name} is at gate')
        yield self.env.timeout(random.uniform(1, 2))
        
        # Pushback
        self.state = AircraftState.PUSHBACK
        print(f'{self.env.now:.1f}: {self.name} is pushing back')
        yield self.env.timeout(1)
        
        # Taxiing to runway
        self.state = AircraftState.TAXIING
        print(f'{self.env.now:.1f}: {self.name} is taxiing to runway')
        yield self.env.timeout(random.uniform(2, 3))
        
        # Takeoff
        self.state = AircraftState.TAKEOFF
        print(f'{self.env.now:.1f}: {self.name} is taking off')
        yield self.env.timeout(1)
        
        # Climbing
        self.state = AircraftState.CLIMBING
        print(f'{self.env.now:.1f}: {self.name} is climbing')
        yield self.env.timeout(2)
        print(f'{self.env.now:.1f}: {self.name} has departed')

class ATCSimulation:
    def __init__(self):
        self.env = simpy.Environment()
        self.runway = simpy.Resource(self.env, capacity=1)
        self.aircraft_list = []

    def generate_aircraft(self):
        # Generate a mix of arrivals and departures
        for i in range(5):
            is_arrival = random.choice([True, False])
            aircraft = Aircraft(self.env, f'FLIGHT{i+1}', is_arrival)
            self.aircraft_list.append(aircraft)
            # Add some random delay between aircraft
            yield self.env.timeout(random.uniform(1, 3))

    def run(self, until=30):
        self.env.process(self.generate_aircraft())
        print('Starting ATC Simulation...')
        self.env.run(until=until)
        print('Simulation finished!')

if __name__ == '__main__':
    # Create and run the simulation
    simulation = ATCSimulation()
    simulation.run() 