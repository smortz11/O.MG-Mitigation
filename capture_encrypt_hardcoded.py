from evdev import InputDevice, list_devices, ecodes, categorize

dev = InputDevice('/dev/input/by-id/usb-Macally_Peripherals_Macally_QKEY_USB_Keyboard-event-kbd') # This can eventually be automated and not hardcoded

print(f"Listening on {dev.path} ({dev.name}) ... Press Ctrl+C to quit.")

for event in dev.read_loop():
    if event.type == ecodes.EV_KEY:
        key_event = categorize(event)
        if key_event.keystate == key_event.key_down:
                print(f"Key pressed: {key_event.keycode}")