"""
tests/research/run_sender_timed.py

Wrapper to run SENDER with timing instrumentation
NO CHANGES to original main.py needed!
"""

import sys
from pathlib import Path

# Add project root to path so we can import SENDER modules
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import timing logger
from tests.research.shared_timer import SharedTimer

# Import SENDER modules
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

import time

INTERVAL = 10
TIME_OFFSET = -0.4
BUFFER_WINDOW = 0.5

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
    # Initialize timing
    timer = SharedTimer("SENDER")
    print("[TIMING] SENDER timing enabled - logging to tests/research/results/timing_log.jsonl")
    
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
            # *** TIMING: Log key capture ***
            timer.log_event("capture", key_event.keycode)
            
            # Check if we're too close to a rotation
            time_until_rotation = get_time_until_rotation(base_time)
            
            if time_until_rotation < BUFFER_WINDOW:
                print(f"[BUFFER] {time_until_rotation:.2f}s until rotation - waiting...")
                time.sleep(time_until_rotation + 0.05)
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
                    # Special keys - send as-is
                    print(f"[PASS-THROUGH] {key}")
                    hid_key = get_hid_code(key)
                    if hid_key:
                        modifier = calculate_modifier(key, shift, caps_lock, ctrl)
                        
                        # *** TIMING: Log before send ***
                        timer.log_event("encrypt_send", key_event.keycode, {'passthrough': True})
                        
                        send_key(modifier, hid_key, key)
                    continue
                
                # Figure out what character the user is typing
                base_char = EVDEV_TO_CHAR.get(key)
                if not base_char:
                    continue
                
                # Determine the actual character being typed
                if base_char.isalpha():
                    if shift ^ caps_lock:
                        original_char = base_char.upper()
                    else:
                        original_char = base_char.lower()
                elif shift and base_char in SHIFT_MAP:
                    original_char = SHIFT_MAP[base_char]
                else:
                    original_char = base_char
                
                print(f"[INPUT] '{original_char}' (key={key}, base='{base_char}', shift={shift}, caps={caps_lock})")
                
                # Scramble the character
                scrambled_char = current_keymap.get(original_char.lower(), original_char.lower())
                
                # Preserve case
                if original_char.isupper():
                    if scrambled_char.isalpha():
                        scrambled_char = scrambled_char.upper()
                    else:
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
                
                # *** TIMING: Log before send ***
                timer.log_event("encrypt_send", key_event.keycode, {
                    'original': original_char,
                    'scrambled': scrambled_char
                })
                
                # Send scrambled key
                send_key(modifier, hid_key, scrambled_evdev)
                print(f"[SENT] '{scrambled_char}' (evdev={scrambled_evdev}, HID=0x{hid_key:02x}, mod=0x{modifier:02x})\n")
    
    except KeyboardInterrupt:
        print("\n[SENDER] Stopped by user.")
        print(f"[TIMING] Log saved to tests/research/results/timing_log.jsonl")

if __name__ == "__main__":
    main()
