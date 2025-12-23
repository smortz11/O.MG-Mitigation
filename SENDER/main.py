
"""Main keyboard forwarding loop with keymap scrambling"""
import time
from SENDER.keyboard_reader import KeyboardReader
from SENDER.key_mapper import (
    get_hid_code, calculate_modifier, 
    evdev_to_char, char_to_evdev, is_mappable_key,
    SHIFT_MAP, MOD_LSHIFT, MOD_LCTRL, EVDEV_TO_CHAR
)
from SENDER.key_sender import send_key
from SENDER.dhe_time import get_symmetric_key, get_base_time
from SENDER.seedgen import generate_seed
from UTILS.keymap import seed_to_keymap

INTERVAL = 10
TIME_OFFSET = -0.4  # Negative so SENDER is ahead
BUFFER_WINDOW = .4  # Don't send if within 0.5s of rotation
POST_ROTATION_GUARD = .4

def get_current_counter(base_time):
    """Calculate counter - adjusted for serial transmission delay"""
    now = time.time()
    counter = int((now - (base_time + TIME_OFFSET)) / INTERVAL)
    return counter

def get_time_until_rotation(base_time):
    """Calculate how many seconds until next counter rotation"""
    now = time.time()
    adjusted_time = now - (base_time + TIME_OFFSET)
    seconds_into_interval = adjusted_time % INTERVAL
    time_until_rotation = INTERVAL - seconds_into_interval
    return time_until_rotation

def main():
    # Initialize encryption
    print("[SENDER] Initializing secure connection...")
    sym_key = get_symmetric_key()
    base_time = get_base_time()
    
    print(f"[SENDER] Symmetric key: {sym_key.hex()[:16]}...")
    print(f"[SENDER] Base time: {base_time}")
    print(f"[SENDER] Current time: {time.time():.2f}")
    print(f"[SENDER] Time offset: {TIME_OFFSET}s")
    print(f"[SENDER] Buffer window: {BUFFER_WINDOW}s")
    print(f"[SENDER] Initial counter: {get_current_counter(base_time)}")
    
    reader = KeyboardReader()
    current_keymap = None
    last_counter = None
    
    print("[SENDER] Starting keyboard with rotating scrambler...")
    print("[SENDER] Press Ctrl+C to stop.\n")
    
    try:
        for key_event, caps_lock, shift, ctrl in reader.read_events():
            # Check if we're too close to a rotation
            time_until_rotation = get_time_until_rotation(base_time)
            
            if time_until_rotation < BUFFER_WINDOW:
                # Too close to rotation - wait for new counter
                print(f"[BUFFER] {time_until_rotation:.2f}s until rotation - waiting...")
                time.sleep(time_until_rotation + POST_ROTATION_GUARD)  # Wait plus small margin
                print("[BUFFER] Rotation complete, resuming...")
            
            # Update keymap if interval changed
            counter = get_current_counter(base_time)
            
            if counter != last_counter:
                last_counter = counter
                seed = generate_seed(sym_key, counter)
                current_keymap = seed_to_keymap(seed)
                now = time.time()
                print(f"\n[KEYMAP ROTATED] Counter={counter}, Seed={seed.hex()[:12]}...")
                print(f"  Time: {now:.2f}, Base: {base_time}, Adjusted: {now - (base_time + TIME_OFFSET):.2f}s")
                print(f"  Sample: a→{current_keymap.get('a', '?')}, !→{current_keymap.get('!', '?')}\n")
            
            key = key_event.keycode
            state = key_event.keystate
            
            if state == key_event.key_down or state == key_event.key_hold:
                # Check if this key can be scrambled
                if not is_mappable_key(key):
                    # Special keys (Enter, Tab, Backspace, etc.) - send as-is
                    print(f"[PASS-THROUGH] {key}")
                    hid_key = get_hid_code(key)
                    if hid_key:
                        modifier = calculate_modifier(key, shift, caps_lock, ctrl)
                        send_key(modifier, hid_key, key)
                    continue
                
                # Figure out what character the user is typing
                base_char = EVDEV_TO_CHAR.get(key)
                if not base_char:
                    continue
                
                # Determine the actual character being typed
                if base_char.isalpha():
                    # Letter: use caps XOR shift for uppercase
                    if shift ^ caps_lock:
                        original_char = base_char.upper()
                    else:
                        original_char = base_char.lower()
                elif shift and base_char in SHIFT_MAP:
                    # Shifted symbol: 1→!, 2→@, etc.
                    original_char = SHIFT_MAP[base_char]
                else:
                    # Unshifted symbol or number
                    original_char = base_char
                
                print(f"[INPUT] '{original_char}' (key={key}, base='{base_char}', shift={shift}, caps={caps_lock})")
                
                # Scramble the character
                # CRITICAL: Always use lowercase for keymap lookup
                scrambled_char = current_keymap.get(original_char.lower(), original_char.lower())
                
                # Preserve case: if input was uppercase, output must be uppercase
                if original_char.isupper():
                    if scrambled_char.isalpha():
                        scrambled_char = scrambled_char.upper()
                    else:
                        # This shouldn't happen with separated letter/symbol pools
                        print(f"[ERROR] Uppercase letter '{original_char}' mapped to non-letter '{scrambled_char}'!")
                        continue
                
                print(f"[SCRAMBLE] '{original_char}' → '{scrambled_char}'")
                
                # Convert scrambled character back to key + shift state
                scrambled_evdev, needs_shift = char_to_evdev(scrambled_char)
                if not scrambled_evdev:
                    print(f"[ERROR] Can't map '{scrambled_char}' to evdev key\n")
                    continue
                
                # Get HID code
                hid_key = get_hid_code(scrambled_evdev)
                if not hid_key:
                    print(f"[ERROR] No HID code for {scrambled_evdev}\n")
                    continue
                
                # Build modifier byte
                modifier = 0
                if needs_shift:
                    modifier |= MOD_LSHIFT
                if ctrl:
                    modifier |= MOD_LCTRL
                
                # Send scrambled key
                send_key(modifier, hid_key, scrambled_evdev)
                print(f"[SENT] '{scrambled_char}' (evdev={scrambled_evdev}, HID=0x{hid_key:02x}, mod=0x{modifier:02x})\n")
    
    except KeyboardInterrupt:
        print("\n[SENDER] Stopped by user.")

if __name__ == "__main__":
    main()
