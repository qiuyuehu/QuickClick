# -*- coding: utf-8 -*-
"""
gui.py — QuickClick 连点器 GUI + 热键管理
Author: qiuyuehu / 凛 (Emperor Agent)

热键：
  F8 — 开始/停止连点
  F7 — 开始/停止录制宏
  F6 — 回放宏
  F9 — 停止一切
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os

from pynput.keyboard import Listener as KeyboardListener, Key

from core import AutoClicker, MacroRecorder

# 热键映射
HOTKEY_TOGGLE_CLICK = Key.f8
HOTKEY_TOGGLE_RECORD = Key.f7
HOTKEY_REPLAY = Key.f6
HOTKEY_STOP_ALL = Key.f9


class App:
    """连点器主界面"""

    def __init__(self):
        self.clicker = AutoClicker()
        self.macro = MacroRecorder()
        self._hotkey_listener = None

        # ── 主窗口 ──
        self.root = tk.Tk()
        self.root.title("QuickClick")
        self.root.geometry("320x580")
        self.root.resizable(False, False)
        self.root.attributes('-topmost', True)

        self._build_ui()
        self._start_hotkey_listener()
        self._update_status()

        # 关闭时清理
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── 界面构建 ──

    def _build_ui(self):
        root = self.root
        pad = {"padx": 12, "pady": 4}

        # 标题
        tk.Label(root, text="连点器", font=("Microsoft YaHei UI", 16, "bold")).pack(anchor='w', **pad)

        # ── 连点设置 ──
        frame_click = tk.LabelFrame(root, text="连点设置", font=("Microsoft YaHei UI", 10))
        frame_click.pack(fill='x', padx=12, pady=(8, 4))

        # 鼠标按键
        row1 = tk.Frame(frame_click)
        row1.pack(fill='x', padx=8, pady=4)
        tk.Label(row1, text="按键:").pack(side='left')
        self.btn_var = tk.StringVar(value="left")
        tk.Radiobutton(row1, text="左键", variable=self.btn_var, value="left").pack(side='left', padx=(8, 4))
        tk.Radiobutton(row1, text="中键", variable=self.btn_var, value="middle").pack(side='left', padx=4)
        tk.Radiobutton(row1, text="右键", variable=self.btn_var, value="right").pack(side='left', padx=4)
        self.double_click_var = tk.BooleanVar(value=False)
        tk.Checkbutton(row1, text="双击", variable=self.double_click_var).pack(side='left', padx=8)

        # 速度
        row2 = tk.Frame(frame_click)
        row2.pack(fill='x', padx=8, pady=4)
        tk.Label(row2, text="速度:").pack(side='left')
        self.cps_var = tk.StringVar(value="10")
        self.cps_entry = tk.Entry(row2, textvariable=self.cps_var, width=6, justify='center')
        self.cps_entry.pack(side='left', padx=(8, 2))
        tk.Label(row2, text="次/秒").pack(side='left')

        # 速度快捷按钮
        row2b = tk.Frame(frame_click)
        row2b.pack(fill='x', padx=8, pady=(0, 4))
        for cps_val in ["5", "10", "20", "50"]:
            tk.Button(row2b, text=cps_val, width=4,
                      command=lambda v=cps_val: self.cps_var.set(v)).pack(side='left', padx=2)

        # ── 锚定坐标 ──
        row_anchor = tk.Frame(frame_click)
        row_anchor.pack(fill='x', padx=8, pady=4)
        tk.Label(row_anchor, text="坐标:").pack(side='left')
        self.anchor_x_var = tk.StringVar(value="")
        self.anchor_y_var = tk.StringVar(value="")
        tk.Entry(row_anchor, textvariable=self.anchor_x_var, width=6, justify='center').pack(side='left', padx=(8, 2))
        tk.Label(row_anchor, text="X").pack(side='left')
        tk.Entry(row_anchor, textvariable=self.anchor_y_var, width=6, justify='center').pack(side='left', padx=(8, 2))
        tk.Label(row_anchor, text="Y").pack(side='left')
        tk.Button(row_anchor, text="拾取", width=4,
                  command=self._pick_anchor).pack(side='left', padx=(8, 0))
        tk.Label(row_anchor, text="(空=跟随)", font=("Microsoft YaHei UI", 8), fg="#888").pack(side='left', padx=4)

        # ── 连点控制 ──
        self.btn_click = tk.Button(
            root, text="▶ 开始连点 (F8)", font=("Microsoft YaHei UI", 11),
            bg="#4CAF50", fg="white", relief='flat', height=2,
            command=self._toggle_click,
        )
        self.btn_click.pack(fill='x', padx=12, pady=4)

        # ── 宏 ──
        frame_macro = tk.LabelFrame(root, text="鼠标宏", font=("Microsoft YaHei UI", 10))
        frame_macro.pack(fill='x', padx=12, pady=(8, 4))

        self.macro_status = tk.Label(frame_macro, text="状态: 未录制", font=("Microsoft YaHei UI", 9))
        self.macro_status.pack(anchor='w', padx=8, pady=2)

        # 回放次数 + 间隔
        row_m1 = tk.Frame(frame_macro)
        row_m1.pack(fill='x', padx=8, pady=2)
        tk.Label(row_m1, text="回放:").pack(side='left')
        self.replay_count_var = tk.StringVar(value="1")
        tk.Entry(row_m1, textvariable=self.replay_count_var, width=4, justify='center').pack(side='left', padx=(8, 2))
        tk.Label(row_m1, text="次 (0=无限)").pack(side='left')
        tk.Label(row_m1, text="间隔:").pack(side='left', padx=(12, 0))
        self.replay_interval_var = tk.StringVar(value="0")
        tk.Entry(row_m1, textvariable=self.replay_interval_var, width=4, justify='center').pack(side='left', padx=(8, 2))
        tk.Label(row_m1, text="秒").pack(side='left')

        # 回放速度
        row_speed = tk.Frame(frame_macro)
        row_speed.pack(fill='x', padx=8, pady=2)
        tk.Label(row_speed, text="速度:").pack(side='left')
        self.speed_var = tk.StringVar(value="1")
        for speed_val in ["0.5", "1", "2", "4", "8"]:
            tk.Radiobutton(row_speed, text=f"{speed_val}x", 
                          variable=self.speed_var, value=speed_val).pack(side='left', padx=2)

        row3 = tk.Frame(frame_macro)
        row3.pack(fill='x', padx=8, pady=4)

        self.btn_record = tk.Button(row3, text="● 录制 (F7)", width=12,
                                    bg="#f44336", fg="white", relief='flat',
                                    command=self._toggle_record)
        self.btn_record.pack(side='left', padx=2)

        self.btn_replay = tk.Button(row3, text="▶ 回放 (F6)", width=12,
                                    relief='flat', command=self._replay_macro)
        self.btn_replay.pack(side='left', padx=2)

        row4 = tk.Frame(frame_macro)
        row4.pack(fill='x', padx=8, pady=(0, 8))
        tk.Button(row4, text="保存宏", width=8, command=self._save_macro).pack(side='left', padx=2)
        tk.Button(row4, text="加载宏", width=8, command=self._load_macro).pack(side='left', padx=2)
        tk.Button(row4, text="清空", width=6, command=self._clear_macro).pack(side='left', padx=2)

        # ── 状态栏 ──
        self.status_label = tk.Label(
            root, text="就绪 | F8连点 F7录制 F6回放 F9停止",
            font=("Microsoft YaHei UI", 8), fg="#888", anchor='w',
        )
        self.status_label.pack(fill='x', padx=12, pady=(8, 4))

        # ── 停止按钮 ──
        self.btn_stop = tk.Button(
            root, text="■ 停止一切 (F9)", font=("Microsoft YaHei UI", 10),
            bg="#9e9e9e", fg="white", relief='flat',
            command=self._stop_all,
        )
        self.btn_stop.pack(fill='x', padx=12, pady=4)

    # ── 热键监听 ──

    def _start_hotkey_listener(self):
        """启动全局热键监听"""
        def _on_press(key):
            if key == HOTKEY_TOGGLE_CLICK:
                self.root.after(0, self._toggle_click)
            elif key == HOTKEY_TOGGLE_RECORD:
                self.root.after(0, self._toggle_record)
            elif key == HOTKEY_REPLAY:
                self.root.after(0, self._replay_macro)
            elif key == HOTKEY_STOP_ALL:
                self.root.after(0, self._stop_all)

        self._hotkey_listener = KeyboardListener(on_press=_on_press)
        self._hotkey_listener.daemon = True
        self._hotkey_listener.start()

    # ── 操作逻辑 ──

    def _apply_settings(self):
        """把界面设置应用到引擎"""
        # 速度
        try:
            cps = int(self.cps_var.get())
            self.clicker.cps = max(1, min(cps, 1000))
        except ValueError:
            self.clicker.cps = 10
            self.cps_var.set("10")

        # 按键
        from pynput.mouse import Button
        btn_map = {"left": Button.left, "right": Button.right, "middle": Button.middle}
        self.clicker.button = btn_map.get(self.btn_var.get(), Button.left)
        
        # 双击设置
        self.clicker.click_count = 2 if self.double_click_var.get() else 1

        # 锚定坐标
        try:
            x_str = self.anchor_x_var.get().strip()
            y_str = self.anchor_y_var.get().strip()
            if x_str and y_str:
                self.clicker.anchor_x = int(x_str)
                self.clicker.anchor_y = int(y_str)
            else:
                self.clicker.anchor_x = None
                self.clicker.anchor_y = None
        except ValueError:
            self.clicker.anchor_x = None
            self.clicker.anchor_y = None
            self.anchor_x_var.set("")
            self.anchor_y_var.set("")

    def _toggle_click(self):
        """切换连点"""
        self._apply_settings()
        self.clicker.toggle()
        self._update_status()

    def _pick_anchor(self):
        """3秒后拾取鼠标坐标作为锚点"""
        self._flash_status("3秒内点击鼠标左键拾取坐标...")
        from pynput.mouse import Listener as MouseListener, Button

        def _on_click(x, y, button, pressed):
            if pressed and button == Button.left:
                self.anchor_x_var.set(str(x))
                self.anchor_y_var.set(str(y))
                self.root.after(0, lambda: self._flash_status(f"已拾取: ({x}, {y})"))
                return False  # 停止监听

        def _start_pick():
            listener = MouseListener(on_click=_on_click)
            listener.start()
            # 5秒超时自动停止
            def _timeout():
                if listener.running:
                    listener.stop()
                    self.root.after(0, lambda: self._flash_status("拾取超时"))
            self.root.after(5000, _timeout)

        self.root.after(100, _start_pick)

    def _toggle_record(self):
        """切换录制"""
        if self.macro.is_recording:
            count = self.macro.stop_recording()
            self._update_status()
            self._flash_status(f"录制完成: {count} 个事件")
        else:
            self.macro.start_recording()
            self._update_status()

    def _replay_macro(self):
        """回放宏"""
        if self.macro.is_playing:
            return
        if not self.macro.events:
            self._flash_status("没有可回放的宏")
            return

        # 读取并校验回放参数
        try:
            count = int(self.replay_count_var.get())
            if count < 0:
                raise ValueError
        except ValueError:
            count = 1
            self.replay_count_var.set("1")
        try:
            interval = float(self.replay_interval_var.get())
            if interval < 0:
                raise ValueError
        except ValueError:
            interval = 0.0
            self.replay_interval_var.set("0")
        
        # 读取速度倍率
        try:
            speed = float(self.speed_var.get())
            if speed <= 0:
                raise ValueError
        except ValueError:
            speed = 1.0
            self.speed_var.set("1")

        def _on_done():
            self.root.after(0, self._update_status)
            self.root.after(0, lambda: self._flash_status("回放完成"))
        
        def _on_progress(current, remaining):
            if remaining == -1:
                text = f"回放中... 第{current}轮 (无限)"
            else:
                text = f"回放中... 第{current}轮 (剩余{remaining}次)"
            self.root.after(0, lambda: self.macro_status.config(text=text))

        self._replay_count = count
        self.macro.replay(count=count, interval=interval, speed=speed,
                         callback=_on_done, progress_callback=_on_progress)
        self._update_status()

    def _stop_all(self):
        """停止一切"""
        self.clicker.stop()
        self.macro.stop_recording()
        self.macro.stop_replay()
        self._update_status()
        self._flash_status("已停止")

    def _save_macro(self):
        """保存宏到文件"""
        if not self.macro.events:
            self._flash_status("没有可保存的宏")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON 文件", "*.json")],
            title="保存鼠标宏",
        )
        if path:
            self.macro.save(path)
            self._flash_status(f"已保存: {os.path.basename(path)}")

    def _load_macro(self):
        """加载宏文件"""
        path = filedialog.askopenfilename(
            filetypes=[("JSON 文件", "*.json")],
            title="加载鼠标宏",
        )
        if path:
            try:
                count = self.macro.load(path)
                self._update_status()
                self._flash_status(f"已加载: {count} 个事件")
            except Exception as e:
                messagebox.showerror("错误", f"加载失败: {e}")

    def _clear_macro(self):
        """清空宏"""
        self.macro.clear()
        self._update_status()

    # ── 状态更新 ──

    def _update_status(self):
        """更新界面状态"""
        # 连点按钮
        if self.clicker.is_running:
            self.btn_click.config(text="■ 停止连点 (F8)", bg="#f44336")
        else:
            self.btn_click.config(text="▶ 开始连点 (F8)", bg="#4CAF50")

        # 录制按钮
        if self.macro.is_recording:
            self.btn_record.config(text="■ 停止录制 (F7)", bg="#ff9800")
        else:
            self.btn_record.config(text="● 录制 (F7)", bg="#f44336")

        # 宏状态
        n = self.macro.event_count
        n_mouse = self.macro.mouse_event_count
        n_move = self.macro.move_event_count
        n_key = self.macro.key_event_count
        detail_parts = []
        if n_mouse > 0:
            detail_parts.append(f"{n_mouse}鼠标")
        if n_move > 0:
            detail_parts.append(f"{n_move}移动")
        if n_key > 0:
            detail_parts.append(f"{n_key}键盘")
        detail = f" ({' '.join(detail_parts)})" if n > 0 and detail_parts else ""
        if self.macro.is_recording:
            self.macro_status.config(text=f"状态: 录制中... ({n} 事件)", fg="#f44336")
        elif self.macro.is_playing:
            count_str = "无限" if getattr(self, '_replay_count', 1) == 0 else str(getattr(self, '_replay_count', 1))
            self.macro_status.config(text=f"状态: 回放中... ({count_str}轮)", fg="#2196F3")
        elif n > 0:
            self.macro_status.config(text=f"状态: 已录制 {n} 个事件{detail}", fg="#4CAF50")
        else:
            self.macro_status.config(text="状态: 未录制", fg="#888")

    def _flash_status(self, msg: str):
        """临时显示状态信息"""
        self.status_label.config(text=msg)
        self.root.after(3000, lambda: self.status_label.config(
            text="就绪 | F8连点 F7录制 F6回放 F9停止"))

    # ── 生命周期 ──

    def _on_close(self):
        """关闭时清理"""
        self._stop_all()
        if self._hotkey_listener:
            self._hotkey_listener.stop()
        self.root.destroy()

    def run(self):
        self.root.mainloop()
