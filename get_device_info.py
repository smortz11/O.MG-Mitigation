import subprocess
import os

def get_key_mapping():
    # Invokes OS command to return keyboard layout and variant if they are found, None otherwise.
    out = subprocess.check_output(["localectl", "status"], text=True)
    layout = None
    variant = None
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("X11 Layout:"):
            layout = line.split(":")[1].strip()
        if line.startswith("X11 Variant"):
            variant = line.split(":")[1].strip()
    
    return layout, variant

def get_keyboard():
    # Invokes OS command to find name of keyboard device. Returns device name if exists, None otherwise.
    try:
        k_out = subprocess.check_output(["ls", "-l", "/dev/input/by-id"], text=True)
        for line in k_out.splitlines():
            if "kbd" in line:
                parts = line.split()
                device_name = parts[-3]
                return device_name
        return None
    
    except subprocess.CalledProcessError as e:
        print(f"Error listing input devices: {e}")
        return None
