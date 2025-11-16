"""
Clash Royale Emote Controller
Detects facial expressions and hand gestures to automatically click emotes
"""

import cv2
import time
import numpy as np
import pyautogui
from camera_handler import CameraHandler
from hand_detector import HandDetector
from face_detector import FaceDetector
from emote_matcher import EmoteMatcher
from config import ACTIVE_CONFIG as Config


class ClashRoyaleEmoteController:
    def __init__(self):
        """Initialize the Clash Royale emote controller"""
        print("="*50)
        print("Clash Royale Emote Controller")
        print("="*50)
        
        # Initialize components
        print("Initializing camera...")
        self.camera = CameraHandler(
            camera_index=Config.CAMERA_INDEX,
            width=Config.CAMERA_WIDTH,
            height=Config.CAMERA_HEIGHT
        )
        
        print("Initializing hand detector...")
        self.hand_detector = HandDetector(
            max_num_hands=Config.MAX_NUM_HANDS,
            min_detection_confidence=Config.MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=Config.MIN_TRACKING_CONFIDENCE
        )
        
        print("Initializing face detector...")
        self.face_detector = FaceDetector()
        
        print("Initializing emote matcher...")
        self.emote_matcher = EmoteMatcher()
        
        # FPS tracking
        self.fps = 0
        self.frame_count = 0
        self.fps_start_time = time.time()
        
        # Running state
        self.running = False
        
        # Emote click cooldown
        self.last_emote_time = 0
        self.emote_cooldown = 2.0  # 2 seconds between emotes
        
        # Current detection state
        self.current_expression = None
        self.current_gesture = None
        self.matched_emote = None
        
        print("Initialization complete!")
        print("="*50)
        
    def count_fingers(self, landmarks):
        """Count extended fingers"""
        finger_tips = [4, 8, 12, 16, 20]
        finger_bases = [2, 5, 9, 13, 17]
        fingers_up = 0
        
        # Thumb (check if tip is right/left of base)
        if landmarks[finger_tips[0]]['x'] > landmarks[finger_bases[0]]['x']:
            fingers_up += 1
        
        # Other fingers (check if tip is above base)
        for i in range(1, 5):
            if landmarks[finger_tips[i]]['y'] < landmarks[finger_bases[i]]['y']:
                fingers_up += 1
        
        return fingers_up
    
    def recognize_hand_gesture(self, landmarks):
        """
        Recognize hand gesture from landmarks
        
        Returns:
            str: Gesture name
        """
        finger_count = self.count_fingers(landmarks)
        
        # Get key points
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        
        # Calculate distance between two points
        def distance(p1, p2):
            return np.sqrt((p1['x'] - p2['x'])**2 + (p1['y'] - p2['y'])**2)
        
        # Fist: All fingers down
        if finger_count == 0:
            return "fist"
        
        # Thumbs up: Only thumb up
        if finger_count == 1 and landmarks[4]['y'] < landmarks[2]['y']:
            return "thumbs_up"
        
        # Thumbs down: Only thumb down
        if finger_count == 1 and landmarks[4]['y'] > landmarks[2]['y']:
            return "thumbs_down"
        
        # Peace sign: Index and middle finger up
        if finger_count == 2:
            index_up = landmarks[8]['y'] < landmarks[6]['y']
            middle_up = landmarks[12]['y'] < landmarks[10]['y']
            if index_up and middle_up:
                return "peace"
        
        # Pointing: Only index finger up
        if finger_count == 1:
            if landmarks[8]['y'] < landmarks[6]['y']:
                return "pointing"
        
        # Open palm: All fingers up
        if finger_count >= 4:
            # Check if fingers are spread (for waving detection)
            index_middle_dist = distance(index_tip, middle_tip)
            if index_middle_dist > 0.08:
                return "waving"
            return "open_palm"
        
        # Three fingers
        if finger_count == 3:
            return "three_fingers"
        
        return "unknown"
        
    def calculate_fps(self):
        """Calculate and update FPS"""
        self.frame_count += 1
        elapsed = time.time() - self.fps_start_time
        if elapsed > 1.0:
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.fps_start_time = time.time()
    
    def click_emote(self, emote_name, click_x=None, click_y=None):
        """
        Click the emote button and then the specific emote at the hand position
        
        Args:
            emote_name: Name of the emote to click
            click_x: X coordinate from hand position (screen coordinates)
            click_y: Y coordinate from hand position (screen coordinates)
        """
        # Check cooldown
        current_time = time.time()
        if current_time - self.last_emote_time < self.emote_cooldown:
            return
        
        try:
            # Get emote position from config
            emote_position = Config.EMOTE_POSITIONS.get(emote_name)
            if not emote_position:
                print(f"Warning: Emote '{emote_name}' not found in config")
                return
            
            print(f"\n>>> CLICKING EMOTE: {emote_name} <<<")
            
            # Click emote button to open menu
            pyautogui.click(Config.EMOTE_BUTTON_POS[0], Config.EMOTE_BUTTON_POS[1])
            time.sleep(0.15)  # Wait for menu to open
            
            # Click specific emote
            pyautogui.click(emote_position[0], emote_position[1])
            time.sleep(0.1)  # Wait for emote selection
            
            # Click at hand position if provided, otherwise click center screen
            if click_x is not None and click_y is not None:
                print(f"    Clicking at hand position: ({click_x}, {click_y})")
                pyautogui.click(click_x, click_y)
            else:
                # Click at screen center as fallback
                screen_width, screen_height = pyautogui.size()
                pyautogui.click(screen_width // 2, screen_height // 2)
            
            self.last_emote_time = current_time
            
        except Exception as e:
            print(f"Error clicking emote: {e}")
    
    def draw_ui(self, frame, hand_screen_x=None, hand_screen_y=None):
        """Draw UI overlay on frame"""
        h, w, _ = frame.shape
        
        # Semi-transparent overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 230), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
        
        y_offset = 30
        
        # FPS
        fps_color = (0, 255, 0) if self.fps >= 25 else (0, 165, 255) if self.fps >= 15 else (0, 0, 255)
        cv2.putText(frame, f"FPS: {self.fps:.1f}", (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, fps_color, 2)
        y_offset += 35
        
        # Facial expression
        expr_color = (0, 255, 0) if self.current_expression else (128, 128, 128)
        expr_text = f"Expression: {self.current_expression if self.current_expression else 'None'}"
        cv2.putText(frame, expr_text, (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, expr_color, 2)
        y_offset += 35
        
        # Hand gesture
        gesture_color = (0, 255, 0) if self.current_gesture else (128, 128, 128)
        gesture_text = f"Gesture: {self.current_gesture if self.current_gesture else 'None'}"
        cv2.putText(frame, gesture_text, (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, gesture_color, 2)
        y_offset += 35
        
        # Matched emote
        if self.matched_emote:
            cv2.putText(frame, f"MATCHED: {self.matched_emote}", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            y_offset += 35
        
        # Hand position on screen
        if Config.SHOW_CURSOR_POSITION and hand_screen_x is not None:
            cv2.putText(frame,
                       f"Hand Pos: ({hand_screen_x}, {hand_screen_y})",
                       (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 0), 2)
            y_offset += 35
        
        # Cooldown indicator
        time_since_last = time.time() - self.last_emote_time
        if time_since_last < self.emote_cooldown:
            cooldown_remaining = self.emote_cooldown - time_since_last
            cv2.putText(frame, f"Cooldown: {cooldown_remaining:.1f}s", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
        
        # Instructions
        instructions = [
            "Make facial expressions and hand gestures to trigger emotes!",
            "Press 'Q' to quit | Press 'C' to calibrate positions"
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
        
        # Detect hands
        frame, hands_data = self.hand_detector.find_hands(frame, draw=True)
        
        # Detect face and expression
        frame, face_data = self.face_detector.detect_face(frame, draw=True)
        
        # Reset current state
        self.current_expression = None
        self.current_gesture = None
        self.matched_emote = None
        hand_screen_x = None
        hand_screen_y = None
        
        # Get facial expression
        if face_data:
            self.current_expression = face_data.get('expression')
        
        # Get hand gesture and position
        if hands_data:
            landmarks = hands_data[0]['landmarks']
            self.current_gesture = self.recognize_hand_gesture(landmarks)
            
            # Get hand position for clicking (use index finger tip or palm center)
            # Using index finger tip (landmark 8) for pointing accuracy
            index_finger = landmarks[8]
            
            # Convert normalized coordinates to screen coordinates
            screen_width, screen_height = pyautogui.size()
            # Flip x coordinate (camera is mirrored)
            hand_screen_x = int((1 - index_finger['x']) * screen_width)
            hand_screen_y = int(index_finger['y'] * screen_height)
        
        # Match emote if both detected
        if self.current_expression and self.current_gesture:
            matched_emote = self.emote_matcher.match_emote(
                self.current_expression,
                self.current_gesture
            )
            
            if matched_emote:
                self.matched_emote = matched_emote
                # Click emote at the hand position
                self.click_emote(matched_emote, hand_screen_x, hand_screen_y)
        
        # Calculate FPS
        self.calculate_fps()
        
        # Draw UI
        if Config.SHOW_CAMERA_FEED:
            self.draw_ui(frame, hand_screen_x, hand_screen_y)
            cv2.imshow("Clash Royale Emote Controller", frame)
        
        return True
    
    def calibrate_positions(self):
        """Help user calibrate emote button positions"""
        print("\n" + "="*50)
        print("EMOTE POSITION CALIBRATION")
        print("="*50)
        print("Move your mouse to the emote button and press ENTER")
        input("Press ENTER when ready...")
        
        button_x, button_y = pyautogui.position()
        print(f"Emote button position recorded: ({button_x}, {button_y})")
        
        print("\nNow move to each emote position and press ENTER:")
        emote_positions = {}
        
        for emote_name in ["laughing", "crying", "angry", "king_thumbs_up", 
                          "thumbs_up", "chicken", "goblin_kiss", "princess_yawn",
                          "wow", "thinking", "screaming", "king_laugh",
                          "goblin_laugh", "princess_cry", "goblin_angry"]:
            input(f"\nMove to '{emote_name}' emote and press ENTER...")
            x, y = pyautogui.position()
            emote_positions[emote_name] = (x, y)
            print(f"  Position recorded: ({x}, {y})")
        
        print("\n" + "="*50)
        print("Add these to your config.py:")
        print("="*50)
        print(f"EMOTE_BUTTON_POS = ({button_x}, {button_y})")
        print(f"\nEMOTE_POSITIONS = {{")
        for name, pos in emote_positions.items():
            print(f'    "{name}": {pos},')
        print("}")
        print("="*50)
    
    def run(self):
        """Run the main application loop"""
        try:
            self.camera.start()
            self.running = True
            
            print("\n" + "="*50)
            print("APPLICATION RUNNING")
            print("="*50)
            print("\nMake facial expressions and hand gestures!")
            print("The system will automatically click matching emotes.")
            print("\nControls:")
            print("  • Press 'Q' = Quit")
            print("  • Press 'C' = Calibrate emote positions")
            print("\nStarting in 3 seconds...")
            print("="*50 + "\n")
            
            time.sleep(3)
            
            while self.running:
                if not self.process_frame():
                    break
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == ord('Q'):
                    print("\nQuit command received")
                    break
                elif key == ord('c') or key == ord('C'):
                    self.cleanup()
                    self.calibrate_positions()
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
        
        if hasattr(self, 'hand_detector'):
            self.hand_detector.release()
        
        if hasattr(self, 'face_detector'):
            self.face_detector.release()
        
        if hasattr(self, 'camera'):
            self.camera.release()
        
        cv2.destroyAllWindows()
        print("Cleanup complete!")


def main():
    """Main entry point"""
    app = ClashRoyaleEmoteController()
    app.run()


if __name__ == "__main__":
    main()