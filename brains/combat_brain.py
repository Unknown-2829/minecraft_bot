"""
Combat Brain - PvP and mob fighting intelligence
Tactics, dodging, combos, weapon selection
"""

from typing import Dict, Optional
from .brain_manager import Brain

class CombatBrain(Brain):
    """Master combat intelligence"""
    
    def __init__(self, logger):
        super().__init__("CombatBrain", "⚔️")
        self.logger = logger.getChild('Combat')
        self.last_target = None
        self.combo_count = 0
    
    def vote(self, perception: Dict) -> int:
        """Vote based on threats and health"""
        # Similar logic to AggressiveBrain but maybe more tactical
        score = 0
        health = perception.get('health', 20)
        threats = [e for e in perception.get('nearby_entities', []) if e.get('hostile')]
        
        if threats:
            score += 40
            # If we are healthy, we want to fight
            if health > 10:
                score += 20
            # If we are low health, we might still want to fight if cornered, but CautiousBrain should take over for fleeing
            
        return min(100, max(0, score))

    def decide(self, perception: Dict) -> Dict:
        """Make combat decision"""
        
        health = perception.get('health', 20)
        threats = self._get_threats(perception)
        
        if not threats:
            return {'action': 'IDLE', 'reason': 'No threats found', 'priority': 'LOW'}
        
        # Choose combat strategy based on health
        if health < 6:
            return {
                'action': 'FLEE', 
                'reason': 'Too low health for combat',
                'priority': 'HIGH',
                'params': {'move_to': {'speed': 'sprint'}}
            }
        
        nearest_threat = threats[0]
        threat_distance = nearest_threat.get('distance', 999)
        threat_type = nearest_threat.get('type', 'mob').lower()
        
        # Special tactics per mob type
        if 'creeper' in threat_type:
            return self._fight_creeper(nearest_threat, threat_distance, health)
        elif 'skeleton' in threat_type:
            return self._fight_skeleton(nearest_threat, threat_distance, health)
        elif 'zombie' in threat_type:
            return self._fight_zombie(nearest_threat, threat_distance, health)
        elif 'enderman' in threat_type:
            return self._fight_enderman(nearest_threat, threat_distance, health)
        elif 'spider' in threat_type:
            return self._fight_spider(nearest_threat, threat_distance, health)
        else:
            # Generic combat
            return self._generic_combat(nearest_threat, threat_distance, health)
    
    def _fight_creeper(self, creeper: Dict, distance: float, health: int) -> Dict:
        """Creeper: Hit and retreat (prevent explosion)"""
        if distance < 3:
            return {
                'action': 'FLEE', 
                'reason': 'Creeper too close - avoiding explosion!',
                'priority': 'HIGH',
                'params': {'move_to': {'speed': 'sprint'}}
            }
        elif distance < 6:
            return {
                'action': 'COMBAT', 
                'reason': 'Hit creeper and retreat',
                'priority': 'HIGH',
                'params': {'interact': {'type': 'attack', 'target_entity_id': creeper.get('id')}}
            }
        else:
            return {
                'action': 'MOVE', 
                'reason': 'Moving closer to creeper',
                'priority': 'MEDIUM',
                'params': {'move_to': {'x': creeper['position']['x'], 'y': creeper['position']['y'], 'z': creeper['position']['z'], 'speed': 'sprint'}}
            }
    
    def _fight_skeleton(self, skeleton: Dict, distance: float, health: int) -> Dict:
        """Skeleton: Dodge arrows, close distance, strafe"""
        # Simplified for now
        if distance > 3:
             return {
                'action': 'MOVE', 
                'reason': 'Closing distance to skeleton',
                'priority': 'HIGH',
                'params': {'move_to': {'x': skeleton['position']['x'], 'y': skeleton['position']['y'], 'z': skeleton['position']['z'], 'speed': 'sprint'}}
            }
        else:
            return {
                'action': 'COMBAT', 
                'reason': 'Attacking skeleton',
                'priority': 'HIGH',
                'params': {'interact': {'type': 'attack', 'target_entity_id': skeleton.get('id')}}
            }
    
    def _fight_zombie(self, zombie: Dict, distance: float, health: int) -> Dict:
        """Zombie: Direct combat with criticals"""
        if distance > 3:
            return {
                'action': 'MOVE', 
                'reason': 'Moving to zombie',
                'priority': 'MEDIUM',
                'params': {'move_to': {'x': zombie['position']['x'], 'y': zombie['position']['y'], 'z': zombie['position']['z'], 'speed': 'sprint'}}
            }
        else:
            return {
                'action': 'COMBAT', 
                'reason': 'Attacking zombie',
                'priority': 'HIGH',
                'params': {'interact': {'type': 'attack', 'target_entity_id': zombie.get('id')}}
            }
    
    def _fight_enderman(self, enderman: Dict, distance: float, health: int) -> Dict:
        """Enderman: Water trap or avoid eye contact"""
        # Simplified
        return {
            'action': 'FLEE', 
            'reason': 'Avoiding enderman (too dangerous)',
            'priority': 'HIGH',
            'params': {'move_to': {'speed': 'sprint'}}
        }
    
    def _fight_spider(self, spider: Dict, distance: float, health: int) -> Dict:
        """Spider: High ground advantage"""
        return {
            'action': 'COMBAT', 
            'reason': 'Attacking spider',
            'priority': 'HIGH',
            'params': {'interact': {'type': 'attack', 'target_entity_id': spider.get('id')}}
        }
    
    def _generic_combat(self, threat: Dict, distance: float, health: int) -> Dict:
        """Generic combat logic"""
        if distance > 3:
            return {
                'action': 'MOVE', 
                'reason': 'Closing for melee',
                'priority': 'MEDIUM',
                'params': {'move_to': {'x': threat['position']['x'], 'y': threat['position']['y'], 'z': threat['position']['z'], 'speed': 'sprint'}}
            }
        else:
            return {
                'action': 'COMBAT', 
                'reason': 'Melee attack',
                'priority': 'HIGH',
                'params': {'interact': {'type': 'attack', 'target_entity_id': threat.get('id')}}
            }
    
    # Helper methods
    def _get_threats(self, perception: Dict) -> list:
        """Get all hostile entities, sorted by distance"""
        entities = perception.get('nearby_entities', [])
        threats = [e for e in entities if e.get('hostile', False)]
        return sorted(threats, key=lambda e: e.get('distance', 999))
