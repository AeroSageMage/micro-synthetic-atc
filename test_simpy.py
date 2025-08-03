import simpy

def test_simulation():
    # Create a SimPy environment
    env = simpy.Environment()
    
    # Define a simple process
    def simple_process(env, name):
        print(f'{name} starting at time {env.now}')
        yield env.timeout(2)  # Wait for 2 time units
        print(f'{name} finished at time {env.now}')
    
    # Add the process to the environment
    env.process(simple_process(env, 'Test Process'))
    
    # Run the simulation
    print('Starting simulation...')
    env.run(until=5)
    print('Simulation finished!')

if __name__ == '__main__':
    test_simulation() 