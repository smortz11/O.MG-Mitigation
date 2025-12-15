import time
import hmac
import struct
from hashlib import sha256

def generate_seed(symmetric_key: bytes, counter: int) -> bytes:
	counter_bytes = struct.pack(">Q", counter)
	seed = hmac.new(symmetric_key, counter_bytes, sha256).digest()
	print(f"[SEEDGEN] counter={counter} -> seed={seed.hex()[:16]}...")
	return seed
