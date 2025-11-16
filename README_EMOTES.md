# Hand Tracking Mouse Control + Emote Recognition System

## 🎯 Overview

This enhanced hand tracking system adds two powerful features:
1. **Multi-Hand Detection with Persistence Tracking** - Intelligently tracks multiple hands and uses the hand that appeared first for mouse control
2. **Emote Recognition** - Detects specific hand and face poses to trigger text outputs

## 🆕 New Features

### 1. Multi-Hand Tracking
- Detects up to 2 hands simultaneously
- Tracks which hand appeared first and uses it for mouse control
- Secondary hands are ignored for mouse but can be used for emotes
- Visual indicators show which hand is controlling the mouse
- Smooth hand tracking even when hands temporarily leave the frame

### 2. Emote Recognition
Recognizes 7 different emotes with combined hand + face detection:

| Emote | Gesture | Output |
|-------|---------|--------|
| 👍 **Thumbs Up** | Thumb extended, other fingers closed | "👍 Nice!" |
| ✌️ **Peace Sign** | Index and middle fingers extended (V shape) | "✌️ Peace!" |
| 👋 **Wave** | Open hand raised | "👋 Hello!" |
| 🤦 **Facepalm** | Hand covering face | "🤦 Facepalm!" |
| 🤔 **Thinking** | Hand near chin | "🤔 Thinking..." |
| 🤘 **Rock On** | Index and pinky extended | "🤘 Rock on!" |
| 👌 **OK Sign** | Thumb and index forming circle | "👌 OK!" |

**How It Works:**
- Hold an emote pose for 1.5 seconds
- A progress bar shows how long you've held the pose
- When complete, text is printed to the terminal
- 2-second cooldown between emote triggers

## 📁 New Files

### `hand_persistence_tracker.py`
Manages multi-hand tracking and determines which hand controls the mouse.

**Key Features:**
- Tracks hands across frames using position matching
- Maintains hand identity even with brief occlusions
- Smooths hand positions over time
- Assigns unique IDs to each hand
- Returns the "primary hand" (first detected) for mouse control

**Main Methods:**
```python
tracker = HandPersistenceTracker()
status = tracker.update(hands_data)
primary_hand = status['primary_hand']  # Hand for mouse control
```

### `emote_recognizer.py`
Detects emotes using hand landmarks and face position.

**Key Features:**
- Uses MediaPipe Face Mesh for face detection
- Analyzes hand poses (finger positions, distances)
- Combines hand and face positions for accurate detection
- Requires consistent detection over multiple frames
- Configurable hold time and confidence thresholds

**Main Methods:**
```python
recognizer = EmoteRecognizer(hold_time=1.5)
emote_status = recognizer.update(hands_data, frame)
# Automatically prints to terminal when emote is triggered
```

### `main_with_emotes.py`
Integrated application combining mouse control and emote recognition.

**Usage:**
```bash
# Run with emote recognition (default)
python main_with_emotes.py

# Run without emote recognition
python main_with_emotes.py --no-emotes
```

## 🎮 Controls

### Mouse Control
- **Open hand** = Move cursor
- **Close fist and hold** = Drag
- **Close and release quickly** = Click

### Emote System
- **Hold emote pose for 1.5 seconds** = Trigger emote (prints to terminal)
- **Press 'E'** = Toggle emote info display on/off

### General
- **Press 'Q'** = Quit application
- **Move mouse to corner** = Emergency stop

## 🏃 Quick Start

### 1. Install Dependencies
```bash
pip install opencv-python mediapipe pyautogui numpy
```

### 2. Test Multi-Hand Tracking
```bash
python hand_persistence_tracker.py
```
This shows how the system tracks multiple hands and identifies the primary hand.

### 3. Test Emote Recognition
```bash
python emote_recognizer.py
```
Try making different hand gestures and holding them for 1.5 seconds.

### 4. Run Full Application
```bash
python main_with_emotes.py
```

## 🔧 Configuration

### Hand Persistence Tracker Settings
```python
tracker = HandPersistenceTracker(
    position_threshold=0.15,      # Distance to match hands (0-1)
    disappear_timeout=0.5         # Time before hand is forgotten (seconds)
)
```

### Emote Recognition Settings
```python
recognizer = EmoteRecognizer(
    confidence_threshold=0.7,     # Minimum confidence (0-1)
    hold_time=1.5                 # Time to hold pose (seconds)
)
```

### Adjusting in `main_with_emotes.py`
Look for these initialization parameters around line 50-60.

## 📊 How Multi-Hand Tracking Works

1. **Detection**: MediaPipe detects all hands in frame
2. **Matching**: Each detected hand is matched to previously tracked hands using position
3. **ID Assignment**: New hands get unique IDs, existing hands keep their IDs
4. **Primary Selection**: The hand with the earliest `first_seen` timestamp is primary
5. **Mouse Control**: Only the primary hand controls the mouse
6. **Emote Detection**: All hands can be used for emote recognition

### Visual Indicators
- **Green circle** = Primary hand (controls mouse)
- **Blue/Yellow/Magenta circles** = Secondary hands
- **Hand ID displayed** = Shows which hand is which
- **Timer** = Shows how long each hand has been tracked

## 🎭 How Emote Recognition Works

1. **Hand Detection**: Analyzes finger positions and hand shape
2. **Face Detection**: Locates face using MediaPipe Face Mesh
3. **Spatial Analysis**: Checks hand-face relationships (for facepalm, thinking pose)
4. **Temporal Smoothing**: Requires consistent detection across 5 frames
5. **Hold Verification**: Must hold pose for configured duration
6. **Trigger**: Prints text to terminal, then cooldown period

### Detection Pipeline
```
Frame → Hand Landmarks + Face Position → Emote Detection Functions → 
Consistency Check → Hold Timer → Trigger Action
```

## 🎨 Customizing Emotes

You can add your own emotes by editing `emote_recognizer.py`:

```python
def detect_my_custom_emote(self, hands_data, face_data):
    """Detect your custom emote"""
    if not hands_data:
        return 0.0
    
    landmarks = hands_data[0]['landmarks']
    
    # Add your detection logic here
    # Return confidence 0.0-1.0
    
    return confidence

# Add to define_emotes():
{
    'name': 'my_emote',
    'description': 'Description of the gesture',
    'detect_func': self.detect_my_custom_emote,
    'output_text': '🎉 Custom emote triggered!'
}
```

## 🐛 Troubleshooting

### Multi-Hand Issues
**Problem**: Hands keep swapping IDs
- **Solution**: Increase `position_threshold` in HandPersistenceTracker
- Keep hands more separated in frame

**Problem**: Hand loses tracking too quickly
- **Solution**: Increase `disappear_timeout` in HandPersistenceTracker

### Emote Recognition Issues
**Problem**: Emotes not triggering
- **Solution**: Lower `confidence_threshold` or `hold_time`
- Ensure face is visible for face-based emotes
- Check terminal for detection feedback

**Problem**: False positive emotes
- **Solution**: Increase `confidence_threshold` or `hold_time`
- Adjust detection logic to be more specific

**Problem**: Progress bar not appearing
- **Solution**: Ensure you're holding the pose consistently
- Check that emote info display is enabled (press 'E')

## 📈 Performance Tips

1. **Frame Skipping**: Set `PROCESS_EVERY_N_FRAMES = 2` in config.py for better performance
2. **Lower Resolution**: Use 480x360 for faster processing
3. **Disable Emotes**: Run with `--no-emotes` flag if you only need mouse control
4. **Model Complexity**: Keep `MODEL_COMPLEXITY = 0` for faster hand detection

## 🔬 Technical Details

### Hand Persistence Algorithm
- Uses Euclidean distance to match hands between frames
- Maintains separate position history for each hand
- Implements timeout mechanism to forget disappeared hands
- Primary hand selection is deterministic (based on first appearance)

### Emote Detection Algorithm
- Each emote has a custom detection function
- Detection functions return confidence scores (0.0-1.0)
- Temporal smoothing requires 60% consistency over 5 frames
- Hold timer starts when consistent detection achieved
- Cooldown prevents rapid re-triggering

### Face Detection
- Uses MediaPipe Face Mesh (468 landmarks)
- Nose tip (landmark 1) used as face center
- Face position used for spatial emotes (facepalm, thinking)
- Runs in parallel with hand detection

## 📝 Example Output

When you trigger an emote, you'll see:
```
==================================================
EMOTE TRIGGERED: THUMBS_UP
👍 Nice!
==================================================
```

## 🎯 Use Cases

### Educational
- Create interactive presentations with gesture controls
- Build sign language learning tools
- Develop accessibility interfaces

### Gaming
- Create gesture-controlled games
- Implement emote systems for streaming
- Build interactive experiences

### Development
- Test gesture recognition algorithms
- Prototype hand-tracking applications
- Demonstrate computer vision capabilities

## 📄 License

Same as the original project.

## 🤝 Contributing

To add new emotes:
1. Create a detection function in `emote_recognizer.py`
2. Add it to the `define_emotes()` method
3. Test with `python emote_recognizer.py`
4. Submit improvements!

## 🙏 Acknowledgments

- **MediaPipe** by Google for hand and face detection
- **OpenCV** for computer vision tools
- **PyAutoGUI** for mouse control

---

**Enjoy your enhanced hand tracking system with emote recognition! 🎉**
