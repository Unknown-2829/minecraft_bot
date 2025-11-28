import json
import os

class KnowledgeManager:
    """
    Provides the bot with comprehensive knowledge about Minecraft.
    - Blocks
    - Items
    - Mobs
    - Structures
    - Recipes (Simplified)
    """
    def __init__(self, bot_version='1.21'):
        self.version = bot_version
        self.knowledge_base = {
            "blocks": {
                "valuable": ["diamond_ore", "gold_ore", "iron_ore", "coal_ore", "ancient_debris"],
                "wood": ["oak_log", "birch_log", "spruce_log", "jungle_log", "acacia_log", "dark_oak_log"],
                "stone": ["stone", "cobblestone", "deepslate", "granite", "diorite", "andesite"]
            },
            "mobs": {
                "hostile": ["zombie", "skeleton", "creeper", "spider", "enderman", "witch", "phantom"],
                "passive": ["cow", "sheep", "pig", "chicken", "villager", "horse"],
                "neutral": ["wolf", "bee", "iron_golem", "zombified_piglin"]
            },
            "food": {
                "high_saturation": ["golden_carrot", "steak", "cooked_porkchop"],
                "medium": ["bread", "cooked_chicken", "baked_potato"],
                "low": ["carrot", "potato", "sweet_berries"]
            },
            "structures": {
                "village": "Found in plains, savanna, taiga, desert. Good for food and beds.",
                "desert_temple": "Found in deserts. Has 4 chests at bottom. Watch out for TNT.",
                "stronghold": "Underground. Contains End Portal.",
                "fortress": "Nether. Contains Blaze Spawners and Nether Wart."
            }
        }

    def get_knowledge(self, category: str) -> dict:
        """Get knowledge by category"""
        return self.knowledge_base.get(category, {})

    def get_mob_info(self, mob_name: str) -> str:
        """Get info about a mob"""
        if mob_name in self.knowledge_base['mobs']['hostile']:
            return "Hostile. Attack or flee."
        elif mob_name in self.knowledge_base['mobs']['passive']:
            return "Passive. Good for food or farming."
        elif mob_name in self.knowledge_base['mobs']['neutral']:
            return "Neutral. Do not provoke."
        return "Unknown mob."

    def get_block_info(self, block_name: str) -> str:
        """Get info about a block"""
        if block_name in self.knowledge_base['blocks']['valuable']:
            return "Valuable resource. Mine with Iron Pickaxe or better."
        return "Common block."
