import time
import math
import threading
import uuid
from typing import Dict, Optional, List, Any
from collections import deque

from core.event_bus import EventBus
from core.perception import EnhancedPerception
from brains.brain_manager import BrainManager

try:
    from javascript import require, On, Once, off
    pathfinder = require('mineflayer-pathfinder')
    pvp = require('mineflayer-pvp')
    Goals = pathfinder.goals
except Exception as e:
    print(f"JS Import Error: {e}")
    pathfinder = None
    pvp = None
    Goals = None

class CommandQueue:
    """
    Manages a queue of actions to be executed sequentially.
    Inspired by Minecraft-GPT.
    """
    def __init__(self):
        self.queue = deque()
        self.current_command = None
        self.history = []

    def add(self, command: Dict):
        """Add a command to the queue"""
        cmd_id = str(uuid.uuid4())[:8]
        command['id'] = cmd_id
        command['status'] = 'pending'
        command['retry_count'] = 0
        self.queue.append(command)
        return cmd_id

    def get_next(self) -> Optional[Dict]:
        """Get the next command if available"""
        if self.queue:
            return self.queue[0]
        return None

    def pop(self):
        """Remove the current command (finished)"""
        if self.queue:
            cmd = self.queue.popleft()
            cmd['status'] = 'completed'
            self.history.append(cmd)
            if len(self.history) > 50:
                self.history.pop(0)

    def clear(self):
        self.queue.clear()
        self.current_command = None

    def is_empty(self):
        return len(self.queue) == 0

class SelfPrompter:
    """
    Triggers the Brain to think when the bot is idle.
    Inspired by Mindcraft.
    """
    def __init__(self, action_manager, interval=5.0):
        self.am = action_manager
        self.interval = interval
        self.last_prompt_time = 0
        self.active = True

    def update(self):
        """Check if we should prompt the brain"""
        if not self.active:
            return

        now = time.time()
        # If queue is empty and enough time has passed
        if self.am.queue.is_empty() and (now - self.last_prompt_time > self.interval):
            self.am.logger.info("🤔 Idle... Self-prompting for new task.")
            self.am.decide_next_action()
            self.last_prompt_time = now

from core.memory import HistoryManager
from core.skills import SkillManager

class ActionManager:
    """
    Central Leader of the Bot.
    Orchestrates Perception, Brains, and Execution using a Queue.
    """
    
    def __init__(self, bot, logger):
        self.bot = bot
        self.logger = logger.getChild('ActionManager')
        self.event_bus = EventBus()
        self.running = False
        
        # Subsystems
        self.queue = CommandQueue()
        self.perception = EnhancedPerception(bot, self.logger)
        self.memory = HistoryManager(bot.username)
        self.brain_manager = BrainManager(self.logger)
        self.skills = SkillManager(bot, self)
        self.self_prompter = SelfPrompter(self)
        
        self._load_plugins()
        self._setup_events()

    # ... (rest of init/start/stop/tick methods same as before) ...

    def decide_next_action(self):
        """Ask brains for the next decision"""
        perception_state = self.perception.get_complete_state()
        
        # Inject Memory Context
        perception_state['memory_context'] = self.memory.get_context()
        
        decision = self.brain_manager.decide(perception_state)
        
        if decision and decision.get('action') != 'IDLE':
            self.logger.info(f"🧠 Brain decided: {decision.get('action')} - {decision.get('reason')}")
            self.queue.add(decision)
            # Log to history
            self.memory.add_turn("assistant", f"Decided to {decision.get('action')}: {decision.get('reason')}")
        else:
            self.logger.debug("🧠 Brain decided to IDLE")

    # ... (event handlers) ...

    def _on_chat(self, message):
        self.logger.info(f"📨 Chat: {message}")
        self.memory.add_turn("user", message) # Assume all chat is user for now

    # --- Execution Logic ---
    def execute(self, decision: Dict):
        """Execute a decision from the queue"""
        try:
            action = decision.get('action', 'IDLE')
            params = decision.get('params', {})
            reason = decision.get('reason', '')
            
            self.logger.info(f"⚡ Executing: {action} ({reason})")
            
            # Atomic Control Mapping
            if action == 'MOVE':
                self._handle_move_to(params.get('move_to'))
            elif action == 'LOOK':
                self._handle_look_at(params.get('look_at'))
            elif action == 'CONTROL':
                self._handle_control_set(params.get('control_set'))
            elif action == 'COMBAT':
                # Use Skill for advanced combat if available, else atomic
                if 'skill' in params:
                    self.skills.execute_skill('combat_hunt', params)
                else:
                    self._handle_interact(params.get('interact'))
            elif action == 'FLEE':
                self._handle_flee(params)
            elif action == 'MINE' or action == 'DIG':
                # Use Skill for resource collection if specified
                if 'skill' in params:
                    self.skills.execute_skill('collect_resource', params)
                else:
                    self._handle_dig(params.get('dig'))
            elif action == 'EAT':
                self._handle_eat(params)
            elif action == 'CRAFT':
                self.skills.execute_skill('craft_item', params)
            elif action == 'BUILD':
                self.skills.execute_skill('build_structure', params)
            elif action == 'FARM':
                self.skills.execute_skill('farm', params)
            elif action == 'TRADE':
                self.skills.execute_skill('trade', params)
            elif action == 'CHAT':
                self._handle_chat(params.get('chat'))
            elif action == 'IDLE':
                self._handle_idle()
            elif action == 'MOUNT':
                self._handle_mount(params)
            elif action == 'DISMOUNT':
                self._handle_dismount()
            elif action == 'SLEEP':
                self._handle_sleep(params)
            elif action == 'WAKE':
                self._handle_wake()
            elif action == 'USE':
                self._handle_use_item(params)
            elif action == 'DROP':
                self._handle_drop_item(params)
            elif action == 'CHAT':
                self._handle_chat(params.get('chat'))
            else:
                self.logger.warning(f"Unknown action: {action}")
            
            self.queue.pop()
                
        except Exception as e:
            self.logger.error(f"Action execution failed: {e}")
            self.queue.pop()
        
    def _load_plugins(self):
        """Load Mineflayer plugins"""
        self.logger.info("🔌 Loading plugins...")
        try:
            if pathfinder:
                self.logger.info(f"   Pathfinder module found: {pathfinder}")
                # Check if already loaded to avoid errors
                if not hasattr(self.bot, 'pathfinder'):
                    self.logger.info("   Loading pathfinder plugin...")
                    self.bot.loadPlugin(pathfinder.pathfinder)
                    self.logger.info("✅ Pathfinder loaded")
                else:
                    self.logger.info("   Pathfinder already attached to bot")
            else:
                self.logger.warning("❌ Pathfinder module is None (Import failed?)")

            if pvp:
                self.logger.info(f"   PvP module found: {pvp}")
                if not hasattr(self.bot, 'pvp'):
                    self.bot.loadPlugin(pvp.plugin)
                    self.logger.info("✅ PvP loaded")
                else:
                    self.logger.info("   PvP already attached to bot")
            else:
                self.logger.warning("❌ PvP module is None (Import failed?)")
                
        except Exception as e:
            self.logger.error(f"Failed to load plugins: {e}")

    def _setup_events(self):
        """Subscribe to important events"""
        self.event_bus.subscribe('health_damage', self._on_damage)
        self.event_bus.subscribe('threat_detected', self._on_threat)
        self.event_bus.subscribe('chat_received', self._on_chat)

    def start(self):
        """Start the main loop"""
        self.running = True
        self.logger.info("🚀 ActionManager taking control (Queue + Self-Prompt)!")
        threading.Thread(target=self._tick_loop, daemon=True).start()

    def stop(self):
        """Stop the bot"""
        self.running = False
        self.logger.info("🛑 ActionManager stopping...")

    def _tick_loop(self):
        """Main heartbeat"""
        while self.running:
            try:
                self.tick()
            except Exception as e:
                self.logger.error(f"Tick error: {e}")
            time.sleep(0.1) # Fast tick for responsiveness

    def tick(self):
        """Single update cycle"""
        # 1. Update Self-Prompter (generates new commands if idle)
        self.self_prompter.update()
        
        # 2. Process Queue
        if not self.queue.is_empty():
            cmd = self.queue.get_next()
            if cmd != self.queue.current_command:
                # New command started
                self.queue.current_command = cmd
                self.execute(cmd)
            else:
                # Monitor current command (timeout, completion check)
                # For now, we assume atomic actions finish quickly or block
                # In a real async system, we'd check status here
                pass

    def decide_next_action(self):
        """Ask brains for the next decision"""
        perception_state = self.perception.get_complete_state()
        decision = self.brain_manager.decide(perception_state)
        
        if decision and decision.get('action') != 'IDLE':
            self.logger.info(f"🧠 Brain decided: {decision.get('action')} - {decision.get('reason')}")
            self.queue.add(decision)
        else:
            self.logger.debug("🧠 Brain decided to IDLE")

    # --- Event Handlers ---
    def _on_damage(self, data):
        self.logger.warning(f"⚠️ Took damage! Clearing queue for survival!")
        self.queue.clear() # Emergency interrupt
        # Force immediate decision
        self.decide_next_action()

    def _on_threat(self, threats):
        if self.queue.is_empty():
            self.logger.warning(f"⚠️ Threats detected! reacting...")
            self.decide_next_action()

    def _on_chat(self, message):
        self.logger.info(f"📨 Chat: {message}")
        # Could trigger a specific "Reply" action here

    def _handle_dig(self, params):
        """Handle mining"""
        if not params:
            return
            
        pos = params.get('pos')
        block_name = params.get('block_name')
        
        if pos:
            # Mine specific position
            from javascript import require
            Vec3 = require('vec3')
            target_pos = Vec3(pos['x'], pos['y'], pos['z'])
            block = self.bot.blockAt(target_pos)
            
            if block:
                if not hasattr(self.bot, 'pathfinder') or not self.bot.pathfinder:
                    self.logger.warning("⚠️ Pathfinder missing. Attempting lazy load...")
                    self._load_plugins()

                if hasattr(self.bot, 'pathfinder') and self.bot.pathfinder:
                    self.bot.pathfinder.setGoal(Goals.GoalBlock(pos['x'], pos['y'], pos['z']))
                else:
                    self.logger.warning("⚠️ Pathfinder not available for mining")
                
                try:
                    self.bot.dig(block)
                except Exception as e:
                    self.logger.error(f"Dig failed: {e}")
        
        elif block_name:
            # Find and mine block by name (fallback)
            block = self.bot.findBlock({
                'matching': lambda b: b.name == block_name,
                'maxDistance': 32
            })
            if block:
                if hasattr(self.bot, 'pathfinder') and self.bot.pathfinder:
                    self.bot.pathfinder.setGoal(Goals.GoalBlock(block.position.x, block.position.y, block.position.z))
                else:
                    self.logger.warning("⚠️ Pathfinder not available for mining")

                try:
                    self.bot.dig(block)
                except Exception as e:
                    self.logger.error(f"Dig failed: {e}")

    def _handle_eat(self, params):
        """Handle eating food"""
        self.logger.info("🍖 Attempting to eat...")
        try:
            # Simple eat logic: find food in inventory and eat it
            # In a real implementation, we'd check food points and saturation
            food_names = ['cooked_beef', 'steak', 'cooked_porkchop', 'bread', 'carrot', 'baked_potato']
            
            # Find food in inventory
            food_item = None
            for item in self.bot.inventory.items():
                if item.name in food_names:
                    food_item = item
                    break
            
            if food_item:
                self.bot.equip(food_item, 'hand')
                self.bot.consume()
                self.logger.info(f"😋 Ate {food_item.name}")
            else:
                self.logger.warning("❌ No food found in inventory!")
                
        except Exception as e:
            self.logger.error(f"Eat failed: {e}")

    def execute(self, decision: Dict):
        """Execute a decision from the queue"""
        try:
            action = decision.get('action', 'IDLE')
            params = decision.get('params', {})
            reason = decision.get('reason', '')
            
            self.logger.info(f"⚡ Executing: {action} ({reason})")
            
            # Atomic Control Mapping
            if action == 'MOVE':
                self._handle_move_to(params.get('move_to'))
            elif action == 'LOOK':
                self._handle_look_at(params.get('look_at'))
            elif action == 'CONTROL':
                self._handle_control_set(params.get('control_set'))
            elif action == 'COMBAT':
                self._handle_interact(params.get('interact'))
            elif action == 'FLEE':
                self._handle_flee(params)
            elif action == 'MINE' or action == 'DIG':
                self._handle_dig(params.get('dig'))
            elif action == 'EAT':
                self._handle_eat(params)
            elif action == 'CRAFT':
                self._handle_craft(params.get('craft'))
            elif action == 'BUILD':
                self._handle_build(params.get('build'))
            elif action == 'CHAT':
                self._handle_chat(params.get('chat'))
            elif action == 'IDLE':
                self._handle_idle()
            else:
                self.logger.warning(f"Unknown action: {action}")
            
            # Mark done immediately for this simple version
            # In advanced version, we'd wait for pathfinder callback
            self.queue.pop()
                
        except Exception as e:
            self.logger.error(f"Action execution failed: {e}")
            self.queue.pop() # Remove failed action

    # --- Atomic Controls (Same as before) ---
    
    def _handle_move_to(self, params):
        """Handle movement to coordinates"""
        if not params:
            return
            
        x = params.get('x')
        y = params.get('y')
        z = params.get('z')
        speed = params.get('speed', 'walk')
        
        if x is None or z is None:
            return
            
        self.logger.info(f"🚶 Moving to ({x}, {y}, {z}) [{speed}]")
        
        # Set speed
        if speed == 'sprint':
            self.bot.setControlState('sprint', True)
        else:
            self.bot.setControlState('sprint', False)
            
        # Set goal
        if not hasattr(self.bot, 'pathfinder') or not self.bot.pathfinder:
            self.logger.warning("⚠️ Pathfinder missing. Attempting lazy load...")
            self._load_plugins()
            
        if hasattr(self.bot, 'pathfinder') and self.bot.pathfinder:
            goal = Goals.GoalNear(x, y, z, 1)
            self.bot.pathfinder.setGoal(goal)
        else:
            self.logger.warning("⚠️ Pathfinder still not available for movement")
        # Note: pathfinder is async. In a full queue system, we'd wait for 'goalReached'

    def _handle_look_at(self, params):
        """Handle looking at coordinates"""
        if not params:
            return
            
        x = params.get('x')
        y = params.get('y')
        z = params.get('z')
        
        if x is not None:
            from javascript import require
            Vec3 = require('vec3')
            target = Vec3(x, y, z)
            self.bot.lookAt(target)

    def _handle_idle(self):
        """Stop all actions"""
        self.bot.clearControlStates()
        if hasattr(self.bot, 'pathfinder') and self.bot.pathfinder:
            self.bot.pathfinder.setGoal(None)

    def _handle_flee(self, params):
        """Flee from danger"""
        self.logger.info("🏃 Fleeing!")
        # Simple flee: move random distance away
        # In real impl, move away from specific entity
        if not hasattr(self.bot, 'pathfinder') or not self.bot.pathfinder:
            return

        # Move 20 blocks in random direction
        import random
        x = self.bot.entity.position.x + random.randint(-20, 20)
        z = self.bot.entity.position.z + random.randint(-20, 20)
        y = self.bot.entity.position.y
        
        goal = Goals.GoalNear(x, y, z, 1)
        self.bot.pathfinder.setGoal(goal)

    def _handle_interact(self, params):
        """Interact with entity or block"""
        # Placeholder
        pass

    def _handle_control_set(self, params):
        """Set control state"""
        # Placeholder
        pass

    def _handle_craft(self, params):
        """Craft item"""
        # Placeholder - should use SkillManager
        pass

    def _handle_build(self, params):
        """Build structure"""
        # Placeholder - should use SkillManager
        pass

    def _handle_mount(self, params):
        pass

    def _handle_dismount(self):
        pass

    def _handle_sleep(self, params):
        pass

    def _handle_wake(self):
        pass

    def _handle_use_item(self, params):
        pass

    def _handle_drop_item(self, params):
        pass
    
    def _handle_chat(self, message):
        if message:
            self.bot.chat(message)


