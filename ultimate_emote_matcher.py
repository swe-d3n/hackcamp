"""
ULTIMATE ML-Based Emote Matcher - Maximum Accuracy
- Hand orientation detection (palm/back)
- Ultra-sensitive face detection
- Advanced mouth tracking (works when covered)
- 98-feature model
"""

import cv2
import numpy as np
import mediapipe as mp
import time
from collections import deque
from emote_classifier import EmoteClassifier


class UltimateEmoteMatcher:
    """Ultimate ML-based emote detection - maximum accuracy"""

    def __init__(self, confidence_threshold=0.75, match_hold_time=1.5, model_path="emote_model_ultimate.pkl"):
        """Initialize ultimate matcher"""
        self.confidence_threshold = confidence_threshold
        self.match_hold_time = match_hold_time

        # MediaPipe setup - ultra-sensitive
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.2,
            min_tracking_confidence=0.2
        )

        self.hands_detection = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            model_complexity=1,
            min_detection_confidence=0.2,
            min_tracking_confidence=0.2
        )

        # Load ML classifier
        self.classifier = EmoteClassifier(model_path=model_path)
        if not self.classifier.is_trained():
            raise ValueError(
                f"No trained model found at {model_path}!\n"
                "Please run ultimate_emote_collector.py and train_ultimate_classifier.py first."
            )

        # Match tracking
        self.current_match = None
        self.match_start_time = None
        self.last_trigger_time = 0
        self.trigger_cooldown = 2.0

        # Smoothing
        self.prediction_history = deque(maxlen=3)

    def detect_hand_orientation(self, hand_landmarks):
        """Detect palm vs back of hand"""
        wrist = hand_landmarks.landmark[0]
        index_mcp = hand_landmarks.landmark[5]
        pinky_mcp = hand_landmarks.landmark[17]

        v1_x = index_mcp.x - wrist.x
        v1_y = index_mcp.y - wrist.y
        v1_z = index_mcp.z - wrist.z

        v2_x = pinky_mcp.x - wrist.x
        v2_y = pinky_mcp.y - wrist.y
        v2_z = pinky_mcp.z - wrist.z

        normal_z = v1_x * v2_y - v1_y * v2_x

        palm_score = (normal_z + 1) / 2
        return float(palm_score)

    def calculate_advanced_mouth_features(self, face_landmarks):
        """Calculate mouth features with redundancy"""
        try:
            upper_lip = face_landmarks.landmark[13]
            lower_lip = face_landmarks.landmark[14]
            mouth_height = abs(upper_lip.y - lower_lip.y)

            left_corner = face_landmarks.landmark[61]
            right_corner = face_landmarks.landmark[291]
            mouth_width = abs(left_corner.x - right_corner.x)

            if mouth_width > 0.001:
                mouth_ratio = mouth_height / mouth_width
            else:
                mouth_ratio = 0.0

            mouth_area = mouth_height * mouth_width
            mouth_center_x = (left_corner.x + right_corner.x) / 2
            mouth_center_y = (upper_lip.y + lower_lip.y) / 2

            return {
                'ratio': mouth_ratio,
                'height': mouth_height,
                'width': mouth_width,
                'area': mouth_area,
                'center_x': mouth_center_x,
                'center_y': mouth_center_y
            }
        except:
            return {
                'ratio': 0.0,
                'height': 0.0,
                'width': 0.0,
                'area': 0.0,
                'center_x': 0.5,
                'center_y': 0.5
            }

    def extract_features(self, frame):
        """Extract 98 features"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = frame.shape

        face_results = self.face_mesh.process(rgb_frame)

        if not face_results.multi_face_landmarks:
            return None, None, None, None

        face_landmarks = face_results.multi_face_landmarks[0]

        # Face features
        x_coords = [lm.x for lm in face_landmarks.landmark]
        y_coords = [lm.y for lm in face_landmarks.landmark]

        face_center_x = sum(x_coords) / len(x_coords)
        face_center_y = sum(y_coords) / len(y_coords)
        face_width = max(x_coords) - min(x_coords)
        face_height = max(y_coords) - min(y_coords)

        face_features = [face_center_x, face_center_y, face_width, face_height]

        face_data = {
            'center': (face_center_x, face_center_y),
            'size': (face_width + face_height) / 2,
            'bbox': (
                int(min(x_coords) * w),
                int(min(y_coords) * h),
                int(face_width * w),
                int(face_height * h)
            )
        }

        # Mouth features
        mouth_data = self.calculate_advanced_mouth_features(face_landmarks)
        mouth_features = [
            mouth_data['ratio'],
            mouth_data['height'],
            mouth_data['width'],
            mouth_data['area'],
            mouth_data['center_x'],
            mouth_data['center_y']
        ]

        # Hand detection with orientation
        hands_results = self.hands_detection.process(rgb_frame)

        left_hand_features = [0.0] * 44
        right_hand_features = [0.0] * 44
        hands_data = {'left': None, 'right': None}

        if hands_results.multi_hand_landmarks:
            for hand_idx, hand_landmarks in enumerate(hands_results.multi_hand_landmarks):
                handedness = hands_results.multi_handedness[hand_idx].classification[0].label.lower()

                hand_coords = []
                for landmark in hand_landmarks.landmark:
                    hand_coords.extend([landmark.x, landmark.y])

                orientation = self.detect_hand_orientation(hand_landmarks)

                # FIX: Invert orientation for left hand only
                if handedness == 'left':
                    orientation = 1.0 - orientation  # Invert for left hand

                wrist = hand_landmarks.landmark[0]
                middle_mcp = hand_landmarks.landmark[9]
                center_x = (wrist.x + middle_mcp.x) / 2
                center_y = (wrist.y + middle_mcp.y) / 2

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

        # 98 total features
        features = face_features + mouth_features + left_hand_features + right_hand_features

        return np.array(features), face_data, hands_data, mouth_data

    def smooth_prediction(self, prediction):
        """Smooth predictions"""
        self.prediction_history.append(prediction)

        if len(self.prediction_history) == 0:
            return prediction

        emote_votes = {}
        confidence_sum = {}

        for pred in self.prediction_history:
            emote = pred['emote']
            conf = pred['confidence']

            if emote not in emote_votes:
                emote_votes[emote] = 0
                confidence_sum[emote] = 0

            emote_votes[emote] += 1
            confidence_sum[emote] += conf

        best_emote = max(emote_votes, key=emote_votes.get)
        avg_confidence = confidence_sum[best_emote] / emote_votes[best_emote]

        avg_probabilities = {}
        for emote in prediction['probabilities'].keys():
            avg_probabilities[emote] = np.mean([
                pred['probabilities'].get(emote, 0.0)
                for pred in self.prediction_history
            ])

        return {
            'emote': best_emote,
            'confidence': avg_confidence,
            'probabilities': avg_probabilities
        }

    def match_emote(self, frame):
        """Match using ultimate ML model"""
        features, face_data, hands_data, mouth_data = self.extract_features(frame)

        if features is None:
            self.prediction_history.clear()
            return {
                'emote': None,
                'confidence': 0.0,
                'triggered': False,
                'hold_progress': 0.0,
                'probabilities': {},
                'face_data': None,
                'hands_data': {'left': None, 'right': None},
                'mouth_data': None
            }

        # Predict
        prediction = self.classifier.predict(features)
        smoothed = self.smooth_prediction(prediction)

        emote_name = smoothed['emote']
        confidence = smoothed['confidence']

        triggered = False
        hold_progress = 0.0
        matched_emote = None

        if confidence >= self.confidence_threshold and emote_name != "None/Neutral":
            matched_emote = emote_name
            current_time = time.time()

            if self.current_match == emote_name:
                elapsed = current_time - self.match_start_time
                hold_progress = min(1.0, elapsed / self.match_hold_time)

                if elapsed >= self.match_hold_time:
                    if current_time - self.last_trigger_time > self.trigger_cooldown:
                        triggered = True
                        self.last_trigger_time = current_time
                        print(f"🎭 EMOTE TRIGGERED: {emote_name} (Confidence: {confidence:.1%})")
            else:
                self.current_match = emote_name
                self.match_start_time = current_time
        else:
            self.current_match = None
            self.match_start_time = None

        return {
            'emote': matched_emote,
            'confidence': confidence,
            'triggered': triggered,
            'hold_progress': hold_progress,
            'probabilities': smoothed['probabilities'],
            'face_data': face_data,
            'hands_data': hands_data,
            'mouth_data': mouth_data
        }

    def draw_debug(self, frame, match_result):
        """Draw debug UI"""
        face_data = match_result['face_data']
        hands_data = match_result['hands_data']
        mouth_data = match_result.get('mouth_data')
        h, w, _ = frame.shape

        # Draw face box
        if face_data:
            x, y, w_box, h_box = face_data['bbox']
            cv2.rectangle(frame, (x, y), (x + w_box, y + h_box), (0, 255, 0), 2)

        # Draw hands with orientation
        for hand_type in ['left', 'right']:
            if hands_data[hand_type]:
                hand_info = hands_data[hand_type]

                self.mp_draw.draw_landmarks(
                    frame, hand_info['landmarks'],
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style()
                )

                pos = hand_info['position']
                x_px = int(pos[0] * w)
                y_px = int(pos[1] * h)

                orient = hand_info['orientation']
                orient_text = "PALM" if orient > 0.5 else "BACK"
                orient_color = (0, 255, 0) if orient > 0.5 else (0, 165, 255)

                cv2.putText(frame, f"{hand_type.upper()}: {orient_text}",
                           (x_px - 60, y_px - 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, orient_color, 2)

        # Mouth indicator
        if mouth_data:
            mouth_color = (0, 255, 0) if mouth_data['ratio'] > 0.35 else (150, 150, 150)
            cv2.putText(frame, f"Mouth: {mouth_data['ratio']:.2f}",
                       (10, h - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, mouth_color, 2)

        # ML Predictions sidebar
        sidebar_x = 10
        sidebar_y = 150

        cv2.putText(frame, "ULTIMATE ML (98 features):", (sidebar_x, sidebar_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        sidebar_y += 30

        if match_result['probabilities']:
            sorted_probs = sorted(
                match_result['probabilities'].items(),
                key=lambda x: x[1],
                reverse=True
            )

            for emote, prob in sorted_probs:
                if emote == "None/Neutral" and prob < 0.3:
                    continue

                if prob >= self.confidence_threshold:
                    color = (0, 255, 0)
                    status = "✓ MATCH"
                elif prob >= 0.5:
                    color = (0, 255, 255)
                    status = "~ Maybe"
                else:
                    color = (100, 100, 100)
                    status = ""

                text = f"{emote}: {prob:.1%} {status}"
                cv2.putText(frame, text, (sidebar_x, sidebar_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                sidebar_y += 25

        # Current match display
        if match_result['emote']:
            emote = match_result['emote']
            confidence = match_result['confidence']
            progress = match_result['hold_progress']

            text_size = cv2.getTextSize(emote, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)[0]
            text_x = (w - text_size[0]) // 2

            cv2.rectangle(frame, (text_x - 10, 10), (text_x + text_size[0] + 10, 50),
                         (0, 0, 0), -1)
            cv2.rectangle(frame, (text_x - 10, 10), (text_x + text_size[0] + 10, 50),
                         (0, 255, 255), 2)

            cv2.putText(frame, emote, (text_x, 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 3)

            cv2.putText(frame, f"Confidence: {confidence:.1%}", (text_x, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            # Progress bar
            bar_width = 400
            bar_height = 30
            bar_x = (w - bar_width) // 2
            bar_y = 90

            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height),
                         (255, 255, 255), 2)

            fill_width = int(bar_width * progress)
            fill_color = (0, 255, 255) if progress < 1.0 else (0, 255, 0)

            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_width, bar_y + bar_height),
                         fill_color, -1)

            bar_text = f"Hold... {progress:.0%}"
            text_size = cv2.getTextSize(bar_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            text_pos = (bar_x + (bar_width - text_size[0]) // 2, bar_y + 20)
            cv2.putText(frame, bar_text, text_pos,
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        else:
            instruction = "Perform an emote pose"
            text_size = cv2.getTextSize(instruction, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            text_x = (w - text_size[0]) // 2

            cv2.rectangle(frame, (text_x - 10, 10), (text_x + text_size[0] + 10, 45),
                         (50, 50, 50), -1)
            cv2.putText(frame, instruction, (text_x, 35),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)

        # Triggered celebration
        if match_result['triggered']:
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, h), (0, 255, 0), -1)
            cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)

            trigger_text = "EMOTE TRIGGERED!"
            text_size = cv2.getTextSize(trigger_text, cv2.FONT_HERSHEY_SIMPLEX, 2.5, 5)[0]
            text_x = (w - text_size[0]) // 2
            text_y = h // 2

            cv2.putText(frame, trigger_text, (text_x + 5, text_y + 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 2.5, (0, 0, 0), 5)
            cv2.putText(frame, trigger_text, (text_x, text_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 2.5, (0, 255, 0), 5)

            emote_text = f">>> {match_result['emote']} <<<"
            text_size2 = cv2.getTextSize(emote_text, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 3)[0]
            text_x2 = (w - text_size2[0]) // 2
            cv2.putText(frame, emote_text, (text_x2, text_y + 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)

        # Version
        cv2.putText(frame, "ULTIMATE | Hand Orientation | Max Accuracy", (10, h - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    def release(self):
        """Release resources"""
        self.face_mesh.close()
        self.hands_detection.close()
