"""
Main Application
Hand Tracking Mouse Control System
"""

import cv2
import time
import numpy as np
from camera_handler import CameraHandler
from hand_detector import HandDetector
from gesture_recognizer import GestureRecognizer
from mouse_controller import MouseController
from config import ACTIVE_CONFIG as Config


class HandMouseApp:
    def __init__(self):
        """Initialize the hand mouse control application"""
        print("="*50)
        print("Hand Tracking Mouse Control System")
        print("="*50)
        
        # Initialize components
        print("Initializing camera...")
        self.camera = CameraHandler(
            camera_index=Config.CAMERA_INDEX,
            width=Config.CAMERA_WIDTH,
            height=Config.CAMERA_HEIGHT
        )
        
        print("Initializing hand detector...")
        self.detector = HandDetector(
            max_num_hands=Config.MAX_NUM_HANDS,
            min_detection_confidence=Config.MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=Config.MIN_TRACKING_CONFIDENCE
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
        
        # Update FPS every second
        elapsed = time.time() - self.fps_start_time
        if elapsed > 1.0:
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.fps_start_time = time.time()
    
    def draw_ui(self, frame, gesture, hand_detected, finger_count=0):
        """
        Draw UI overlay on frame

        Args:
            frame: Camera frame
            gesture: Current gesture ("open", "closed", or None)
            hand_detected: Whether a hand was detected
            finger_count: Number of fingers detected
        """
        h, w, _ = frame.shape

        # Semi-transparent overlay for better text visibility
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

        # Hand detection status
        if hand_detected:
            cv2.putText(frame, "Hand: DETECTED", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "Hand: NOT DETECTED", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        y_offset += 35

        # Get cursor info for drag status
        cursor_info = self.controller.get_cursor_info()

        # Gesture status with drag indication
        # Finger count display
        if hand_detected:
            finger_color = (255, 200, 0)  # Cyan color for finger count
            cv2.putText(frame, f"Fingers: {finger_count}", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, finger_color, 2)
            y_offset += 35

        # Gesture status
        if Config.SHOW_GESTURE_STATUS and gesture:
            if cursor_info['is_dragging']:
                gesture_text = "DRAGGING"
                color = (255, 0, 255)  # Magenta for dragging
            elif gesture == "open":
                gesture_text = "HOVER"
                color = Config.COLOR_OPEN_HAND
            else:
                gesture_text = "CLOSED"
                color = Config.COLOR_CLOSED_HAND

            cv2.putText(frame, f"Gesture: {gesture_text}", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            y_offset += 35

        # Cursor position
        if Config.SHOW_CURSOR_POSITION:
            cv2.putText(frame,
                       f"Cursor: ({cursor_info['x']}, {cursor_info['y']})",
                       (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, Config.COLOR_TEXT, 2)

        # Instructions (bottom of screen)
        instructions = [
            "Controls: Open Hand = Move | Close & Hold = Drag | Quick Close = Click",
            "Press 'Q' to quit | Move mouse to corner for emergency stop"
        ]

        y_pos = h - 60
        for instruction in instructions:
            cv2.putText(frame, instruction, (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, Config.COLOR_TEXT, 1)
            y_pos += 25
    
    def process_frame(self):
        """
        Process a single frame
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Read frame
        ret, frame = self.camera.read_frame()
        if not ret:
            print("Failed to read frame")
            return False
        
        # Detect hands
        frame, hands_data = self.detector.find_hands(
            frame, 
            draw=Config.DRAW_HAND_LANDMARKS
        )
        
        gesture = None
        hand_detected = len(hands_data) > 0
        finger_count = 0

        if hand_detected:
            # Get first hand
            landmarks = hands_data[0]['landmarks']

            # Calculate palm center (average of palm base landmarks)
            # Landmarks: 0=wrist, 1=thumb_cmc, 5=index_mcp, 9=middle_mcp, 13=ring_mcp, 17=pinky_mcp
            palm_landmarks = [0]
            hand_x = sum(landmarks[i]['x'] for i in palm_landmarks) / len(palm_landmarks)
            hand_y = sum(landmarks[i]['y'] for i in palm_landmarks) / len(palm_landmarks)

            # Recognize gesture
            gesture = self.recognizer.get_smoothed_gesture(landmarks)

            # Get finger count from recognizer
            finger_count = self.recognizer.current_finger_count

            # Update mouse control
            try:
                self.controller.update(hand_x, hand_y, gesture)
            except Exception as e:
                print(f"Mouse control error: {e}")
                return False

        # Calculate FPS
        self.calculate_fps()

        # Draw UI
        if Config.SHOW_CAMERA_FEED:
            self.draw_ui(frame, gesture, hand_detected, finger_count)
            cv2.imshow("Hand Mouse Control", frame)
        
        return True
    
    def run(self):
        """Run the main application loop"""
        try:
            # Start camera
            self.camera.start()
            self.running = True
            
            print("\n" + "="*50)
            print("APPLICATION RUNNING")
            print("="*50)
            print("\nControls:")
            print("  • Open hand = Move cursor")
            print("  • Close fist and hold = Drag")
            print("  • Close and release quickly = Click")
            print("  • Press 'Q' = Quit")
            print("  • Move mouse to corner = Emergency stop")
            print("\nStarting in 3 seconds...")
            print("="*50 + "\n")
            
            # Give user time to prepare
            time.sleep(3)
            
            # Main loop
            while self.running:
                # Process frame
                if not self.process_frame():
                    break
                
                # Check for quit command
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == ord('Q'):
                    print("\nQuit command received")
                    break
                
                # Optional: Cap FPS to reduce CPU usage
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
        
        # Clean up mouse controller (release any held buttons)
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
    app = HandMouseApp()
    app.run()


if __name__ == "__main__":
    main()