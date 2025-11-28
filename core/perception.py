"""
Enhanced Perception System
Complete awareness of game state, resources, threats, and opportunities
"""

from typing import Dict, List, Optional, Any
import logging



from core.event_bus import EventBus

class EnhancedPerception:
    """Complete game state awareness system"""
    
    def __init__(self, bot, logger: logging.Logger):
        self.bot = bot
        self.logger = logger.getChild('Perception')
        self.event_bus = EventBus()
        self.last_scan = {}
        self.last_health = 20
        self.last_food = 20
    
    def get_complete_state(self) -> Dict:
        """Gather comprehensive perception data"""
        try:
            if not self.bot or not hasattr(self.bot, 'entity'):
                return self._get_minimal_state()
            
            # Check for changes and emit events
            current_health = getattr(self.bot, 'health', 20)
            if current_health < self.last_health:
                self.event_bus.emit('health_damage', {'old': self.last_health, 'new': current_health})
            self.last_health = current_health
            
            current_food = getattr(self.bot, 'food', 20)
            if current_food < self.last_food:
                self.event_bus.emit('food_decrease', {'old': self.last_food, 'new': current_food})
            self.last_food = current_food

            state = {
                # Core vitals
                'health': current_health,
                'food': current_food,
                
                # Position and environment
                'position': self._get_position(),
                'dimension': self._get_dimension(),
                'biome': self._get_biome(),
                'weather': self._get_weather(),
                'time': self._get_time(),
                'gamemode': self._get_gamemode(),
                'effects': self._get_effects(),
                
                # Inventory and equipment
                'inventory': self._get_inventory(),
                'equipped': self._get_equipped(),
                
                # Surroundings
                'nearby_entities': self._scan_entities(),
                'nearby_players': self._scan_players(),
                'nearby_blocks': self._scan_blocks(),
                
                # Social
                'recent_chat': self._get_recent_chat(),
                
                # Analysis
                'threat_level': self._assess_threat_level(),
                'resource_priority': self._assess_resources(),
                'craftable_items': self._get_craftable_items(),
            }
            
            self.last_scan = state
            return state
            
        except Exception as e:
            self.logger.error(f"Error getting perception: {e}")
            return self._get_minimal_state()
    
    def _get_minimal_state(self) -> Dict:
        """Minimal state when bot not ready"""
        return {
            'health': 20,
            'food': 20,
            'position': {'x': 0, 'y': 0, 'z': 0},
            'dimension': 'overworld',
            'time_of_day': 'day',
            'gamemode': 'survival',
            'inventory': {},
            'equipped': None,
            'nearby_entities': [],
            'nearby_players': [],
            'nearby_blocks': [],
            'recent_chat': '',
            'threat_level': 'SAFE',
            'resource_priority': 'EXPLORE'
        }
    
    def _get_position(self) -> Dict:
        """Get current position"""
        try:
            pos = self.bot.entity.position
            return {
                'x': float(pos.x),
                'y': float(pos.y),
                'z': float(pos.z)
            }
        except:
            return {'x': 0, 'y': 0, 'z': 0}
    
    def _get_dimension(self) -> str:
        """Get current dimension"""
        try:
            return str(self.bot.game.dimension).replace('minecraft:', '')
        except:
            return 'overworld'
            
    def _get_biome(self) -> str:
        """Get current biome"""
        try:
            # Mineflayer exposes biome info via blockAt or specialized calls
            # This is a simplified lookup based on position
            pos = self.bot.entity.position
            block = self.bot.blockAt(pos)
            if block and hasattr(block, 'biome'):
                return str(block.biome.name)
            return 'unknown'
        except:
            return 'unknown'

    def _get_weather(self) -> Dict:
        """Get weather state"""
        try:
            return {
                'raining': getattr(self.bot, 'isRaining', False),
                'thundering': getattr(self.bot, 'thunderState', 0) > 0
            }
        except:
            return {'raining': False, 'thundering': False}
    
    def _get_time(self) -> Dict:
        """Get detailed time"""
        try:
            time = self.bot.time.timeOfDay
            return {
                'time_of_day': time,
                'is_day': time < 13000 or time > 23000,
                'phase': self._get_time_phase(time)
            }
        except:
            return {'time_of_day': 0, 'is_day': True, 'phase': 'Day'}

    def _get_time_phase(self, time: int) -> str:
        if time < 6000: return 'Morning'
        elif time < 12000: return 'Noon'
        elif time < 13000: return 'Sunset'
        elif time < 18000: return 'Night'
        elif time < 23000: return 'Midnight'
        else: return 'Sunrise'
    
    def _get_gamemode(self) -> str:
        """Get gamemode"""
        try:
            return str(self.bot.game.gameMode)
        except:
            return 'survival'

    def _get_effects(self) -> List[Dict]:
        """Get active potion effects"""
        try:
            effects = []
            if hasattr(self.bot.entity, 'effects'):
                # Mineflayer effects are stored by ID
                # We need to map them to names if possible, or just return IDs
                # For now, returning raw list
                for effect_id in self.bot.entity.effects:
                    effect = self.bot.entity.effects[effect_id]
                    effects.append({
                        'id': effect_id,
                        'amplifier': effect.amplifier,
                        'duration': effect.duration
                    })
            return effects
        except:
            return []
    
    def _get_inventory(self) -> Dict:
        """Get inventory items"""
        try:
            inventory = {}
            if hasattr(self.bot, 'inventory') and hasattr(self.bot.inventory, 'items'):
                for item in self.bot.inventory.items():
                    name = item.name if hasattr(item, 'name') else str(item)
                    count = item.count if hasattr(item, 'count') else 1
                    inventory[name] = inventory.get(name, 0) + count
            return inventory
        except:
            return {}
    
    def _get_equipped(self) -> Optional[str]:
        """Get equipped item"""
        try:
            held = self.bot.heldItem
            return held.name if held else None
        except:
            return None
    
    def _scan_entities(self) -> List[Dict]:
        """Scan nearby entities"""
        try:
            entities = []
            if not hasattr(self.bot, 'entities'):
                return []
            
            bot_pos = self.bot.entity.position
            hostile_types = ['zombie', 'skeleton', 'creeper', 'spider', 'enderman', 'witch']
            
            for entity in Object.values(self.bot.entities):
                if entity.type == 'mob' and entity.position:
                    distance = bot_pos.distanceTo(entity.position)
                    if distance < 32:  # 32 block range
                        is_hostile = any(h in (entity.name or '').lower() for h in hostile_types)
                        entities.append({
                            'type': entity.name or 'unknown',
                            'distance': float(distance),
                            'hostile': is_hostile,
                            'position': {
                                'x': float(entity.position.x),
                                'y': float(entity.position.y),
                                'z': float(entity.position.z)
                            }
                        })
            
            # Emit threat event if new hostile found close
            # (Simplified: just emit if any hostile < 10 blocks)
            close_threats = [e for e in entities if e['hostile'] and e['distance'] < 10]
            if close_threats:
                self.event_bus.emit('threat_detected', close_threats)

            return sorted(entities, key=lambda e: e['distance'])
        except:
            return []
    
    def _scan_players(self) -> List[str]:
        """Scan nearby players"""
        try:
            players = []
            if hasattr(self.bot, 'players'):
                for username in Object.keys(self.bot.players):
                    if username != self.bot.username:
                        players.append(str(username))
            
            if players:
                self.event_bus.emit('player_detected', players)
                
            return players
        except:
            return []
    
    def _scan_blocks(self) -> List[Dict]:
        """Scan nearby valuable blocks"""
        try:
            blocks = []
            if not hasattr(self.bot, 'findBlocks'):
                return []
            
            valuable_blocks = [
                'coal_ore', 'iron_ore', 'gold_ore', 'diamond_ore', 'emerald_ore',
                'oak_log', 'birch_log', 'spruce_log',
                'chest', 'crafting_table', 'furnace'
            ]
            
            bot_pos = self.bot.entity.position
            max_distance = 16
            
            for block_name in valuable_blocks:
                try:
                    found = self.bot.findBlocks({
                        'matching': block_name,
                        'maxDistance': max_distance,
                        'count': 5
                    })
                    
                    for block_pos in found:
                        distance = bot_pos.distanceTo(block_pos)
                        blocks.append({
                            'name': block_name,
                            'distance': float(distance),
                            'position': {
                                'x': float(block_pos.x),
                                'y': float(block_pos.y),
                                'z': float(block_pos.z)
                            }
                        })
                except:
                    continue
            
            return sorted(blocks, key=lambda b: b['distance'])[:10]
        except:
            return []
    
    def _get_recent_chat(self) -> str:
        """Get recent chat messages (from memory)"""
        # This would be populated by chat event handler
        return getattr(self, '_last_chat_message', '')
    
    def set_last_chat(self, message: str):
        """Store last chat message"""
        self._last_chat_message = message
        self.event_bus.emit('chat_received', message)
    
    def _assess_threat_level(self) -> str:
        """Assess overall threat level"""
        health = getattr(self.bot, 'health', 20)
        entities = self.last_scan.get('nearby_entities', [])
        
        if health < 6:
            return 'CRITICAL'
        
        hostile_nearby = [e for e in entities if e.get('hostile') and e.get('distance', 999) < 8]
        if hostile_nearby:
            return 'HIGH'
        
        if health < 12:
            return 'MEDIUM'
        
        return 'SAFE'
    
    def _assess_resources(self) -> str:
        """Assess resource gathering priority"""
        inventory = self.last_scan.get('inventory', {})
        
        # Check for tools
        has_pickaxe = any('pickaxe' in item.lower() for item in inventory.keys())
        has_sword = any('sword' in item.lower() for item in inventory.keys())
        
        if not has_pickaxe:
            return 'CRAFT_TOOLS'
        elif not has_sword:
            return 'CRAFT_WEAPONS'
        else:
            return 'MINE_RESOURCES'

    def _get_craftable_items(self) -> List[str]:
        """Determine what can be crafted with current inventory"""
        # This is a simplified check. In a real scenario, we'd query the bot's recipe book.
        # Since we can't easily access the full recipe graph synchronously here without lag,
        # we'll do a heuristic check for common items.
        
        inventory = self.last_scan.get('inventory', {})
        craftable = []
        
        # Wood basics
        logs = sum(count for name, count in inventory.items() if 'log' in name)
        planks = sum(count for name, count in inventory.items() if 'plank' in name)
        sticks = inventory.get('stick', 0)
        cobble = inventory.get('cobblestone', 0)
        iron = inventory.get('iron_ingot', 0)
        
        if logs > 0: craftable.append('planks')
        if planks >= 2: craftable.append('stick')
        if planks >= 4: craftable.append('crafting_table')
        
        # Tools (Wood)
        if planks >= 3 and sticks >= 2: craftable.append('wooden_pickaxe')
        if planks >= 2 and sticks >= 1: craftable.append('wooden_sword')
        
        # Tools (Stone)
        if cobble >= 3 and sticks >= 2: craftable.append('stone_pickaxe')
        if cobble >= 2 and sticks >= 1: craftable.append('stone_sword')
        if cobble >= 8: craftable.append('furnace')
        
        # Tools (Iron)
        if iron >= 3 and sticks >= 2: craftable.append('iron_pickaxe')
        
        return craftable

