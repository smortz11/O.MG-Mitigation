import serial
import subprocess
import time
from cryptography.hazmat.primitives.asymmetric.x25519 import (
	X25519PrivateKey, X25519PublicKey
)
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization

SERIAL_PORT = "/dev/ttyGS0"
BAUD = 115200

_cached_symmetric_key = None
_cached_base_time = None

def send_frame(ser, data: bytes):
	"""Frame = <len:4 bytes><data>"""
	ser.write(len(data).to_bytes(4, "big") + data)

def recv_frame(ser):
	"""Read 4-byte length, then payload"""
	length_bytes = ser.read(4)
	if len(length_bytes) < 4:
		raise IOError("Serial broke")
	length = int.from_bytes(length_bytes, "big")
	return ser.read(length)

def main():
	print("[PI A] OPENING SERIAL...")
	ser = serial.Serial(SERIAL_PORT, BAUD, timeout=2)
	time.sleep(1)

	# gen priv/pubs
	private_key = X25519PrivateKey.generate()
	public_key = private_key.public_key()
	public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )

	print("[PI A] SENDING PUBLIC KEY...")
	send_frame(ser, public_bytes)

	print("[PI A] WAITING FOR ENDPOINT PUBLIC KEY...")
	peer_public_bytes = recv_frame(ser)

	peer_public_key = X25519PublicKey.from_public_bytes(peer_public_bytes)

	# compute shared secret
	shared_secret = private_key.exchange(peer_public_key)

	# derive symmetric
	kdf = HKDF(
		algorithm=hashes.SHA256(),
		length=32,
		salt=None,
		info=b"serial-handshake",
	)
	symmetric_key = kdf.derive(shared_secret)

	print("[PI A] SYMMETRIC KEY DERIVED:")
	print(symmetric_key.hex())

	# time sync
	base_time = int(recv_frame(ser).decode())
	print("[PI A] RECEIVED TIME:", base_time)

	subprocess.run(["date", "-s", f"@{base_time}"])
	print("[PI A] SYSTEM TIME SET")

	return symmetric_key, base_time

# GETTERS FOR TESTING

def get_symmetric_key():
	global _cached_symmetric_key, _cached_base_time
	if _cached_symmetric_key is None:
		_cached_symmetric_key, _cached_base_time = main()
	return _cached_symmetric_key

def get_base_time():
	global _cached_symmetric_key, _cached_base_time
	if _cached_base_time is None:
		_cached_symmetric_key, _cached_base_time = main()
	return _cached_base_time

if __name__ == "__main__":
	main()
