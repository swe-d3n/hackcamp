"""
Test ULTIMATE Emote Detection System
Maximum accuracy with all advanced features
"""

import cv2
from ultimate_emote_matcher import UltimateEmoteMatcher
import sys
import os


def main():
    print("="*70)
    print("ULTIMATE EMOTE DETECTION SYSTEM")
    print("Maximum Accuracy Edition")
    print("="*70)
    print("\nFEATURES:")
    print("  ✓ Ultra-sensitive face detection (edge cases)")
    print("  ✓ Hand orientation detection (palm/back)")
    print("  ✓ Advanced mouth tracking (works when covered)")
    print("  ✓ 98-feature ML model")
    print()

    # Check if model exists
    if not os.path.exists("emote_model_ultimate.pkl"):
        print("ERROR: No ultimate model found!")
        print()
        print("Please complete these steps:")
        print("  1. python ultimate_emote_collector.py")
        print("     (Collect 40-60 samples per emote)")
        print("  2. python train_ultimate_classifier.py")
        print("     (Train the ultimate model)")
        print()
        sys.exit(1)

    try:
        print("Loading ultimate ML model...")
        matcher = UltimateEmoteMatcher(
            confidence_threshold=0.75,
            match_hold_time=1.5,
            model_path="emote_model_ultimate.pkl"
        )
        print("✓ Ultimate model loaded!\n")

    except Exception as e:
        print(f"ERROR: {e}")
        print("\nMake sure you've trained the ultimate model first.")
        sys.exit(1)

    # Open webcam
    print("Opening webcam...")
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("ERROR: Could not open webcam!")
        sys.exit(1)

    print("✓ Webcam ready!\n")
    print("="*70)
    print("INSTRUCTIONS:")
    print("  - Perform emote poses")
    print("  - System detects hand orientation automatically")
    print("  - Face detection works even with hands covering face")
    print("  - Mouth tracking for yawn detection")
    print("  - Hold pose for 1.5 seconds to trigger")
    print("  - Press 'Q' to quit")
    print("="*70)
    print()

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        frame = cv2.flip(frame, 1)

        # Match emote
        result = matcher.match_emote(frame)

        # Draw debug
        matcher.draw_debug(frame, result)

        cv2.imshow('Ultimate Emote Detection', frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    matcher.release()

    print("\n" + "="*70)
    print("Session ended!")
    print("="*70)


if __name__ == "__main__":
    main()
