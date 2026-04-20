import os
import sys
import inspect

# Local CybORG source
sys.path.append(os.path.join(os.getcwd(), 'api', 'venv', 'src', 'cyborg'))

from CybORG import CybORG
from CybORG.Simulator.SimulationController import SimulationController

print("\nCybORG.__init__ signature:")
print(inspect.signature(CybORG.__init__))

print("\nCybORG._create_env_controller signature:")
print(inspect.signature(CybORG._create_env_controller))

print("\nSimulationController.step signature:")
print(inspect.signature(SimulationController.step))
