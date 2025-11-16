"""
Main Application with Clash Emote Recognition
Hand Tracking Mouse Control with Clash Royale Emote Detection
"""

import cv2
import time
import sys
sys.path.insert(0, '/mnt/user-data/uploads')

from camera_handler import CameraHandler
from hand_detector import HandDetector
from gesture_recognizer import GestureRecognizer
from mouse_controller import MouseController
from config import ACTIVE_CONFIG as Config
from clash_emote_recognizer import ClashEmoteRecognizer


class HandMouseEmoteApp:
    def __init__(self):
        """Initialize the hand mouse control application with emote detection"""
        print("="*60)
        print("Hand Tracking Mouse Control with Clash Emotes")
        print("="*60)
        
        # Initialize components
        print("Initializing camera...")
        self.camera = CameraHandler(
            camera_index=Config.CAMERA_INDEX,
            width=Config.CAMERA_WIDTH,
            height=Config.CAMERA_HEIGHT
        )
        
        print("Initializing hand detector (2 hands for emotes)...")
        self.detector = HandDetector(
            max_num_hands=2,  # Need 2 hands for emote detection
            min_detection_confidence=Config.MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=Config.MIN_TRACKING_CONFIDENCE,
            model_complexity=getattr(Config, 'MODEL_COMPLEXITY', 0)
        )
        
        print("Initializing gesture recognizer...")
        self.gesture_recognizer = GestureRecognizer(
            smoothing_frames=Config.GESTURE_SMOOTHING_FRAMES,
            closed_threshold=Config.CLOSED_HAND_THRESHOLD
        )
        
        print("Initializing Clash emote recognizer...")
        self.emote_recognizer = ClashEmoteRecognizer(
            smoothing_frames=8,
            confidence_threshold=0.6
        )
        
        print("Initializing mouse controller...")
        self.controller = MouseController(
            smoothing_factor=Config.CURSOR_SMOOTHING_FACTOR,
            click_cooldown=Config.CLICK_COOLDOWN,
            screen_margin=Config.SCREEN_MARGIN,
            movement_threshold=Config.MOVEMENT_THRESHOLD,
            tracking_zone_min=Config.TRACKING_ZONE_MIN,
            tracking_zone_max=Config.TRACKING_ZONE_MAX
        )
        
        # FPS tracking
        self.fps = 0
        self.frame_count = 0
        self.fps_start_time = time.time()
        
        # Mode: "mouse" or "emote"
        self.mode = "mouse"
        
        # Emote trigger log
        self.last_emote_triggered = None
        self.last_emote_time = 0
        
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
    
    def handle_emote_trigger(self, emote):
        """
        Handle when an emote is triggered
        
        Args:
            emote: The emote code that was triggered
        """
        self.last_emote_triggered = emote
        self.last_emote_time = time.time()
        
        # You can add custom actions here for each emote
        if emote == "GOBLIN_CRYING":
            print("🎮 GOBLIN CRYING emote triggered! 😢")
            # Could trigger a keyboard shortcut or action here
            
        elif emote == "WIZARD_67":
            print("🎮 WIZARD 67 emote triggered! 🤷")
            # Could trigger a different action
            
        elif emote == "PRINCESS_YAWNING":
            print("🎮 PRINCESS YAWNING emote triggered! 🥱")
            # Could trigger another action
    
    def draw_ui(self, frame, hands_data, gesture, emote_result):
        """
        Draw UI overlay on frame
        
        Args:
            frame: Camera frame
            hands_data: Detected hands data
            gesture: Current gesture for mouse control
            emote_result: Emote detection result
        """
        h, w = frame.shape[:2]
        
        # Draw tracking zone
        if Config.SHOW_TRACKING_ZONE:
            zone_x1 = int(w * Config.TRACKING_ZONE_MIN)
            zone_y1 = int(h * Config.TRACKING_ZONE_MIN)
            zone_x2 = int(w * Config.TRACKING_ZONE_MAX)
            zone_y2 = int(h * Config.TRACKING_ZONE_MAX)
            cv2.rectangle(frame, (zone_x1, zone_y1), (zone_x2, zone_y2),
                         (0, 255, 255), 2)
        
        # Semi-transparent overlay for UI
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 200), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)
        
        y_offset = 30
        
        # FPS
        if Config.SHOW_FPS:
            fps_color = (0, 255, 0) if self.fps > 25 else (0, 255, 255) if self.fps > 15 else (0, 0, 255)
            cv2.putText(frame, f"FPS: {self.fps:.1f}", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, fps_color, 2)
            y_offset += 30
        
        # Hands detected
        cv2.putText(frame, f"Hands: {len(hands_data)}", (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        y_offset += 30
        
        # Mode indicator
        mode_color = (0, 255, 0) if self.mode == "mouse" else (255, 165, 0)
        cv2.putText(frame, f"Mode: {self.mode.upper()}", (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, mode_color, 2)
        y_offset += 30
        
        # Emote detection status
        if emote_result['emote']:
            emote_name = self.emote_recognizer.get_emote_display_name(emote_result['emote'])
            color = (0, 255, 0) if emote_result['triggered'] else (0, 255, 255)
            
            cv2.putText(frame, f"Emote: {emote_name}", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            y_offset += 25
            
            # Progress bar
            bar_width = int(250 * emote_result['hold_progress'])
            cv2.rectangle(frame, (10, y_offset), (260, y_offset + 20), (100, 100, 100), -1)
            cv2.rectangle(frame, (10, y_offset), (10 + bar_width, y_offset + 20), color, -1)
            cv2.rectangle(frame, (10, y_offset), (260, y_offset + 20), (255, 255, 255), 2)
            
            if emote_result['triggered']:
                cv2.putText(frame, "TRIGGERED!", (270, y_offset + 15),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            y_offset += 35
        else:
            cv2.putText(frame, "Emote: None", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (150, 150, 150), 2)
            y_offset += 35
        
        # Mouse control status (only for single hand)
        if len(hands_data) == 1 and gesture:
            cursor_info = self.controller.get_cursor_info()
            
            if cursor_info['is_dragging']:
                status = "DRAGGING"
                color = (255, 0, 255)
            elif gesture == "closed":
                status = "CLICK"
                color = (0, 0, 255)
            else:
                status = "HOVER"
                color = (0, 255, 0)
            
            cv2.putText(frame, f"Mouse: {status}", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Last triggered emote (show for 3 seconds)
        if self.last_emote_triggered and time.time() - self.last_emote_time < 3.0:
            emote_display = self.emote_recognizer.get_emote_display_name(self.last_emote_triggered)
            cv2.putText(frame, f"Last: {emote_display}", (w - 300, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Instructions at bottom
        instructions = [
            "EMOTES: Goblin Crying (fists to eyes) | Wizard 67 (shrug) | Princess Yawn (hand to mouth)",
            "MOUSE: Single hand - Open=Move | Close=Click/Drag | Press 'Q' to quit"
        ]
        
        y_pos = h - 50
        for inst in instructions:
            cv2.putText(frame, inst, (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
            y_pos += 22
    
    def process_frame(self):
        """Process a single frame"""
        ret, frame = self.camera.read_frame()
        if not ret:
            print("Failed to read frame")
            return False
        
        # Detect hands
        frame, hands_data = self.detector.find_hands(frame, draw=Config.DRAW_HAND_LANDMARKS)
        
        gesture = None
        emote_result = {'emote': None, 'confidence': 0, 'triggered': False, 'hold_progress': 0}
        
        # Always check for emotes (works with 1 or 2 hands)
        if hands_data:
            emote_result = self.emote_recognizer.get_smoothed_emote(hands_data)
            
            # Handle emote trigger
            if emote_result['triggered']:
                self.handle_emote_trigger(emote_result['emote'])
        
        # Mouse control only with single hand and no emote detected
        if len(hands_data) == 1 and not emote_result['emote']:
            self.mode = "mouse"
            landmarks = hands_data[0]['landmarks']
            
            # Get wrist position for cursor control
            wrist = landmarks[0]
            hand_x = wrist['x']
            hand_y = wrist['y']
            
            # Recognize gesture for clicking
            gesture = self.gesture_recognizer.get_smoothed_gesture(landmarks)
            
            # Update mouse
            try:
                self.controller.update(hand_x, hand_y, gesture)
            except Exception as e:
                print(f"Mouse control error: {e}")
        elif emote_result['emote']:
            self.mode = "emote"
        else:
            self.mode = "idle"
        
        # Calculate FPS
        self.calculate_fps()
        
        # Draw UI
        if Config.SHOW_CAMERA_FEED:
            self.draw_ui(frame, hands_data, gesture, emote_result)
            cv2.imshow("Hand Mouse Control + Clash Emotes", frame)
        
        return True
    
    def run(self):
        """Run the main application loop"""
        try:
            self.camera.start()
            self.running = True
            
            print("\n" + "="*60)
            print("APPLICATION RUNNING")
            print("="*60)
            print("\nCLASH EMOTE GESTURES:")
            print("  • Goblin Crying: Both fists near eyes 😢")
            print("  • Wizard 67: Both hands open, palms up (shrug) 🤷")
            print("  • Princess Yawning: One hand near mouth 🥱")
            print("\nMOUSE CONTROL (single hand):")
            print("  • Open hand = Move cursor")
            print("  • Close fist = Click/Drag")
            print("\nHold an emote gesture for 1 second to trigger!")
            print("Press 'Q' to quit | Move mouse to corner = Emergency stop")
            print("\nStarting in 3 seconds...")
            print("="*60 + "\n")
            
            time.sleep(3)
            
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
        
        if hasattr(self, 'controller'):
            self.controller.cleanup()
        
        if hasattr(self, 'detector'):
            self.detector.release()
        
        if hasattr(self, 'camera'):
            self.camera.release()
        
        cv2.destroyAllWindows()
        print("Cleanup complete. Goodbye!")


def main():
    """Main entry point"""
    app = HandMouseEmoteApp()
    app.run()


if __name__ == "__main__":
    main()
