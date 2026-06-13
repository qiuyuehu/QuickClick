# -*- coding: utf-8 -*-
"""
tray.py — QuickClick 系统托盘管理

功能：
- 系统托盘图标
- 右键菜单：显示窗口、退出
- 点击托盘图标显示窗口
"""

import threading
from PIL import Image
import pystray
from pystray import MenuItem, Icon


class TrayManager:
    """系统托盘图标管理"""

    def __init__(self, icon_path: str, on_show=None, on_exit=None):
        """
        参数:
            icon_path: 图标文件路径
            on_show: 显示窗口回调
            on_exit: 退出回调
        """
        self._icon_path = icon_path
        self._on_show = on_show
        self._on_exit = on_exit
        self._icon = None
        self._thread = None

    def _create_menu(self):
        """创建右键菜单"""
        return pystray.Menu(
            MenuItem("显示窗口", self._on_show, default=True),
            pystray.Menu.SEPARATOR,
            MenuItem("退出", self._on_exit),
        )

    def _run(self):
        """托盘图标运行（阻塞，在子线程中调用）"""
        image = Image.open(self._icon_path)
        self._icon = Icon("QuickClick", image, "QuickClick", menu=self._create_menu())
        self._icon.run()

    def start(self):
        """启动托盘图标（非阻塞）"""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """停止托盘图标"""
        if self._icon:
            self._icon.stop()
