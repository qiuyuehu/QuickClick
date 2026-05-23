# -*- coding: utf-8 -*-
"""
main.py — 连点器入口

用法: python -B main.py
"""

import sys
import os

# 确保从脚本所在目录加载
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from gui import App


def main():
    # 检查依赖
    try:
        import pynput
    except ImportError:
        print("正在安装 pynput...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pynput"])

    app = App()
    app.run()


if __name__ == "__main__":
    main()
