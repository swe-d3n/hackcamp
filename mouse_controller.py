"""
Mouse Controller Module
Controls mouse cursor movement and clicking
"""

import pyautogui
import time
from collections import deque


class MouseController:
    def __init__(self, smoothing_factor=0.3, click_cooldown=0.3, 
                 screen_margin=50, movement_threshold=2):
        """
        Initialize mouse controller
        
        Args:
            smoothing_factor: Exponential smoothing (0-1, lower = more smooth)
            click_cooldown: Minimum seconds between clicks
            screen_margin: Pixels from screen edge to create dead zone
            movement_threshold: Minimum pixel movement to update cursor
        """
        self.smoothing_factor = smoothing_factor
        self.click_cooldown = click_cooldown
        self.screen_margin = screen_margin
        self.movement_threshold = movement_threshold
        
        # Screen dimensions
        self.screen_width, self.screen_height = pyautogui.size()
        print(f"Screen size: {self.screen_width}x{self.screen_height}")
        
        # Smoothed cursor position
        self.smooth_x = self.screen_width // 2
        self.smooth_y = self.screen_height // 2
        
        # Click state tracking
        self.last_click_time = 0
        self.previous_gesture = "open"
        self.is_clicking = False
        
        # Safety settings
        pyautogui.FAILSAFE = True  # Move to corner to stop
        pyautogui.PAUSE = 0.01  # Small pause between actions
        
    def map_to_screen(self, hand_x, hand_y):
        """
        Map normalized hand coordinates (0-1) to screen coordinates
        
        Args:
            hand_x: Normalized x coordinate (0-1)
            hand_y: Normalized y coordinate (0-1)
            
        Returns:
            tuple: (screen_x, screen_y)
        """
        # Map to screen coordinates
        screen_x = int(hand_x * self.screen_width)
        screen_y = int(hand_y * self.screen_height)
        
        # Apply margins (keep cursor away from edges)
        screen_x = max(self.screen_margin, 
                      min(screen_x, self.screen_width - self.screen_margin))
        screen_y = max(self.screen_margin,
                      min(screen_y, self.screen_height - self.screen_margin))
        
        return screen_x, screen_y
    
    def smooth_position(self, new_x, new_y):
        """
        Apply exponential smoothing to cursor position
        
        Args:
            new_x: New x coordinate
            new_y: New y coordinate
            
        Returns:
            tuple: (smoothed_x, smoothed_y)
        """
        # Exponential moving average
        self.smooth_x = (self.smoothing_factor * new_x + 
                        (1 - self.smoothing_factor) * self.smooth_x)
        self.smooth_y = (self.smoothing_factor * new_y + 
                        (1 - self.smoothing_factor) * self.smooth_y)
        
        return int(self.smooth_x), int(self.smooth_y)
    
    def move_cursor(self, hand_x, hand_y):
        """
        Move cursor based on hand position
        
        Args:
            hand_x: Normalized hand x position (0-1)
            hand_y: Normalized hand y position (0-1)
        """
        # Map to screen coordinates
        screen_x, screen_y = self.map_to_screen(hand_x, hand_y)
        
        # Apply smoothing
        smooth_x, smooth_y = self.smooth_position(screen_x, screen_y)
        
        # Get current cursor position
        current_x, current_y = pyautogui.position()
        
        # Only move if movement is significant (reduces jitter)
        distance = ((smooth_x - current_x)**2 + (smooth_y - current_y)**2)**0.5
        
        if distance > self.movement_threshold:
            try:
                pyautogui.moveTo(smooth_x, smooth_y, _pause=False)
            except pyautogui.FailSafeException:
                print("FailSafe triggered - mouse moved to corner")
                raise
    
    def handle_click(self, gesture):
        """
        Handle click based on gesture

        Args:
            gesture: Current gesture ("open" or "closed")
        """
        current_time = time.time()

        # Detect transition from open to closed (click trigger)
        if gesture == "closed" and self.previous_gesture == "open":
            # Check if enough time has passed since last click
            if current_time - self.last_click_time > self.click_cooldown:
                try:
                    pyautogui.click()
                    self.last_click_time = current_time
                    self.is_clicking = True
                    print("Click!")
                except pyautogui.FailSafeException:
                    print("FailSafe triggered during click")
                    raise

        # Update clicking state
        if gesture == "open":
            self.is_clicking = False

        # Update previous gesture
        self.previous_gesture = gesture

    def update(self, hand_x, hand_y, gesture):
        """
        Update cursor position and handle clicks

        Args:
            hand_x: Normalized hand x position (0-1)
            hand_y: Normalized hand y position (0-1)
            gesture: Current gesture ("open" or "closed")
        """
        # Move cursor
        self.move_cursor(hand_x, hand_y)

        # Handle clicks
        self.handle_click(gesture)
    
    def get_cursor_info(self):
        """
        Get current cursor information
        
        Returns:
            dict: Cursor position and state info
        """
        current_x, current_y = pyautogui.position()
        
        return {
            'x': current_x,
            'y': current_y,
            'is_clicking': self.is_clicking,
            'screen_width': self.screen_width,
            'screen_height': self.screen_height
        }


if __name__ == "__main__":
    # Test mouse controller
    from camera_handler import CameraHandler
    from hand_detector import HandDetector
    from gesture_recognizer import GestureRecognizer
    
    camera = CameraHandler()
    camera.start()
    
    detector = HandDetector()
    recognizer = GestureRecognizer()
    controller = MouseController()
    
    print("Hand Mouse Control Test")
    print("Open hand = move cursor")
    print("Closed fist = click")
    print("Press 'q' to quit")
    print("Move mouse to screen corner to emergency stop")
    
    while camera.is_opened():
        ret, frame = camera.read_frame()
        
        if not ret:
            break
        
        # Detect hands
        frame, hands_data = detector.find_hands(frame, draw=True)
        
        if hands_data:
            # Get first hand
            landmarks = hands_data[0]['landmarks']
            
            # Get index finger tip position (use as cursor control point)
            index_tip = landmarks[8]  # Index finger tip
            hand_x = index_tip['x']
            hand_y = index_tip['y']
            
            # Recognize gesture
            gesture = recognizer.get_smoothed_gesture(landmarks)
            
            # Update mouse
            try:
                controller.update(hand_x, hand_y, gesture)
            except pyautogui.FailSafeException:
                print("Emergency stop activated!")
                break
            
            # Display info
            color = (0, 255, 0) if gesture == "open" else (0, 0, 255)
            cv2.putText(frame, f"Gesture: {gesture.upper()}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            
            cursor_info = controller.get_cursor_info()
            cv2.putText(frame, f"Cursor: ({cursor_info['x']}, {cursor_info['y']})",
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        cv2.imshow("Mouse Control Test", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    detector.release()
    camera.release()
    cv2.destroyAllWindows()
