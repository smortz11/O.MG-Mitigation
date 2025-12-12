"""Main keyboard forwarding loop - EXACT logic from main_SENDER.py"""
from SENDER.keyboard_reader import KeyboardReader
from SENDER.key_mapper import get_hid_code, calculate_modifier
from SENDER.key_sender import send_key

def main():
    reader = KeyboardReader()
    # reader.dev.grab()  # Uncomment for exclusive access
    
    try:
        for key_event, caps_lock, shift, ctrl in reader.read_events():
            key = key_event.keycode
            state = key_event.keystate
            
            # Log and send keys if key is pressed or held
            if state == key_event.key_down or state == key_event.key_hold:
                hid_key = get_hid_code(key)
                if hid_key is None:
                    print(f"Warning: No HID mapping for {key} (code: {key_event.scancode})")
                    continue
                
                modifier = calculate_modifier(key, shift, caps_lock, ctrl)
                send_key(modifier, hid_key, key)
    
    except KeyboardInterrupt:
        print("\nStopped by user.")

if __name__ == "__main__":
    main()
