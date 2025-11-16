"""
Clash Emote Recognizer Module
Recognizes specific Clash Royale emote gestures:
- Goblin Crying: Both fists near eyes
- Wizard 67: Both hands open, palms up (shrug gesture)
- Princess Yawning: One hand near mouth
"""

import numpy as np
from collections import deque
import time


class ClashEmoteRecognizer:
    def __init__(self, smoothing_frames=8, confidence_threshold=0.6):
        """
        Initialize Clash emote recognizer
        
        Args:
            smoothing_frames: Number of frames for temporal smoothing
            confidence_threshold: Minimum confidence to trigger emote
        """
        self.smoothing_frames = smoothing_frames
        self.confidence_threshold = confidence_threshold
        
        # Emote history for smoothing
        self.emote_history = deque(maxlen=smoothing_frames)
        
        # Current detected emote
        self.current_emote = None
        self.emote_start_time = 0
        self.emote_triggered = False
        
        # Hold time required to trigger emote action
        self.hold_time = 1.0  # seconds
        
        # Cooldown between emote triggers
        self.cooldown = 2.0  # seconds
        self.last_trigger_time = 0
        
    def calculate_distance(self, point1, point2):
        """Calculate Euclidean distance between two points"""
        dx = point1['x'] - point2['x']
        dy = point1['y'] - point2['y']
        return np.sqrt(dx**2 + dy**2)
    
    def is_hand_closed(self, landmarks):
        """
        Check if hand is closed (fist)
        
        Args:
            landmarks: List of 21 landmark dicts for one hand
            
        Returns:
            bool: True if hand is closed
        """
        if len(landmarks) < 21:
            return False
        
        # Check if fingertips are below their PIP joints (curled)
        finger_pairs = [
            (8, 6),   # Index
            (12, 10), # Middle
            (16, 14), # Ring
            (20, 18)  # Pinky
        ]
        
        closed_count = 0
        for tip_idx, pip_idx in finger_pairs:
            tip = landmarks[tip_idx]
            pip = landmarks[pip_idx]
            # Finger is curled if tip is below (higher y value) than PIP
            if tip['y'] > pip['y'] - 0.02:
                closed_count += 1
        
        # Hand is closed if at least 3 fingers are curled
        return closed_count >= 3
    
    def is_hand_open_palm_up(self, landmarks):
        """
        Check if hand is open with palm facing up (for Wizard 67)
        
        Args:
            landmarks: List of 21 landmark dicts for one hand
            
        Returns:
            bool: True if hand is open with palm up
        """
        if len(landmarks) < 21:
            return False
        
        # Check if fingers are extended
        finger_pairs = [
            (8, 6),   # Index
            (12, 10), # Middle
            (16, 14), # Ring
            (20, 18)  # Pinky
        ]
        
        extended_count = 0
        for tip_idx, pip_idx in finger_pairs:
            tip = landmarks[tip_idx]
            pip = landmarks[pip_idx]
            # Finger is extended if tip is above PIP
            if tip['y'] < pip['y'] + 0.02:
                extended_count += 1
        
        # Check palm orientation - for palm up, wrist should be below fingers
        wrist = landmarks[0]
        middle_tip = landmarks[12]
        
        # Palm is up if wrist is lower (higher y) than middle finger
        palm_up = wrist['y'] > middle_tip['y'] - 0.1
        
        return extended_count >= 3 and palm_up
    
    def get_hand_center(self, landmarks):
        """Get the center position of a hand"""
        if len(landmarks) < 21:
            return None
        
        # Use wrist and middle finger base
        wrist = landmarks[0]
        middle_base = landmarks[9]
        
        return {
            'x': (wrist['x'] + middle_base['x']) / 2,
            'y': (wrist['y'] + middle_base['y']) / 2
        }
    
    def detect_goblin_crying(self, hands_data):
        """
        Detect Goblin Crying gesture: Both fists near eyes (upper face area)
        
        Args:
            hands_data: List of hand data dicts (can have 1 or 2 hands)
            
        Returns:
            float: Confidence score (0-1)
        """
        if len(hands_data) < 2:
            return 0.0
        
        # Need both hands to be closed fists
        hand1_closed = self.is_hand_closed(hands_data[0]['landmarks'])
        hand2_closed = self.is_hand_closed(hands_data[1]['landmarks'])
        
        if not (hand1_closed and hand2_closed):
            return 0.0
        
        # Get hand positions
        hand1_center = self.get_hand_center(hands_data[0]['landmarks'])
        hand2_center = self.get_hand_center(hands_data[1]['landmarks'])
        
        if not hand1_center or not hand2_center:
            return 0.0
        
        # Check if both hands are in upper portion of frame (near face/eyes)
        # Y coordinate < 0.4 means upper 40% of frame
        hand1_high = hand1_center['y'] < 0.45
        hand2_high = hand2_center['y'] < 0.45
        
        if not (hand1_high and hand2_high):
            return 0.0
        
        # Check if hands are relatively close together horizontally (near eyes)
        # But not too close (should be apart like rubbing both eyes)
        horizontal_distance = abs(hand1_center['x'] - hand2_center['x'])
        
        # Distance should be between 0.15 and 0.6 (normalized coords)
        if 0.1 < horizontal_distance < 0.7:
            # Calculate confidence based on how well positioned
            confidence = 0.8
            
            # Bonus for being very high up (closer to eyes)
            avg_y = (hand1_center['y'] + hand2_center['y']) / 2
            if avg_y < 0.35:
                confidence += 0.2
            
            return min(confidence, 1.0)
        
        return 0.0
    
    def detect_wizard_67(self, hands_data):
        """
        Detect Wizard 67 gesture: Both hands open, palms up (shrug/presenting)
        
        Args:
            hands_data: List of hand data dicts
            
        Returns:
            float: Confidence score (0-1)
        """
        if len(hands_data) < 2:
            return 0.0
        
        # Need both hands to be open
        hand1_open = self.is_hand_open_palm_up(hands_data[0]['landmarks'])
        hand2_open = self.is_hand_open_palm_up(hands_data[1]['landmarks'])
        
        if not (hand1_open and hand2_open):
            return 0.0
        
        # Get hand positions
        hand1_center = self.get_hand_center(hands_data[0]['landmarks'])
        hand2_center = self.get_hand_center(hands_data[1]['landmarks'])
        
        if not hand1_center or not hand2_center:
            return 0.0
        
        # Check if hands are spread apart (shrug position)
        horizontal_distance = abs(hand1_center['x'] - hand2_center['x'])
        
        # Hands should be spread apart
        if horizontal_distance > 0.3:
            confidence = 0.7
            
            # Bonus for hands being at similar height
            vertical_diff = abs(hand1_center['y'] - hand2_center['y'])
            if vertical_diff < 0.15:
                confidence += 0.2
            
            # Bonus for hands being in middle/lower area (not near face)
            avg_y = (hand1_center['y'] + hand2_center['y']) / 2
            if avg_y > 0.4:
                confidence += 0.1
            
            return min(confidence, 1.0)
        
        return 0.0
    
    def detect_princess_yawning(self, hands_data):
        """
        Detect Princess Yawning gesture: One hand near mouth
        
        Args:
            hands_data: List of hand data dicts
            
        Returns:
            float: Confidence score (0-1)
        """
        if len(hands_data) < 1:
            return 0.0
        
        # Check each hand
        for hand_data in hands_data:
            landmarks = hand_data['landmarks']
            hand_center = self.get_hand_center(landmarks)
            
            if not hand_center:
                continue
            
            # Hand should be in center-upper area (near mouth)
            # X should be relatively centered (0.3 to 0.7)
            # Y should be in upper-middle area (0.25 to 0.5)
            x_centered = 0.25 < hand_center['x'] < 0.75
            y_near_mouth = 0.2 < hand_center['y'] < 0.55
            
            if x_centered and y_near_mouth:
                # Check if hand is open (covering yawn)
                is_open = self.is_hand_open_palm_up(landmarks) or not self.is_hand_closed(landmarks)
                
                if is_open:
                    confidence = 0.75
                    
                    # Bonus for being very centered
                    if 0.35 < hand_center['x'] < 0.65:
                        confidence += 0.15
                    
                    # Bonus for being at mouth height
                    if 0.3 < hand_center['y'] < 0.45:
                        confidence += 0.1
                    
                    return min(confidence, 1.0)
        
        return 0.0
    
    def detect_emote(self, hands_data):
        """
        Detect which Clash emote is being performed
        
        Args:
            hands_data: List of hand data dicts from hand detector
            
        Returns:
            tuple: (emote_name, confidence) or (None, 0)
        """
        if not hands_data:
            return None, 0.0
        
        # Calculate confidence for each emote
        goblin_conf = self.detect_goblin_crying(hands_data)
        wizard_conf = self.detect_wizard_67(hands_data)
        princess_conf = self.detect_princess_yawning(hands_data)
        
        # Find the emote with highest confidence
        emotes = [
            ("GOBLIN_CRYING", goblin_conf),
            ("WIZARD_67", wizard_conf),
            ("PRINCESS_YAWNING", princess_conf)
        ]
        
        best_emote, best_conf = max(emotes, key=lambda x: x[1])
        
        if best_conf >= self.confidence_threshold:
            return best_emote, best_conf
        
        return None, 0.0
    
    def get_smoothed_emote(self, hands_data):
        """
        Get smoothed emote detection with temporal filtering
        
        Args:
            hands_data: List of hand data dicts
            
        Returns:
            dict: Emote detection info
        """
        # Detect current emote
        emote, confidence = self.detect_emote(hands_data)
        
        # Add to history
        self.emote_history.append(emote)
        
        # If not enough history, return current
        if len(self.emote_history) < self.smoothing_frames // 2:
            return {
                'emote': emote,
                'confidence': confidence,
                'triggered': False,
                'hold_progress': 0.0
            }
        
        # Count emote occurrences in history
        emote_counts = {}
        for e in self.emote_history:
            if e:
                emote_counts[e] = emote_counts.get(e, 0) + 1
        
        # Find most common emote
        if emote_counts:
            smoothed_emote = max(emote_counts.keys(), key=lambda x: emote_counts[x])
            emote_frequency = emote_counts[smoothed_emote] / len(self.emote_history)
            
            # Only accept if it appears in majority of frames
            if emote_frequency < 0.5:
                smoothed_emote = None
        else:
            smoothed_emote = None
        
        # Track emote hold time
        current_time = time.time()
        hold_progress = 0.0
        triggered = False
        
        if smoothed_emote:
            if smoothed_emote != self.current_emote:
                # New emote detected
                self.current_emote = smoothed_emote
                self.emote_start_time = current_time
                self.emote_triggered = False
            else:
                # Same emote continuing
                hold_duration = current_time - self.emote_start_time
                hold_progress = min(hold_duration / self.hold_time, 1.0)
                
                # Check if should trigger
                if (hold_duration >= self.hold_time and 
                    not self.emote_triggered and
                    current_time - self.last_trigger_time > self.cooldown):
                    triggered = True
                    self.emote_triggered = True
                    self.last_trigger_time = current_time
        else:
            # No emote detected
            self.current_emote = None
            self.emote_triggered = False
        
        return {
            'emote': smoothed_emote,
            'confidence': confidence,
            'triggered': triggered,
            'hold_progress': hold_progress
        }
    
    def get_emote_display_name(self, emote_code):
        """Get human-readable emote name"""
        names = {
            "GOBLIN_CRYING": "Goblin Crying 😢",
            "WIZARD_67": "Wizard 67 🤷",
            "PRINCESS_YAWNING": "Princess Yawning 🥱"
        }
        return names.get(emote_code, emote_code)
    
    def reset(self):
        """Reset emote detection state"""
        self.emote_history.clear()
        self.current_emote = None
        self.emote_triggered = False


if __name__ == "__main__":
    # Test the emote recognizer
    import cv2
    import sys
    sys.path.insert(0, '/mnt/user-data/uploads')
    from camera_handler import CameraHandler
    from hand_detector import HandDetector
    
    camera = CameraHandler()
    camera.start()
    
    # Detect up to 2 hands for emotes that require both hands
    detector = HandDetector(max_num_hands=2)
    recognizer = ClashEmoteRecognizer()
    
    print("="*60)
    print("CLASH EMOTE RECOGNITION TEST")
    print("="*60)
    print("\nPerform these gestures:")
    print("  1. GOBLIN CRYING: Both fists near eyes")
    print("  2. WIZARD 67: Both hands open, palms up (shrug)")
    print("  3. PRINCESS YAWNING: One hand near mouth")
    print("\nHold gesture for 1 second to trigger!")
    print("Press 'Q' to quit")
    print("="*60)
    
    while camera.is_opened():
        ret, frame = camera.read_frame()
        
        if not ret:
            break
        
        # Detect hands
        frame, hands_data = detector.find_hands(frame, draw=True)
        
        # Recognize emote
        result = recognizer.get_smoothed_emote(hands_data)
        
        # Draw UI
        h, w = frame.shape[:2]
        
        # Semi-transparent overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 120), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)
        
        # Display hands detected
        cv2.putText(frame, f"Hands: {len(hands_data)}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Display detected emote
        if result['emote']:
            emote_name = recognizer.get_emote_display_name(result['emote'])
            color = (0, 255, 0) if result['triggered'] else (0, 255, 255)
            
            cv2.putText(frame, f"Emote: {emote_name}", (10, 65),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            
            # Draw hold progress bar
            bar_width = int(300 * result['hold_progress'])
            cv2.rectangle(frame, (10, 85), (310, 105), (100, 100, 100), -1)
            cv2.rectangle(frame, (10, 85), (10 + bar_width, 105), color, -1)
            cv2.rectangle(frame, (10, 85), (310, 105), (255, 255, 255), 2)
            
            if result['triggered']:
                cv2.putText(frame, "TRIGGERED!", (320, 100),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "Emote: None detected", (10, 65),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (150, 150, 150), 2)
        
        # Instructions at bottom
        cv2.putText(frame, "Hold gesture for 1 second to trigger | Press 'Q' to quit",
                   (10, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        cv2.imshow("Clash Emote Recognition", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    detector.release()
    camera.release()
    cv2.destroyAllWindows()
