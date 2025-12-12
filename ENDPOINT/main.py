"""ENDPOINT - Receive and decode scrambled keystrokes"""
import time
from ENDPOINT.keyboard_reader import KeyboardReader
from ENDPOINT.keyboard_writer import KeyboardWriter
from ENDPOINT.key_mapper import char_to_keycode, CHAR_TO_KEYCODE
from ENDPOINT.dhe_time_ENDPOINT import get_symmetric_key, get_base_time
from ENDPOINT.seedgen_ENDPOINT import generate_seed
from UTILS.keymap import seed_to_keymap, reverse_keymap

INTERVAL = 10

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

def main():
    # Initialize encryption
    print("[ENDPOINT] Initializing secure connection...")
    sym_key = get_symmetric_key()
    base_time = get_base_time()
    
    reader = KeyboardReader()
    writer = KeyboardWriter()
    
    current_keymap = None
    current_reverse_map = None
    last_counter = None
    
    print("[ENDPOINT] Starting decoder with rotating keymap...")
    print("[ENDPOINT] Press Ctrl+C to stop.")
    
    try:
        for event in reader.read_events():
            # Update keymap if interval changed
            now = time.time()
            counter = int((now - base_time) / INTERVAL)
            if counter != last_counter:
                last_counter = counter
                seed = generate_seed(sym_key, base_time, INTERVAL)
                current_keymap = seed_to_keymap(seed)
                current_reverse_map = reverse_keymap(current_keymap)
                print(f"\n[KEYMAP ROTATED] Counter={counter}, Seed={seed.hex()[:12]}...\n")
            
            key = event['key']
            shift = event['shift']
            ctrl = event['ctrl']
            
            # Check if this is a mappable key
            scrambled_char = EVDEV_TO_CHAR.get(key)
            
            if not scrambled_char:
                # Special keys (Enter, Tab, etc.) - pass through as-is
                # Just write the key directly to output
                keycode = getattr(__import__('evdev.ecodes', fromlist=['ecodes']), key, None)
                if keycode:
                    modifier = 0
                    if shift:
                        modifier |= 0x02
                    if ctrl:
                        modifier |= 0x01
                    writer.write_key(keycode, modifier)
                continue
            
            # Handle case
            is_uppercase = shift
            if is_uppercase:
                scrambled_char = scrambled_char.upper()
            
            # Decode: scrambled → original
            original_char = current_reverse_map.get(scrambled_char.lower(), scrambled_char.lower())
            
            # Preserve case
            if scrambled_char.isupper():
                original_char = original_char.upper()
            
            # Convert original character → keycode
            keycode, modifier = char_to_keycode(original_char)
            if not keycode:
                print(f"Warning: Can't map '{original_char}' to keycode")
                continue
            
            # Add Ctrl if needed
            if ctrl:
                modifier |= 0x01
            
            # Write decoded key
            writer.write_key(keycode, modifier)
            print(f"  '{scrambled_char}' → '{original_char}'")
    
    except KeyboardInterrupt:
        print("\n[ENDPOINT] Stopped by user.")
    finally:
	reader.close()
        writer.close()

if __name__ == "__main__":
    main()
