"""ENDPOINT - Receive and decode scrambled keystrokes"""
import time
from ENDPOINT.keyboard_reader import KeyboardReader
from ENDPOINT.keyboard_writer import KeyboardWriter
from ENDPOINT.key_mapper import char_to_keycode, CHAR_TO_KEYCODE
from ENDPOINT.dhe_time_ENDPOINT import get_symmetric_key, get_base_time
from ENDPOINT.seedgen_ENDPOINT import generate_seed
from UTILS.keymap import seed_to_keymap, reverse_keymap

INTERVAL = 10
TIME_OFFSET = 0.0  # ENDPOINT doesn't need offset (it's the reference)

# Map evdev keys to characters (for incoming scrambled keys)
EVDEV_TO_CHAR = {
    'KEY_A': 'a', 'KEY_B': 'b', 'KEY_C': 'c', 'KEY_D': 'd',
    'KEY_E': 'e', 'KEY_F': 'f', 'KEY_G': 'g', 'KEY_H': 'h',
    'KEY_I': 'i', 'KEY_J': 'j', 'KEY_K': 'k', 'KEY_L': 'l',
    'KEY_M': 'm', 'KEY_N': 'n', 'KEY_O': 'o', 'KEY_P': 'p',
    'KEY_Q': 'q', 'KEY_R': 'r', 'KEY_S': 's', 'KEY_T': 't',
    'KEY_U': 'u', 'KEY_V': 'v', 'KEY_W': 'w', 'KEY_X': 'x',
    'KEY_Y': 'y', 'KEY_Z': 'z',
    'KEY_0': '0', 'KEY_1': '1', 'KEY_2': '2', 'KEY_3': '3',
    'KEY_4': '4', 'KEY_5': '5', 'KEY_6': '6', 'KEY_7': '7',
    'KEY_8': '8', 'KEY_9': '9',
    'KEY_SPACE': ' ', 'KEY_MINUS': '-', 'KEY_EQUAL': '=',
    'KEY_LEFTBRACE': '[', 'KEY_RIGHTBRACE': ']',
    'KEY_SEMICOLON': ';', 'KEY_APOSTROPHE': "'",
    'KEY_GRAVE': '`', 'KEY_BACKSLASH': '\\',
    'KEY_COMMA': ',', 'KEY_DOT': '.', 'KEY_SLASH': '/',
}

# Reverse mapping for special keys that need to be passed through
SPECIAL_KEYS = [
    'KEY_ENTER', 'KEY_ESC', 'KEY_BACKSPACE', 'KEY_TAB',
    'KEY_UP', 'KEY_DOWN', 'KEY_LEFT', 'KEY_RIGHT',
    'KEY_HOME', 'KEY_END', 'KEY_PAGEUP', 'KEY_PAGEDOWN',
    'KEY_DELETE', 'KEY_INSERT',
]

def get_current_counter(base_time):
    """Calculate counter - MUST match test code exactly"""
    now = int(time.time())
    counter = (now - base_time) // INTERVAL
    return counter

def main():
    # Initialize encryption
    print("[ENDPOINT] Initializing secure connection...")
    sym_key = get_symmetric_key()
    base_time = get_base_time()
    
    print(f"[ENDPOINT] Symmetric key: {sym_key.hex()[:16]}...")
    print(f"[ENDPOINT] Base time: {base_time}")
    print(f"[ENDPOINT] Current counter: {get_current_counter(base_time)}")
    
    reader = KeyboardReader()
    writer = KeyboardWriter()
    
    current_keymap = None
    current_reverse_map = None
    last_counter = None
    
    print("[ENDPOINT] Starting decoder with rotating keymap...")
    print("[ENDPOINT] Press Ctrl+C to stop.\n")
    
    try:
        for event in reader.read_events():
            # Update keymap if interval changed
            counter = get_current_counter(base_time)
            
            if counter != last_counter:
                last_counter = counter
                seed = generate_seed(sym_key, counter)  # Pass counter directly!
                current_keymap = seed_to_keymap(seed)
                current_reverse_map = reverse_keymap(current_keymap)
                now = time.time()
                print(f"\n[KEYMAP ROTATED] Counter={counter}, Seed={seed.hex()[:12]}...")
                print(f"  Time: {now:.2f}, Base: {base_time}, Diff: {now - base_time:.2f}s")
                print(f"  Forward: a→{current_keymap.get('a', '?')}, e→{current_keymap.get('e', '?')}")
                print(f"  Reverse: {current_keymap.get('a', '?')}→a, {current_keymap.get('e', '?')}→e")
                print(f"  Reverse map has {len(current_reverse_map)} entries\n")
            
            key = event['key']
            shift = event['shift']
            ctrl = event['ctrl']
            
            # Check if this is a special key (Enter, Tab, etc.) - pass through as-is
            if key in SPECIAL_KEYS:
                print(f"[SPECIAL] {key}")
                keycode = getattr(__import__('evdev.ecodes', fromlist=['ecodes']), key, None)
                if keycode:
                    modifier = 0
                    if shift:
                        modifier |= 0x02
                    if ctrl:
                        modifier |= 0x01
                    writer.write_key(keycode, modifier)
                continue
            
            # Check if this is a mappable key
            scrambled_char = EVDEV_TO_CHAR.get(key)
            
            if not scrambled_char:
                # Unknown key - pass through as-is
                print(f"[UNKNOWN] {key}")
                keycode = getattr(__import__('evdev.ecodes', fromlist=['ecodes']), key, None)
                if keycode:
                    modifier = 0
                    if shift:
                        modifier |= 0x02
                    if ctrl:
                        modifier |= 0x01
                    writer.write_key(keycode, modifier)
                continue
            
            # Store original shift state for special characters
            original_shift = shift
            
            # For reverse lookup, we need to consider what the SENDER sent
            # The SENDER shifts special chars, so we need to figure out what char they sent
            lookup_char = scrambled_char
            
            # If shift was pressed, figure out what shifted character was sent
            if shift:
                # Check if this creates a special character
                shift_map = {
                    '1': '!', '2': '@', '3': '#', '4': '$', '5': '%',
                    '6': '^', '7': '&', '8': '*', '9': '(', '0': ')',
                    '-': '_', '=': '+',
                    '[': '{', ']': '}',
                    ';': ':', "'": '"',
                    '`': '~', '\\': '|',
                    ',': '<', '.': '>', '/': '?',
                }
                if scrambled_char in shift_map:
                    lookup_char = shift_map[scrambled_char]
                else:
                    # It's a letter, convert to uppercase
                    lookup_char = scrambled_char.upper()
            
            print(f"[SCRAMBLED] '{lookup_char}' (key={key}, shift={shift})")
            
            # Decode: scrambled → original
            # Use lowercase for lookup in reverse map
            original_char = current_reverse_map.get(lookup_char.lower(), lookup_char.lower())
            
            # Preserve case/shift state
            if lookup_char.isupper():
                original_char = original_char.upper()
            
            print(f"[DECODED] '{lookup_char}' → '{original_char}'")
            
            # Convert original character → keycode
            keycode, modifier = char_to_keycode(original_char)
            if not keycode:
                print(f"[ERROR] Can't map '{original_char}' to keycode\n")
                continue
            
            # Add Ctrl if it was pressed
            if ctrl:
                modifier |= 0x01
            
            # Write decoded key
            writer.write_key(keycode, modifier)
            print(f"✓ '{lookup_char}' → '{original_char}'\n")
    
    except KeyboardInterrupt:
        print("\n[ENDPOINT] Stopped by user.")
    finally:
        reader.close()
        writer.close()

if __name__ == "__main__":
    main()
