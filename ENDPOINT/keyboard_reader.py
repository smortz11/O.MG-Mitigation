"""Read HID input from USB gadget interface"""
from evdev import InputDevice, ecodes, categorize

class KeyboardReader:
    def __init__(self, device_path='/dev/hidg0'):
        """
        Initialize HID gadget reader
        
        Args:
            device_path: Path to HID gadget device (usually /dev/hidg0)
        """
        try:
            self.dev = InputDevice(device_path)
            print(f"[ENDPOINT] Listening on {device_path}")
        except Exception as e:
            print(f"[ENDPOINT] Error opening {device_path}: {e}")
            print("[ENDPOINT] Trying to find HID device...")
            # Fallback: try to find any HID device
            from evdev import list_devices
            devices = [InputDevice(path) for path in list_devices()]
            for device in devices:
                if 'hid' in device.name.lower():
                    self.dev = device
                    print(f"[ENDPOINT] Found HID device: {device.name}")
                    break
            else:
                raise RuntimeError("No HID device found")
    
    def read_events(self):
        """Generator yielding keyboard events with modifiers"""
        shift = False
        ctrl = False
        alt = False
        
        for event in self.dev.read_loop():
            if event.type == ecodes.EV_KEY:
                key_event = categorize(event)
                key = key_event.keycode
                state = key_event.keystate
                
                # Track modifiers
                if key in ['KEY_LEFTSHIFT', 'KEY_RIGHTSHIFT']:
                    shift = (state == key_event.key_down)
                    continue
                elif key in ['KEY_LEFTCTRL', 'KEY_RIGHTCTRL']:
                    ctrl = (state == key_event.key_down)
                    continue
                elif key in ['KEY_LEFTALT', 'KEY_RIGHTALT']:
                    alt = (state == key_event.key_down)
                    continue
                
                # Yield key events
                if state == key_event.key_down or state == key_event.key_hold:
                    yield {
                        'key': key,
                        'shift': shift,
                        'ctrl': ctrl,
                        'alt': alt,
                        'state': state,
                        'key_event': key_event
                    }
