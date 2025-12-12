import time
import hmac
import struct
from hashlib import sha256

def generate_seed(symmetric_key: bytes, base_time: int, interval_seconds: int) -> bytes:
	now = int(time.time())
	print(now, base_time)
	counter = (now - int(base_time)) // interval_seconds
	counter_bytes = struct.pack(">Q", counter)
	seed = hmac.new(symmetric_key, counter_bytes, sha256).digest()
	
	return seed
