"""
LLM Brain - Advanced Intelligence
Uses Large Language Models to make complex decisions.
"""

import requests
import time
import logging
from typing import Dict, List, Optional
from .brain_manager import Brain

class LLMBrain(Brain):
    SYSTEM_PROMPT = """SYSTEM: You are the Autonomous Minecraft Agent (AMA). 
You control a live bot instance on a Minecraft server. Your job: survive, gather resources, craft, build, fight, chat and follow higher-level goals in real-time.

CONTEXT:
You will receive a JSON object containing:
- "perception": Current game state (health, inventory, nearby blocks/entities).
- "memory_context": Your history and known locations.

DECISION FRAMEWORK:
1. Analyze perception and memory.
2. Determine the best high-level goal (e.g., "Build Shelter", "Get Food").
3. Output a JSON decision to execute that goal.

RESPONSE FORMAT (STRICT JSON):
{
  "action": "ONE_OF[MOVE,LOOK,CONTROL,COMBAT,FLEE,MINE,EAT,CRAFT,BUILD,CHAT,IDLE]",
  "params": { 
      // Action-specific parameters.
      // For SKILLS (Complex actions):
      // COMBAT: {"skill": true, "target": "zombie", "radius": 20}
      // MINE: {"skill": true, "block": "oak_log", "count": 5}
      // MINE: {"skill": true, "block": "oak_log", "count": 5}
      // CRAFT: {"item": "planks", "count": 4}
      // BUILD: {"type": "shelter"}
      // FARM: {"action": "harvest", "crop": "wheat"}
      // TRADE: {"villager_id": 123}
      
      // For ATOMIC (Low-level):
      // MOVE: {"move_to": {"x": 100, "y": 64, "z": 100}}
      // CHAT: {"message": "Hello world"}
  },
  "reason": "short human-readable reason",
  "interrupt_on": ["health_drop","threat_detected"]
}

OUTPUT ONLY THE JSON object. DO NOT write extra text."""

    def __init__(self, apis: List[Dict], logger: logging.Logger):
        super().__init__("LLM_Brain", "🧠")
        self.apis = sorted(apis, key=lambda x: x.get('priority', 999))
        self.logger = logger.getChild('LLMBrain')
        self.api_status = {}
        self.event_bus = None
        
        for api in self.apis:
            self.api_status[api['id']] = {
                'available': True,
                'error_count': 0,
                'last_success': None,
                'last_error': None
            }
            
    def set_event_bus(self, bus):
        self.event_bus = bus

    def set_knowledge(self, knowledge):
        self.knowledge = knowledge

    def vote(self, perception: Dict) -> int:
        """Vote based on complexity of situation"""
        # LLM is expensive, so only vote high if situation is complex or other brains are unsure
        # For now, give a solid medium vote to be a reliable fallback/leader
        return 60 

    def decide(self, perception: Dict) -> Dict:
        """Make intelligent decision with fallback chain"""
        context = self._build_context(perception)
        
        for api in self.apis:
            api_id = api['id']
            
            # Skip if too many errors
            if self.api_status[api_id]['error_count'] > 3:
                continue
            
            try:
                self.logger.debug(f"Trying {api['name']}...")
                
                result = None
                if api['type'] == 'huggingface':
                    result = self._call_huggingface(api, context)
                elif api['type'] == 'openai_compatible':
                    result = self._call_openai_compatible(api, context)
                elif api['type'] == 'rules':
                    result = self._call_rules(perception)
                
                if result:
                    self.api_status[api_id]['available'] = True
                    self.api_status[api_id]['last_success'] = time.time()
                    self.api_status[api_id]['error_count'] = 0
                    self.logger.info(f"✅ {api['name']}: {result['action']} - {result['reason']}")
                    return result
                    
            except Exception as e:
                self.logger.error(f"❌ {api['name']} failed: {e}")
                self.api_status[api_id]['error_count'] += 1
                self.api_status[api_id]['last_error'] = str(e)
                continue
        
        # Ultimate fallback
        self.logger.warning("All APIs failed, using rule-based fallback")
        return self._call_rules(perception)
    
    def _build_context(self, perception: Dict) -> str:
        """Build rich context for AI"""
        ctx = f"""CURRENT SITUATION:

Health: {perception.get('health', 20)}/20 {'⚠️ LOW!' if perception.get('health', 20) < 6 else '✓'}
Food: {perception.get('food', 20)}/20 {'⚠️ HUNGRY!' if perception.get('food', 20) < 6 else '✓'}
Position: ({perception.get('position', {}).get('x', 0):.0f}, {perception.get('position', {}).get('y', 0):.0f}, {perception.get('position', {}).get('z', 0):.0f})
Time: {perception.get('time_of_day', 'Day')}
Dimension: {perception.get('dimension', 'overworld')}
Gamemode: {perception.get('gamemode', 'survival')}

INVENTORY ({len(perception.get('inventory', {}))} items):
{self._format_inventory(perception.get('inventory', {}))}

THREATS:
{self._format_threats(perception.get('nearby_entities', []))}

NEARBY PLAYERS:
{self._format_players(perception.get('nearby_players', []))}

RESOURCES DETECTED:
{self._format_blocks(perception.get('nearby_blocks', []))}

RECENT CHAT:
{perception.get('recent_chat', 'No recent messages')}

Based on this situation, what should the bot do next?

KNOWLEDGE TIPS:
- Mobs: {self.knowledge.get_knowledge('mobs')}
- Structures: {self.knowledge.get_knowledge('structures')}
"""
        
        return ctx
    
    def _format_inventory(self, inventory: Dict) -> str:
        """Format inventory for context"""
        if not inventory:
            return "  Empty - Need to gather resources!"
        
        items = []
        for item, count in list(inventory.items())[:8]:
            items.append(f"  • {item}: {count}")
        
        return '\n'.join(items) if items else "  Empty"
    
    def _format_threats(self, entities: List[Dict]) -> str:
        """Format threats for context"""
        threats = [e for e in entities if e.get('hostile')]
        if not threats:
            return "  No immediate threats"
        
        threat_list = []
        for threat in threats[:3]:
            distance = threat.get('distance', 999)
            threat_list.append(f"  ⚠️ {threat.get('type', 'mob')} at {distance:.1f} blocks")
        
        return '\n'.join(threat_list)
    
    def _format_players(self, players: List[str]) -> str:
        """Format players for context"""
        if not players:
            return "  None nearby"
        return '\n'.join([f"  👤 {p}" for p in players[:5]])
    
    def _format_blocks(self, blocks: List[Dict]) -> str:
        """Format nearby blocks for context"""
        if not blocks:
            return "  Scanning..."
        
        valuable = ['coal_ore', 'iron_ore', 'gold_ore', 'diamond_ore', 'tree', 'chest']
        found = [b for b in blocks if any(v in b.get('name', '').lower() for v in valuable)]
        
        if not found:
            return "  No valuable resources nearby"
        
        return '\n'.join([f"  💎 {b.get('name')} at {b.get('distance', 0):.1f} blocks" for b in found[:5]])
    
    def _call_huggingface(self, api: Dict, context: str) -> Optional[Dict]:
        """Call Hugging Face with professional prompt"""
        full_prompt = f"{self.SYSTEM_PROMPT}\n\n{context}"
        
        headers = {"Content-Type": "application/json"}
        if api.get('api_key'):
            headers["Authorization"] = f"Bearer {api['api_key']}"
        
        response = requests.post(
            api['endpoint'],
            headers=headers,
            json={
                "inputs": full_prompt,
                "parameters": {
                    "max_new_tokens": api.get('max_tokens', 100),
                    "temperature": api.get('temperature', 0.7),
                    "return_full_text": False
                }
            },
            timeout=api.get('timeout', 15)
        )
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                text = result[0].get('generated_text', '').strip()
                return self._parse_ai_response(text)
        
        return None
    
    def _call_openai_compatible(self, api: Dict, context: str) -> Optional[Dict]:
        """Call OpenAI-compatible API (Groq/OpenAI) with professional prompt"""
        if not api.get('api_key') or api['api_key'] == "YOUR_API_KEY_HERE":
            self.logger.error("❌ No valid API key provided for LLM!")
            return None

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api['api_key']}"
        }
        
        # Construct messages
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": context}
        ]
        
        payload = {
            "model": api.get('model', 'llama-3.1-70b-versatile'),
            "messages": messages,
            "max_tokens": api.get('max_tokens', 1024),
            "temperature": 0.7,
            "response_format": {"type": "json_object"} # Force JSON if supported
        }

        try:
            response = requests.post(
                api['endpoint'],
                headers=headers,
                json=payload,
                timeout=api.get('timeout', 15)
            )
            
            if response.status_code == 200:
                result = response.json()
                text = result['choices'][0]['message']['content']
                return self._parse_ai_response(text)
            else:
                self.logger.error(f"❌ API Error {response.status_code}: {response.text}")
                return None
        except Exception as e:
            self.logger.error(f"❌ Request failed: {e}")
            return None
    
    def _parse_ai_response(self, text: str) -> Optional[Dict]:
        """Parse AI response into structured decision"""
        import json
        import re
        
        try:
            # Try to find JSON block
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                decision = json.loads(json_str)
                
                # Validate required fields
                if 'action' in decision:
                    return decision
            
            # Fallback: try to parse entire text as JSON
            decision = json.loads(text)
            if 'action' in decision:
                return decision
                
        except Exception as e:
            self.logger.error(f"Failed to parse JSON decision: {e}")
            self.logger.debug(f"Raw text: {text}")
        
        return None
    
    def _call_rules(self, perception: Dict) -> Dict:
        """Intelligent rule-based fallback"""
        health = perception.get('health', 20)
        food = perception.get('food', 20)
        threats = [e for e in perception.get('nearby_entities', []) if e.get('hostile')]
        
        # CRITICAL: Low health
        if health < 6:
            return {
                'action': 'FLEE',
                'reason': 'Critical health - immediate retreat required',
                'priority': 'HIGH',
                'params': {'move_to': {'speed': 'sprint'}},
                'interrupt_on': ['health_damage']
            }
        
        # HIGH: Nearby threat
        if threats and health > 10:
            nearest = min(threats, key=lambda e: e.get('distance', 999))
            return {
                'action': 'COMBAT',
                'reason': f"Engaging {nearest.get('type', 'mob')} while healthy",
                'priority': 'HIGH',
                'params': {'interact': {'type': 'attack', 'target_entity_id': nearest.get('id')}},
                'interrupt_on': ['health_damage']
            }
        elif threats:
            return {
                'action': 'FLEE',
                'reason': 'Threats present with low health',
                'priority': 'HIGH',
                'params': {'move_to': {'speed': 'sprint'}},
                'interrupt_on': ['health_damage']
            }
        
        # MEDIUM: Hungry
        if food < 6:
            return {
                'action': 'EAT',
                'reason': 'Low food level requires eating',
                'priority': 'MEDIUM',
                'params': {},
                'interrupt_on': ['threat_detected']
            }
        
        # DEFAULT: Explore
        return {
            'action': 'IDLE',
            'reason': 'Safe conditions - waiting for opportunities',
            'priority': 'LOW',
            'params': {},
            'interrupt_on': ['chat_received', 'threat_detected']
        }
