"""
Debug Emote Detection
See what's being detected in real-time
"""

import cv2
import warnings
import os

# Suppress warnings
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from ultimate_emote_matcher import UltimateEmoteMatcher

def main():
    print("="*70)
    print("EMOTE DETECTION DEBUG")
    print("="*70)
    
    # Check if model exists
    if not os.path.exists("emote_model_ultimate.pkl"):
        print("ERROR: No model found!")
        print("You need to train the model first.")
        return
    
    # Load matcher
    try:
        matcher = UltimateEmoteMatcher(
            confidence_threshold=0.60,  # LOWERED to 60%
            match_hold_time=1.0,  # Only 1 second hold
            model_path="emote_model_ultimate.pkl"
        )
        print("✓ Model loaded!")
    except Exception as e:
        print(f"ERROR loading model: {e}")
        return
    
    # Open camera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("ERROR: Cannot open camera!")
        return
    
    print("\n" + "="*70)
    print("INSTRUCTIONS:")
    print("  - Show BOTH hands to camera")
    print("  - Perform emote poses")
    print("  - Watch the probabilities in top-left")
    print("  - Hold pose for 1 second to trigger")
    print("  - Press 'Q' to quit")
    print("="*70 + "\n")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Flip for mirror effect
        frame = cv2.flip(frame, 1)
        
        # Run detection
        result = matcher.match_emote(frame)
        
        # Draw debug info
        matcher.draw_debug(frame, result)
        
        # ADDITIONAL DEBUG INFO
        h, w, _ = frame.shape
        
        # Show if face/hands detected
        if result['face_data']:
            cv2.putText(frame, "FACE: YES", (10, h - 100),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "FACE: NO", (10, h - 100),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
        left_detected = result['hands_data']['left'] is not None
        right_detected = result['hands_data']['right'] is not None
        
        cv2.putText(frame, f"LEFT HAND: {'YES' if left_detected else 'NO'}", (10, h - 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, 
                   (0, 255, 0) if left_detected else (0, 0, 255), 2)
        
        cv2.putText(frame, f"RIGHT HAND: {'YES' if right_detected else 'NO'}", (10, h - 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                   (0, 255, 0) if right_detected else (0, 0, 255), 2)
        
        # Show ALL probabilities
        y_pos = 200
        if result['probabilities']:
            cv2.putText(frame, "ALL PREDICTIONS:", (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            y_pos += 30
            
            sorted_probs = sorted(result['probabilities'].items(), 
                                 key=lambda x: x[1], reverse=True)
            
            for emote, prob in sorted_probs:
                color = (0, 255, 0) if prob > 0.6 else (255, 255, 255)
                cv2.putText(frame, f"{emote}: {prob:.1%}", (10, y_pos),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                y_pos += 25
        
        cv2.imshow('Emote Debug', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    matcher.release()
    
    print("\n" + "="*70)
    print("Debug session ended")
    print("="*70)


if __name__ == "__main__":
    main()