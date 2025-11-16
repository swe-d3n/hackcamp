"""
Face Detector Module
Detects faces and facial expressions using MediaPipe
"""

import cv2
import mediapipe as mp
import numpy as np


class FaceDetector:
    def __init__(self):
        """Initialize face detector with MediaPipe"""
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Key landmark indices for expression detection
        self.MOUTH_LANDMARKS = [61, 291, 0, 17, 269, 405]  # Mouth corners and center
        self.EYE_LANDMARKS = [33, 133, 362, 263]  # Eye corners
        self.EYEBROW_LANDMARKS = [70, 300]  # Eyebrow centers
        
    def get_expression(self, landmarks, image_shape):
        """
        Determine facial expression from landmarks
        
        Args:
            landmarks: Face mesh landmarks
            image_shape: Image dimensions (height, width)
        
        Returns:
            str: Expression name or None
        """
        h, w = image_shape[:2]
        
        # Convert landmarks to pixel coordinates
        points = []
        for lm in landmarks:
            x = int(lm.x * w)
            y = int(lm.y * h)
            points.append((x, y))
        
        # Calculate mouth openness (vertical distance)
        mouth_top = points[13]  # Upper lip
        mouth_bottom = points[14]  # Lower lip
        mouth_open_ratio = abs(mouth_top[1] - mouth_bottom[1]) / h
        
        # Calculate mouth width
        mouth_left = points[61]
        mouth_right = points[291]
        mouth_width = abs(mouth_right[0] - mouth_left[0]) / w
        
        # Calculate eye openness
        left_eye_top = points[159]
        left_eye_bottom = points[145]
        left_eye_open = abs(left_eye_top[1] - left_eye_bottom[1]) / h
        
        right_eye_top = points[386]
        right_eye_bottom = points[374]
        right_eye_open = abs(right_eye_top[1] - right_eye_bottom[1]) / h
        
        avg_eye_open = (left_eye_open + right_eye_open) / 2
        
        # Calculate eyebrow position (for angry/surprised)
        left_eyebrow = points[70]
        right_eyebrow = points[300]
        left_eye = points[33]
        right_eye = points[263]
        
        eyebrow_raise = (
            (left_eye[1] - left_eyebrow[1]) + 
            (right_eye[1] - right_eyebrow[1])
        ) / (2 * h)
        
        # Expression detection logic
        # Laughing/Happy: Wide smile, eyes slightly closed
        if mouth_width > 0.15 and mouth_open_ratio > 0.02:
            return "laughing"
        
        # Crying/Sad: Mouth down, eyes may be closed
        if mouth_width < 0.10 and eyebrow_raise < 0.08:
            return "crying"
        
        # Angry: Eyebrows down, mouth neutral or frown
        if eyebrow_raise < 0.06 and mouth_width < 0.12:
            return "angry"
        
        # Surprised/Shocked: Eyes wide, mouth open
        if avg_eye_open > 0.04 and mouth_open_ratio > 0.04:
            return "surprised"
        
        # Neutral
        return "neutral"
    
    def detect_face(self, image, draw=True):
        """
        Detect face and expression in image
        
        Args:
            image: Input image (BGR format)
            draw: Whether to draw landmarks on image
        
        Returns:
            tuple: (processed_image, face_data dict or None)
        """
        # Convert to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Process image
        results = self.face_mesh.process(rgb_image)
        
        face_data = None
        
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                # Get expression
                landmarks_list = face_landmarks.landmark
                expression = self.get_expression(landmarks_list, image.shape)
                
                face_data = {
                    'expression': expression,
                    'landmarks': landmarks_list
                }
                
                # Draw landmarks if requested
                if draw:
                    self.mp_drawing.draw_landmarks(
                        image=image,
                        landmark_list=face_landmarks,
                        connections=self.mp_face_mesh.FACEMESH_CONTOURS,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=self.mp_drawing_styles
                        .get_default_face_mesh_contours_style()
                    )
                    
                    # Draw expression text
                    cv2.putText(
                        image,
                        f"Expression: {expression}",
                        (10, image.shape[0] - 20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 255),
                        2
                    )
                
                break  # Only process first face
        
        return image, face_data
    
    def release(self):
        """Release resources"""
        self.face_mesh.close()