"""
Emote Matcher Module
Maps facial expressions and hand gestures to Clash Royale emotes
"""


class EmoteMatcher:
    def __init__(self):
        """Initialize emote matching system"""
        
        # Define emote mappings: (expression, gesture) -> emote_name
        self.emote_map = {
            # Laughing emotes
            ("laughing", "thumbs_up"): "laughing",
            ("laughing", "peace"): "goblin_laugh",
            ("laughing", "open_palm"): "king_laugh",
            
            # Crying emotes
            ("crying", "fist"): "crying",
            ("crying", "open_palm"): "princess_cry",
            
            # Angry emotes
            ("angry", "fist"): "angry",
            ("angry", "pointing"): "goblin_angry",
            
            # Thumbs up emotes
            ("neutral", "thumbs_up"): "king_thumbs_up",
            ("laughing", "thumbs_down"): "thumbs_up",
            
            # Special gestures
            ("surprised", "open_palm"): "wow",
            ("neutral", "peace"): "chicken",
            ("laughing", "waving"): "goblin_kiss",
            ("crying", "pointing"): "princess_yawn",
            
            # Additional combinations
            ("neutral", "fist"): "thinking",
            ("angry", "open_palm"): "screaming",
        }
        
        # History for smoothing (prevent rapid switching)
        self.match_history = []
        self.history_size = 3
        
    def match_emote(self, expression, gesture):
        """
        Match expression and gesture to emote
        
        Args:
            expression: Facial expression name
            gesture: Hand gesture name
        
        Returns:
            str: Emote name or None
        """
        # Look up emote
        key = (expression, gesture)
        emote = self.emote_map.get(key)
        
        if emote:
            # Add to history
            self.match_history.append(emote)
            if len(self.match_history) > self.history_size:
                self.match_history.pop(0)
            
            # Require consistency (same emote detected multiple times)
            if len(self.match_history) >= self.history_size:
                if all(e == emote for e in self.match_history):
                    self.match_history.clear()  # Clear after match
                    return emote
        
        return None
    
    def get_all_mappings(self):
        """Get all emote mappings for display/debugging"""
        return self.emote_map
    
    def clear_history(self):
        """Clear match history"""
        self.match_history.clear()