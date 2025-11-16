"""
Gesture Recognizer Module
Recognizes hand gestures (open/closed)
"""

import numpy as np
from collections import deque
import pyautogui
import time

class GestureRecognizer:
    def __init__(self, smoothing_frames=5, closed_threshold=0.30):
        """
        Initialize gesture recognizer
        
        Args:
            smoothing_frames: Number of frames to smooth gesture detection
            closed_threshold: Distance threshold for closed hand detection
        """
        self.smoothing_frames = smoothing_frames
        self.closed_threshold = closed_threshold
        
        # Gesture history for smoothing
        self.gesture_history = deque(maxlen=smoothing_frames)
        
        # Previous gesture state
        self.previous_gesture = "open"

        # Previous finger count for number key presses
        self.previous_finger_count = 0

        # Last stable finger count (when hand was fully open)
        self.stable_finger_count = 0

        # Track if we're in a closing/opening transition
        self.in_transition = False

        # Current finger count for display
        self.current_finger_count = 0

        # Time-based tracking for stable finger counts
        self.last_finger_count_change_time = time.time()
        self.time_at_current_count = 0.0
        self.stable_threshold = 0.5  # Time needed to be considered stable (seconds)
        self.transition_window = 0.3  # Time window to detect quick transitions (seconds)

    def calculate_distance(self, point1, point2):
        """
        Calculate Euclidean distance between two points
        
        Args:
            point1: Dict with 'x' and 'y' keys (normalized coords)
            point2: Dict with 'x' and 'y' keys
            
        Returns:
            float: Distance
        """
        dx = point1['x'] - point2['x']
        dy = point1['y'] - point2['y']
        return np.sqrt(dx**2 + dy**2)
    
    def is_finger_extended(self, landmarks, finger_tip_idx, finger_pip_idx):
        """
        Check if a finger is extended based on tip and PIP joint positions
        
        Args:
            landmarks: List of landmark dicts
            finger_tip_idx: Index of finger tip
            finger_pip_idx: Index of PIP joint (knuckle)
        """
        tip = landmarks[finger_tip_idx]
        pip = landmarks[finger_pip_idx]
        
        return tip['y'] < pip['y'] - 0.02
    
    def is_thumb_extended(self, landmarks, finger_tip_idx, finger_pip_idx):

        tip = landmarks[finger_tip_idx]
        pip = landmarks[finger_pip_idx]
        
        return tip['x'] > pip['x'] -0.01
    
    
    

    def detect_gesture(self, landmarks):
        """
        Detect if hand is open or closed
        
        Args:
            landmarks: List of landmark dicts from hand detector
            
        Returns:
            str: "open" or "closed"
        """
        if landmarks is None or len(landmarks) < 21:
            return self.previous_gesture
        
        # Method 1: Check finger extension
        # Indices: thumb=4, index=8, middle=12, ring=16, pinky=20
        # PIP joints: thumb=2, index=6, middle=10, ring=14, pinky=18
        
        fingers_extended = []
        
        # Check each finger (except thumb - it moves differently)
        finger_pairs = [
            (8, 6),   # Index finger
            (12, 10), # Middle finger
            (16, 14), # Ring finger
            (20, 18)  # Pinky finger
        ]
        
        for tip_idx, pip_idx in finger_pairs:
            fingers_extended.append(self.is_finger_extended(landmarks, tip_idx, pip_idx))
        
        fingers_extended.append(self.is_thumb_extended(landmarks, 4, 2))

        # Hand is open if at least 3 fingers are extended

        total_fingers_extended = sum(fingers_extended)
        current_time = time.time()

        # Determine if hand is open (3+ fingers)
        open_gesture = total_fingers_extended >= 1

        # Track how long we've been at the current finger count
        if total_fingers_extended != self.previous_finger_count:
            # Finger count changed
            self.last_finger_count_change_time = current_time
            self.time_at_current_count = 0.0
        else:
            # Same count, accumulate time
            self.time_at_current_count = current_time - self.last_finger_count_change_time

        # Smart finger count handling with time-based stability:
        # - A finger count becomes "stable" after being held for stable_threshold seconds
        # - If we see a brief change (< transition_window) followed by 0 fingers, revert to last stable count

        if total_fingers_extended == 0:
            # Hand is fully closed
            # Check if we recently changed from the stable count (within transition window)
            time_since_change = current_time - self.last_finger_count_change_time

            if (self.previous_finger_count != 0 and
                self.previous_finger_count != self.stable_finger_count and
                time_since_change < self.transition_window):
                # We briefly showed a different finger count, then closed quickly
                # This is likely an unintentional change during closing
                # Re-press the stable count
                if self.stable_finger_count > 0:
                    pyautogui.press(str(self.stable_finger_count))
                    print(f">>> Quick close detected, re-pressed stable key: {self.stable_finger_count}")

            self.in_transition = True

        elif 1 <= total_fingers_extended <= 4:
            # Showing 1-4 fingers

            # Check if this count has been stable long enough
            if self.time_at_current_count >= self.stable_threshold:
                # This is a stable finger count
                if total_fingers_extended != self.stable_finger_count:
                    # New stable count detected - press the key
                    self.stable_finger_count = total_fingers_extended
                    pyautogui.press(str(total_fingers_extended))
                    print(f">>> New stable count: {total_fingers_extended}")
                    self.in_transition = False
            else:
                # Not stable yet - still accumulating time
                # If we're in transition and back to stable count, exit transition
                if self.in_transition and total_fingers_extended == self.stable_finger_count:
                    self.in_transition = False
                    print(f">>> Returned to stable count: {self.stable_finger_count}")

        self.previous_finger_count = total_fingers_extended

        # Update current finger count for display
        self.current_finger_count = total_fingers_extended


        # For Debugging
        print(f"Fingers extended: {fingers_extended}, Count: {sum(fingers_extended)}, Open: {open_gesture}")
        
        # Combine both methods
        # Hand is closed if fingers are not extended
        if not open_gesture:
            gesture = "closed"
        else:
            gesture = "open"
        
        return gesture
    
    def get_smoothed_gesture(self, landmarks):
        """
        Get smoothed gesture with temporal filtering
        
        Args:
            landmarks: List of landmark dicts
            
        Returns:
            str: "open" or "closed" (smoothed)
        """
        # Detect current gesture
        current_gesture = self.detect_gesture(landmarks)
        
        # Add to history
        self.gesture_history.append(current_gesture)
        
        # If we don't have enough history, return current
        if len(self.gesture_history) < self.smoothing_frames:
            self.previous_gesture = current_gesture
            return current_gesture
        
        # Count occurrences in history
        open_count = self.gesture_history.count("open")
        closed_count = self.gesture_history.count("closed")
        
        # Return majority vote
        if closed_count > open_count:
            smoothed_gesture = "closed"
        else:
            smoothed_gesture = "open"
        
        self.previous_gesture = smoothed_gesture
        return smoothed_gesture
    
    def reset(self):
        """Reset gesture history"""
        self.gesture_history.clear()
        self.previous_gesture = "open"


if __name__ == "__main__":
    # Test gesture recognizer
    from camera_handler import CameraHandler
    from hand_detector import HandDetector
    
    camera = CameraHandler()
    camera.start()
    
    detector = HandDetector()
    recognizer = GestureRecognizer()
    
    print("Show your hand. Open hand = hover, Closed fist = click")
    print("Press 'q' to quit.")
    
    while camera.is_opened():
        ret, frame = camera.read_frame()
        
        if not ret:
            break
        
        # Detect hands
        frame, hands_data = detector.find_hands(frame, draw=True)
        
        gesture = "None"
        
        if hands_data:
            # Get first hand
            landmarks = hands_data[0]['landmarks']
            
            # Recognize gesture
            gesture = recognizer.get_smoothed_gesture(landmarks)
            
            # Display gesture
            color = (0, 255, 0) if gesture == "open" else (0, 0, 255)
            cv2.putText(frame, f"Gesture: {gesture.upper()}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        
        cv2.imshow("Gesture Recognition Test", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    detector.release()
    camera.release()
    cv2.destroyAllWindows()
