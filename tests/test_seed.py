import time
from seedgen import generate_seed
from piA_send import get_symmetric_key, get_base_time

INTERVAL = 10
TIME_OFFSET = -.4

def main():
	sym_key = get_symmetric_key()
	base_time = get_base_time()

	print("Symmetric key:", sym_key.hex())
	print("Base time:", base_time)

	last_counter = None

	while True:
		now = time.time()
		counter = int((now - (base_time + TIME_OFFSET)) / INTERVAL)

		if counter != last_counter:
			last_counter = counter
			seed = generate_seed(sym_key, base_time, INTERVAL, TIME_OFFSET)

			print(f"Counter={counter} Seed={seed.hex()}")

		time.sleep(0.05)

if __name__ == "__main__":
	main()
