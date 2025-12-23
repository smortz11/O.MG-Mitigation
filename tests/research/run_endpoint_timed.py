"""
tests/research/run_endpoint_timed.py

Wrapper to run ENDPOINT with timing instrumentation
NO CHANGES to original main.py needed!
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import timing logger
from tests.research.shared_timer import SharedTimer

# Import ENDPOINT modules
from ENDPOINT.keyboard_reader import KeyboardReader
from ENDPOINT.keyboard_writer import KeyboardWriter
from ENDPOINT.key_mapper import char_to_keycode
from ENDPOINT.dhe_time_ENDPOINT import get_symmetric_key, get_base_time
from ENDPOINT.seedgen_ENDPOINT import generate_seed
from UTILS.keymap import seed_to_keymap, reverse_keymap

import time

INTERVAL = 10
TIME_OFFSET = 0.0

# Map evdev keys to characters
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

SPECIAL_KEYS = [
    'KEY_ENTER', 'KEY_ESC', 'KEY_BACKSPACE', 'KEY_TAB',
    'KEY_UP', 'KEY_DOWN', 'KEY_LEFT', 'KEY_RIGHT',
    'KEY_HOME', 'KEY_END', 'KEY_PAGEUP', 'KEY_PAGEDOWN',
    'KEY_DELETE', 'KEY_INSERT',
]

SHIFT_MAP = {
    '1': '!', '2': '@', '3': '#', '4': '$', '5': '%',
    '6': '^', '7': '&', '8': '*', '9': '(', '0': ')',
    '-': '_', '=': '+',
    '[': '{', ']': '}',
    ';': ':', "'": '"',
    '`': '~', '\\': '|',
    ',': '<', '.': '>', '/': '?',
}

def get_current_counter(base_time):
    """Calculate counter"""
    now = int(time.time())
    counter = (now - base_time) // INTERVAL
    return counter

def main():
    # Initialize timing
    timer = SharedTimer("ENDPOINT")
    print("[TIMING] ENDPOINT timing enabled - logging to tests/research/results/timing_log.jsonl")
    
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
            # *** TIMING: Log key receive ***
            timer.log_event("receive", event['key'])
            
            # Update keymap if interval changed
            counter = get_current_counter(base_time)
            
            if counter != last_counter:
                last_counter = counter
                seed = generate_seed(sym_key, counter)
                current_keymap = seed_to_keymap(seed)
                current_reverse_map = reverse_keymap(current_keymap)
                now = time.time()
                print(f"\n[KEYMAP ROTATED] Counter={counter}, Seed={seed.hex()[:12]}...")
                print(f"  Time: {now:.2f}, Base: {base_time}, Diff: {now - base_time:.2f}s")
                print(f"  Reverse map has {len(current_reverse_map)} entries\n")
            
            key = event['key']
            shift = event['shift']
            ctrl = event['ctrl']
            
            # Check if this is a special key - pass through as-is
            if key in SPECIAL_KEYS:
                print(f"[PASS-THROUGH] {key}")
                keycode = getattr(__import__('evdev.ecodes', fromlist=['ecodes']), key, None)
                if keycode:
                    modifier = 0
                    if shift:
                        modifier |= 0x02
                    if ctrl:
                        modifier |= 0x01
                    
                    # *** TIMING: Log before inject ***
                    timer.log_event("decrypt_inject", key, {'passthrough': True})
                    
                    writer.write_key(keycode, modifier)
                continue
            
            # Get the base character for this key
            base_char = EVDEV_TO_CHAR.get(key)
            
            if not base_char:
                print(f"[UNKNOWN] {key}")
                keycode = getattr(__import__('evdev.ecodes', fromlist=['ecodes']), key, None)
                if keycode:
                    modifier = 0
                    if shift:
                        modifier |= 0x02
                    if ctrl:
                        modifier |= 0x01
                    
                    # *** TIMING: Log before inject ***
                    timer.log_event("decrypt_inject", key, {'unknown': True})
                    
                    writer.write_key(keycode, modifier)
                continue
            
            # Determine what character was actually sent
            if base_char.isalpha():
                scrambled_char = base_char.upper() if shift else base_char.lower()
            elif shift and base_char in SHIFT_MAP:
                scrambled_char = SHIFT_MAP[base_char]
            else:
                scrambled_char = base_char
            
            print(f"[RECEIVED] '{scrambled_char}' (key={key}, base='{base_char}', shift={shift})")
            
            # Decode: scrambled → original
            original_char = current_reverse_map.get(scrambled_char.lower(), scrambled_char.lower())
            
            # Preserve case
            if scrambled_char.isupper() and original_char.isalpha():
                original_char = original_char.upper()
            
            print(f"[DECODED] '{scrambled_char}' → '{original_char}'")
            
            # Convert original character → keycode
            keycode, modifier = char_to_keycode(original_char)
            if not keycode:
                print(f"[ERROR] Can't map '{original_char}' to keycode\n")
                continue
            
            # Add Ctrl if it was pressed
            if ctrl:
                modifier |= 0x01
            
            # *** TIMING: Log before inject ***
            timer.log_event("decrypt_inject", key, {
                'scrambled': scrambled_char,
                'original': original_char
            })
            
            # Write decoded key
            writer.write_key(keycode, modifier)
            print(f"✓ '{scrambled_char}' → '{original_char}'\n")
    
    except KeyboardInterrupt:
        print("\n[ENDPOINT] Stopped by user.")
        print(f"[TIMING] Log saved to tests/research/results/timing_log.jsonl")
    finally:
        reader.close()
        writer.close()

if __name__ == "__main__":
    main()
