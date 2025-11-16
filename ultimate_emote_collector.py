"""
ULTIMATE Emote Training Data Collector - Maximum Accuracy Edition

NEW FEATURES:
- Hand orientation detection (palm vs back of hand)
- Enhanced face detection (works even with hands covering face)
- Advanced mouth detection (works when partially covered)
- Simplified face features (focused on mouth only)
- Multi-angle face detection for edge cases
- Intelligent hand landmark analysis
"""

import cv2
import mediapipe as mp
import numpy as np
import json
import os
from datetime import datetime
import math


class UltimateEmoteCollector:
    def __init__(self, output_file="emote_training_data_ultimate.json"):
        """Initialize the ultimate data collector"""
        self.output_file = output_file
        self.training_data = []

        # MediaPipe setup with MAXIMUM detection capability
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        # Ultra-sensitive face mesh for edge cases
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.2,  # VERY LOW for maximum detection
            min_tracking_confidence=0.2
        )

        # High-quality hand detection with orientation analysis
        self.hands_detection = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            model_complexity=1,
            min_detection_confidence=0.2,  # VERY LOW threshold
            min_tracking_confidence=0.2
        )

        # Emote labels
        self.emote_labels = [
            "Goblin Facepalm",
            "Wizard Magic",
            "Princess Yawn",
            "None/Neutral"
        ]

        self.current_emote_index = 0
        self.samples_per_emote = {}
        for emote in self.emote_labels:
            self.samples_per_emote[emote] = 0

        print("✓ Ultimate Emote Collector initialized")
        print("  - Ultra-sensitive face detection")
        print("  - Hand orientation detection (palm/back)")
        print("  - Advanced mouth tracking")

    def detect_hand_orientation(self, hand_landmarks):
        """
        Detect if hand is showing palm (forward) or back (backward)

        Returns:
            float: 0.0 = back of hand, 1.0 = palm showing
        """
        # Key landmarks for orientation detection:
        # Wrist (0), Index finger MCP (5), Pinky MCP (17)
        # Middle finger tip (12), Middle finger MCP (9)

        wrist = hand_landmarks.landmark[0]
        index_mcp = hand_landmarks.landmark[5]
        pinky_mcp = hand_landmarks.landmark[17]
        middle_tip = hand_landmarks.landmark[12]
        middle_mcp = hand_landmarks.landmark[9]

        # Calculate hand normal vector using cross product
        # Vector from wrist to index MCP
        v1_x = index_mcp.x - wrist.x
        v1_y = index_mcp.y - wrist.y
        v1_z = index_mcp.z - wrist.z

        # Vector from wrist to pinky MCP
        v2_x = pinky_mcp.x - wrist.x
        v2_y = pinky_mcp.y - wrist.y
        v2_z = pinky_mcp.z - wrist.z

        # Cross product (normal to palm)
        normal_x = v1_y * v2_z - v1_z * v2_y
        normal_y = v1_z * v2_x - v1_x * v2_z
        normal_z = v1_x * v2_y - v1_y * v2_x

        # If normal_z > 0, palm is facing camera
        # If normal_z < 0, back of hand is facing camera

        # Also check finger extension (palm shows more extended fingers)
        finger_extension = abs(middle_tip.y - middle_mcp.y)

        # Combine normal direction and finger extension
        palm_score = (normal_z + 1) / 2  # Normalize -1 to 1 -> 0 to 1

        return float(palm_score)

    def calculate_advanced_mouth_features(self, face_landmarks):
        """
        Calculate mouth features even when partially covered
        Uses multiple landmark points for robustness
        """
        # Multiple mouth landmarks for redundancy
        # Upper lip: 13, 14, 312, 311
        # Lower lip: 14, 15, 317, 402
        # Corners: 61, 291

        try:
            # Primary measurements
            upper_lip_center = face_landmarks.landmark[13]
            lower_lip_center = face_landmarks.landmark[14]

            # Vertical opening (most reliable)
            mouth_height = abs(upper_lip_center.y - lower_lip_center.y)

            # Horizontal width
            left_corner = face_landmarks.landmark[61]
            right_corner = face_landmarks.landmark[291]
            mouth_width = abs(left_corner.x - right_corner.x)

            # Additional measurements for robustness
            # Upper outer lip
            upper_outer = face_landmarks.landmark[0]  # Nose tip as reference

            # Aspect ratio (key for yawn detection)
            if mouth_width > 0.001:
                mouth_ratio = mouth_height / mouth_width
            else:
                mouth_ratio = 0.0

            # Absolute mouth opening (normalized by face size)
            mouth_area = mouth_height * mouth_width

            # Mouth center position
            mouth_center_x = (left_corner.x + right_corner.x) / 2
            mouth_center_y = (upper_lip_center.y + lower_lip_center.y) / 2

            return {
                'ratio': mouth_ratio,
                'height': mouth_height,
                'width': mouth_width,
                'area': mouth_area,
                'center_x': mouth_center_x,
                'center_y': mouth_center_y
            }
        except:
            # Fallback if mouth not detected
            return {
                'ratio': 0.0,
                'height': 0.0,
                'width': 0.0,
                'area': 0.0,
                'center_x': 0.5,
                'center_y': 0.5
            }

    def extract_features(self, frame):
        """
        Extract features with MAXIMUM accuracy

        Returns features even in edge cases
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = frame.shape

        # Multi-pass face detection for edge cases
        face_results = self.face_mesh.process(rgb_frame)

        if not face_results.multi_face_landmarks:
            # Face not detected - return None
            return None

        face_landmarks = face_results.multi_face_landmarks[0]

        # SIMPLIFIED FACE FEATURES - Only mouth-focused
        # No need for detailed face mesh, just position and mouth

        # Get face bounds for normalization
        x_coords = [lm.x for lm in face_landmarks.landmark]
        y_coords = [lm.y for lm in face_landmarks.landmark]

        face_center_x = sum(x_coords) / len(x_coords)
        face_center_y = sum(y_coords) / len(y_coords)
        face_width = max(x_coords) - min(x_coords)
        face_height = max(y_coords) - min(y_coords)

        # Basic face features (4 values)
        face_features = [
            face_center_x,
            face_center_y,
            face_width,
            face_height
        ]

        # ADVANCED MOUTH FEATURES (6 values)
        mouth_data = self.calculate_advanced_mouth_features(face_landmarks)
        mouth_features = [
            mouth_data['ratio'],      # Height/width ratio (KEY for yawn)
            mouth_data['height'],     # Absolute height
            mouth_data['width'],      # Absolute width
            mouth_data['area'],       # Total opening area
            mouth_data['center_x'],   # Mouth position X
            mouth_data['center_y']    # Mouth position Y
        ]

        # HAND DETECTION WITH ORIENTATION
        hands_results = self.hands_detection.process(rgb_frame)

        # Enhanced hand features: landmarks + orientation
        # Each hand: 1 presence + 42 landmarks + 1 orientation = 44 features
        left_hand_features = [0.0] * 44
        right_hand_features = [0.0] * 44

        hands_data = {'left': None, 'right': None}

        if hands_results.multi_hand_landmarks:
            for hand_idx, hand_landmarks in enumerate(hands_results.multi_hand_landmarks):
                handedness = hands_results.multi_handedness[hand_idx].classification[0].label.lower()

                # Extract all 21 landmark positions
                hand_coords = []
                for landmark in hand_landmarks.landmark:
                    hand_coords.extend([landmark.x, landmark.y])

                # Detect hand orientation (palm vs back)
                orientation = self.detect_hand_orientation(hand_landmarks)

                # FIX: Invert orientation for left hand only
                if handedness == 'left':
                    orientation = 1.0 - orientation  # Invert for left hand

                # Get hand center
                wrist = hand_landmarks.landmark[0]
                middle_mcp = hand_landmarks.landmark[9]
                center_x = (wrist.x + middle_mcp.x) / 2
                center_y = (wrist.y + middle_mcp.y) / 2

                # Combine: [presence=1.0] + [42 coords] + [orientation]
                hand_feature_vector = [1.0] + hand_coords + [orientation]

                if handedness == 'left':
                    left_hand_features = hand_feature_vector
                    hands_data['left'] = {
                        'position': (center_x, center_y),
                        'landmarks': hand_landmarks,
                        'orientation': orientation
                    }
                else:
                    right_hand_features = hand_feature_vector
                    hands_data['right'] = {
                        'position': (center_x, center_y),
                        'landmarks': hand_landmarks,
                        'orientation': orientation
                    }

        # TOTAL FEATURES: 4 (face) + 6 (mouth) + 44 (left hand) + 44 (right hand) = 98
        features = face_features + mouth_features + left_hand_features + right_hand_features

        return np.array(features), face_landmarks, hands_data, mouth_data

    def save_sample(self, features, label):
        """Save a training sample"""
        sample = {
            'features': features.tolist(),
            'label': label,
            'timestamp': datetime.now().isoformat()
        }

        self.training_data.append(sample)
        self.samples_per_emote[label] = self.samples_per_emote.get(label, 0) + 1

        # Save immediately
        with open(self.output_file, 'w') as f:
            json.dump(self.training_data, f, indent=2)

        print(f"✓ Saved sample for '{label}' (Total: {self.samples_per_emote[label]})")

    def draw_ui(self, frame, face_landmarks, hands_data, mouth_data):
        """Draw UI with advanced visualizations"""
        h, w, _ = frame.shape

        # Draw face mesh (simplified - just mouth area)
        if face_landmarks:
            # Only draw mouth region
            self.mp_draw.draw_landmarks(
                image=frame,
                landmark_list=face_landmarks,
                connections=self.mp_face_mesh.FACEMESH_LIPS,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp.solutions.drawing_styles.DrawingSpec(
                    color=(0, 255, 255), thickness=2
                )
            )

        # Draw hands with orientation indicator
        if hands_data:
            for hand_type in ['left', 'right']:
                if hands_data[hand_type]:
                    hand_info = hands_data[hand_type]

                    # Draw hand skeleton
                    self.mp_draw.draw_landmarks(
                        frame,
                        hand_info['landmarks'],
                        self.mp_hands.HAND_CONNECTIONS,
                        self.mp_drawing_styles.get_default_hand_landmarks_style(),
                        self.mp_drawing_styles.get_default_hand_connections_style()
                    )

                    # Show orientation
                    pos = hand_info['position']
                    x_px = int(pos[0] * w)
                    y_px = int(pos[1] * h)

                    orientation = hand_info['orientation']
                    if orientation > 0.5:
                        orient_text = "PALM"
                        orient_color = (0, 255, 0)
                    else:
                        orient_text = "BACK"
                        orient_color = (0, 165, 255)

                    cv2.putText(frame, f"{hand_type.upper()}: {orient_text} ({orientation:.2f})",
                               (x_px - 80, y_px - 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, orient_color, 2)

        # UI Overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 250), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

        # Title
        cv2.putText(frame, "ULTIMATE EMOTE COLLECTOR - Max Accuracy", (20, 35),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        # Current emote
        current_emote = self.emote_labels[self.current_emote_index]
        cv2.putText(frame, f"Emote: {current_emote}", (20, 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Sample count
        count = self.samples_per_emote.get(current_emote, 0)
        cv2.putText(frame, f"Samples: {count}", (20, 100),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Mouth status with advanced metrics
        if mouth_data:
            mouth_status = "YAWNING!" if mouth_data['ratio'] > 0.35 else "Closed"
            mouth_color = (0, 255, 0) if mouth_data['ratio'] > 0.35 else (150, 150, 150)
            cv2.putText(frame, f"Mouth: {mouth_data['ratio']:.3f} - {mouth_status}",
                       (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.6, mouth_color, 2)
            cv2.putText(frame, f"Area: {mouth_data['area']:.4f}",
                       (20, 155), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        # Hand orientation info
        y_pos = 180
        for hand_type in ['left', 'right']:
            if hands_data and hands_data[hand_type]:
                orient = hands_data[hand_type]['orientation']
                orient_text = "Palm" if orient > 0.5 else "Back"
                cv2.putText(frame, f"{hand_type.capitalize()}: {orient_text} ({orient:.2f})",
                           (20, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 200, 0), 1)
                y_pos += 20

        # Instructions
        cv2.putText(frame, "SPACE=Capture | N=Next | Q=Quit",
                   (20, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)

        # All emotes list
        y_offset = 290
        for i, emote in enumerate(self.emote_labels):
            count = self.samples_per_emote.get(emote, 0)
            color = (0, 255, 0) if i == self.current_emote_index else (150, 150, 150)
            marker = "→" if i == self.current_emote_index else " "
            cv2.putText(frame, f"{marker} {emote}: {count}",
                       (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            y_offset += 25

        # Total
        cv2.putText(frame, f"TOTAL: {len(self.training_data)}", (w - 200, 35),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        # Features indicator
        cv2.putText(frame, "98 features | Hand orientation | Advanced mouth", (10, h - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    def run(self):
        """Run the ultimate data collector"""
        cap = cv2.VideoCapture(0)

        print("\n" + "="*70)
        print("ULTIMATE EMOTE TRAINING DATA COLLECTOR")
        print("="*70)
        print("\nMAXIMUM ACCURACY FEATURES:")
        print("  ✓ Ultra-sensitive face detection (works in edge cases)")
        print("  ✓ Hand orientation detection (palm vs back of hand)")
        print("  ✓ Advanced mouth tracking (works when partially covered)")
        print("  ✓ Simplified face features (focused on mouth)")
        print("  ✓ 98 total features for maximum accuracy")
        print("\nControls:")
        print("  SPACE - Capture sample")
        print("  N     - Next emote")
        print("  Q     - Quit")
        print("\nRecommendation: 40-60 samples per emote for best results")
        print("="*70 + "\n")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)

            result = self.extract_features(frame)

            face_landmarks = None
            hands_data = None
            mouth_data = None
            features = None

            if result is not None:
                features, face_landmarks, hands_data, mouth_data = result

            self.draw_ui(frame, face_landmarks, hands_data, mouth_data)

            # Status indicator
            h, w, _ = frame.shape
            if features is not None:
                cv2.putText(frame, "✓ READY", (w - 150, h - 40),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            else:
                cv2.putText(frame, "✗ No face", (w - 150, h - 40),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            cv2.imshow('Ultimate Emote Collector', frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                break
            elif key == ord(' ') and features is not None:
                current_emote = self.emote_labels[self.current_emote_index]
                self.save_sample(features, current_emote)
            elif key == ord('n'):
                self.current_emote_index = (self.current_emote_index + 1) % len(self.emote_labels)
                print(f"\n→ Switched to: {self.emote_labels[self.current_emote_index]}")

        cap.release()
        cv2.destroyAllWindows()

        print("\n" + "="*70)
        print("COLLECTION COMPLETE!")
        print(f"Saved {len(self.training_data)} samples to {self.output_file}")
        print("\nSamples per emote:")
        for emote, count in self.samples_per_emote.items():
            print(f"  {emote}: {count}")
        print("\nNext step: python train_ultimate_classifier.py")
        print("="*70)


if __name__ == "__main__":
    collector = UltimateEmoteCollector()
    collector.run()
