"""Minimal battery monitor for the Lenovo Legion M6X Pro mouse."""
import ctypes
import os
import traceback
import threading
from ctypes import wintypes

import pystray
from pystray import MenuItem as item

from config import (
    load_config, save_config, is_auto_start_enabled, is_auto_start_blocked,
    set_auto_start,
)
from icon_generator import create_battery_icon
from battery_reader import BatteryReader


class M6XBatteryApp:
    def __init__(self):
        self.config = load_config()
        self.running = True
        self.stop_event = threading.Event()
        # Build the tray icon before making any HID calls. Some Windows HID
        # drivers can block during enumeration/open, which otherwise leaves a
        # visible process with no tray icon.
        self.last_status = {"connected": False, "battery": 0, "charging": False, "mode": "未连接"}
        self.notified_low_battery = False
        self.reader = BatteryReader()

        self.icon = pystray.Icon(
            name="M6XProBattery",
            icon=self._get_current_icon(),
            title=self._get_tooltip_text(),
            menu=self._build_menu(),
        )

    def _get_current_icon(self):
        if not self.last_status or not self.last_status["connected"]:
            return create_battery_icon(0, offline=True)
        return create_battery_icon(self.last_status["battery"])

    def _get_tooltip_text(self):
        if not self.last_status or not self.last_status["connected"]:
            return "M6X PRO 电量：未连接"
        state = "正在充电" if self.last_status["charging"] else "正在使用"
        return f"M6X PRO 电量：{self.last_status['battery']}%（{state}）"

    def _build_menu(self):
        def status_label(menu_item):
            if not self.last_status or not self.last_status["connected"]:
                return "电量：未连接"
            state = " · 正在充电" if self.last_status["charging"] else ""
            return f"电量：{self.last_status['battery']}%{state}"

        def toggle_notify(icon, menu_item):
            self.config["low_battery_notify"] = not self.config.get("low_battery_notify", True)
            save_config(self.config)
            self.icon.update_menu()

        def notify_checked(menu_item):
            return self.config.get("low_battery_notify", True)

        def toggle_autostart(icon, menu_item):
            blocked = is_auto_start_blocked()
            # A blocked entry counts as off: clicking re-enables and clears
            # the Windows startup switch in one step.
            enabled = blocked or not is_auto_start_enabled()
            if set_auto_start(enabled):
                self.config["auto_start"] = enabled
                save_config(self.config)
                if enabled and blocked:
                    message = "已重新启用开机自启动"
                elif enabled:
                    message = "已开启开机自启动"
                else:
                    message = "已关闭开机自启动"
                title = "启动设置已更新"
            else:
                message = "Windows 未确认启动项设置，请稍后重试。"
                title = "开机自启动设置失败"
            try:
                self.icon.notify(message, title)
            except Exception:
                pass
            self.icon.update_menu()

        def autostart_label(menu_item):
            if is_auto_start_blocked():
                return "开机自启动（已被 Windows 禁用，点击修复）"
            return "开机自启动"

        def autostart_checked(menu_item):
            return is_auto_start_enabled()

        return pystray.Menu(
            item(status_label, None, enabled=False),
            pystray.Menu.SEPARATOR,
            item("立即刷新", self.on_refresh),
            item("低电量提醒（低于 20%）", toggle_notify, checked=notify_checked),
            item(autostart_label, toggle_autostart, checked=autostart_checked),
            pystray.Menu.SEPARATOR,
            item("退出", self.on_exit),
        )

    def update_ui(self):
        if not self.running:
            return
        try:
            self.icon.icon = self._get_current_icon()
            self.icon.title = self._get_tooltip_text()
            self.icon.menu = self._build_menu()
            self.icon.update_menu()
        except Exception:
            pass

    def on_refresh(self, icon=None, menu_item=None):
        self.last_status = self.reader.read_status()
        self._check_low_battery(self.last_status)
        self.update_ui()

    def on_exit(self, icon=None, menu_item=None):
        self.running = False
        self.stop_event.set()
        self.icon.stop()

    def worker_loop(self):
        # Repair a missing Run entry in the background so registry access can
        # never prevent the tray UI from appearing.
        if self.config.get("auto_start") and not is_auto_start_enabled():
            set_auto_start(True)
        elif is_auto_start_blocked():
            # Never silently re-enable: the user may have turned the switch
            # off on purpose, so surface it instead.
            try:
                self.icon.notify(
                    "开机自启动已被 Windows 禁用，点击托盘菜单中的"
                    "“开机自启动”可重新启用。",
                    "自启动已被系统关闭",
                )
            except Exception:
                pass
        while self.running:
            try:
                status = self.reader.read_status()
                self.last_status = status
                self._check_low_battery(status)
                self.update_ui()
            except Exception:
                pass

            # One minute keeps the displayed value and low-battery alert current
            # while avoiding constant HID polling.
            self.stop_event.wait(60)

    def _check_low_battery(self, status):
        if not status["connected"] or status["charging"] or status["battery"] > 20:
            self.notified_low_battery = False
            return
        if self.config.get("low_battery_notify", True) and not self.notified_low_battery:
            try:
                self.icon.notify(
                    f"鼠标电量仅剩 {status['battery']}%，请及时充电。",
                    "M6X PRO 低电量提醒",
                )
            except Exception:
                pass
            self.notified_low_battery = True

    def run(self):
        threading.Thread(target=self.worker_loop, daemon=True).start()
        self.icon.run()


if __name__ == "__main__":
    try:
        ctypes.set_last_error(0)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        create_mutex = kernel32.CreateMutexW
        create_mutex.argtypes = (wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR)
        create_mutex.restype = wintypes.HANDLE
        mutex_handle = create_mutex(None, False, "Local\\M6XProBatteryMonitor.SingleInstance")
        if not mutex_handle:
            raise ctypes.WinError(ctypes.get_last_error())
        if ctypes.get_last_error() == 183:  # ERROR_ALREADY_EXISTS
            kernel32.CloseHandle(mutex_handle)
        else:
            # Keep the mutex handle alive for the entire lifetime of the app.
            M6XBatteryApp().run()
    except Exception:
        # A --noconsole build has no stderr. Preserve startup failures so a
        # stranded process can be diagnosed without a visible console.
        try:
            folder = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "M6X_Battery_Monitor")
            os.makedirs(folder, exist_ok=True)
            with open(os.path.join(folder, "startup.log"), "a", encoding="utf-8") as log:
                log.write(traceback.format_exc() + "\n")
        except Exception:
            pass
