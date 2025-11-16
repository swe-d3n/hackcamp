"""
Configuration File
Centralized settings for the hand tracking mouse control system
"""
import numpy as np


class Config:
    # Camera Settings
    CAMERA_INDEX = 0  # Default camera (usually 0)
    CAMERA_WIDTH = 640
    CAMERA_HEIGHT = 480
    CAMERA_FPS = 30
    
    # Hand Detection Settings
    MAX_NUM_HANDS = 1
    MIN_DETECTION_CONFIDENCE = 0.7
    MIN_TRACKING_CONFIDENCE = 0.5
    
    # Gesture Recognition Settings
    GESTURE_SMOOTHING_FRAMES = 5  # Number of frames for smoothing
    CLOSED_HAND_THRESHOLD = 0.08  # Distance threshold for closed hand
    
    # Mouse Control Settings
    CURSOR_SMOOTHING_FACTOR = 0.3  # 0-1, lower = smoother but slower
    CLICK_COOLDOWN = 0.3  # Seconds between clicks
    SCREEN_MARGIN = 50  # Pixels from edge to prevent cursor going offscreen
    MOVEMENT_THRESHOLD = 2  # Minimum pixels to move (reduces jitter)
    
    # UI Settings
    SHOW_CAMERA_FEED = True
    DRAW_HAND_LANDMARKS = True
    SHOW_FPS = True
    SHOW_GESTURE_STATUS = True
    SHOW_CURSOR_POSITION = True
    
    # Performance Settings
    MAX_FPS = 30  # Cap FPS to reduce CPU usage
    
    # Control Point Settings
    # Which landmark to use for cursor control
    # 8 = index finger tip (default)
    # 4 = thumb tip
    # 12 = middle finger tip
    CURSOR_CONTROL_LANDMARK = 8  # Index finger tip
    
    # Color Settings (BGR format)
    COLOR_OPEN_HAND = (0, 255, 0)  # Green
    COLOR_CLOSED_HAND = (0, 0, 255)  # Red
    COLOR_TEXT = (255, 255, 255)  # White
    COLOR_FPS_GOOD = (0, 255, 0)  # Green (>25 FPS)
    COLOR_FPS_MEDIUM = (0, 255, 255)  # Yellow (15-25 FPS)
    COLOR_FPS_BAD = (0, 0, 255)  # Red (<15 FPS)

    EMOTE_BUTTON_POS = (1800, 950)  # CHANGE THIS
    
    # Individual emote positions in the emote menu
    # These are examples - calibrate for your setup!
    EMOTE_POSITIONS = {
        "laughing": (1500, 700),
        "crying": (1600, 700),
        "angry": (1700, 700),
        "king_thumbs_up": (1800, 700),
        "thumbs_up": (1500, 800),
        "chicken": (1600, 800),
        "goblin_kiss": (1700, 800),
        "princess_yawn": (1800, 800),
        "wow": (1500, 900),
        "thinking": (1600, 900),
        "screaming": (1700, 900),
        "king_laugh": (1800, 900),
        "goblin_laugh": (1500, 1000),
        "princess_cry": (1600, 1000),
        "goblin_angry": (1700, 1000),
    }

ACTIVE_CONFIG = Config()