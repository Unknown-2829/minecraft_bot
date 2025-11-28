"""
Strategic Brain - Smart, calculated, long-term planning
"""

from typing import Dict
from .brain_manager import Brain


class StrategicBrain(Brain):
    """Think ahead, plan progression, optimal decisions"""
    
    def __init__(self):
        super().__init__("StrategicBrain", "🧠")
    
    def vote(self, perception: Dict) -> int:
        """Vote higher when strategic thinking needed"""
        score = 50  # Base strategic value
        
        health = perception.get('health', 20)
        inv = perception.get('inventory', {})
        blocks = perception.get('nearby_blocks', [])
        dimension = perception.get('dimension', 'overworld')
        
        # Good health = can think strategically
        if health > 15:
            score += 20
        
        # Have resources = plan next steps
        if len(inv) > 5:
            score += 15
        
        # Valuable blocks nearby = strategic mining
        valuable = [b for b in blocks if any(ore in b.get('name', '') 
                    for ore in ['diamond', 'iron', 'gold'])]
        if valuable:
            score += 20
        
        # Progression opportunities
        if not any('pickaxe' in item for item in inv.keys()):
            score += 25  # Need tools = strategic crafting
        
        # Dimension-specific strategies
        if dimension == 'overworld' and not any('obsidian' in item for item in inv.keys()):
            score += 15  # Plan for nether
        
        return min(100, max(0, score))
    
    def decide(self, perception: Dict) -> Dict:
        """Make strategic long-term decision"""
        inv = perception.get('inventory', {})
        blocks = perception.get('nearby_blocks', [])
        
        # Progression priorities
        if not any('log' in item or 'plank' in item for item in inv.keys()):
            return {
                'action': 'MINE', 
                'priority': 'MEDIUM',
                'params': {'dig': {'block_name': 'tree'}},
                'reason': 'Strategic: Need wood for tools'
            }
        
        if not any('crafting_table' in item for item in inv.keys()):
            return {
                'action': 'CRAFT', 
                'priority': 'MEDIUM',
                'params': {'craft': {'recipe': 'crafting_table'}},
                'reason': 'Strategic: Need workbench'
            }
        
        if not any('pickaxe' in item for item in inv.keys()):
            return {
                'action': 'CRAFT', 
                'priority': 'MEDIUM',
                'params': {'craft': {'recipe': 'wooden_pickaxe'}},
                'reason': 'Strategic: Need mining tool'
            }
        
        # Mine valuable ores
        ores = [b for b in blocks if 'ore' in b.get('name', '')]
        if ores:
            best_ore = max(ores, key=lambda b: self._ore_value(b.get('name', '')))
            return {
                'action': 'MINE', 
                'priority': 'MEDIUM',
                'params': {'dig': {'block_name': best_ore.get('name')}},
                'reason': f"Strategic: Mine {best_ore.get('name')}"
            }
        
        # Explore for resources
        return {
            'action': 'IDLE', 
            'priority': 'LOW',
            'params': {},
            'reason': 'Strategic: Scouting for resources'
        }
    
    def _ore_value(self, name: str) -> int:
        """Rate ore value"""
        if 'diamond' in name:
            return 100
        if 'gold' in name or 'iron' in name:
            return 50
        if 'coal' in name:
            return 20
        return 10
