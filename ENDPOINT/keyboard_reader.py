"""Read HID input from the SENDER device"""
from evdev import InputDevice, ecodes, categorize, list_devices

class KeyboardReader:
    def __init__(self):
        """
        Find and open the keyboard device from SENDER
        """
        print("[ENDPOINT] Looking for input devices...")
        
        # List all input devices
        devices = [InputDevice(path) for path in list_devices()]
        
        # Find the keyboard HID gadget device (not mouse)
        self.dev = None
        for device in devices:
            # Check if it's a keyboard by looking at capabilities
            caps = device.capabilities()
            
            # Must have EV_KEY (keyboard events)
            if ecodes.EV_KEY not in caps:
                continue
            
            # Check if it has letter keys (keyboards have KEY_A, etc.)
            key_codes = caps.get(ecodes.EV_KEY, [])
            has_letters = any(code in key_codes for code in [
                ecodes.KEY_A, ecodes.KEY_B, ecodes.KEY_C, ecodes.KEY_Z
            ])
            
            # Should NOT have mouse buttons
            has_mouse = any(code in key_codes for code in [
                ecodes.BTN_LEFT, ecodes.BTN_RIGHT, ecodes.BTN_MIDDLE
            ])
            
            # If it has letters and no mouse buttons, it's probably the keyboard
            if has_letters and not has_mouse and 'rikka' in device.name.lower():
                self.dev = device
                print(f"[ENDPOINT] Using keyboard: {device.name} at {device.path}")
                break
        
        if not self.dev:
            print("[ENDPOINT] Could not auto-detect keyboard device")
            print("[ENDPOINT] Available devices:")
            for device in devices:
                caps = device.capabilities()
                has_key = ecodes.EV_KEY in caps
                print(f"  {device.name} - {device.path} [EV_KEY: {has_key}]")
            raise RuntimeError("No suitable keyboard device found")
    
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
