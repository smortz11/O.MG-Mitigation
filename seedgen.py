import time
import hmac
import struct
from hashlib import sha256

def generate_seed(symmetric_key: bytes, base_time: int, interval_seconds: int, time_offset: float = 0.0) -> bytes:
	"""gen a seed every interval seconds"""

	now = time.time()
	counter = int((now - (base_time + time_offset)) / interval_seconds)
	counter_bytes = struct.pack(">Q", counter)
	seed = hmac.new(symmetric_key, counter_bytes, sha256).digest()

	return seed
