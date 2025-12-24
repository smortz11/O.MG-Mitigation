"""Read HID input from ALL keyboard devices"""
from evdev import InputDevice, ecodes, categorize, list_devices
import select

class KeyboardReader:
    def __init__(self):
        """Find and grab ALL keyboard devices"""
        print("[ENDPOINT] Looking for input devices...")
        
        devices = [InputDevice(path) for path in list_devices()]
        
        self.devs = []
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
            
            # REMOVED 'rikka' check - grab ALL keyboards!
            if has_letters and not has_mouse:
                try:
                    device.grab()
                    self.devs.append(device)
                    print(f"[ENDPOINT] ✓ Grabbed: {device.name} at {device.path}")
                except Exception as e:
                    print(f"[ENDPOINT] ✗ Failed to grab {device.name}: {e}")
        
        if not self.devs:
            raise RuntimeError("No suitable keyboard devices found")
        
        print(f"[ENDPOINT] Monitoring {len(self.devs)} keyboard device(s)")
    
    def read_events(self):
        """Generator yielding keyboard events from ALL devices"""
        shift = False
        ctrl = False
        alt = False
        
        # Create device map for select()
        dev_map = {dev.fd: dev for dev in self.devs}
        
        while True:
            # Wait for input from ANY device
            r, w, x = select.select(dev_map, [], [])
            
            for fd in r:
                device = dev_map[fd]
                
                # Read all pending events from this device
                for event in device.read():
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
                        
                        # Only yield key down events
                        if state == key_event.key_down:
                            yield {
                                'key': key,
                                'shift': shift,
                                'ctrl': ctrl,
                                'alt': alt,
                                'state': state,
                                'key_event': key_event,
                                'device': device.name  # For debugging
                            }
    
    def close(self):
        """Release all grabbed devices"""
        for dev in self.devs:
            try:
                dev.ungrab()
            except:
                pass
