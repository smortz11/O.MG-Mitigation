"""HID key mappings - EXACT copy from main_SENDER.py"""
from hidpi.keyboard_keys import *

MOD_LSHIFT = 0x02
MOD_RSHIFT = 0x20
MOD_LCTRL = 0x01
MOD_RCTRL = 0x10
MOD_LALT = 0x04
MOD_RALT = 0x40

KEY_MAPPING = {
    'KEY_LEFTBRACE': 0x2F, 'KEY_RIGHTBRACE': 0x30,
    'KEY_DOT': 0x37, 'KEY_COMMA': 0x36,
    'KEY_SLASH': 0x38, 'KEY_SEMICOLON': 0x33,
    'KEY_APOSTROPHE': 0x34, 'KEY_GRAVE': 0x35,
    'KEY_MINUS': 0x2D, 'KEY_EQUAL': 0x2E,
    'KEY_BACKSLASH': 0x31,
    'KEY_KP0': 0x27, 'KEY_KP1': 0x1E, 'KEY_KP2': 0x1F,
    'KEY_KP3': 0x20, 'KEY_KP4': 0x21, 'KEY_KP5': 0x22,
    'KEY_KP6': 0x23, 'KEY_KP7': 0x24, 'KEY_KP8': 0x25,
    'KEY_KP9': 0x26, 'KEY_KPDOT': 0x37, 'KEY_KPSLASH': 0x38,
    'KEY_KPASTERISK': 0x55, 'KEY_KPMINUS': 0x2D,
    'KEY_KPPLUS': 0x2E, 'KEY_KPENTER': 0x28,
}

def get_hid_code(key):
    """Look up the keycode from hidpi constants or our manual mapping"""
    return globals().get(key) or KEY_MAPPING.get(key)

def calculate_modifier(key, shift, caps_lock, ctrl):
    """EXACT logic from main_SENDER.py"""
    modifier = 0
    
    # Special handling for numpad plus (needs shift)
    if key == 'KEY_KPPLUS':
        return MOD_LSHIFT
    
    # Check if it's a single letter key (A-Z)
    is_letter = (key.startswith("KEY_") and 
                len(key) == 5 and 
                key[4:].isalpha())
    
    if is_letter:
        if shift ^ caps_lock:  # XOR: uppercase if exactly one is active
            modifier = MOD_LSHIFT
    else:
        # For non-letter keys: only apply shift if the shift key is actually pressed
        if shift:
            modifier = MOD_LSHIFT
    
    # Add Ctrl modifier if Ctrl is pressed
    if ctrl:
        modifier |= MOD_LCTRL
    
    return modifier

"""HID key mappings and character conversions"""
from hidpi.keyboard_keys import *

# ... (keep your existing MOD_* and KEY_MAPPING as-is) ...

# ============================================================================
# CHARACTER MAPPING - for keymap scrambling
# ============================================================================

# Map evdev keys to their base characters (unshifted)
EVDEV_TO_CHAR = {
    # Letters (lowercase only)
    'KEY_A': 'a', 'KEY_B': 'b', 'KEY_C': 'c', 'KEY_D': 'd',
    'KEY_E': 'e', 'KEY_F': 'f', 'KEY_G': 'g', 'KEY_H': 'h',
    'KEY_I': 'i', 'KEY_J': 'j', 'KEY_K': 'k', 'KEY_L': 'l',
    'KEY_M': 'm', 'KEY_N': 'n', 'KEY_O': 'o', 'KEY_P': 'p',
    'KEY_Q': 'q', 'KEY_R': 'r', 'KEY_S': 's', 'KEY_T': 't',
    'KEY_U': 'u', 'KEY_V': 'v', 'KEY_W': 'w', 'KEY_X': 'x',
    'KEY_Y': 'y', 'KEY_Z': 'z',
    
    # Numbers
    'KEY_0': '0', 'KEY_1': '1', 'KEY_2': '2', 'KEY_3': '3',
    'KEY_4': '4', 'KEY_5': '5', 'KEY_6': '6', 'KEY_7': '7',
    'KEY_8': '8', 'KEY_9': '9',
    
    # Basic symbols (unshifted)
    'KEY_SPACE': ' ',
    'KEY_MINUS': '-',
    'KEY_EQUAL': '=',
    'KEY_LEFTBRACE': '[',
    'KEY_RIGHTBRACE': ']',
    'KEY_SEMICOLON': ';',
    'KEY_APOSTROPHE': "'",
    'KEY_GRAVE': '`',
    'KEY_BACKSLASH': '\\',
    'KEY_COMMA': ',',
    'KEY_DOT': '.',
    'KEY_SLASH': '/',
    
    # Numpad (map to regular numbers/symbols)
    'KEY_KP0': '0', 'KEY_KP1': '1', 'KEY_KP2': '2',
    'KEY_KP3': '3', 'KEY_KP4': '4', 'KEY_KP5': '5',
    'KEY_KP6': '6', 'KEY_KP7': '7', 'KEY_KP8': '8',
    'KEY_KP9': '9',
    'KEY_KPDOT': '.',
    'KEY_KPSLASH': '/',
    'KEY_KPASTERISK': '*',
    'KEY_KPMINUS': '-',
    'KEY_KPPLUS': '+',
}

# Shift transformations (when shift is pressed)
SHIFT_MAP = {
    # Numbers → Symbols
    '1': '!', '2': '@', '3': '#', '4': '$', '5': '%',
    '6': '^', '7': '&', '8': '*', '9': '(', '0': ')',
    
    # Symbols → Shifted symbols
    '-': '_', '=': '+',
    '[': '{', ']': '}',
    ';': ':', "'": '"',
    '`': '~', '\\': '|',
    ',': '<', '.': '>', '/': '?',
}

# Reverse mapping: character → evdev key
CHAR_TO_EVDEV = {}
for evdev_key, char in EVDEV_TO_CHAR.items():
    # For letters, only map lowercase
    if char.isalpha():
        CHAR_TO_EVDEV[char.lower()] = evdev_key
    else:
        CHAR_TO_EVDEV[char] = evdev_key

# Add shifted characters to reverse map
for base, shifted in SHIFT_MAP.items():
    evdev_key = CHAR_TO_EVDEV.get(base)
    if evdev_key:
        CHAR_TO_EVDEV[shifted] = evdev_key


def evdev_to_char(key, is_uppercase=False):
    """
    Convert evdev key to character.
    
    Args:
        key: evdev key name (e.g., 'KEY_A')
        is_uppercase: True if shift or caps should apply
    
    Returns:
        Character string or None if not mappable
    """
    base_char = EVDEV_TO_CHAR.get(key)
    if not base_char:
        return None
    
    # Handle uppercase letters
    if base_char.isalpha() and is_uppercase:
        return base_char.upper()
    
    return base_char


def char_to_evdev(char):
    """
    Convert character to evdev key name.
    
    Returns:
        (evdev_key, needs_shift) tuple
    """
    # Check if it's a shifted character
    for base, shifted in SHIFT_MAP.items():
        if char == shifted:
            evdev_key = CHAR_TO_EVDEV.get(base)
            return (evdev_key, True) if evdev_key else (None, False)
    
    # Check direct mapping (handles uppercase letters too)
    evdev_key = CHAR_TO_EVDEV.get(char.lower())
    needs_shift = char.isupper()
    
    return (evdev_key, needs_shift)


def is_mappable_key(key):
    """Check if a key can be scrambled by the keymap"""
    return key in EVDEV_TO_CHAR


# ... (keep all your existing functions: get_hid_code, calculate_modifier, etc.) ...
