"""Character to evdev key mappings for ENDPOINT"""
from evdev import ecodes

# Map characters to evdev keycodes
CHAR_TO_KEYCODE = {
    # Letters
    'a': ecodes.KEY_A, 'b': ecodes.KEY_B, 'c': ecodes.KEY_C, 'd': ecodes.KEY_D,
    'e': ecodes.KEY_E, 'f': ecodes.KEY_F, 'g': ecodes.KEY_G, 'h': ecodes.KEY_H,
    'i': ecodes.KEY_I, 'j': ecodes.KEY_J, 'k': ecodes.KEY_K, 'l': ecodes.KEY_L,
    'm': ecodes.KEY_M, 'n': ecodes.KEY_N, 'o': ecodes.KEY_O, 'p': ecodes.KEY_P,
    'q': ecodes.KEY_Q, 'r': ecodes.KEY_R, 's': ecodes.KEY_S, 't': ecodes.KEY_T,
    'u': ecodes.KEY_U, 'v': ecodes.KEY_V, 'w': ecodes.KEY_W, 'x': ecodes.KEY_X,
    'y': ecodes.KEY_Y, 'z': ecodes.KEY_Z,
    
    # Numbers
    '0': ecodes.KEY_0, '1': ecodes.KEY_1, '2': ecodes.KEY_2, '3': ecodes.KEY_3,
    '4': ecodes.KEY_4, '5': ecodes.KEY_5, '6': ecodes.KEY_6, '7': ecodes.KEY_7,
    '8': ecodes.KEY_8, '9': ecodes.KEY_9,
    
    # Symbols (unshifted)
    ' ': ecodes.KEY_SPACE,
    '-': ecodes.KEY_MINUS,
    '=': ecodes.KEY_EQUAL,
    '[': ecodes.KEY_LEFTBRACE,
    ']': ecodes.KEY_RIGHTBRACE,
    ';': ecodes.KEY_SEMICOLON,
    "'": ecodes.KEY_APOSTROPHE,
    '`': ecodes.KEY_GRAVE,
    '\\': ecodes.KEY_BACKSLASH,
    ',': ecodes.KEY_COMMA,
    '.': ecodes.KEY_DOT,
    '/': ecodes.KEY_SLASH,
}

# Shifted characters mapping
SHIFTED_CHARS = {
    '!': '1', '@': '2', '#': '3', '$': '4', '%': '5',
    '^': '6', '&': '7', '*': '8', '(': '9', ')': '0',
    '_': '-', '+': '=',
    '{': '[', '}': ']',
    ':': ';', '"': "'",
    '~': '`', '|': '\\',
    '<': ',', '>': '.', '?': '/',
}

# Modifier constants
MOD_LSHIFT = 0x02
MOD_LCTRL = 0x01
MOD_LALT = 0x04


def char_to_keycode(char):
    """
    Convert character to evdev keycode and modifier.
    
    Returns:
        (keycode, modifier) tuple
    """
    # Check if it's a shifted character
    if char in SHIFTED_CHARS:
        base_char = SHIFTED_CHARS[char]
        keycode = CHAR_TO_KEYCODE.get(base_char)
        return (keycode, MOD_LSHIFT) if keycode else (None, 0)
    
    # Check if it's uppercase letter
    if char.isupper():
        keycode = CHAR_TO_KEYCODE.get(char.lower())
        return (keycode, MOD_LSHIFT) if keycode else (None, 0)
    
    # Direct mapping
    keycode = CHAR_TO_KEYCODE.get(char)
    return (keycode, 0) if keycode else (None, 0)
