"""
Cautious Brain - Survival first, avoid danger
"""

from typing import Dict
from .brain_manager import Brain


class CautiousBrain(Brain):
    """Run away! Hide! Survive!"""
    
    def __init__(self):
        super().__init__("CautiousBrain", "🛡️")
    
    def vote(self, perception: Dict) -> int:
        """Vote higher when threatened or weak"""
        score = 30  # Base caution
        
        health = perception.get('health', 20)
        threats = [e for e in perception.get('nearby_entities', []) if e.get('hostile')]
        time = perception.get('time_of_day', 'day')
        
        # Low health = RUN!
        if health < 8:
            score += 60
        elif health < 15:
            score += 30
        
        # Threats nearby = DANGER!
        for threat in threats:
            distance = threat.get('distance', 999)
            if distance < 5:
                score += 40  # Very close!
            elif distance < 10:
                score += 20
            else:
                score += 5
        
        # Night is dangerous
        if time == 'Night':
            score += 25
        
        # Multiple threats = panic!
        if len(threats) > 2:
            score += 20
        
        return min(100, max(0, score))
    
    def decide(self, perception: Dict) -> Dict:
        """Flee to safety!"""
        health = perception.get('health', 20)
        threats = [e for e in perception.get('nearby_entities', []) if e.get('hostile')]
        
        if health < 10 or threats:
            return {
                'action': 'FLEE',
                'reason': 'Too dangerous! Running away!',
                'priority': 'HIGH',
                'params': {'move_to': {'speed': 'sprint'}}
            }
        
        # Safe? Hide anyway
        return {
            'action': 'FLEE',
            'reason': 'Being cautious, finding safe spot',
            'priority': 'MEDIUM',
            'params': {'move_to': {'speed': 'walk'}}
        }
