from evdev import InputDevice, ecodes, categorize
import subprocess
import get_device_info
from keymaps import QWERTY_MAP, DVORAK_MAP, SHIFT_MAP  # Import shift map too

# Toggleable keys to track for accurate reading
caps_lock = False
shift = False

keyboard_name = get_device_info.get_keyboard()  # Invoke function to grab keyboard name
if not keyboard_name:
    print("ERROR: Keyboard not found")
    exit(1)

dev = InputDevice('/dev/input/by-id/' + keyboard_name)  # Full path to device to read raw input
# dev.grab()  # NOTE: WHEN THIS IS TOGGLED ON, KEYBOARD INPUT STOPS WORKING, BUT READS MORE ACCURATELY

print(f"Listening on {dev.path} ({dev.name}) ... Press Ctrl+C to quit.")

# Logic to determine dvorak/qwerty
layout, variant = get_device_info.get_key_mapping()

try:
    if layout == 'us' and variant == 'dvorak':
        keycode_char_map = DVORAK_MAP
    elif layout == 'us' and variant == 'qwerty':
        keycode_char_map = QWERTY_MAP
except Exception as e:
        print(f"Error detecting keyboard layout or variant: {e}")
        print("Defaulting to qwerty layout...")
        keycode_char_map = QWERTY_MAP
    

for event in dev.read_loop():
    if event.type == ecodes.EV_KEY:
        key_event = categorize(event)
        key = key_event.keycode
        state = key_event.keystate

        if key == 'KEY_CAPSLOCK' and state == key_event.key_down:
            caps_lock = not caps_lock  # Toggle caps_lock state
            print(f"[Caps Lock {'ON' if caps_lock else 'OFF'}]")

        elif key in ['KEY_LEFTSHIFT', 'KEY_RIGHTSHIFT']: # Message for toggle shift lags script
            shift = state == key_event.key_down  # True on key down, False on up

        elif state == key_event.key_down:
            base_char = keycode_char_map.get(key)  # Sanitize input to get raw character

            if base_char:
                # Determine if we need to capitalize
                if base_char.isalpha():
                    # XOR: one or the other, both would negate each other
                    if caps_lock ^ shift:
                        base_char = base_char.upper()

                elif shift:
                    # Handle shift keys that arent normal caps
                    base_char = SHIFT_MAP.get(base_char, base_char)

                print(f"Key pressed: {base_char}")
            else:
                print(f"Key pressed: {key}")
