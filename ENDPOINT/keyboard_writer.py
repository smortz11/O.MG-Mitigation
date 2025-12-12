"""Write decoded keystrokes as virtual keyboard"""
from evdev import UInput, ecodes

class KeyboardWriter:
    def __init__(self):
        # Create virtual keyboard device
        self.ui = UInput()
        print("[ENDPOINT] Virtual keyboard created")
    
    def write_key(self, keycode, modifier=0):
        """
        Write a key to the virtual keyboard
        
        Args:
            keycode: evdev keycode (e.g., ecodes.KEY_A)
            modifier: modifier flags (shift, ctrl, etc.)
        """
        # Press modifiers first
        if modifier & 0x02:  # Left Shift
            self.ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTSHIFT, 1)
        if modifier & 0x01:  # Left Ctrl
            self.ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTCTRL, 1)
        if modifier & 0x04:  # Left Alt
            self.ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTALT, 1)
        
        # Press the key
        self.ui.write(ecodes.EV_KEY, keycode, 1)
        self.ui.syn()
        
        # Release the key
        self.ui.write(ecodes.EV_KEY, keycode, 0)
        self.ui.syn()
        
        # Release modifiers
        if modifier & 0x02:
            self.ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTSHIFT, 0)
        if modifier & 0x01:
            self.ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTCTRL, 0)
        if modifier & 0x04:
            self.ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTALT, 0)
        
        self.ui.syn()
    
    def close(self):
        """Clean up the virtual keyboard"""
        self.ui.close()
