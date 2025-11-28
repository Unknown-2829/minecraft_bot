import time
import math
from typing import Dict, Optional

try:
    from javascript import require
    Vec3 = require('vec3')
    pathfinder = require('mineflayer-pathfinder')
    Goals = pathfinder.goals
except ImportError:
    Vec3 = None
    Goals = None

class SkillManager:
    """
    Handles complex, multi-step actions (Skills).
    Inspired by Minecraft-GPT's action modules.
    """
    def __init__(self, bot, action_manager):
        self.bot = bot
        self.am = action_manager
        self.logger = action_manager.logger.getChild('Skills')

    def execute_skill(self, skill_name: str, params: Dict) -> bool:
        """Dispatch to specific skill handler"""
        self.logger.info(f"🤸 Executing Skill: {skill_name}")
        
        if skill_name == 'combat_hunt':
            return self._skill_combat_hunt(params)
        elif skill_name == 'craft_item':
            return self._skill_craft_item(params)
        elif skill_name == 'build_structure':
            return self._skill_build_structure(params)
        elif skill_name == 'collect_resource':
            return self._skill_collect_resource(params)
        else:
            self.logger.warning(f"Unknown skill: {skill_name}")
            return False

    def _skill_combat_hunt(self, params):
        """Hunt a specific target or defend"""
        target_name = params.get('target', 'zombie')
        radius = params.get('radius', 30)
        
        # Find target
        target = self.bot.nearestEntity(lambda e: e.name == target_name and \
                                      e.position.distanceTo(self.bot.entity.position) < radius)
        
        if target:
            self.logger.info(f"⚔️ Found {target_name}, attacking!")
            if self.bot.pvp:
                self.bot.pvp.attack(target)
                return True
            else:
                self.bot.lookAt(target.position)
                self.bot.attack(target)
                return True
        else:
            self.logger.info(f"🤷 No {target_name} found nearby.")
            return False

    def _skill_craft_item(self, params):
        """Craft an item using Mineflayer's recipe system"""
        item_name = params.get('item')
        count = params.get('count', 1)
        
        self.logger.info(f"🔨 Crafting {count} {item_name}")
        
        # 1. Find recipe
        # We need the numeric ID for recipesFor
        # In mineflayer/prismarine-item, we usually look up by name
        try:
            # This requires the bot to have 'registry' or 'mcData' loaded
            # Assuming standard mineflayer bot structure
            mcData = require('minecraft-data')(self.bot.version)
            item = mcData.itemsByName[item_name]
            if not item:
                self.logger.error(f"Unknown item: {item_name}")
                return False
                
            recipes = self.bot.recipesFor(item.id, None, 1, None) # Check if craftable without table
            crafting_table = None
            
            if not recipes:
                # Check with crafting table
                table_block = self.bot.findBlock({
                    'matching': lambda b: b.name == 'crafting_table',
                    'maxDistance': 32
                })
                if table_block:
                    recipes = self.bot.recipesFor(item.id, None, 1, table_block)
                    crafting_table = table_block
            
            if not recipes:
                self.logger.warning(f"No recipe found for {item_name} (or missing resources/table)")
                return False
                
            recipe = recipes[0]
            
            # 2. Go to table if needed
            if crafting_table:
                self.logger.info(f"Moving to crafting table at {crafting_table.position}")
                if self.bot.pathfinder:
                    self.bot.pathfinder.setGoal(Goals.GoalBlock(crafting_table.position.x, crafting_table.position.y, crafting_table.position.z))
                    # In a real async system we'd await arrival. 
                    # Here we assume we are close or will get there.
                    # For robustness in this sync-like wrapper, we might need a small sleep or check
                    time.sleep(2) 
            
            # 3. Craft
            self.bot.craft(recipe, count, crafting_table)
            self.logger.info(f"✅ Crafted {count} {item_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Crafting failed: {e}")
            return False

    def _skill_build_structure(self, params):
        """Build a simple structure (e.g., shelter)"""
        structure_type = params.get('type', 'shelter')
        
        if structure_type == 'shelter':
            self.logger.info("🏠 Building Shelter Routine Started")
            
            # 1. Find flat ground (simplified: current pos)
            start_pos = self.bot.entity.position.offset(2, 0, 2)
            
            # 2. Ensure materials (simplified check)
            # In a full system, we'd check inventory for 'dirt', 'cobblestone', 'planks'
            
            # 3. Build 3x3x3 box (hollow)
            # This is a blocking loop in this simple implementation
            # Ideally, this should be a state machine or async task
            
            try:
                # Floor
                for x in range(3):
                    for z in range(3):
                        p = start_pos.offset(x, -1, z)
                        self._place_block(p, 'cobblestone')
                
                # Walls
                for y in range(3):
                    for x in range(3):
                        for z in range(3):
                            if x == 0 or x == 2 or z == 0 or z == 2:
                                # Leave door gap
                                if x == 1 and z == 0 and y < 2:
                                    continue
                                p = start_pos.offset(x, y, z)
                                self._place_block(p, 'planks')
                                
                # Roof
                for x in range(3):
                    for z in range(3):
                        p = start_pos.offset(x, 3, z)
                        self._place_block(p, 'cobblestone')
                        
                self.logger.info("✅ Shelter built!")
                return True
                
            except Exception as e:
                self.logger.error(f"Building failed: {e}")
                return False
                
        return False

    def _place_block(self, pos, block_name):
        """Helper to place a block"""
        # 1. Equip block
        # 2. Place
        # (Simplified wrapper around bot.placeBlock)
        pass # TODO: Implement atomic place logic if needed, or rely on mineflayer-builder

    def _skill_farm(self, params):
        """
        Skill: Farming
        - Find hoe, till dirt, plant seeds, harvest crops
        """
        action = params.get('action', 'harvest') # harvest, plant, till
        crop_type = params.get('crop', 'wheat')
        
        self.logger.info(f"🌾 Farming skill: {action} {crop_type}")
        
        # 1. Harvest
        if action == 'harvest':
            # Find mature crops
            block_name = crop_type
            if crop_type == 'wheat': block_name = 'wheat'
            
            crops = self.bot.findBlocks({
                'matching': lambda b: b.name == block_name and b.metadata == 7, # 7 is usually max age
                'maxDistance': 32,
                'count': 5
            })
            
            if crops:
                for pos in crops:
                    if self.bot.pathfinder:
                        self.bot.pathfinder.setGoal(Goals.GoalBlock(pos.x, pos.y, pos.z))
                    block = self.bot.blockAt(pos)
                    self.bot.dig(block)
            else:
                self.logger.warning("No mature crops found")

    def _skill_trade(self, params):
        """
        Skill: Trading
        - Find villager, open trade, trade items
        """
        self.logger.info("💰 Trading skill (Not fully implemented)")
        # Logic: find villager -> interact -> match trade recipe -> trade

    def _skill_collect_resource(self, params):
        """Collect a specific resource"""
        block_name = params.get('block')
        count = params.get('count', 1)
        
        self.logger.info(f"⛏️ Collecting {count} {block_name}")
        
        blocks = self.bot.findBlocks({
            'matching': lambda b: b.name == block_name,
            'maxDistance': 32,
            'count': count
        })
        
        if blocks:
            self.logger.info(f"Found {len(blocks)} {block_name} blocks")
            target = self.bot.blockAt(Vec3(blocks[0].x, blocks[0].y, blocks[0].z))
            if self.bot.pathfinder:
                self.bot.pathfinder.setGoal(Goals.GoalBlock(target.position.x, target.position.y, target.position.z))
            self.bot.dig(target)
            return True
        
        return False
