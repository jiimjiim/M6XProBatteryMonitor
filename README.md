# M6X Pro Battery Monitor

A small Windows tray app for the Lenovo Legion M6X Pro mouse.

## Features

- Shows battery percentage as a large number in the tray. The number changes from green through orange to red as charge drops.
- Refreshes automatically every minute; choose **Refresh now** from the tray menu for an immediate update.
- Sends one Windows notification when battery reaches 20% or less while discharging. The reminder can be turned off in the tray menu.
- Optional launch at Windows sign-in. The app also detects when Windows has turned the startup switch off (Task Manager → Startup apps) and lets you re-enable it from the tray menu.
- Allows only one running instance.

The tray menu contains battery status, Refresh now, Low battery reminder, Start with Windows, and Exit.

## Build

Install Python, Pillow, hidapi, pystray, and PyInstaller, then run `build.bat`. The script regenerates the app icon, creates a single-file executable, and copies it to the Desktop. NumPy is excluded because the app does not use it.

```powershell
python -m pip install Pillow hidapi pystray pyinstaller
```

## HID device

The monitor reads the M6X Pro's 33-byte feature report `0x20` from Lenovo VID `0x17EF`, PIDs `0x61B7` (2.4 GHz) and `0x61B8` (USB). Battery percentage and charging state are read from bytes 18 and 19.
