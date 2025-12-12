"""Read keyboard events from evdev"""
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
        self.shift = False
        self.ctrl = False
    
    def read_events(self):
        """Generator yielding (key_event, caps_lock, shift, ctrl)"""
        for event in self.dev.read_loop():
            if event.type == ecodes.EV_KEY:
                key_event = categorize(event)
                key = key_event.keycode
                state = key_event.keystate
                
                # Handle state BEFORE yielding
                if key == 'KEY_CAPSLOCK' and state == key_event.key_down:
                    self.caps_lock = not self.caps_lock
                    print(f"[Caps Lock {'ON' if self.caps_lock else 'OFF'}]")
                    continue
                
                elif key in ['KEY_LEFTSHIFT', 'KEY_RIGHTSHIFT']:
                    self.shift = (state == key_event.key_down)
                    continue
                
                elif key in ['KEY_LEFTCTRL', 'KEY_RIGHTCTRL']:
                    self.ctrl = (state == key_event.key_down)
                    continue
                
                # Yield everything else
                yield key_event, self.caps_lock, self.shift, self.ctrl
