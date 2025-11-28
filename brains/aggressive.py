"""
Aggressive Brain - Loves combat and taking risks
"""

from typing import Dict
from .brain_manager import Brain


class AggressiveBrain(Brain):
    """Fight everything! Take risks! ATTACK!"""
    
    def __init__(self):
        super().__init__("AggressiveBrain", "🔥")
    
    def vote(self, perception: Dict) -> int:
        """Vote higher when strong and enemies nearby"""
        score = 40  # Base aggression
        
        health = perception.get('health', 20)
        food = perception.get('food', 20)
        inv = perception.get('inventory', {})
        threats = [e for e in perception.get('nearby_entities', []) if e.get('hostile')]
        
        # Strong = more aggressive
        if health > 15:
            score += 30
        elif health < 8:
            score -= 20  # Too weak
        
        # Well-fed = aggressive
        if food > 15:
            score += 10
        
        # Have weapons = FIGHT!
        if any('sword' in item for item in inv.keys()):
            score += 30
        if any('diamond' in item for item in inv.keys()):
            score += 20
        
        # Enemies nearby = exciting!
        score += len(threats) * 15
        
        # Night = more enemies = fun!
        if perception.get('time_of_day') == 'Night':
            score += 10
        
        return min(100, max(0, score))
    
    def decide(self, perception: Dict) -> Dict:
        """Attack nearest enemy aggressively!"""
        threats = [e for e in perception.get('nearby_entities', []) if e.get('hostile')]
        
        if threats:
            nearest = min(threats, key=lambda e: e['distance'])
            return {
                'action': 'COMBAT',
                'priority': 'HIGH',
                'params': {'interact': {'type': 'attack', 'target_entity_id': nearest.get('id')}},
                'reason': f"ATTACK {nearest['type']}! No fear!"
            }
        
        # No enemies? Explore for fights!
        return {
            'action': 'IDLE',
            'priority': 'LOW',
            'params': {},
            'reason': 'Looking for combat!'
        }
