"""Send keys via HID"""
from hidpi import Keyboard

def send_key(modifier, hid_key, key_name):
    """Send a key with modifiers"""
    try:
        print(f"DEBUG: key={key_name}, modifier=0x{modifier:02x}, hid_key=0x{hid_key:02x}")
        Keyboard.send_key(modifier, hid_key)
    except Exception as e:
        print(f"Error sending key {key_name}: {e}")
