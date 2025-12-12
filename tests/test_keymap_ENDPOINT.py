from ENDPOINT.seedgen_ENDPOINT import generate_seed
from ENDPOINT.dhe_time_ENDPOINT import get_symmetric_key, get_base_time
from UTILS.keymap import seed_to_keymap, apply_keymap, decrypt_text

INTERVAL = 10

def main():
    sym_key = get_symmetric_key()
    base_time = get_base_time()
    
    # Generate seed
    seed = generate_seed(sym_key, base_time, INTERVAL)
    print(f"Seed: {seed.hex()}")
    
    # Create keymap
    keymap = seed_to_keymap(seed)
    print(f"\nKeymap sample:")
    for key in ['h', 'e', 'l', 'o']:
        print(f"  '{key}' -> '{keymap[key]}'")
    
    # Test encryption/decryption
    original = "hello world 123"
    scrambled = apply_keymap(original, keymap)
    decrypted = decrypt_text(scrambled, keymap)
    
    print(f"\nOriginal:  {original}")
    print(f"Scrambled: {scrambled}")
    print(f"Decrypted: {decrypted}")

if __name__ == "__main__":
    main()
