"""
Brains Package - Multi-Brain Competition System
"""

from .brain_manager import BrainManager, Brain
from .aggressive import AggressiveBrain
from .cautious import CautiousBrain
from .health import HealthBrain
from .strategic import StrategicBrain
from .combat_brain import CombatBrain
from .survival_brain import SurvivalBrain

__all__ = [
    'BrainManager',
    'Brain',
    'AggressiveBrain',
    'CautiousBrain',
    'HealthBrain',
    'StrategicBrain',
    'CombatBrain',
    'SurvivalBrain'
]
