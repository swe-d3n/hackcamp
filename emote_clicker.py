"""
Simple Emote Clicker
Clicks emote button then the specific emote when triggered
"""

import pyautogui
import time


class EmoteClicker:
    def __init__(self, emote_button_pos, emote_positions, click_delay=0.1):
        """
        Initialize emote clicker
        
        Args:
            emote_button_pos: (x, y) position of main emote button
            emote_positions: Dict of emote_name -> (x, y) position
            click_delay: Delay between clicks in seconds (default 0.1 for speed)
        """
        self.emote_button_pos = emote_button_pos
        self.emote_positions = emote_positions
        self.click_delay = click_delay
        
        # Cooldown to prevent spam clicking
        self.last_click_time = 0
        self.cooldown = 1.5  # 1.5 seconds between emote clicks
        
        # Safety features
        pyautogui.FAILSAFE = True  # Move mouse to corner to stop
        pyautogui.PAUSE = 0.01  # Minimal pause for fast clicking
    
    def can_click(self):
        """Check if enough time has passed since last click"""
        return (time.time() - self.last_click_time) >= self.cooldown
    
    def click_emote(self, emote_name):
        """
        Quickly click emote button then the specific emote
        
        Args:
            emote_name: Name of emote to click (must match key in emote_positions)
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Check cooldown
        if not self.can_click():
            time_left = self.cooldown - (time.time() - self.last_click_time)
            print(f"Cooldown: {time_left:.1f}s remaining...")
            return False
        
        # Check if emote exists
        if emote_name not in self.emote_positions:
            print(f"Error: Emote '{emote_name}' not found in positions")
            return False
        
        try:
            print(f"\n>>> CLICKING EMOTE: {emote_name} <<<")
            
            # Step 1: Click emote button to open menu
            print("  1. Opening emote menu...")
            pyautogui.click(self.emote_button_pos[0], self.emote_button_pos[1])
            time.sleep(self.click_delay)  # Wait for menu to open
            
            # Step 2: Click the specific emote
            emote_pos = self.emote_positions[emote_name]
            print(f"  2. Clicking {emote_name} at ({emote_pos[0]}, {emote_pos[1]})...")
            pyautogui.click(emote_pos[0], emote_pos[1])
            
            # Update last click time
            self.last_click_time = time.time()
            print("  ✓ Emote clicked successfully!")
            return True
            
        except Exception as e:
            print(f"Error clicking emote: {e}")
            return False
    
    def get_cooldown_remaining(self):
        """Get time remaining until next emote can be clicked"""
        elapsed = time.time() - self.last_click_time
        remaining = max(0, self.cooldown - elapsed)
        return remaining
    
    def is_ready(self):
        """Check if clicker is ready (not on cooldown)"""
        return self.get_cooldown_remaining() == 0
    
    def set_cooldown(self, seconds):
        """Change the cooldown time"""
        self.cooldown = seconds


# ============================================================
# CALIBRATION TOOL
# ============================================================

def calibrate():
    """Interactive calibration for emote positions"""
    print("\n" + "="*60)
    print("CLASH ROYALE EMOTE POSITION CALIBRATION")
    print("="*60)
    print("\nInstructions:")
    print("1. Open Clash Royale and start a match")
    print("2. Move your mouse to each position when prompted")
    print("3. Press ENTER to record each position")
    print("\n" + "="*60)
    
    input("\n[Step 1/2] Move mouse to the EMOTE BUTTON and press ENTER...")
    button_x, button_y = pyautogui.position()
    print(f"✓ Emote button recorded: ({button_x}, {button_y})")
    
    print("\n[Step 2/2] Now click the emote button to open the menu...")
    input("Press ENTER when the emote menu is open...")
    
    emote_positions = {}
    
    # Common Clash Royale emotes
    emote_list = [
        "laughing",
        "crying", 
        "angry",
        "king_laugh",
        "thumbs_up",
        "surprised",
        "chicken",
        "princess_yawn",
        "goblin_kiss"
    ]
    
    print("\nNow record each emote position:")
    for emote_name in emote_list:
        response = input(f"\n  Move to '{emote_name}' and press ENTER (or type 'skip')... ")
        if response.lower() == 'skip':
            continue
        x, y = pyautogui.position()
        emote_positions[emote_name] = (x, y)
        print(f"  ✓ {emote_name}: ({x}, {y})")
    
    # Output the configuration
    print("\n" + "="*60)
    print("CALIBRATION COMPLETE!")
    print("="*60)
    print("\nCopy this into your config.py:\n")
    print("-" * 60)
    print(f"\nEMOTE_BUTTON_POS = ({button_x}, {button_y})")
    print(f"\nEMOTE_POSITIONS = {{")
    for name, (x, y) in emote_positions.items():
        print(f'    "{name}": ({x}, {y}),')
    print("}")
    print("\n" + "-" * 60)
    print("\nYou can now use these in your code!")
    print("="*60)


# ============================================================
# TEST MODE
# ============================================================

def test_mode():
    """Test the clicker with keyboard controls"""
    print("\n" + "="*60)
    print("EMOTE CLICKER TEST MODE")
    print("="*60)
    print("\nYou need to add your positions first!")
    print("Example configuration:\n")
    
    # Example positions (CHANGE THESE TO YOUR ACTUAL POSITIONS!)
    EMOTE_BUTTON_POS = (1800, 950)
    EMOTE_POSITIONS = {
        "laughing": (1500, 700),
        "crying": (1600, 700),
        "angry": (1700, 700),
    }
    
    print(f"EMOTE_BUTTON_POS = {EMOTE_BUTTON_POS}")
    print(f"EMOTE_POSITIONS = {EMOTE_POSITIONS}\n")
    
    response = input("Have you updated these positions? (yes/no): ")
    if response.lower() != 'yes':
        print("\nPlease run calibrate() first or update the positions above!")
        return
    
    clicker = EmoteClicker(EMOTE_BUTTON_POS, EMOTE_POSITIONS)
    
    print("\n" + "="*60)
    print("TEST CONTROLS:")
    print("  Press 1 = Laughing emote")
    print("  Press 2 = Crying emote")
    print("  Press 3 = Angry emote")
    print("  Press Q = Quit")
    print("="*60)
    
    while True:
        key = input("\nPress a key: ").lower()
        
        if key == '1':
            clicker.click_emote("laughing")
        elif key == '2':
            clicker.click_emote("crying")
        elif key == '3':
            clicker.click_emote("angry")
        elif key == 'q':
            print("Exiting test mode...")
            break
        else:
            print("Invalid key!")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("EMOTE CLICKER SETUP")
    print("="*60)
    print("\nWhat would you like to do?")
    print("  1. Calibrate emote positions")
    print("  2. Test the clicker")
    print("="*60)
    
    choice = input("\nEnter choice (1 or 2): ")
    
    if choice == "1":
        calibrate()
    elif choice == "2":
        test_mode()
    else:
        print("Invalid choice!")