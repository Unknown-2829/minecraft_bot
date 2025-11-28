#!/usr/bin/env python3
"""
🤖 AUTONOMOUS MINECRAFT BOT - Advanced Version
Run with: python bot.py

Features:
- Advanced brain system (brain/ folder)
- Enhanced perception (core/ folder)
- Complete survival progression (wood → diamond)
- Tactical combat system (mob-specific strategies)
- All configuration in settings.json
- Full logging system

Author: AI-Powered Bot System
"""

import json
import time
import threading
import sys
import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict, List, Optional

# Fix Windows Unicode console output
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Check for Node.js bridge
try:
    from javascript import require
    HAS_NODE = True
except ImportError:
    HAS_NODE = False

# Import multi-brain competition system
from brains import (BrainManager, AggressiveBrain, CautiousBrain, 
                     HealthBrain, StrategicBrain, CombatBrain, SurvivalBrain)
from core.perception import EnhancedPerception

from core.action_manager import ActionManager

# ==================== CONFIGURATION ====================
class ConfigManager:
    """Manages settings from settings.json"""
    
    DEFAULT_CONFIG = {
        "bot": {
            "default_server": "my_server",
            "ai_decision_interval": 3,
            "auto_reconnect": True
        },
        "servers": {
            "my_server": {
                "name": "My Minecraft Server",
                "host": "doxy_play.aternos.me",
                "port": 33739,
                "version": "1.21",
                "username": "AIBot",
                "auth": "offline",
                "enabled": True
            }
        },
        "logging": {
            "level": "INFO",
            "console_level": "INFO",
            "log_dir": "logs",
            "colorize_console": True
        },
        "llm": {
            "enabled": True,
            "provider": "groq",
            "api_key": "YOUR_API_KEY_HERE",
            "model": "llama-3.1-70b-versatile",
            "system_prompt_path": "brains/prompts/system.txt"
        }
    }
    
    def __init__(self, config_path: str = "settings.json"):
        self.config_path = Path(config_path)
        self.config = None
    
    def load(self) -> Dict:
        """Load settings or create default"""
        if not self.config_path.exists():
            print(f"📝 Creating {self.config_path}")
            self.config = self.DEFAULT_CONFIG.copy()
            self.save()
        else:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            print(f"✅ Loaded {self.config_path}")
        
        return self.config
    
    def save(self):
        """Save settings"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)
    
    def get(self, path: str, default=None):
        """Get setting by path (e.g., 'bot.ai_decision_interval')"""
        keys = path.split('.')
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def get_server(self, name: str) -> Optional[Dict]:
        """Get server config"""
        return self.config.get('servers', {}).get(name)


# ==================== LOGGING ====================
class LogManager:
    """Colored logging to console and files"""
    
    Colors = {'INFO': '\033[32m', 'WARNING': '\033[33m', 'ERROR': '\033[31m', 'RESET': '\033[0m'}
    
    def __init__(self, config: Dict):
        self.config = config
        self.log_dir = Path(config.get('log_dir', 'logs'))
        self.log_dir.mkdir(exist_ok=True)
    
    def setup(self) -> logging.Logger:
        """Setup logging"""
        logger = logging.getLogger('Bot')
        logger.setLevel(logging.DEBUG)
        logger.handlers.clear()
        
        # Console
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(logging.INFO)
        if self.config.get('colorize_console'):
            console.setFormatter(self.ColoredFormatter())
        logger.addHandler(console)
        
        # File
        file_handler = RotatingFileHandler(
            self.log_dir / 'bot.log',
            maxBytes=10485760,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
        
        return logger
    
    class ColoredFormatter(logging.Formatter):
        def format(self, record):
            level = record.levelname
            if level in LogManager.Colors:
                record.levelname = f"{LogManager.Colors[level]}{level}{LogManager.Colors['RESET']}"
            return super().format(record)



# ==================== MAIN BOT ====================
class MinecraftBot:
    """Main bot controller"""
    
    def __init__(self, config: ConfigManager, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.bot = None
        self.connected = False
        self.running = True
        
        self.action_manager = None # Will be created after connection
    
    def connect(self, server_name: str) -> bool:
        """Connect to server"""
        server = self.config.get_server(server_name)
        if not server:
            self.logger.error(f"Server '{server_name}' not found")
            return False
        
        self.logger.info(f"📡 Connecting to {server['name']}")
        self.logger.info(f"   {server['host']}:{server['port']}")

        # Reset ActionManager to ensure it uses the new bot instance
        if self.action_manager:
            self.logger.info("♻️ Resetting ActionManager for new connection...")
            self.action_manager.stop()
            self.action_manager = None
        
        if not HAS_NODE:
            self.logger.error("❌ Install: pip install javascript")
            self.logger.error("❌ Install: npm install mineflayer mineflayer-pathfinder")
            return False
        
        try:
            mineflayer = require('mineflayer')
            
            self.bot = mineflayer.createBot({
                'host': server['host'],
                'port': server['port'],
                'username': server['username'],
                'version': server.get('version', False)  # False = auto-detect
            })
            
            self._setup_handlers()
            return True
        except Exception as e:
            self.logger.error(f"❌ Connection failed: {e}")
            return False
    
    def _setup_handlers(self):
        """Setup event handlers"""
        def on_login(*args):
            self.logger.info(f"✅ Logged in to {self.bot.game.dimension}")
            self.connected = True
        
        def on_spawn(*args):
            pos = self.bot.entity.position
            self.logger.info(f"✅ Spawned at ({pos.x:.0f}, {pos.y:.0f}, {pos.z:.0f})")
            self._start_ai()
        
        def on_chat(*args):
            # Chat is now handled by ActionManager via EventBus (or directly if we wanted)
            # But we still log it here for debugging or if ActionManager isn't ready
            if len(args) >= 2:
                username, msg = args[0], args[1]
                self.logger.info(f"💬 <{username}> {msg}")
        
        def on_death(*args):
            self.logger.warning("💀 Died! Respawning...")
        
        self.bot.on('login', on_login)
        self.bot.on('spawn', on_spawn)
        self.bot.on('chat', on_chat)
        self.bot.on('death', on_death)
    
    def _start_ai(self):
        """Start AI decision loop with ActionManager as leader"""
        if self.action_manager:
            return # Already started
            
        self.logger.info("🧠 Initializing ActionManager (The Brain)...")
        self.action_manager = ActionManager(self.bot, self.logger)
        
        # Register Brains
        from brains import AggressiveBrain, CautiousBrain, HealthBrain, StrategicBrain, CombatBrain, SurvivalBrain
        from brains.llm_brain import LLMBrain
        
        bm = self.action_manager.brain_manager
        bm.register_brain(AggressiveBrain())
        bm.register_brain(CautiousBrain())
        bm.register_brain(HealthBrain())
        bm.register_brain(StrategicBrain())
        bm.register_brain(CombatBrain(self.logger))
        bm.register_brain(SurvivalBrain(self.logger))
        
        # Register LLM Brain
        llm_apis = []
        ai_apis_config = self.config.get('ai_apis', {})
        
        # Convert settings.json format to LLMBrain format
        for key, api_conf in ai_apis_config.items():
            if isinstance(api_conf, dict) and api_conf.get('enabled'):
                api_entry = {
                    'id': key,
                    'type': api_conf.get('type', 'openai_compatible'),
                    'name': api_conf.get('name', key),
                    'api_key': api_conf.get('api_key'),
                    'endpoint': api_conf.get('endpoint'),
                    'model': api_conf.get('model'),
                    'priority': api_conf.get('priority', 999),
                    'timeout': api_conf.get('timeout', 15),
                    'max_tokens': api_conf.get('max_tokens', 150)
                }
                llm_apis.append(api_entry)
        
        if llm_apis:
            self.logger.info(f"🧠 LLM Brain enabled with {len(llm_apis)} providers")
        else:
            self.logger.warning("⚠️ LLM Brain has no enabled providers in settings.json")

        llm_brain = LLMBrain(llm_apis, self.logger)
        llm_brain.set_knowledge(self.action_manager.knowledge)
        bm.register_brain(llm_brain)
        
        self.action_manager.start()
    
    def stop(self):
        """Stop bot"""
        self.running = False
        if self.action_manager:
            self.action_manager.stop()
        if self.bot:
            self.bot.quit()
        self.logger.info("👋 Bot stopped")


# ==================== MAIN ====================
def main():
    print("=" * 70)
    print("🤖 AUTONOMOUS MINECRAFT BOT")
    print("   ActionManager Leader | Event-Driven | Multi-Brain")
    print("=" * 70)
    
    # Load config
    config = ConfigManager()
    settings = config.load()
    
    # Setup logging
    log_mgr = LogManager(settings['logging'])
    logger = log_mgr.setup()
    
    logger.info("🧠 System initializing...")
    
    # Create bot
    bot = MinecraftBot(config, logger)


# ==================== LOGGING ====================
class LogManager:
    """Colored logging to console and files"""
    
    Colors = {'INFO': '\033[32m', 'WARNING': '\033[33m', 'ERROR': '\033[31m', 'RESET': '\033[0m'}
    
    def __init__(self, config: Dict):
        self.config = config
        self.log_dir = Path(config.get('log_dir', 'logs'))
        self.log_dir.mkdir(exist_ok=True)
    
    def setup(self) -> logging.Logger:
        """Setup logging"""
        logger = logging.getLogger('Bot')
        logger.setLevel(logging.DEBUG)
        logger.handlers.clear()
        
        # Console
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(logging.INFO)
        if self.config.get('colorize_console'):
            console.setFormatter(self.ColoredFormatter())
        logger.addHandler(console)
        
        # File
        file_handler = RotatingFileHandler(
            self.log_dir / 'bot.log',
            maxBytes=10485760,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
        
        return logger
    
    class ColoredFormatter(logging.Formatter):
        def format(self, record):
            level = record.levelname
            if level in LogManager.Colors:
                record.levelname = f"{LogManager.Colors[level]}{level}{LogManager.Colors['RESET']}"
            return super().format(record)



# ==================== MAIN BOT ====================
class MinecraftBot:
    """Main bot controller"""
    
    def __init__(self, config: ConfigManager, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.bot = None
        self.connected = False
        self.running = True
        
        self.action_manager = None # Will be created after connection
    
    def connect(self, server_name: str) -> bool:
        """Connect to server"""
        server = self.config.get_server(server_name)
        if not server:
            self.logger.error(f"Server '{server_name}' not found")
            return False
        
        self.logger.info(f"📡 Connecting to {server['name']}")
        self.logger.info(f"   {server['host']}:{server['port']}")
        
        if not HAS_NODE:
            self.logger.error("❌ Install: pip install javascript")
            self.logger.error("❌ Install: npm install mineflayer mineflayer-pathfinder")
            return False
        
        try:
            mineflayer = require('mineflayer')
            
            self.bot = mineflayer.createBot({
                'host': server['host'],
                'port': server['port'],
                'username': server['username'],
                'version': server.get('version', False)  # False = auto-detect
            })
            
            self._setup_handlers()
            return True
        except Exception as e:
            self.logger.error(f"❌ Connection failed: {e}")
            return False
    
    def _setup_handlers(self):
        """Setup event handlers"""
        def on_login(*args):
            self.logger.info(f"✅ Logged in to {self.bot.game.dimension}")
            self.connected = True
        
        def on_spawn(*args):
            pos = self.bot.entity.position
            self.logger.info(f"✅ Spawned at ({pos.x:.0f}, {pos.y:.0f}, {pos.z:.0f})")
            self._start_ai()
        
        def on_chat(*args):
            # Chat is now handled by ActionManager via EventBus (or directly if we wanted)
            # But we still log it here for debugging or if ActionManager isn't ready
            if len(args) >= 2:
                username, msg = args[0], args[1]
                self.logger.info(f"💬 <{username}> {msg}")
        
        def on_death(*args):
            self.logger.warning("💀 Died! Respawning...")
        
        def on_end(*args):
            self.logger.warning("🔌 Disconnected from server")
            self.connected = False
            
        def on_kicked(*args):
            reason = args[0] if args else "Unknown"
            self.logger.warning(f"👢 Kicked: {reason}")
            self.connected = False

        self.bot.on('login', on_login)
        self.bot.on('spawn', on_spawn)
        self.bot.on('chat', on_chat)
        self.bot.on('death', on_death)
        self.bot.on('end', on_end)
        self.bot.on('kicked', on_kicked)
    
    def _start_ai(self):
        """Start AI decision loop with ActionManager as leader"""
        if self.action_manager:
            return # Already started
            
        self.logger.info("🧠 Initializing ActionManager (The Brain)...")
        self.action_manager = ActionManager(self.bot, self.logger)
        
        # Register Brains
        from brains import AggressiveBrain, CautiousBrain, HealthBrain, StrategicBrain, CombatBrain, SurvivalBrain
        from brains.llm_brain import LLMBrain
        
        bm = self.action_manager.brain_manager
        bm.register_brain(AggressiveBrain())
        bm.register_brain(CautiousBrain())
        bm.register_brain(HealthBrain())
        bm.register_brain(StrategicBrain())
        bm.register_brain(CombatBrain(self.logger))
        bm.register_brain(SurvivalBrain(self.logger))
        
        # Register LLM Brain
        llm_apis = []
        ai_apis_config = self.config.get('ai_apis', {})
        
        # Convert settings.json format to LLMBrain format
        for key, api_conf in ai_apis_config.items():
            if isinstance(api_conf, dict) and api_conf.get('enabled'):
                api_entry = {
                    'id': key,
                    'type': api_conf.get('type', 'openai_compatible'),
                    'name': api_conf.get('name', key),
                    'api_key': api_conf.get('api_key'),
                    'endpoint': api_conf.get('endpoint'),
                    'model': api_conf.get('model'),
                    'priority': api_conf.get('priority', 999),
                    'timeout': api_conf.get('timeout', 15),
                    'max_tokens': api_conf.get('max_tokens', 150)
                }
                llm_apis.append(api_entry)
        
        if llm_apis:
            self.logger.info(f"🧠 LLM Brain enabled with {len(llm_apis)} providers")
        else:
            self.logger.warning("⚠️ LLM Brain has no enabled providers in settings.json")

        bm.register_brain(LLMBrain(llm_apis, self.logger))
        
        self.action_manager.start()
    
    def stop(self):
        """Stop bot"""
        self.running = False
        if self.action_manager:
            self.action_manager.stop()
        if self.bot:
            self.bot.quit()
        self.logger.info("👋 Bot stopped")


# ==================== MAIN ====================
def main():
    print("=" * 70)
    print("🤖 AUTONOMOUS MINECRAFT BOT")
    print("   ActionManager Leader | Event-Driven | Multi-Brain")
    print("=" * 70)
    
    # Load config
    config = ConfigManager()
    settings = config.load()
    
    # Setup logging
    log_mgr = LogManager(settings['logging'])
    logger = log_mgr.setup()
    
    logger.info("🧠 System initializing...")
    
    # Create bot
    bot = MinecraftBot(config, logger)
    
    # Connect Loop
    server_name = config.get('bot.default_server')
    reconnect_delay = config.get('bot.reconnect_delay', 5)
    
    while True:
        try:
            if bot.connect(server_name):
                logger.info("⏳ Waiting for login...")
                
                # Wait for login (timeout 30s)
                start_wait = time.time()
                while not bot.connected and bot.running:
                    time.sleep(0.1)
                    if time.time() - start_wait > 30:
                        logger.error("❌ Login timed out")
                        bot.stop()
                        break
                
                if bot.connected:
                    logger.info("✅ Login successful! Bot is running.")
                    # Keep alive loop
                    while bot.connected and bot.running:
                        time.sleep(1)
            else:
                logger.error("❌ Connection failed")
        except KeyboardInterrupt:
            logger.info("🛑 Stopping bot...")
            bot.stop()
            break
        except Exception as e:
            logger.error(f"❌ Critical error: {e}")
        
        if not bot.running:
            break
            
        logger.info(f"🔄 Reconnecting in {reconnect_delay}s...")
        time.sleep(reconnect_delay)
        bot.connected = False # Reset state
        bot.running = True    # Reset running state for retry

    logger.info("👋 Bot shutdown complete")


if __name__ == "__main__":
    main()
