"""
Main Application
Hand Tracking Mouse Control System with Emote Detection
"""

import cv2
import time
import numpy as np
import os
import warnings
import pyautogui

# Suppress protobuf warnings
warnings.filterwarnings('ignore', category=UserWarning, module='google.protobuf')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from camera_handler import CameraHandler
from hand_detector import HandDetector
from gesture_recognizer import GestureRecognizer
from mouse_controller import MouseController
from config import ACTIVE_CONFIG as Config

# Import emote detection if model is trained
try:
    if os.path.exists("emote_model_ultimate.pkl"):
        from ultimate_emote_matcher import UltimateEmoteMatcher
        EMOTE_DETECTION_ENABLED = True
    else:
        EMOTE_DETECTION_ENABLED = False
        print("Note: Emote detection disabled (model not trained)")
except ImportError:
    EMOTE_DETECTION_ENABLED = False
    print("Note: Emote detection not available")


class HandMouseApp:
    def __init__(self):
        """Initialize the hand mouse control application"""
        print("="*50)
        print("Hand Tracking Mouse Control System")
        if EMOTE_DETECTION_ENABLED:
            print("with Emote Detection")
        print("="*50)

        # =====================================================
        # EMOTE STATE VARIABLE
        # =====================================================
        # Possible values: "none", "Princess Yawn", "Goblin Facepalm", "Wizard Magic"
        self.current_emote_state = "none"
        self.emote_state_display_time = 3.0  # How long to disable clicking
        self.emote_state_start_time = 0

        # Emote to key mapping
        self.emote_key_map = {
            "Princess Yawn": "p",
            "Goblin Facepalm": "g",
            "Wizard Magic": "w"
        }

        # Initialize components
        print("Initializing camera...")
        self.camera = CameraHandler(
            camera_index=Config.CAMERA_INDEX,
            width=Config.CAMERA_WIDTH,
            height=Config.CAMERA_HEIGHT
        )

        print("Initializing hand detector...")
        self.detector = HandDetector(
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.4
        )

        print("Initializing gesture recognizer...")
        self.recognizer = GestureRecognizer(
            smoothing_frames=Config.GESTURE_SMOOTHING_FRAMES,
            closed_threshold=Config.CLOSED_HAND_THRESHOLD
        )

        print("Initializing mouse controller...")
        self.controller = MouseController(
            smoothing_factor=Config.CURSOR_SMOOTHING_FACTOR,
            click_cooldown=Config.CLICK_COOLDOWN,
            screen_margin=Config.SCREEN_MARGIN,
            movement_threshold=Config.MOVEMENT_THRESHOLD
        )

        # Initialize emote detection
        self.emote_matcher = None
        self.emote_check_interval = 0.2
        self.last_emote_check = 0
        self.current_emote_result = None

        if EMOTE_DETECTION_ENABLED:
            print("Initializing emote detection...")
            try:
                self.emote_matcher = UltimateEmoteMatcher(
                    confidence_threshold=0.65,
                    match_hold_time=1.0,
                    model_path="emote_model_ultimate.pkl"
                )
                print("Emote detection ready!")
            except Exception as e:
                print(f"Emote detection failed: {e}")
                self.emote_matcher = None

        # FPS tracking
        self.fps = 0
        self.frame_count = 0
        self.fps_start_time = time.time()

        # Running state
        self.running = False

        print("Initialization complete!")
        print("="*50)

    def calculate_fps(self):
        """Calculate and update FPS"""
        self.frame_count += 1
        elapsed = time.time() - self.fps_start_time
        if elapsed > 1.0:
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.fps_start_time = time.time()

    def update_emote_state(self):
        """Update emote state based on time elapsed"""
        current_time = time.time()
        
        # If emote state is active and time has elapsed, reset to "none"
        if self.current_emote_state != "none":
            if current_time - self.emote_state_start_time > self.emote_state_display_time:
                print(f"Emote state cleared: {self.current_emote_state} -> none")
                self.current_emote_state = "none"

    def trigger_emote_action(self, emote_name):
        """
        Trigger keyboard action for emote
        
        Args:
            emote_name: Name of the emote triggered
        """
        try:
            # Press 'e' first
            pyautogui.press('e')
            print(f"Pressed: 'e'")
            
            # Small delay
            time.sleep(0.1)
            
            # Press emote-specific key
            if emote_name in self.emote_key_map:
                key = self.emote_key_map[emote_name]
                pyautogui.press(key)
                print(f"Pressed: '{key}' for {emote_name}")
            else:
                print(f"Warning: No key mapping for {emote_name}")
                
        except Exception as e:
            print(f"Error pressing keys: {e}")

    def check_emote(self, frame):
        """Check for emote detection"""
        if not self.emote_matcher:
            return None

        current_time = time.time()

        # Check periodically
        if current_time - self.last_emote_check < self.emote_check_interval:
            return self.current_emote_result

        self.last_emote_check = current_time

        try:
            # ENABLE EMOTE MODE (disable clicking)
            self.recognizer.set_emote_mode(True)
            
            # Run emote detection
            result = self.emote_matcher.match_emote(frame)
            
            # DISABLE EMOTE MODE
            self.recognizer.set_emote_mode(False)

            # Store result
            self.current_emote_result = result

            # Check if emote was triggered
            if result.get('triggered'):
                emote_name = result['emote']
                
                # UPDATE EMOTE STATE
                self.current_emote_state = emote_name
                self.emote_state_start_time = current_time
                
                print(f"\n🎭 EMOTE TRIGGERED: {emote_name}")
                print(f"Confidence: {result['confidence']:.1%}")
                
                # TRIGGER KEYBOARD ACTION
                self.trigger_emote_action(emote_name)
                
                print(f"State: {self.current_emote_state}")
                print(f"Clicking: DISABLED for {self.emote_state_display_time}s\n")

            return result

        except Exception as e:
            self.recognizer.set_emote_mode(False)
            print(f"Emote detection error: {e}")
            return None

    def should_allow_clicking(self):
        """
        Determine if clicking should be allowed based on emote state
        
        Returns:
            bool: True if clicking allowed, False otherwise
        """
        return self.current_emote_state == "none"

    def draw_ui(self, frame, gesture, hand_detected):
        """Draw minimal UI overlay"""
        h, w, _ = frame.shape

        # Semi-transparent overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 150), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)

        y_offset = 30

        # FPS
        if Config.SHOW_FPS:
            fps_color = Config.COLOR_FPS_GOOD
            if self.fps < 15:
                fps_color = Config.COLOR_FPS_BAD
            elif self.fps < 25:
                fps_color = Config.COLOR_FPS_MEDIUM

            cv2.putText(frame, f"FPS: {self.fps:.1f}", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, fps_color, 2)
            y_offset += 35

        # Hand status
        cv2.putText(frame, f"Hand: {'DETECTED' if hand_detected else 'NOT DETECTED'}", 
                   (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, 
                   (0, 255, 0) if hand_detected else (0, 0, 255), 2)
        y_offset += 35

        # Gesture
        if gesture:
            cursor_info = self.controller.get_cursor_info()
            
            # Check if clicking is allowed
            clicking_allowed = self.should_allow_clicking()
            
            if not clicking_allowed:
                gesture_text = "EMOTE MODE"
                color = (255, 0, 255)
            elif cursor_info['is_dragging']:
                gesture_text = "DRAGGING"
                color = (255, 0, 255)
            elif gesture == "open":
                gesture_text = "HOVER"
                color = (0, 255, 0)
            else:
                gesture_text = "CLOSED"
                color = (0, 0, 255)

            cv2.putText(frame, f"Gesture: {gesture_text}", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            y_offset += 35

        # EMOTE STATE INDICATOR (small, top-left)
        if self.current_emote_state != "none":
            state_color = (255, 0, 0)  # Red when emote active
            state_text = f"Emote: {self.current_emote_state}"
        else:
            state_color = (0, 255, 0)  # Green when normal
            state_text = "Emote: Ready"
        
        cv2.putText(frame, state_text, (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, state_color, 2)

        # Instructions (bottom)
        instructions = [
            "RIGHT HAND: Mouse | BOTH HANDS: Emotes",
            "Press 'Q' to quit"
        ]

        y_pos = h - 60
        for instruction in instructions:
            cv2.putText(frame, instruction, (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y_pos += 25

    def process_frame(self):
        """Process a single frame"""
        ret, frame = self.camera.read_frame()
        if not ret:
            return False

        # Update emote state (auto-clear after time)
        self.update_emote_state()

        # Detect hands
        frame, hands_data = self.detector.find_hands(frame, draw=Config.DRAW_HAND_LANDMARKS)

        gesture = None
        hand_detected = len(hands_data) > 0

        # Use RIGHT hand for cursor
        right_hand = None
        for hand in hands_data:
            if hand['handedness'].lower() == 'right':
                right_hand = hand
                break

        if right_hand:
            landmarks = right_hand['landmarks']
            hand_x = landmarks[0]['x']
            hand_y = landmarks[0]['y']
            gesture = self.recognizer.get_smoothed_gesture(landmarks)

            # ONLY allow clicking if emote state is "none"
            if self.should_allow_clicking():
                try:
                    self.controller.update(hand_x, hand_y, gesture)
                except Exception as e:
                    print(f"Mouse control error: {e}")
                    return False
            else:
                # Move cursor but don't click
                try:
                    self.controller.move_cursor(hand_x, hand_y)
                except Exception as e:
                    print(f"Mouse control error: {e}")
                    return False

        # Check for emotes
        self.check_emote(frame)

        # Calculate FPS
        self.calculate_fps()

        # Draw minimal UI
        if Config.SHOW_CAMERA_FEED:
            self.draw_ui(frame, gesture, hand_detected)
            cv2.imshow("Hand Mouse Control", frame)

        return True

    def run(self):
        """Run main loop"""
        try:
            self.camera.start()
            self.running = True

            print("\n" + "="*50)
            print("APPLICATION RUNNING")
            print("="*50)
            print("\nEMOTE KEYBOARD SHORTCUTS:")
            print("  Princess Yawn → Press 'e' then 'p'")
            print("  Goblin Facepalm → Press 'e' then 'g'")
            print("  Wizard Magic → Press 'e' then 'w'")
            print("\nEMOTE STATE SYSTEM:")
            print("  - State: 'none' = Normal clicking enabled")
            print("  - State: 'Emote Active' = Clicking disabled for 3s")
            print("\nControls:")
            print("  RIGHT HAND: Mouse cursor")
            print("  BOTH HANDS: Emote detection")
            print("\nPress 'Q' to quit")
            print("="*50 + "\n")

            time.sleep(3)

            while self.running:
                if not self.process_frame():
                    break

                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == ord('Q'):
                    print("\nQuit command received")
                    break

                if Config.MAX_FPS > 0:
                    time.sleep(1.0 / Config.MAX_FPS)

        except KeyboardInterrupt:
            print("\nInterrupted by user")

        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()

        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        print("\nCleaning up...")
        self.running = False

        if hasattr(self, 'controller'):
            self.controller.cleanup()
        if hasattr(self, 'detector'):
            self.detector.release()
        if hasattr(self, 'camera'):
            self.camera.release()
        if hasattr(self, 'emote_matcher') and self.emote_matcher:
            self.emote_matcher.release()

        cv2.destroyAllWindows()
        print("Cleanup complete. Goodbye!")


def main():
    """Main entry point"""
    app = HandMouseApp()
    app.run()


if __name__ == "__main__":
    main()