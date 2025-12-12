"""Read HID input from the SENDER device"""
from evdev import InputDevice, ecodes, categorize, list_devices

class KeyboardReader:
    def __init__(self):
        """Find and open the keyboard device from SENDER"""
        print("[ENDPOINT] Looking for input devices...")
        
        devices = [InputDevice(path) for path in list_devices()]
        
        self.dev = None
        for device in devices:
            # Skip virtual keyboards
            if 'virtual' in device.name.lower() or 'uinput' in device.name.lower():
                print(f"[ENDPOINT] Skipping virtual device: {device.name}")
                continue
            
            caps = device.capabilities()
            if ecodes.EV_KEY not in caps:
                continue
            
            key_codes = caps.get(ecodes.EV_KEY, [])
            has_letters = any(code in key_codes for code in [
                ecodes.KEY_A, ecodes.KEY_B, ecodes.KEY_C, ecodes.KEY_Z
            ])
            
            has_mouse = any(code in key_codes for code in [
                ecodes.BTN_LEFT, ecodes.BTN_RIGHT, ecodes.BTN_MIDDLE
            ])
            
            if has_letters and not has_mouse and 'rikka' in device.name.lower():
                self.dev = device
                print(f"[ENDPOINT] Using keyboard: {device.name} at {device.path}")
                break
        
        if not self.dev:
            raise RuntimeError("No suitable keyboard device found")
        
        # GRAB the device to prevent scrambled keys from leaking through!
        self.dev.grab()
        print("[ENDPOINT] Device grabbed - scrambled keys will not leak through")
    
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
                
                # Only yield key down events (not hold!)
                if state == key_event.key_down:
                    yield {
                        'key': key,
                        'shift': shift,
                        'ctrl': ctrl,
                        'alt': alt,
                        'state': state,
                        'key_event': key_event
                    }
    
    def close(self):
        """Release the grabbed device"""
        if self.dev:
            self.dev.ungrab()
