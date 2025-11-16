"""
BlueStacks Emote Controller
Controls Clash Royale emotes in BlueStacks using keyboard shortcuts
Maps detected emotes to keyboard key sequences
"""

import pyautogui
import time


class EmoteClicker:
    def __init__(self, emote_button_key='e', emote_key_map=None, cooldown=1.5):
        """
        Initialize BlueStacks emote controller
        
        Args:
            emote_button_key: Key to open emote menu (default 'e')
            emote_key_map: Dict mapping emote_name -> key to press
                          If None, uses default mapping
            cooldown: Minimum seconds between emotes (default 1.5)
        """
        self.emote_button_key = emote_button_key
        
        # Default key mapping for emotes
        # Customize these based on your BlueStacks key mapping configuration
        self.emote_key_map = emote_key_map or {
            # Row 1
            "laughing": "1",
            "crying": "2",
            "angry": "3",
            "king_thumbs_up": "4",
            
            # Row 2
            "thumbs_up": "q",
            "chicken": "w",
            "goblin_kiss": "r",
            "princess_yawn": "t",
            
            # Row 3
            "wow": "a",
            "thinking": "s",
            "screaming": "d",
            "king_laugh": "f",
            
            # Row 4
            "goblin_laugh": "z",
            "princess_cry": "x",
            "goblin_angry": "c",
        }
        
        self.cooldown = cooldown
        self.last_emote_time = 0
        
        # Safety features
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.01
        
        # Delay between key presses
        self.key_delay = 0.05  # 50ms between keystrokes
    
    def can_trigger_emote(self):
        """Check if enough time has passed since last emote"""
        return (time.time() - self.last_emote_time) >= self.cooldown
    
    def trigger_emote(self, emote_name):
        """
        Trigger emote by pressing key sequence
        
        Args:
            emote_name: Name of emote to trigger (must match key in emote_key_map)
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Check cooldown
        if not self.can_trigger_emote():
            time_left = self.cooldown - (time.time() - self.last_emote_time)
            print(f"Cooldown: {time_left:.1f}s remaining...")
            return False
        
        # Check if emote exists in mapping
        if emote_name not in self.emote_key_map:
            print(f"Warning: Emote '{emote_name}' not found in key mapping")
            return False
        
        try:
            emote_key = self.emote_key_map[emote_name]
            
            print(f"\n>>> TRIGGERING EMOTE: {emote_name} <<<")
            
            # Step 1: Press emote button to open menu
            print(f"  1. Opening emote menu (pressing '{self.emote_button_key}')...")
            pyautogui.press(self.emote_button_key)
            time.sleep(self.key_delay)
            
            # Step 2: Press specific emote key
            print(f"  2. Selecting emote (pressing '{emote_key}')...")
            pyautogui.press(emote_key)
            
            # Update last emote time
            self.last_emote_time = time.time()
            print("  ✓ Emote triggered successfully!")
            return True
            
        except Exception as e:
            print(f"Error triggering emote: {e}")
            return False
    
    def get_cooldown_remaining(self):
        """Get time remaining until next emote can be triggered"""
        elapsed = time.time() - self.last_emote_time
        remaining = max(0, self.cooldown - elapsed)
        return remaining
    
    def is_ready(self):
        """Check if controller is ready (not on cooldown)"""
        return self.get_cooldown_remaining() == 0
    
    def set_cooldown(self, seconds):
        """Change the cooldown time"""
        self.cooldown = seconds
    
    def set_key_mapping(self, emote_name, key):
        """
        Add or update key mapping for an emote
        
        Args:
            emote_name: Name of emote
            key: Keyboard key to trigger it
        """
        self.emote_key_map[emote_name] = key
        print(f"Updated key mapping: {emote_name} -> '{key}'")
    
    def get_mapped_emotes(self):
        """Get list of all mapped emote names"""
        return list(self.emote_key_map.keys())
    
    def print_key_mapping(self):
        """Print current key mapping configuration"""
        print("\n" + "="*60)
        print("BLUESTACKS EMOTE KEY MAPPING")
        print("="*60)
        print(f"Emote Menu Key: '{self.emote_button_key}'")
        print(f"Cooldown: {self.cooldown}s")
        print("\nEmote Key Bindings:")
        print("-" * 60)
        for emote_name, key in sorted(self.emote_key_map.items()):
            print(f"  {emote_name:20} -> '{key}'")
        print("="*60 + "\n")


# ============================================================
# CONFIGURATION HELPER
# ============================================================

def setup_bluestacks_keys():
    """
    Interactive guide for setting up BlueStacks key mapping
    """
    print("\n" + "="*60)
    print("BLUESTACKS KEY MAPPING SETUP GUIDE")
    print("="*60)
    
    print("\nSTEP 1: Configure BlueStacks Key Mapping")
    print("-" * 60)
    print("1. Open BlueStacks")
    print("2. Start Clash Royale")
    print("3. Click the keyboard icon (⌨️) in BlueStacks toolbar")
    print("4. Click 'Advanced editor' or 'Key mapping editor'")
    print("5. Map keys to emote positions:")
    print()
    print("   Recommended layout:")
    print("   - Press 'E' to open emote menu")
    print("   - Press number/letter keys for emotes:")
    print()
    print("     ROW 1: 1  2  3  4")
    print("     ROW 2: Q  W  R  T")
    print("     ROW 3: A  S  D  F")
    print("     ROW 4: Z  X  C  V")
    print()
    print("6. Save the key mapping in BlueStacks")
    
    print("\n" + "-" * 60)
    input("Press ENTER when you've configured BlueStacks keys...")
    
    print("\nSTEP 2: Test Your Configuration")
    print("-" * 60)
    print("Let's test if your key mapping works!")
    print()
    
    # Create controller with default mapping
    controller = EmoteClicker()
    controller.print_key_mapping()
    
    print("Now testing keyboard controls...")
    print("Make sure BlueStacks is in focus!")
    input("Press ENTER to test opening emote menu...")
    
    pyautogui.press('e')
    time.sleep(0.5)
    
    print("Did the emote menu open? (yes/no)")
    response = input("> ").lower()
    
    if response != 'yes':
        print("\n⚠️  Emote menu didn't open!")
        print("Solutions:")
        print("1. Make sure BlueStacks window is focused/active")
        print("2. Check that 'E' is mapped to emote button in BlueStacks")
        print("3. Try clicking on BlueStacks window first")
        return
    
    print("\n✓ Great! Emote menu opened.")
    print("\nNow let's test triggering an emote...")
    input("Press ENTER to trigger 'laughing' emote (key '1')...")
    
    pyautogui.press('1')
    
    print("\nDid the emote play? (yes/no)")
    response = input("> ").lower()
    
    if response == 'yes':
        print("\n🎉 SUCCESS! Your BlueStacks key mapping is working!")
        print("\nYou can now use this controller with your emote detection code.")
    else:
        print("\n⚠️  Emote didn't trigger!")
        print("Solutions:")
        print("1. Check that number keys are mapped correctly in BlueStacks")
        print("2. Make sure emote menu was still open")
        print("3. Verify key positions match your emote grid")
    
    print("\n" + "="*60)


# ============================================================
# TEST MODE
# ============================================================

def test_emote_controller():
    """Test the emote controller with keyboard input"""
    print("\n" + "="*60)
    print("BLUESTACKS EMOTE CONTROLLER - TEST MODE")
    print("="*60)
    
    print("\nMake sure:")
    print("✓ BlueStacks is running")
    print("✓ Clash Royale is open")
    print("✓ BlueStacks window is focused")
    print("✓ You've configured key mapping in BlueStacks")
    
    input("\nPress ENTER to continue...")
    
    # Create controller
    controller = EmoteClicker()
    controller.print_key_mapping()
    
    print("TEST CONTROLS:")
    print("  1 = Laughing emote")
    print("  2 = Crying emote")
    print("  3 = Angry emote")
    print("  4 = King thumbs up")
    print("  q = Quit test")
    print("="*60)
    
    print("\nFocus BlueStacks window now!")
    time.sleep(2)
    
    while True:
        key = input("\nPress a key (or 'q' to quit): ").lower()
        
        if key == 'q':
            print("Exiting test mode...")
            break
        elif key == '1':
            controller.trigger_emote("laughing")
        elif key == '2':
            controller.trigger_emote("crying")
        elif key == '3':
            controller.trigger_emote("angry")
        elif key == '4':
            controller.trigger_emote("king_thumbs_up")
        else:
            print("Invalid key! Use 1-4 or 'q'")


# ============================================================
# INTEGRATION EXAMPLE
# ============================================================

def example_integration():
    """
    Example showing how to integrate with emote detection
    """
    print("""
# ============================================================
# INTEGRATION WITH YOUR EMOTE DETECTION CODE
# ============================================================

# In your main emote detection script:

from bluestacks_emote_controller import BlueStacksEmoteController

# Initialize controller
emote_controller = BlueStacksEmoteController(
    emote_button_key='e',  # Key that opens emote menu
    cooldown=1.5           # Seconds between emotes
)

# In your detection loop:
def on_emote_detected(emote_name):
    '''Called when your face/hand detection recognizes an emote'''
    
    # Check if we can trigger an emote
    if emote_controller.is_ready():
        # Trigger the emote in BlueStacks
        success = emote_controller.trigger_emote(emote_name)
        
        if success:
            print(f"Triggered {emote_name} in game!")
        else:
            print(f"Failed to trigger {emote_name}")
    else:
        remaining = emote_controller.get_cooldown_remaining()
        print(f"Cooldown: {remaining:.1f}s remaining")

# Example usage:
# When you detect "laughing" expression + "thumbs_up" gesture:
on_emote_detected("laughing")

# ============================================================
""")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("BLUESTACKS EMOTE CONTROLLER")
    print("="*60)
    print("\nWhat would you like to do?")
    print("  1. Setup guide for BlueStacks key mapping")
    print("  2. Test emote controller")
    print("  3. Show integration example")
    print("="*60)
    
    choice = input("\nEnter choice (1, 2, or 3): ")
    
    if choice == "1":
        setup_bluestacks_keys()
    elif choice == "2":
        test_emote_controller()
    elif choice == "3":
        example_integration()
    else:
        print("Invalid choice!")