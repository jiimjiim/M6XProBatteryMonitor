"""Minimal HID reader for M6X Pro battery status."""
import threading
import time
from typing import Any, Dict

import hid


LENOVO_VID = 0x17EF
SUPPORTED_PIDS = {
    0x61B7: "2.4G 无线",
    0x61B8: "USB 有线",
}


class BatteryReader:
    def __init__(self):
        self._lock = threading.Lock()

    def read_status(self) -> Dict[str, Any]:
        with self._lock:
            for pid, mode in SUPPORTED_PIDS.items():
                try:
                    devices = hid.enumerate(LENOVO_VID, pid)
                except Exception:
                    continue
                for info in devices:
                    if info.get("usage_page") != 0xFF00 or info.get("usage") != 0x01:
                        continue
                    dev = hid.device()
                    try:
                        dev.open_path(info["path"])
                        request = [0x0C, 0x01, 0x20] + [0x00] * 30
                        dev.send_feature_report(request)
                        time.sleep(0.04)
                        response = dev.get_feature_report(0x0C, 33)
                        if response and len(response) >= 20 and response[2] == 0x20:
                            return {
                                "connected": True,
                                "battery": max(0, min(100, int(response[18]))),
                                "charging": response[19] == 1,
                                "mode": mode,
                            }
                    except Exception:
                        pass
                    finally:
                        try:
                            dev.close()
                        except Exception:
                            pass

            return {
                "connected": False,
                "battery": 0,
                "charging": False,
                "mode": "未连接",
            }
