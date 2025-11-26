#!/bin/bash
# setup.sh - Setup script for O.MG Mitigation

set -e #exit on error

echo "=============================="
echo "O.MG Mitigation Setup Script"
echo "=============================="

echo "[1/5] Updating system..."
sudo apt update && sudo apt upgrade -y

echo "[2/5] Installing dependencies..."
sudo apt install -y python3-venv python3-pip git

echo "[3/5] Installing HIDPi..."
sudo apt install libusb-1.0-0-dev libudev-dev -y
if [ ! -f /usr/local/bin/HIDPi ] && [ ! -d /sys/kernel/config/usb_gadget/hid_gadget ]; then
	curl https://raw.githubusercontent.com/rikka-chunibyo/HIDPi/refs/heads/master/HIDPi_Setup.py -o HIDPi_Setup.py
	sudo python3 HIDPi_Setup.py
else
	echo "HIDPi already installed, skipping..."
fi

echo "[4/5] Creating Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

echo "[5/5] Configuring USB serial for DHE key exchange..."

sudo tee /usr/local/bin/add-usb-serial.sh > /dev/null <<'EOF'
#!/bin/bash
# Add USB serial function to existing HID gadget

GADGET_PATH="/sys/kernel/config/usb_gadget/hid_gadget"

if [ ! -d "$GADGET_PATH" ]; then
	echo "Error: HIDPi gadget not found at $GADGET_PATH"
	exit 1
fi

cd "$GADGET_PATH"

UDC=$(cat UDC)
echo "" > UDC

if [ ! -d "functions/acm.usb0" ]; then
	mkdir -p functions/acm.usb0
	ln -s functions/acm.usb0 configs/c.1/
fi

echo "$UDC" > UDC

sleep 1
if [ -e "/dev/ttyGS0" ]; then
	chmod 666 /dev/ttyGS0
	echo "USB serial configured: /dev/ttyGS0"
else
	echo "Warning: /dev/ttyGS0 not found"
fi
EOF

sudo chmod +x /usr/local/bin/add-usb-serial.sh

sudo tee /etc/systemd/system/usb-serial-setup.service > /dev/null <<'EOF'
[Unit]
Description=Add USB Serial Function to HID Gadget
After=HIDPi.service
Requires=HIDPi.service

[Service]
Type=oneshot
ExecStartPre=/bin/sleep 5
ExecStart=/usr/local/bin/add-usb-serial.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable usb-serial-setup.service
sudo systemctl start usb-serial-setup.service

echo "Setting up rc.local for boot persistence..."

if [ ! -f /etc/rc.local ]; then
	sudo tee /etc/rc.local > /dev/null <<'RCLOCAL'
#!/bin/bash
# Wait for system to be ready
sleep 5
# Add USB serial function
/usr/local/bin/add-usb-serial.sh
exit 0
RCLOCAL
else
	if ! grep -q "add-usb-serial.sh" /etc/rc.local; then
	sudo set -i '/^exit 0/d' /etc/rc.local
	sudo tee -a /etc/rc.local > /dev/null <<'RCLOCAL'
sleep 5
/usr/local/bin/add-usb-serial.sh
exit 0
RCLOCAL
	fi
fi

sudo chmod +x /etc/rc.local

sudo systemctl enable rc-local 2>/dev/null || true

echo "Adding cron job for boot persistence..."
(sudo crontab -l 2>/dev/null | grep -v "add-usb-serial.sh"; echo "@reboot sleep 15 && /usr/local/bin/add-usb-serial.sh") | sudo crontab -

echo ""
echo "=============================="
echo "Setup Complete!"
echo "=============================="
echo ""
echo "Next steps:"
echo "1. Reboot the Pi: sudo reboot"
echo "2. After reboot, activate venv: source .venv/bin/activate"
echo "3. Run main.py: python3 main.py"
echo ""
echo "USB HID: Will appear as 'Rikka HIDPi' keyboard"
echo "USB Serial: /dev/ttyGS0 on Pi, /dev/ttyACM0 on host"
echo ""
