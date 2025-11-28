"""
Health Brain - Paranoid about HP, eats constantly
"""

from typing import Dict
from .brain_manager import Brain


class HealthBrain(Brain):
    """HP is LIFE! Must stay at max health!"""
    
    def __init__(self):
        super().__init__("HealthBrain", "❤️")
    
    def vote(self, perception: Dict) -> int:
        """Vote higher when any damage taken"""
        score = 20  # Base health concern
        
        health = perception.get('health', 20)
        food = perception.get('food', 20)
        inv = perception.get('inventory', {})
        
        # ANY damage = PANIC
        if health < 20:
            damage = 20 - health
            score += damage * 5  # Each HP lost = +5 score
        
        # Low food = can't regen
        if food < 15:
            score += 30
        if food < 10:
            score += 20
        
        # Check if have healing items
        has_food = any(item in ['bread', 'cooked_beef', 'cooked_porkchop', 'golden_apple'] 
                       for item in inv.keys())
        if has_food and (health < 20 or food < 15):
            score += 25  # Have food and need it!
        
        # No armor = vulnerable
        # (Would check armor here if available)
        
        return min(100, max(0, score))
    
    def decide(self, perception: Dict) -> Dict:
        """Heal and eat!"""
        health = perception.get('health', 20)
        food = perception.get('food', 20)
        inv = perception.get('inventory', {})
        
        # Eat if needed
        food_items = [item for item in inv.keys() 
                      if any(f in item for f in ['bread', 'beef', 'porkchop', 'apple'])]
        
        if food < 15 and food_items:
            return {
                'action': 'EAT',
                'priority': 'HIGH',
                'params': {},
                'reason': f'Must eat! Food at {food}/20'
            }
        
        if health < 20:
            return {
                'action': 'FLEE',
                'reason': f'Healing! HP: {health}/20',
                'priority': 'HIGH',
                'params': {'move_to': {'speed': 'walk'}}
            }
        
        return {
            'action': 'IDLE',
            'reason': 'HP perfect, monitoring health'
        }
