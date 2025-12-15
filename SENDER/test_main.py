
"""Main keyboard forwarding loop with keymap scrambling"""
import time
from SENDER.keyboard_reader import KeyboardReader
from SENDER.key_mapper import (
    get_hid_code, calculate_modifier, 
    evdev_to_char, char_to_evdev, is_mappable_key,
    MOD_LSHIFT, MOD_LCTRL
)
from SENDER.key_sender import send_key
from SENDER.dhe_time import get_symmetric_key, get_base_time
from SENDER.seedgen import generate_seed
from UTILS.keymap import seed_to_keymap

INTERVAL = 10
TIME_OFFSET = -0.4  # Negative so SENDER is ahead

def main():
    # Initialize encryption
    print("[SENDER] Initializing secure connection...")
    sym_key = get_symmetric_key()
    base_time = get_base_time()
    
    reader = KeyboardReader()
    current_keymap = None
    last_counter = None
    
    print("[SENDER] Starting keyboard with rotating scrambler...")
    print("[SENDER] Press Ctrl+C to stop.")
    
    try:
        for key_event, caps_lock, shift, ctrl in reader.read_events():
            # Update keymap if interval changed
            now = time.time()
            counter = int((now - (base_time + TIME_OFFSET)) / INTERVAL)
            
            if counter != last_counter:
                last_counter = counter
                seed = generate_seed(sym_key, counter)  # FIXED: Only pass counter
                current_keymap = seed_to_keymap(seed)
                print(f"\n[KEYMAP ROTATED] Counter={counter}, Seed={seed.hex()[:12]}...\n")
            
            key = key_event.keycode
            state = key_event.keystate
            
            if state == key_event.key_down or state == key_event.key_hold:
                # Check if this key can be scrambled
                if not is_mappable_key(key):
                    # Special keys (Enter, Tab, Backspace, etc.) - send as-is
                    hid_key = get_hid_code(key)
                    if hid_key:
                        modifier = calculate_modifier(key, shift, caps_lock, ctrl)
                        send_key(modifier, hid_key, key)
                    continue
                
                # Convert evdev key → character
                is_uppercase = shift ^ caps_lock
                original_char = evdev_to_char(key, is_uppercase)
                if not original_char:
                    continue
                
                # Apply keymap scrambling (lowercase only for mapping)
                scrambled_char = current_keymap.get(original_char.lower(), original_char.lower())
                
                # Preserve case
                if original_char.isupper():
                    scrambled_char = scrambled_char.upper()
                
                # Convert scrambled character → evdev key
                scrambled_evdev, needs_shift = char_to_evdev(scrambled_char)
                if not scrambled_evdev:
                    print(f"Warning: Can't map '{scrambled_char}' back to evdev")
                    continue
                
                # Get HID code and build modifier
                hid_key = get_hid_code(scrambled_evdev)
                if not hid_key:
                    continue
                
                # Build modifier byte
                modifier = 0
                if needs_shift or scrambled_char.isupper():
                    modifier |= MOD_LSHIFT
                if ctrl:
                    modifier |= MOD_LCTRL
                
                # Send scrambled key
                send_key(modifier, hid_key, scrambled_evdev)
                print(f"  '{original_char}' → '{scrambled_char}'")
    
    except KeyboardInterrupt:
        print("\n[SENDER] Stopped by user.")

if __name__ == "__main__":
    main()
