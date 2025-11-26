# O.MG-Mitigation
---
## Installation
1. Clone the repository
```
git clone https://github.com/smortz11/O.MG-Mitigation.git
```
2. Navigate to the installed directory
```
cd O.MG-Mitigation
```
3. Run the setup script
```
sudo ./setup.sh
```
4. After the script runs, reboot the device
```
sudo reboot
```
5. Begin sending keystrokes with
```
python3 main.py
```
6. Test sending data to the host
On the host:
```
cat /dev/ttyACM0
```
On the Pi:
```
echo "This is a test!" > /dev/ttyGS0
```
7. Test sending data to the Pi
On the Pi:
```
cat /dev/ttyGS0
```
On the host:
```
echo "This is a test!" > /dev/ttyACM0
```
