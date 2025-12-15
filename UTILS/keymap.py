import random

# Standard QWERTY layout - all keys we want to remap
KEYS = [
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
    'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
    ' ', '.', ',', '!', '?', '-', '_', '@', '#', '$', '%', '&', '*',
    '(', ')', '[', ']', '{', '}', ':', ';', '"', "'", '/', '\\', '|',
    '+', '=', '<', '>', '~', '`'
]

def seed_to_keymap(seed: bytes) -> dict:
    """
    Convert a seed into a deterministic key remapping.
    Returns a dict: {original_key: scrambled_key}
    """
    # Use seed as random state
    seed_int = int.from_bytes(seed, byteorder='big')
    rng = random.Random(seed_int)
    
    # Create a shuffled copy of keys
    scrambled = KEYS.copy()
    rng.shuffle(scrambled)
    
    # Map original -> scrambled
    keymap = {original: scrambled[i] for i, original in enumerate(KEYS)}
    
    return keymap

def apply_keymap(text: str, keymap: dict) -> str:
    """Apply the keymap to scramble text"""
    return ''.join(keymap.get(c.lower(), c) for c in text)

def reverse_keymap(keymap: dict) -> dict:
    """Create inverse mapping for decryption"""
    return {scrambled: original for original, scrambled in keymap.items()}

def decrypt_text(scrambled_text: str, keymap: dict) -> str:
    """Decrypt scrambled text using the keymap"""
    inverse = reverse_keymap(keymap)
    return ''.join(inverse.get(c.lower(), c) for c in scrambled_text)
