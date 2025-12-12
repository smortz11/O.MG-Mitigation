from evdev import InputDevice, ecodes, categorize
import get_device_info
from hidpi import Keyboard
from hidpi.keyboard_keys import *

# Define modifier constants manually (if not already imported from hidpi)
MOD_LSHIFT = 0x02
MOD_RSHIFT = 0x20
MOD_LCTRL = 0x01
MOD_RCTRL = 0x10
MOD_LALT = 0x04
MOD_RALT = 0x40

# Manual key mappings for keys that might not be in hidpi.keyboard_keys
# These are standard HID keyboard scan codes
KEY_MAPPING = {
    'KEY_LEFTBRACE': 0x2F,   # [ and {
    'KEY_RIGHTBRACE': 0x30,  # ] and }
    'KEY_DOT': 0x37,         # . and >
    'KEY_COMMA': 0x36,       # , and <
    'KEY_SLASH': 0x38,       # / and ?
    'KEY_SEMICOLON': 0x33,   # ; and :
    'KEY_APOSTROPHE': 0x34,  # ' and "
    'KEY_GRAVE': 0x35,       # ` and ~
    'KEY_MINUS': 0x2D,       # - and _
    'KEY_EQUAL': 0x2E,       # = and +
    'KEY_BACKSLASH': 0x31,   # \ and |
    # Numpad keys - mapped to regular number keys for compatibility
    'KEY_KP0': 0x27,         # Numpad 0 -> regular 0
    'KEY_KP1': 0x1E,         # Numpad 1 -> regular 1
    'KEY_KP2': 0x1F,         # Numpad 2 -> regular 2
    'KEY_KP3': 0x20,         # Numpad 3 -> regular 3
    'KEY_KP4': 0x21,         # Numpad 4 -> regular 4
    'KEY_KP5': 0x22,         # Numpad 5 -> regular 5
    'KEY_KP6': 0x23,         # Numpad 6 -> regular 6
    'KEY_KP7': 0x24,         # Numpad 7 -> regular 7
    'KEY_KP8': 0x25,         # Numpad 8 -> regular 8
    'KEY_KP9': 0x26,         # Numpad 9 -> regular 9
    'KEY_KPDOT': 0x37,       # Numpad . -> regular period
    'KEY_KPSLASH': 0x38,     # Numpad / -> regular /
    'KEY_KPASTERISK': 0x55,  # Numpad * (keep original, no regular equivalent)
    'KEY_KPMINUS': 0x2D,     # Numpad - -> regular -
    'KEY_KPPLUS': 0x2E,      # Numpad + -> regular = (then shift for +)
    'KEY_KPENTER': 0x28,     # Numpad Enter -> regular Enter
}

# Track toggleable keys and modifiers
caps_lock = False
shift = False
ctrl = False

# Get keyboard device name
keyboard_name = get_device_info.get_keyboard()
if not keyboard_name:
    print("ERROR: Keyboard not found")
    exit(1)

# Open the input device
dev = InputDevice('/dev/input/by-id/' + keyboard_name)
# dev.grab()  # Uncomment if you want exclusive access (blocks normal typing)

print(f"Listening on {dev.path} ({dev.name}) ... Press Ctrl+C to quit.")

# Main read loop
try:
    for event in dev.read_loop():
        if event.type == ecodes.EV_KEY:
            key_event = categorize(event)
            key = key_event.keycode  # e.g. "KEY_A"
            state = key_event.keystate  # 1 = key down, 0 = key up, 2 = hold

            # Handle Caps Lock
            if key == 'KEY_CAPSLOCK' and state == key_event.key_down:
                caps_lock = not caps_lock
                print(f"[Caps Lock {'ON' if caps_lock else 'OFF'}]")
                continue  # Don't forward Caps Lock

            # Handle Shift (Track down/up properly, ignore hold)
            elif key in ['KEY_LEFTSHIFT', 'KEY_RIGHTSHIFT']:
                if state == key_event.key_down:
                    shift = True
                elif state == key_event.key_up:
                    shift = False
                continue  # Don't forward Shift keys

            # Handle Ctrl (Track down/up properly, ignore hold)
            elif key in ['KEY_LEFTCTRL', 'KEY_RIGHTCTRL']:
                if state == key_event.key_down:
                    ctrl = True
                elif state == key_event.key_up:
                    ctrl = False
                continue  # Don't forward Ctrl keys

            # Log and send keys if key is pressed or held
            if state == key_event.key_down or state == key_event.key_hold:
                # Initialize modifier for this key press
                modifier = 0
                
                # Look up the keycode from hidpi constants or our manual mapping
                hid_key = globals().get(key) or KEY_MAPPING.get(key)
                if hid_key is None:
                    print(f"Warning: No HID mapping for {key} (code: {key_event.scancode})")
                    continue  # Skip unmapped keys (e.g., modifiers like KEY_LEFTCTRL)

                # Special handling for numpad plus (needs shift)
                if key == 'KEY_KPPLUS':
                    modifier = MOD_LSHIFT  # Force shift for +
                
                # Handle upper or lower case based on caps_lock/shift
                # Check if it's a single letter key (A-Z)
                is_letter = (key.startswith("KEY_") and 
                            len(key) == 5 and 
                            key[4:].isalpha())
                
                if is_letter:  # Single letter keys only
                    if shift ^ caps_lock:  # XOR: uppercase if exactly one is active
                        modifier = MOD_LSHIFT
                    # else: no shift modifier needed for lowercase
                else:
                    # For non-letter keys (symbols, numbers, etc.):
                    # Only apply shift if the shift key is actually pressed
                    if shift:
                        modifier = MOD_LSHIFT
                
                # Add Ctrl modifier if Ctrl is pressed
                if ctrl:
                    modifier |= MOD_LCTRL

                # Send the key with the appropriate modifier
                try:
                    print(f"DEBUG: key={key}, shift={shift}, caps={caps_lock}, modifier=0x{modifier:02x}, hid_key=0x{hid_key:02x}")
                    Keyboard.send_key(modifier, hid_key)
                except Exception as e:
                    print(f"Error sending key {key}: {e}")

except KeyboardInterrupt:
    print("\nStopped by user.")
