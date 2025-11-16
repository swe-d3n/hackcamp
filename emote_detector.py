import pyautogui
import numpy as np
import time

class EmoteController:
    def __init__(self, emote_coords, cooldown=1.0):
        """
        Args:
            emote_coords: dict mapping emote_name -> (x, y) screen coordinates
            cooldown: minimum seconds between emotes
        """
        self.emote_coords = emote_coords
        self.cooldown = cooldown
        self.last_emote_time = 0

    def detect_emote(self, hand1_landmarks, hand2_landmarks, emote_signatures):
        """
        Determine which emote matches current hand pose
        Args:
            hand1_landmarks, hand2_landmarks: list of dicts from Mediapipe
            emote_signatures: dict of emote_name -> np.array feature vector
        Returns:
            str: detected emote name
        """
        # Flatten normalized x,y coords of both hands into feature vector
        current_vector = np.array([lm['x'] for lm in hand1_landmarks + hand2_landmarks] +
                                  [lm['y'] for lm in hand1_landmarks + hand2_landmarks])

        best_emote = None
        min_dist = float('inf')
        for emote, signature in emote_signatures.items():
            dist = np.linalg.norm(current_vector - signature)
            if dist < min_dist:
                min_dist = dist
                best_emote = emote
        return best_emote

    def click_emote(self, emote_name):
        """
        Click the emote button on screen if cooldown passed
        Args:
            emote_name: str
        """
        current_time = time.time()
        if current_time - self.last_emote_time < self.cooldown:
            return  # still in cooldown

        if emote_name not in self.emote_coords:
            print(f"Emote {emote_name} not in coordinates map")
            return

        x, y = self.emote_coords[emote_name]
        orig_x, orig_y = pyautogui.position()
        pyautogui.click(x, y)
        pyautogui.moveTo(orig_x, orig_y, _pause=False)
        self.last_emote_time = current_time
        print(f"Emote {emote_name} clicked!")
