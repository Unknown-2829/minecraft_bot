import json
import os
import time
from typing import List, Dict, Any, Optional

class HistoryManager:
    """
    Manages the bot's memory, including:
    1. Short-term history (recent turns)
    2. Long-term memory (summarized context)
    3. Location memory (saved points of interest)
    Inspired by Mindcraft's History and MemoryBank.
    """
    def __init__(self, bot_name: str, log_dir: str = "logs"):
        self.bot_name = bot_name
        self.memory_file = os.path.join(log_dir, f"{bot_name}_memory.json")
        self.history_file = os.path.join(log_dir, f"{bot_name}_history.json")
        
        # State
        self.turns: List[Dict] = []
        self.memory_summary: str = ""
        self.locations: Dict[str, List[float]] = {}
        
        # Config
        self.max_turns = 20
        self.summary_chunk_size = 5
        
        self.load()

    def add_turn(self, role: str, content: str):
        """Add a message/action to history"""
        timestamp = time.strftime("%H:%M:%S")
        entry = {
            "role": role, 
            "content": content,
            "timestamp": timestamp
        }
        self.turns.append(entry)
        
        # Auto-save/prune
        if len(self.turns) > self.max_turns:
            # In a full implementation, we would trigger a summarization here
            # For now, just prune the oldest
            self.turns.pop(0)
            
        self.save()

    def remember_location(self, name: str, x: float, y: float, z: float):
        """Save a location"""
        self.locations[name] = [round(x, 1), round(y, 1), round(z, 1)]
        self.save()

    def recall_location(self, name: str) -> Optional[List[float]]:
        """Get a saved location"""
        return self.locations.get(name)

    def get_context(self) -> str:
        """Build a context string for the LLM"""
        context = []
        
        if self.memory_summary:
            context.append(f"MEMORY: {self.memory_summary}")
            
        if self.locations:
            locs = ", ".join([f"{k}:{v}" for k, v in self.locations.items()])
            context.append(f"KNOWN LOCATIONS: {locs}")
            
        context.append("RECENT HISTORY:")
        for turn in self.turns[-10:]:
            context.append(f"[{turn['timestamp']}] {turn['role'].upper()}: {turn['content']}")
            
        return "\n".join(context)

    def save(self):
        """Save memory to disk"""
        data = {
            "memory_summary": self.memory_summary,
            "locations": self.locations,
            "turns": self.turns
        }
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to save memory: {e}")

    def load(self):
        """Load memory from disk"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                    self.memory_summary = data.get("memory_summary", "")
                    self.locations = data.get("locations", {})
                    self.turns = data.get("turns", [])
            except Exception as e:
                print(f"Failed to load memory: {e}")
