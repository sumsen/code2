# -*- coding: utf-8 -*-
"""
Created on Wed Apr 13 10:44:20 2016

@author: sumsen
"""

import itertools
import random

import simpy


RANDOM_SEED = 42
GAS_STATION_SIZE = 17000     # liters (tank size * 10)
THRESHOLD = 10             # Threshold for calling the tank truck (in %)
WATER_TANK_SIZE = 1700        # liters (sourced from internet for large aircraft)
WATER_TANK_LEVEL = [50, 1500]  # Min/max levels of water tanks (in liters)
REWATERING_SPEED = 0.2        # liters / second
TANK_TRUCK_TIME = 300      # Seconds it takes the tank truck to arrive
T_INTER = [30, 300]        # Create a aircraft every [min, max] seconds
SIM_TIME = 1000            # Simulation time in seconds


def airc(name, env, gas_station, water_pump):
    """A aircraft arrives at the gas station for rewatering.

    It requests one of the gas station's water pumps and tries to get the
    desired amount of gas from it. If the stations reservoir is
    depleted, the aircraft has to wait for the tank truck to arrive.

    """
    water_tank_level = random.randint(*WATER_TANK_LEVEL)
    print('%s arriving at airport at %.1f' % (name, env.now))
    with gas_station.request() as req:
        start = env.now
        # Request one of the gas pumps
        yield req

        # Get the required amount of water
        liters_required = WATER_TANK_SIZE - water_tank_level
        yield water_pump.get(liters_required)

        # The "actual" rewatering process takes some time
        yield env.timeout(liters_required / REWATERING_SPEED)

        print('%s finished rewatering in %.1f seconds.' % (name,
                                                          env.now - start))


def gas_station_control(env, water_pump):
    """Periodically check the level of the *water_pump* and call the tank
    truck if the level falls below a threshold."""
    while True:
        if water_pump.level / water_pump.capacity * 100 < THRESHOLD:
            # We need to call the tank truck now!
            print('Calling tank truck at %d' % env.now)
            # Wait for the tank truck to arrive and refuel the station
            yield env.process(tank_truck(env, fuel_pump))

        yield env.timeout(10)  # Check every 10 seconds


def tank_truck(env, fuel_pump):
    """Arrives at the gas station after a certain delay and refuels it."""
    yield env.timeout(TANK_TRUCK_TIME)
    print('Tank truck arriving at time %d' % env.now)
    ammount = fuel_pump.capacity - fuel_pump.level
    print('Tank truck refuelling %.1f liters.' % ammount)
    yield fuel_pump.put(ammount)


def car_generator(env, gas_station, fuel_pump):
    """Generate new cars that arrive at the gas station."""
    for i in itertools.count():
        yield env.timeout(random.randint(*T_INTER))
        env.process(airc('Aircraft %d' % i, env, gas_station, fuel_pump))


# Setup and start the simulation
print('Gas Station refuelling')
random.seed(RANDOM_SEED)

# Create environment and start processes
env = simpy.Environment()
gas_station = simpy.Resource(env, 2)
fuel_pump = simpy.Container(env, GAS_STATION_SIZE, init=GAS_STATION_SIZE)
env.process(gas_station_control(env, fuel_pump))
env.process(car_generator(env, gas_station, fuel_pump))

# Execute!
env.run(until=SIM_TIME)