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
        
        # Find the HID gadget device (from SENDER)
        # It might show up as "raspberrypi" or "HID Gadget" or similar
        self.dev = None
        for device in devices:
            print(f"  Found: {device.name} at {device.path}")
            # Look for keywords that indicate it's from the SENDER
            if any(keyword in device.name.lower() for keyword in ['gadget', 'raspberrypi', 'hid']):
                self.dev = device
                print(f"[ENDPOINT] Using: {device.name}")
                break
        
        if not self.dev:
            # If can't auto-detect, let user choose or use first keyboard
            print("[ENDPOINT] Could not auto-detect SENDER device")
            print("[ENDPOINT] Available devices:")
            for i, device in enumerate(devices):
                print(f"  {i}: {device.name} - {device.path}")
            
            # For now, just use the first keyboard-like device
            for device in devices:
                caps = device.capabilities()
                # Check if it has keyboard capabilities
                if ecodes.EV_KEY in caps:
                    self.dev = device
                    print(f"[ENDPOINT] Using: {device.name}")
                    break
        
        if not self.dev:
            raise RuntimeError("No suitable input device found")
    
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
