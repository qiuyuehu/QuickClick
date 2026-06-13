# -*- coding: utf-8 -*-
"""
main.py — QuickClick v2.0 入口

功能：
- 启动 GUI + 托盘图标
- 关闭窗口时最小化到托盘
- 托盘右键菜单：显示窗口、退出
"""

import sys
import os

# 确保从脚本所在目录加载
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from gui import App
from tray import TrayManager


def get_icon_path():
    """获取图标路径"""
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'icon.ico')
    else:
        path = os.path.join(os.path.dirname(__file__), 'icon.ico')
        return path if os.path.exists(path) else None


def main():
    # 检查依赖
    try:
        import pynput
    except ImportError:
        print("正在安装 pynput...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pynput"])

    try:
        import pystray
    except ImportError:
        print("正在安装 pystray...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pystray"])

    # 创建 GUI
    app = App()

    # 创建托盘管理器
    icon_path = get_icon_path()
    if icon_path:
        tray = TrayManager(
            icon_path=icon_path,
            on_show=lambda: app.root.after(0, app.show),
            on_exit=lambda: app.root.after(0, app.quit),
        )
        app.set_tray_manager(tray)
        tray.start()

    # 启动
    app.run()


if __name__ == "__main__":
    main()
