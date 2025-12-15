
"""Read keyboard events from evdev with proper modifier tracking"""
from evdev import InputDevice, ecodes, categorize
from UTILS import get_device_info

class KeyboardReader:
    def __init__(self):
        keyboard_name = get_device_info.get_keyboard()
        if not keyboard_name:
            raise RuntimeError("ERROR: Keyboard not found")
        
        self.dev = InputDevice('/dev/input/by-id/' + keyboard_name)
        print(f"Listening on {self.dev.path} ({self.dev.name}) ... Press Ctrl+C to quit.")
        
        self.caps_lock = False
        self.shift_left = False
        self.shift_right = False
        self.ctrl_left = False
        self.ctrl_right = False
    
    def read_events(self):
        """Generator yielding (key_event, caps_lock, shift, ctrl)"""
        for event in self.dev.read_loop():
            if event.type == ecodes.EV_KEY:
                key_event = categorize(event)
                key = key_event.keycode
                state = key_event.keystate
                
                # Track left shift
                if key == 'KEY_LEFTSHIFT':
                    self.shift_left = (state == key_event.key_down or state == key_event.key_hold)
                    print(f"[MOD] Left Shift: {self.shift_left}")
                    continue
                
                # Track right shift
                elif key == 'KEY_RIGHTSHIFT':
                    self.shift_right = (state == key_event.key_down or state == key_event.key_hold)
                    print(f"[MOD] Right Shift: {self.shift_right}")
                    continue
                
                # Track left ctrl
                elif key == 'KEY_LEFTCTRL':
                    self.ctrl_left = (state == key_event.key_down or state == key_event.key_hold)
                    print(f"[MOD] Left Ctrl: {self.ctrl_left}")
                    continue
                
                # Track right ctrl
                elif key == 'KEY_RIGHTCTRL':
                    self.ctrl_right = (state == key_event.key_down or state == key_event.key_hold)
                    print(f"[MOD] Right Ctrl: {self.ctrl_right}")
                    continue
                
                # Handle caps lock toggle
                elif key == 'KEY_CAPSLOCK' and state == key_event.key_down:
                    self.caps_lock = not self.caps_lock
                    print(f"[MOD] Caps Lock: {self.caps_lock}")
                    continue
                
                # For all other keys, yield with current modifier state
                shift = self.shift_left or self.shift_right
                ctrl = self.ctrl_left or self.ctrl_right
                
                # Only yield key down and hold events (not release)
                if state == key_event.key_down or state == key_event.key_hold:
                    yield key_event, self.caps_lock, shift, ctrl
