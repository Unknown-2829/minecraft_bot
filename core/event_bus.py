"""
Event Bus - Real-Time Communication System
Allows different parts of the bot to talk to each other instantly.
"""

import logging
from typing import Dict, List, Callable, Any
from collections import defaultdict

class EventBus:
    """Central communication hub for the bot"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventBus, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.logger = logging.getLogger('EventBus')
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._initialized = True
        self.logger.info("📡 Event Bus initialized")
    
    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to an event"""
        self.subscribers[event_type].append(callback)
        # self.logger.debug(f"Subscribed to {event_type}")
        
    def emit(self, event_type: str, data: Any = None):
        """Emit an event to all subscribers"""
        if event_type in self.subscribers:
            # self.logger.debug(f"Emitting {event_type}")
            for callback in self.subscribers[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    self.logger.error(f"Error in subscriber for {event_type}: {e}")
