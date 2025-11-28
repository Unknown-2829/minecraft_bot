"""
Brain Manager - Multi-Brain Competition System
Different AI personalities compete for control!
"""

from typing import Dict, List, Tuple
import logging



from core.event_bus import EventBus

class BrainManager:
    """Manages multiple competing brain personalities"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger.getChild('BrainManager')
        self.brains = []
        self.history = []  # Track decisions
        self.event_bus = EventBus()
    
    def register_brain(self, brain):
        """Register a brain personality"""
        self.brains.append(brain)
        # Inject event bus into brain if it supports it
        if hasattr(brain, 'set_event_bus'):
            brain.set_event_bus(self.event_bus)
            
        self.logger.info(f"✅ Registered: {brain.name}")
    
    def decide(self, perception: Dict) -> Dict:
        """Let all brains compete, highest vote wins!"""
        
        if not self.brains:
            return {'action': 'IDLE', 'reason': 'No brains registered'}
        
        # Each brain votes
        votes = []
        for brain in self.brains:
            try:
                score = brain.vote(perception)
                votes.append((brain, score))
            except Exception as e:
                self.logger.error(f"{brain.name} vote failed: {e}")
                votes.append((brain, 0))
        
        # Sort by score (highest first)
        votes.sort(key=lambda x: x[1], reverse=True)
        
        # Log competition
        self.logger.info("🧠 Brain Competition:")
        for brain, score in votes:
            emoji = brain.emoji if hasattr(brain, 'emoji') else '🤖'
            winner_mark = " ← WINNER!" if brain == votes[0][0] else ""
            self.logger.info(f"   {emoji} {brain.name}: {score}{winner_mark}")
        
        # Winner decides
        winner_brain, winner_score = votes[0]
        decision = winner_brain.decide(perception)
        decision['brain'] = winner_brain.name
        decision['score'] = winner_score
        
        # Save history
        self.history.append({
            'perception': perception,
            'votes': votes,
            'decision': decision
        })
        
        return decision


# Base Brain Class
class Brain:
    """Base class for all brain personalities"""
    
    def __init__(self, name: str, emoji: str = "🤖"):
        self.name = name
        self.emoji = emoji
    
    def vote(self, perception: Dict) -> int:
        """Return vote score (0-100) based on situation"""
        raise NotImplementedError
    
    def decide(self, perception: Dict) -> Dict:
        """Make decision (only called if won vote)"""
        raise NotImplementedError
