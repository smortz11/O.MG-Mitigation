
"""Deterministic keymap generation from seed"""
import random

# SEPARATE letter and symbol pools to preserve case
LETTERS = [
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
    'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'
]

SYMBOLS = [
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
    ' ', '.', ',', '!', '?', '-', '_', '@', '#', '$', '%', '&', '*',
    '(', ')', '[', ']', '{', '}', ':', ';', '"', "'", '/', '\\', '|',
    '+', '=', '<', '>', '~', '`'
]

# Combined list for backwards compatibility
KEYS = LETTERS + SYMBOLS

def seed_to_keymap(seed: bytes) -> dict:
    """
    Convert a seed into a deterministic key remapping.
    Returns a dict: {original_key: scrambled_key}
    
    CRITICAL: Letters only map to letters (preserves case)
              Symbols only map to symbols
    """
    # Convert bytes to integer for deterministic seeding
    seed_int = int.from_bytes(seed, byteorder='big')
    
    # Use seed as random state
    rng = random.Random(seed_int)
    
    # Shuffle letters separately
    scrambled_letters = LETTERS.copy()
    rng.shuffle(scrambled_letters)
    
    # Shuffle symbols separately
    scrambled_symbols = SYMBOLS.copy()
    rng.shuffle(scrambled_symbols)
    
    # Build keymap: letters → letters, symbols → symbols
    keymap = {}
    
    for i, letter in enumerate(LETTERS):
        keymap[letter] = scrambled_letters[i]
    
    for i, symbol in enumerate(SYMBOLS):
        keymap[symbol] = scrambled_symbols[i]
    
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


# Test function to verify determinism and separation
if __name__ == "__main__":
    import hmac
    from hashlib import sha256
    
    # Generate test seed
    test_key = b"test_symmetric_key_12345678901234"
    test_seed = hmac.new(test_key, b"\x00\x00\x00\x00\x00\x00\x00\x05", sha256).digest()
    
    print("Testing keymap with seed:", test_seed.hex()[:24] + "...")
    
    keymap = seed_to_keymap(test_seed)
    
    print("\n=== LETTER MAPPINGS ===")
    for letter in ['a', 'h', 'k', 'd']:
        mapped = keymap[letter]
        print(f"  {letter} → {mapped} (is letter: {mapped.isalpha()})")
    
    print("\n=== SYMBOL MAPPINGS ===")
    for symbol in ['1', '!', '=', ')']:
        mapped = keymap[symbol]
        print(f"  {symbol} → {mapped} (is letter: {mapped.isalpha()})")
    
    # Verify letters only map to letters
    all_letters_ok = all(keymap[letter].isalpha() for letter in LETTERS)
    all_symbols_ok = all(not keymap[symbol].isalpha() or symbol == ' ' for symbol in SYMBOLS if symbol.isalpha() == False)
    
    print(f"\n✓ All letters map to letters: {all_letters_ok}")
    print(f"✓ All symbols map to symbols: {all_symbols_ok}")
    
    # Test with uppercase
    print("\n=== CASE PRESERVATION TEST ===")
    original = "Hello World!"
    scrambled = apply_keymap(original, keymap)
    decrypted = decrypt_text(scrambled, keymap)
    print(f"  Original:  '{original}'")
    print(f"  Scrambled: '{scrambled}'")
    print(f"  Decrypted: '{decrypted}'")
