# M6X Pro 电量监测

一款面向联想拯救者 M6X Pro 鼠标的 Windows 托盘小工具。

## 功能

- 在托盘区以大号数字显示电量百分比，数字颜色随电量下降从绿色渐变为橙色再到红色。
- 每分钟自动刷新；可在托盘菜单中选择**立即刷新**手动更新。
- 放电状态下电量降到 20% 及以下时发送一次 Windows 通知提醒，可在托盘菜单中关闭。
- 可选开机自启动。当 Windows 侧（任务管理器 → 启动应用）关闭了自启动开关时，程序能检测到并允许你在托盘菜单中一键重新启用。
- 仅允许同时运行一个实例。

托盘菜单包含：电量状态、立即刷新、低电量提醒、开机自启动、退出。

## 构建

安装 Python、Pillow、hidapi、pystray 和 PyInstaller，然后运行 `build.bat`。脚本会重新生成应用图标、构建单文件可执行程序并复制到桌面。NumPy 被显式排除，因为应用并不使用它。

```powershell
python -m pip install Pillow hidapi pystray pyinstaller
```

## HID 设备

程序通过 HID 读取 M6X Pro 的 33 字节 feature report `0x20`（联想 VID `0x17EF`，PID `0x61B7` 为 2.4 GHz 接收器、`0x61B8` 为 USB 有线）。电量百分比和充电状态分别位于第 18、19 字节。
