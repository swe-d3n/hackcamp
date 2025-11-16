"""
Clash Royale Emote Controller - Main Integration
Combines face detection, hand gestures, and BlueStacks keyboard control
"""

import cv2
import time
import numpy as np
from camera_handler import CameraHandler
from hand_detector import HandDetector
from face_detector import FaceDetector
from emote_matcher import EmoteMatcher
from emote_clicker import EmoteClicker
from config import ACTIVE_CONFIG as Config


class ClashRoyaleEmoteApp:
    def __init__(self):
        """Initialize the Clash Royale emote control application"""
        print("="*60)
        print("CLASH ROYALE EMOTE CONTROLLER")
        print("="*60)
        
        # Initialize camera
        print("Initializing camera...")
        self.camera = CameraHandler(
            camera_index=Config.CAMERA_INDEX,
            width=Config.CAMERA_WIDTH,
            height=Config.CAMERA_HEIGHT
        )
        
        # Initialize detectors
        print("Initializing hand detector...")
        self.hand_detector = HandDetector(
            max_num_hands=Config.MAX_NUM_HANDS,
            min_detection_confidence=Config.MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=Config.MIN_TRACKING_CONFIDENCE,
            model_complexity=getattr(Config, 'MODEL_COMPLEXITY', 0)
        )
        
        print("Initializing face detector...")
        self.face_detector = FaceDetector()
        
        # Initialize emote matcher
        print("Initializing emote matcher...")
        self.emote_matcher = EmoteMatcher()
        
        # Initialize BlueStacks controller
        print("Initializing BlueStacks controller...")
        self.emote_controller = EmoteClicker(
            emote_button_key='e',  # Customize this
            cooldown=1.5
        )
        
        # FPS tracking
        self.fps = 0
        self.frame_count = 0
        self.fps_start_time = time.time()
        
        # Current detection state
        self.current_expression = "neutral"
        self.current_gesture = "none"
        self.last_matched_emote = None
        
        # Running state
        self.running = False
        
        print("Initialization complete!")
        print("="*60)
    
    def calculate_fps(self):
        """Calculate and update FPS"""
        self.frame_count += 1
        elapsed = time.time() - self.fps_start_time
        if elapsed > 1.0:
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.fps_start_time = time.time()
    
    def recognize_hand_gesture(self, landmarks):
        """
        Recognize hand gesture from landmarks
        Returns: gesture name (e.g., "thumbs_up", "peace", "fist", etc.)
        """
        if landmarks is None or len(landmarks) < 21:
            return "none"
        
        # Simple gesture recognition based on finger positions
        # You can expand this with more sophisticated gesture detection
        
        # Check for thumbs up
        thumb_tip = landmarks[4]
        thumb_base = landmarks[2]
        index_tip = landmarks[8]
        
        # Thumbs up: thumb extended up, other fingers closed
        if thumb_tip['y'] < thumb_base['y'] - 0.1:
            # Check if other fingers are closed
            fingers_closed = all(
                landmarks[tip]['y'] > landmarks[tip-2]['y']
                for tip in [8, 12, 16, 20]
            )
            if fingers_closed:
                return "thumbs_up"
        
        # Peace sign: index and middle extended, others closed
        index_extended = landmarks[8]['y'] < landmarks[6]['y']
        middle_extended = landmarks[12]['y'] < landmarks[10]['y']
        ring_closed = landmarks[16]['y'] > landmarks[14]['y']
        pinky_closed = landmarks[20]['y'] > landmarks[18]['y']
        
        if index_extended and middle_extended and ring_closed and pinky_closed:
            return "peace"
        
        # Open palm: all fingers extended
        all_extended = all(
            landmarks[tip]['y'] < landmarks[tip-2]['y']
            for tip in [8, 12, 16, 20]
        )
        if all_extended:
            return "open_palm"
        
        # Fist: all fingers closed
        all_closed = all(
            landmarks[tip]['y'] > landmarks[tip-2]['y']
            for tip in [8, 12, 16, 20]
        )
        if all_closed:
            return "fist"
        
        # Pointing: only index extended
        if index_extended and not middle_extended and ring_closed and pinky_closed:
            return "pointing"
        
        return "none"
    
    def draw_ui(self, frame):
        """Draw UI overlay on frame"""
        h, w, _ = frame.shape
        
        # Semi-transparent overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 200), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
        
        y_offset = 30
        
        # FPS
        cv2.putText(frame, f"FPS: {self.fps:.1f}", (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        y_offset += 35
        
        # Expression
        cv2.putText(frame, f"Expression: {self.current_expression}", (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        y_offset += 35
        
        # Gesture
        cv2.putText(frame, f"Gesture: {self.current_gesture}", (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        y_offset += 35
        
        # Last matched emote
        if self.last_matched_emote:
            cv2.putText(frame, f"Emote: {self.last_matched_emote}", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            y_offset += 35
        
        # Cooldown status
        if not self.emote_controller.is_ready():
            remaining = self.emote_controller.get_cooldown_remaining()
            cv2.putText(frame, f"Cooldown: {remaining:.1f}s", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        else:
            cv2.putText(frame, "Ready to emote!", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Instructions
        instructions = [
            "Make facial expressions + hand gestures",
            "Emotes trigger automatically in BlueStacks",
            "Press 'Q' to quit"
        ]
        
        y_pos = h - 90
        for instruction in instructions:
            cv2.putText(frame, instruction, (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y_pos += 25
    
    def process_frame(self):
        """Process a single frame"""
        ret, frame = self.camera.read_frame()
        if not ret:
            return False
        
        # Detect face and expression
        frame, face_data = self.face_detector.detect_face(frame, draw=True)
        if face_data:
            self.current_expression = face_data['expression']
        else:
            self.current_expression = "neutral"
        
        # Detect hand and gesture
        frame, hands_data = self.hand_detector.find_hands(frame, draw=True)
        if hands_data and len(hands_data) > 0:
            landmarks = hands_data[0]['landmarks']
            self.current_gesture = self.recognize_hand_gesture(landmarks)
        else:
            self.current_gesture = "none"
        
        # Try to match emote
        if self.current_gesture != "none":
            matched_emote = self.emote_matcher.match_emote(
                self.current_expression,
                self.current_gesture
            )
            
            if matched_emote:
                print(f"\n🎯 MATCHED: {matched_emote}")
                print(f"   Expression: {self.current_expression}")
                print(f"   Gesture: {self.current_gesture}")
                
                # Try to trigger emote in BlueStacks
                if self.emote_controller.is_ready():
                    success = self.emote_controller.trigger_emote(matched_emote)
                    if success:
                        self.last_matched_emote = matched_emote
                        # Clear history to prevent re-triggering
                        self.emote_matcher.clear_history()
        
        # Calculate FPS
        self.calculate_fps()
        
        # Draw UI
        self.draw_ui(frame)
        
        # Show frame
        cv2.imshow("Clash Royale Emote Control", frame)
        
        return True
    
    def run(self):
        """Run the main application loop"""
        try:
            self.camera.start()
            self.running = True
            
            print("\n" + "="*60)
            print("APPLICATION RUNNING")
            print("="*60)
            print("\nInstructions:")
            print("  • Make facial expressions (laughing, crying, angry, etc.)")
            print("  • Show hand gestures (thumbs up, peace sign, fist, etc.)")
            print("  • Matching emotes will trigger automatically in BlueStacks")
            print("  • Press 'Q' to quit")
            print("\nMake sure BlueStacks is running and focused!")
            print("="*60 + "\n")
            
            # Give user time to prepare
            time.sleep(3)
            
            # Main loop
            while self.running:
                if not self.process_frame():
                    break
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == ord('Q'):
                    print("\nQuit command received")
                    break
        
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
        
        if hasattr(self, 'face_detector'):
            self.face_detector.release()
        if hasattr(self, 'hand_detector'):
            self.hand_detector.release()
        if hasattr(self, 'camera'):
            self.camera.release()
        
        cv2.destroyAllWindows()
        print("Cleanup complete. Goodbye!")


def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("CLASH ROYALE EMOTE CONTROLLER")
    print("="*60)
    print("\nSetup Checklist:")
    print("  ✓ BlueStacks is installed and running")
    print("  ✓ Clash Royale is open in BlueStacks")
    print("  ✓ BlueStacks key mapping is configured:")
    print("      - 'E' opens emote menu")
    print("      - Number/letter keys trigger emotes")
    print("  ✓ Camera has good lighting")
    print("  ✓ Plain background behind you")
    print("\nReady to start?")
    print("="*60)
    
    input("Press ENTER to begin...")
    
    app = ClashRoyaleEmoteApp()
    app.run()


if __name__ == "__main__":
    main()