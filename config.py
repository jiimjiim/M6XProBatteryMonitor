"""
Configuration and Windows Startup Management
"""
import os
import sys
import json
import winreg

APP_NAME = "M6XProBatteryMonitor"

def get_config_path() -> str:
    app_data = os.environ.get("APPDATA")
    if not app_data:
        app_data = os.path.expanduser("~")
    dir_path = os.path.join(app_data, "M6X_Battery_Monitor")
    try:
        os.makedirs(dir_path, exist_ok=True)
    except Exception:
        pass
    return os.path.join(dir_path, "config.json")

CONFIG_FILE = get_config_path()

DEFAULT_CONFIG = {
    "low_battery_notify": True,
    "auto_start": False,
}

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
# Windows keeps a per-entry on/off switch here; the Run value surviving with
# this switch set to disabled means the entry exists but never launches.
STARTUP_APPROVED_KEY = (
    r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"
)

def load_config() -> dict:
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for key in DEFAULT_CONFIG:
                    if key in data:
                        config[key] = data[key]
        except Exception:
            pass

    return config

def save_config(config: dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving config: {e}")

def is_auto_start_enabled() -> bool:
    expected = get_auto_start_command()
    if not expected:
        return False
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, RUN_KEY, 0,
            winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
        ) as key:
            val, _ = winreg.QueryValueEx(key, APP_NAME)
        return _normalize_command(val) == _normalize_command(expected)
    except Exception:
        return False


def _startup_approved_disabled() -> bool:
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, STARTUP_APPROVED_KEY, 0,
            winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
        ) as key:
            val, _ = winreg.QueryValueEx(key, APP_NAME)
    except Exception:
        return False
    # First byte odd (0x03...) = disabled, even (0x02...) = enabled.
    return isinstance(val, bytes) and len(val) >= 4 and bool(val[0] & 1)


def is_auto_start_blocked() -> bool:
    """Run entry exists but the Windows startup switch turned it off."""
    return is_auto_start_enabled() and _startup_approved_disabled()


def get_auto_start_command() -> str:
    if getattr(sys, "frozen", False):
        executable = os.path.abspath(sys.executable)
        if not os.path.isfile(executable):
            return ""
        return f'"{executable}"'

    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "main.py"))
    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if not os.path.exists(pythonw):
        pythonw = sys.executable
    return f'"{os.path.abspath(pythonw)}" "{script_path}"'


def _normalize_command(command: str) -> str:
    return os.path.normcase(os.path.normpath(command.strip()))


def set_auto_start(enable: bool) -> bool:
    try:
        with winreg.CreateKeyEx(
            winreg.HKEY_CURRENT_USER,
            RUN_KEY,
            0,
            winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY,
        ) as key:
            if enable:
                command = get_auto_start_command()
                if not command:
                    return False
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                except FileNotFoundError:
                    pass
            winreg.FlushKey(key)

        # Clear the per-app switch so an entry disabled from Task Manager or
        # Settings becomes effective again (an absent value means enabled).
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, STARTUP_APPROVED_KEY, 0,
                winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY,
            ) as approved_key:
                winreg.DeleteValue(approved_key, APP_NAME)
        except FileNotFoundError:
            pass

        return is_auto_start_enabled() == enable
    except Exception:
        return False
