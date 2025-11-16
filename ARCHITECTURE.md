# Enhanced Hand Tracking System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          CAMERA INPUT (OpenCV)                           │
│                              640x480 @ 30fps                             │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    HAND DETECTOR (MediaPipe Hands)                       │
│                         max_num_hands = 2                                │
│                    Returns: List of hand landmarks                       │
└──────────────────┬──────────────────────────────┬───────────────────────┘
                   │                              │
                   │                              │
         ┌─────────▼─────────┐         ┌─────────▼─────────┐
         │  HAND PERSISTENCE │         │   EMOTE DETECTOR  │
         │     TRACKER       │         │  (Face + Hands)   │
         └─────────┬─────────┘         └─────────┬─────────┘
                   │                              │
                   │                              │
    ┌──────────────▼──────────────┐               │
    │   Assigns unique IDs to     │               │
    │   each detected hand        │               │
    │                             │               │
    │   Tracks hand positions     │               │
    │   across frames             │               │
    │                             │               │
    │   Determines PRIMARY hand   │               │
    │   (first detected = mouse)  │               │
    └──────────────┬──────────────┘               │
                   │                              │
                   │                              │
         ┌─────────▼─────────┐         ┌─────────▼─────────┐
         │  PRIMARY HAND     │         │   EMOTE ANALYSIS  │
         │  LANDMARKS        │         │                   │
         └─────────┬─────────┘         │ • Finger positions│
                   │                   │ • Hand-face dist  │
                   │                   │ • Gesture patterns│
         ┌─────────▼─────────┐         │                   │
         │  GESTURE          │         │ Hold for 1.5s     │
         │  RECOGNIZER       │         │                   │
         │                   │         └─────────┬─────────┘
         │ Open vs Closed    │                   │
         └─────────┬─────────┘                   │
                   │                              │
                   │                              │
         ┌─────────▼─────────┐         ┌─────────▼─────────┐
         │   MOUSE           │         │   TERMINAL        │
         │   CONTROLLER      │         │   OUTPUT          │
         │                   │         │                   │
         │ • Move cursor     │         │ "👍 Nice!"       │
         │ • Click           │         │ "✌️ Peace!"      │
         │ • Drag            │         │ "👋 Hello!"      │
         └───────────────────┘         └───────────────────┘


═══════════════════════════════════════════════════════════════════════════
                            DATA FLOW DETAILS
═══════════════════════════════════════════════════════════════════════════

1. CAMERA → HAND DETECTOR
   Input:  BGR frame (640x480)
   Output: [
             {landmarks: [...], handedness: 'Right'},
             {landmarks: [...], handedness: 'Left'}
           ]

2. HAND DETECTOR → HAND PERSISTENCE TRACKER
   Input:  List of detected hands
   Process:
     • Calculate hand center (wrist + middle finger base)
     • Match to existing tracked hands by position
     • Assign new IDs to unmatched hands
     • Remove hands that disappeared
   Output: {
             num_hands: 2,
             tracked_hands: [
               {id: 0, first_seen: timestamp, landmarks: [...], ...},
               {id: 1, first_seen: timestamp, landmarks: [...], ...}
             ],
             primary_hand: {id: 0, ...}  // Earliest first_seen
           }

3. PRIMARY HAND → GESTURE RECOGNIZER
   Input:  Hand landmarks (21 points)
   Process:
     • Check finger extension (tip vs PIP joint Y-coords)
     • Count extended fingers
     • Smooth over 5 frames
   Output: "open" or "closed"

4. GESTURE + POSITION → MOUSE CONTROLLER
   Input:  Index finger tip (x, y), gesture state
   Process:
     • Map hand coords to screen coords
     • Apply exponential smoothing
     • Detect gesture transitions:
       * open → closed: Start drag (mouseDown)
       * closed → open: End drag/click (mouseUp)
   Output: Mouse movement, clicks, drags

5. ALL HANDS → EMOTE DETECTOR
   Input:  All detected hand landmarks + frame
   Process:
     • Detect face using MediaPipe Face Mesh
     • Run detection functions for each emote:
       - thumbs_up: Check thumb extended, others closed
       - peace_sign: Check index+middle extended
       - facepalm: Check hand-face distance
       - etc.
     • Smooth detections over 5 frames (60% consistency)
     • Start hold timer when consistent
     • Trigger when hold_time reached
   Output: Terminal text when emote triggered


═══════════════════════════════════════════════════════════════════════════
                          MULTI-HAND BEHAVIOR
═══════════════════════════════════════════════════════════════════════════

Scenario 1: ONE HAND DETECTED
  Hand 0 (first) → Controls mouse ✓
  
Scenario 2: TWO HANDS DETECTED
  Hand 0 (first)  → Controls mouse ✓
  Hand 1 (second) → Ignored for mouse, used for emotes ✓
  
Scenario 3: HAND 0 LEAVES, HAND 1 REMAINS
  After 0.5s timeout:
    Hand 1 → Promoted to primary, controls mouse ✓
  
Scenario 4: BOTH HANDS LEAVE AND RETURN
  If same positions within 0.5s → Same IDs retained
  If different positions → New IDs assigned
  Earliest first_seen → Controls mouse


═══════════════════════════════════════════════════════════════════════════
                           EMOTE DETECTION LOGIC
═══════════════════════════════════════════════════════════════════════════

Emote: THUMBS_UP
  Check:
    ✓ Thumb tip Y < Thumb IP Y (thumb pointing up)
    ✓ Index, Middle, Ring, Pinky all curled
  Confidence: 0.9

Emote: PEACE_SIGN
  Check:
    ✓ Index finger extended
    ✓ Middle finger extended  
    ✓ Ring finger curled
    ✓ Pinky curled
  Confidence: 0.9

Emote: FACEPALM
  Check:
    ✓ Hand center position
    ✓ Face center position (from face mesh)
    ✓ Distance < 0.15 (normalized coords)
  Confidence: 0.85

Emote: THINKING
  Check:
    ✓ Index finger tip position
    ✓ Face chin position (center + offset)
    ✓ Distance < 0.12
  Confidence: 0.8


═══════════════════════════════════════════════════════════════════════════
                         PERFORMANCE OPTIMIZATION
═══════════════════════════════════════════════════════════════════════════

• Frame Skipping: Process every Nth frame (PROCESS_EVERY_N_FRAMES)
  - Hand detection still runs every frame
  - Expensive ML operations skip frames
  - Cache last results for skipped frames

• Model Complexity: Use Lite model (MODEL_COMPLEXITY = 0)
  - Faster inference
  - Slightly less accurate but sufficient

• Coordinate Smoothing: 
  - Hand positions smoothed over 5 frames
  - Gesture states smoothed over 5 frames
  - Mouse cursor exponentially smoothed

• Resolution Scaling: 640x480 balances speed vs accuracy


═══════════════════════════════════════════════════════════════════════════
                           FILE STRUCTURE
═══════════════════════════════════════════════════════════════════════════

camera_handler.py               - Webcam capture
hand_detector.py                - MediaPipe hand detection
gesture_recognizer.py           - Open/closed hand detection
mouse_controller.py             - PyAutoGUI mouse control
hand_persistence_tracker.py     - Multi-hand tracking & ID management [NEW]
emote_recognizer.py             - Face + hand emote detection [NEW]
main_with_emotes.py             - Integrated application [NEW]
config.py                       - Configuration settings
test_enhanced_system.py         - Test suite [NEW]
```
