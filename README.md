# O.MG-Mitigation
In case of a Pi wipe:
1. Clone this repo
2. sudo apt update && sudo apt install libusb-1.0-0-dev libudev-dev -y && curl https://raw.githubusercontent.com/rikka-chunibyo/HIDPi/refs/heads/master/HIDPi_Setup.py -o HIDPi_Setup.py && sudo python3 HIDPi_Setup.py
3. Restart the pi
4. Create a venv and install the requirements in requirements.txt
5. Run with python3 main.py
