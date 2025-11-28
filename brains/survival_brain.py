"""
Survival Brain - Complete autonomous survival intelligence
Health, food, shelter, resource gathering, progression
NO external APIs - pure intelligent rules
"""

from typing import Dict, Optional
from .brain_manager import Brain

class SurvivalBrain(Brain):
    """Master survival intelligence"""
    
    def __init__(self, logger):
        super().__init__("SurvivalBrain", "🌲")
        self.logger = logger.getChild('Survival')
        self.progression_level = 0  # 0=naked, 1=wood, 2=stone, 3=iron, 4=diamond
    
    def vote(self, perception: Dict) -> int:
        """Vote based on survival needs"""
        score = 30 # Base survival instinct
        
        health = perception.get('health', 20)
        food = perception.get('food', 20)
        
        # Hungry?
        if food < 10:
            score += 40
        
        # Hurt?
        if health < 15:
            score += 20
            
        # Need basic tools?
        inv = perception.get('inventory', {})
        if not any('pickaxe' in item for item in inv.keys()):
            score += 20
            
        return min(100, max(0, score))

    def decide(self, perception: Dict) -> Dict:
        """Make survival decision"""
        
        # PRIORITY 1: Immediate danger
        danger = self._assess_danger(perception)
        if danger:
            return danger
        
        # PRIORITY 2: Health management
        health_action = self._manage_health(perception)
        if health_action:
            return health_action
        
        # PRIORITY 3: Food management
        food_action = self._manage_food(perception)
        if food_action:
            return food_action
        
        # PRIORITY 4: Shelter (if night)
        # Simplified: just hide if night and no shelter
        if perception.get('time_of_day') == 'Night':
             return {'action': 'FLEE', 'reason': 'Night time - hiding', 'priority': 'MEDIUM', 'params': {'move_to': {'speed': 'walk'}}}
        
        # PRIORITY 5: Progression
        progression_action = self._progress(perception)
        if progression_action:
            return progression_action
        
        # DEFAULT: Idle
        return {'action': 'IDLE', 'reason': 'Survival needs met', 'priority': 'LOW'}
    
    def _assess_danger(self, perception: Dict) -> Optional[Dict]:
        """Check for immediate dangers"""
        health = perception.get('health', 20)
        
        # Critical health
        if health <= 4:
            return {
                'action': 'FLEE', 
                'reason': 'CRITICAL health - immediate retreat!', 
                'priority': 'HIGH',
                'params': {'move_to': {'speed': 'sprint'}}
            }
        
        return None
    
    def _manage_health(self, perception: Dict) -> Optional[Dict]:
        """Manage health"""
        health = perception.get('health', 20)
        
        if health < 10:
            # Try to eat for regeneration
            if self._has_food(perception):
                return {
                    'action': 'EAT', 
                    'reason': f'Low health ({health}/20) - eating for regen',
                    'priority': 'HIGH',
                    'params': {}
                }
            # Find safe place to heal
            return {
                'action': 'FLEE', 
                'reason': 'Low health - finding safe place',
                'priority': 'HIGH',
                'params': {'move_to': {'speed': 'walk'}}
            }
        
        return None
    
    def _manage_food(self, perception: Dict) -> Optional[Dict]:
        """Manage food"""
        food = perception.get('food', 20)
        
        if food < 6:
            # Eat if we have food
            if self._has_food(perception):
                return {
                    'action': 'EAT', 
                    'reason': f'Hungry ({food}/20) - eating now',
                    'priority': 'HIGH',
                    'params': {}
                }
            
            # Look for food
            return {
                'action': 'IDLE', 
                'reason': 'Searching for food (not implemented)',
                'priority': 'MEDIUM'
            }
        
        return None
    
    def _progress(self, perception: Dict) -> Optional[Dict]:
        """Progress through tech tree"""
        inventory = perception.get('inventory', {})
        blocks = perception.get('nearby_blocks', [])
        
        # Level 0: Get wood
        if not self._has_wood(inventory):
            trees = [b for b in blocks if 'log' in b.get('name', '')]
            if trees:
                return {
                    'action': 'MINE', 
                    'reason': 'Getting wood for tools',
                    'priority': 'MEDIUM',
                    'params': {'dig': {'block_name': trees[0].get('name')}}
                }
            return None
        
        # Level 1: Make crafting table
        if not self._has_item(inventory, 'crafting_table'):
             return {
                'action': 'CRAFT', 
                'reason': 'Crafting basic workstation',
                'priority': 'MEDIUM',
                'params': {'craft': {'recipe': 'crafting_table'}}
            }
        
        # Level 2: Make wooden pickaxe
        if not self._has_pickaxe(inventory):
             return {
                'action': 'CRAFT', 
                'reason': 'Crafting first pickaxe',
                'priority': 'MEDIUM',
                'params': {'craft': {'recipe': 'wooden_pickaxe'}}
            }
        
        return None
    
    # Helper methods
    def _has_food(self, perception: Dict) -> bool:
        """Check for any food"""
        inventory = perception.get('inventory', {})
        food_items = ['bread', 'cooked_beef', 'cooked_porkchop', 'cooked_chicken', 
                      'apple', 'golden_apple', 'cooked_mutton', 'baked_potato']
        return any(food in inventory for food in food_items)
    
    def _has_wood(self, inventory: Dict) -> bool:
        """Check for wood"""
        wood_types = ['oak_log', 'birch_log', 'spruce_log', 'oak_planks', 'birch_planks']
        return any(wood in inventory for wood in wood_types)
    
    def _has_pickaxe(self, inventory: Dict) -> bool:
        """Check for any pickaxe"""
        return any('pickaxe' in item for item in inventory.keys())
    
    def _has_item(self, inventory: Dict, item_name: str, min_count: int = 1) -> bool:
        """Check for specific item with minimum count"""
        return inventory.get(item_name, 0) >= min_count
