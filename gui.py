# -*- coding: utf-8 -*-
"""
gui.py — QuickClick 连点器 GUI + 热键管理（Win11 纯 tk 自绘版）
Author: qiuyuehu / 凛 (Emperor Agent)

热键：
  F8 — 开始/停止连点
  F7 — 开始/停止录制宏
  F6 — 回放宏
  F9 — 停止一切
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import os

from PIL import Image, ImageDraw, ImageTk

from pynput.keyboard import Listener as KeyboardListener, Key

from core import AutoClicker, MacroRecorder

# ── 热键映射 ──────────────────────────────────────────────
HOTKEY_TOGGLE_CLICK = Key.f8
HOTKEY_TOGGLE_RECORD = Key.f7
HOTKEY_REPLAY = Key.f6
HOTKEY_STOP_ALL = Key.f9

# ── Win11 配色方案 ────────────────────────────────────────
BG = "#f3f3f3"              # 窗口背景
CARD_BG = "#ffffff"          # 卡片背景
CARD_BORDER = "#e0e0e0"      # 卡片边框
CARD_SHADOW = "#d8d8d8"      # 卡片阴影（底部 1px 模拟）

TEXT_TITLE = "#1a1a1a"       # 标题
TEXT_BODY = "#2d2d2d"        # 正文
TEXT_HINT = "#8a8a8a"        # 提示文字

ACCENT = "#0078d4"           # Win11 蓝
ACCENT_DARK = "#106ebe"      # Win11 蓝（按下）
RED = "#e81123"              # 录制红
RED_DARK = "#c50f1f"         # 录制红（按下）
GRAY = "#6b7280"             # 停止灰
GRAY_DARK = "#4b5563"        # 停止灰（按下）

RADIO_FILL = "#0078d4"       # 单选框选中填充
CHECK_FILL = "#0078d4"       # 复选框选中填充
BORDER_IDLE = "#8a8a8a"      # 控件边框未选中
BORDER_FOCUS = "#0078d4"     # 控件边框选中

FONT_TITLE = ("Microsoft YaHei UI", 18, "bold")
FONT_SECTION = ("Microsoft YaHei UI", 12, "bold")
FONT_BODY = ("Microsoft YaHei UI", 10)
FONT_SMALL = ("Microsoft YaHei UI", 8)
FONT_BTN = ("Microsoft YaHei UI", 11, "bold")
FONT_CHIP = ("Microsoft YaHei UI", 9)


# ── Canvas 自绘控件 ───────────────────────────────────────

class RoundRectButton(tk.Canvas):
    """圆角矩形按钮（Pillow 抗锯齿绘制）"""

    def __init__(self, parent, text, bg_color, fg_color="white",
                 width=120, height=36, radius=8, command=None, **kwargs):
        super().__init__(parent, width=width, height=height,
                         bg=parent["bg"], highlightthickness=0, **kwargs)
        self.command = command
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.text = text
        self.radius = radius
        self._photo = None  # 保持引用防止 GC
        self._draw()
        self.bind("<ButtonRelease-1>", self._on_click)

    def _draw(self):
        self.delete("all")
        w, h = int(self["width"]), int(self["height"])
        r = self.radius

        # 用 Pillow 绘制抗锯齿圆角矩形（4x 超采样）
        scale = 4
        img = Image.new("RGBA", (w * scale, h * scale), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle(
            [0, 0, w * scale - 1, h * scale - 1],
            radius=r * scale,
            fill=self.bg_color
        )
        # 缩小回原尺寸（抗锯齿）
        img = img.resize((w, h), Image.Resampling.LANCZOS)
        self._photo = ImageTk.PhotoImage(img)

        # 显示图片
        self.create_image(0, 0, anchor="nw", image=self._photo)

        # 文字（居中）
        self.create_text(w // 2, h // 2, text=self.text,
                         fill=self.fg_color, font=FONT_BTN)

    def _on_click(self, event):
        if self.command:
            self.command()

    def update_colors(self, bg_color, fg_color="white"):
        self.bg_color = bg_color
        self.fg_color = fg_color
        self._draw()


class RadioOption(tk.Canvas):
    """macOS 风格单选框（圆形 + 文字）"""

    def __init__(self, parent, text, variable, value, **kwargs):
        super().__init__(parent, width=20, height=20,
                         bg=parent["bg"], highlightthickness=0, **kwargs)
        self.variable = variable
        self.value = value
        self.text = text
        self._draw()
        self.bind("<Button-1>", self._on_click)
        variable.trace_add("write", lambda *_: self._draw())

    def _draw(self):
        self.delete("all")
        selected = self.variable.get() == self.value
        # 外圈（macOS 风格：细边框）
        self.create_oval(3, 3, 17, 17,
                         outline=RADIO_FILL if selected else "#c0c0c0",
                         width=1.5, fill=CARD_BG)
        # 内圈（选中时填充，更小更精致）
        if selected:
            self.create_oval(7, 7, 13, 13, fill=RADIO_FILL, outline=RADIO_FILL)

    def _on_click(self, event):
        self.variable.set(self.value)


class CheckOption(tk.Canvas):
    """macOS 风格复选框（圆角方形 + 文字）"""

    def __init__(self, parent, text, variable, **kwargs):
        super().__init__(parent, width=20, height=20,
                         bg=parent["bg"], highlightthickness=0, **kwargs)
        self.variable = variable
        self.text = text
        self._draw()
        self.bind("<Button-1>", self._on_click)
        variable.trace_add("write", lambda *_: self._draw())

    def _draw(self):
        self.delete("all")
        checked = self.variable.get()
        # 圆角方形（macOS 风格：更大圆角）
        self.create_polygon(
            5, 3, 15, 3, 17, 5, 17, 15, 15, 17, 5, 17, 3, 15, 3, 5,
            fill=CHECK_FILL if checked else CARD_BG,
            outline=CHECK_FILL if checked else "#c0c0c0",
            width=1.5, smooth=True
        )
        # 勾（更精致的线条）
        if checked:
            self.create_line([(7, 10), (9, 14), (14, 6)],
                             fill="white", width=1.8, capstyle="round")

    def _on_click(self, event):
        self.variable.set(not self.variable.get())


def radio_group(parent, label_text, options, variable):
    """创建一行单选框组：[标签] ○选项1 ○选项2 ..."""
    row = tk.Frame(parent, bg=CARD_BG)
    row.pack(fill="x", pady=(0, 10))
    tk.Label(row, text=label_text, font=FONT_BODY,
             fg=TEXT_BODY, bg=CARD_BG).pack(side="left")
    for text, value in options:
        item = tk.Frame(row, bg=CARD_BG)
        item.pack(side="left", padx=(8, 4))
        RadioOption(item, text, variable, value).pack(side="left")
        tk.Label(item, text=text, font=FONT_BODY,
                 fg=TEXT_BODY, bg=CARD_BG).pack(side="left", padx=(2, 0))
    return row


def check_box(parent, text, variable):
    """创建一行复选框：☑文字"""
    item = tk.Frame(parent, bg=CARD_BG)
    item.pack(side="left", padx=(8, 0))
    CheckOption(item, text, variable).pack(side="left")
    tk.Label(item, text=text, font=FONT_BODY,
             fg=TEXT_BODY, bg=CARD_BG).pack(side="left", padx=(2, 0))
    return item


# ── 卡片容器 ──────────────────────────────────────────────

class Card(tk.Frame):
    """Win11 风格白色卡片（无阴影）"""

    def __init__(self, parent, title="", **kwargs):
        super().__init__(parent, bg=CARD_BG, highlightbackground=CARD_BORDER,
                         highlightthickness=1, **kwargs)
        self.pack(fill="x", padx=20, pady=(0, 14))

        if title:
            tk.Label(self, text=title, font=FONT_SECTION,
                     fg=TEXT_TITLE, bg=CARD_BG).pack(anchor="w", padx=16, pady=(14, 10))


# ── 主应用 ────────────────────────────────────────────────

class App:
    """连点器主界面"""

    def __init__(self):
        self.clicker = AutoClicker()
        self.macro = MacroRecorder()
        self._hotkey_listener = None

        # ── 主窗口 ──
        self.root = tk.Tk()
        self.root.title("QuickClick")
        self.root.geometry("440x660")
        self.root.resizable(False, False)
        self.root.attributes('-topmost', True)
        self.root.configure(bg=BG)

        self._build_ui()
        self._start_hotkey_listener()
        self._update_status()

        # 关闭时清理
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── 界面构建 ──────────────────────────────────────────

    def _build_ui(self):
        root = self.root

        # ── 标题 ──
        tk.Label(root, text="连点器", font=FONT_TITLE,
                 fg=TEXT_TITLE, bg=BG).pack(anchor="w", padx=24, pady=(20, 14))

        # ── 连点设置卡片 ──
        card1 = Card(root, "连点设置")

        # 按键选择
        self.btn_var = tk.StringVar(value="left")
        radio_group(card1, "按键:", [("左键", "left"), ("中键", "middle"), ("右键", "right")],
                    self.btn_var)

        # 双击 + 按键行追加
        # （放在 radio_group 的 row 里会比较紧凑，单独一行）
        row_double = tk.Frame(card1, bg=CARD_BG)
        row_double.pack(fill="x", padx=16, pady=(0, 10))
        self.double_click_var = tk.BooleanVar(value=False)
        check_box(row_double, "双击", self.double_click_var)

        # 速度
        row = tk.Frame(card1, bg=CARD_BG)
        row.pack(fill="x", padx=16, pady=(0, 8))
        tk.Label(row, text="速度:", font=FONT_BODY,
                 fg=TEXT_BODY, bg=CARD_BG).pack(side="left")
        self.cps_var = tk.StringVar(value="10")
        tk.Entry(row, textvariable=self.cps_var, width=6, justify="center",
                 font=FONT_BODY, bg=CARD_BG, fg="#000000",
                 insertbackground="#000000", relief="solid", bd=1).pack(
            side="left", padx=(8, 2))
        tk.Label(row, text="次/秒", font=FONT_BODY,
                 fg=TEXT_BODY, bg=CARD_BG).pack(side="left")

        # 快捷按钮
        row = tk.Frame(card1, bg=CARD_BG)
        row.pack(fill="x", padx=16, pady=(0, 10))
        for val in ["5", "10", "20", "50"]:
            RoundRectButton(row, val, bg_color="#f0f0f0", fg_color=TEXT_BODY,
                            width=48, height=28, radius=6,
                            command=lambda v=val: self.cps_var.set(v)).pack(
                side="left", padx=2)

        # 坐标
        row = tk.Frame(card1, bg=CARD_BG)
        row.pack(fill="x", padx=16, pady=(0, 16))
        tk.Label(row, text="坐标:", font=FONT_BODY,
                 fg=TEXT_BODY, bg=CARD_BG).pack(side="left")
        self.anchor_x_var = tk.StringVar(value="")
        self.anchor_y_var = tk.StringVar(value="")
        for var in (self.anchor_x_var, self.anchor_y_var):
            tk.Entry(row, textvariable=var, width=6, justify="center",
                     font=FONT_BODY, bg=CARD_BG, fg="#000000",
                     insertbackground="#000000", relief="solid", bd=1).pack(
                side="left", padx=(8, 2))
        RoundRectButton(row, "拾取", bg_color="#f0f0f0", fg_color=TEXT_BODY,
                        width=48, height=28, radius=6,
                        command=self._pick_anchor).pack(side="left", padx=(8, 0))
        tk.Label(row, text="(空=跟随)", font=FONT_SMALL,
                 fg=TEXT_HINT, bg=CARD_BG).pack(side="left", padx=4)

        # ── 连点控制按钮 ──
        self.btn_click = RoundRectButton(
            root, "▶ 开始连点 (F8)", bg_color=ACCENT, fg_color="white",
            width=400, height=42, radius=8, command=self._toggle_click)
        self.btn_click.pack(padx=20, pady=(0, 14))

        # ── 宏卡片 ──
        card2 = Card(root, "鼠标宏")

        self.macro_status = tk.Label(card2, text="状态: 未录制",
                                     font=FONT_BODY, fg=TEXT_HINT, bg=CARD_BG)
        self.macro_status.pack(anchor="w", padx=16, pady=(0, 8))

        # 回放次数 + 间隔
        row = tk.Frame(card2, bg=CARD_BG)
        row.pack(fill="x", padx=16, pady=(0, 8))
        tk.Label(row, text="回放:", font=FONT_BODY,
                 fg=TEXT_BODY, bg=CARD_BG).pack(side="left")
        self.replay_count_var = tk.StringVar(value="1")
        tk.Entry(row, textvariable=self.replay_count_var, width=4, justify="center",
                 font=FONT_BODY, bg=CARD_BG, fg="#000000",
                 insertbackground="#000000", relief="solid", bd=1).pack(
            side="left", padx=(8, 2))
        tk.Label(row, text="次 (0=无限)", font=FONT_BODY,
                 fg=TEXT_BODY, bg=CARD_BG).pack(side="left")
        tk.Label(row, text="间隔:", font=FONT_BODY,
                 fg=TEXT_BODY, bg=CARD_BG).pack(side="left", padx=(12, 0))
        self.replay_interval_var = tk.StringVar(value="0")
        tk.Entry(row, textvariable=self.replay_interval_var, width=4, justify="center",
                 font=FONT_BODY, bg=CARD_BG, fg="#000000",
                 insertbackground="#000000", relief="solid", bd=1).pack(
            side="left", padx=(8, 2))
        tk.Label(row, text="秒", font=FONT_BODY,
                 fg=TEXT_BODY, bg=CARD_BG).pack(side="left")

        # 回放速度
        self.speed_var = tk.StringVar(value="1")
        row = tk.Frame(card2, bg=CARD_BG)
        row.pack(fill="x", padx=16, pady=(0, 10))
        tk.Label(row, text="速度:", font=FONT_BODY,
                 fg=TEXT_BODY, bg=CARD_BG).pack(side="left")
        for val in ["0.5", "1", "2", "4", "8"]:
            item = tk.Frame(row, bg=CARD_BG)
            item.pack(side="left", padx=2)
            RadioOption(item, val, self.speed_var, val).pack(side="left")
            tk.Label(item, text=f"{val}x", font=FONT_BODY,
                     fg=TEXT_BODY, bg=CARD_BG).pack(side="left", padx=(2, 0))

        # 录制 / 回放
        row = tk.Frame(card2, bg=CARD_BG)
        row.pack(fill="x", padx=16, pady=(0, 8))
        self.btn_record = RoundRectButton(
            row, "● 录制 (F7)", bg_color=RED, fg_color="white",
            width=180, height=36, radius=8, command=self._toggle_record)
        self.btn_record.pack(side="left", padx=(0, 8), fill="x", expand=True)
        self.btn_replay = RoundRectButton(
            row, "▶ 回放 (F6)", bg_color=ACCENT, fg_color="white",
            width=180, height=36, radius=8, command=self._replay_macro)
        self.btn_replay.pack(side="left", fill="x", expand=True)

        # 文件操作
        row = tk.Frame(card2, bg=CARD_BG)
        row.pack(fill="x", padx=16, pady=(0, 16))
        for txt, cmd in [("保存宏", self._save_macro), ("加载宏", self._load_macro),
                         ("清空", self._clear_macro)]:
            RoundRectButton(row, txt, bg_color="#f0f0f0", fg_color=TEXT_BODY,
                            width=100, height=28, radius=6,
                            command=cmd).pack(side="left", padx=(0, 8), fill="x",
                                              expand=True)

        # ── 状态栏 ──
        self.status_label = tk.Label(root, text="就绪 | F8连点 F7录制 F6回放 F9停止",
                                     font=FONT_SMALL, fg=TEXT_HINT, bg=BG)
        self.status_label.pack(fill="x", padx=24, pady=(0, 8))

        # ── 停止按钮 ──
        self.btn_stop = RoundRectButton(
            root, "■ 停止一切 (F9)", bg_color=GRAY, fg_color="white",
            width=400, height=40, radius=8, command=self._stop_all)
        self.btn_stop.pack(padx=20, pady=(0, 20))

    # ── 热键监听 ──────────────────────────────────────────

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

    # ── 操作逻辑 ──────────────────────────────────────────

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

    # ── 状态更新 ──────────────────────────────────────────

    def _update_status(self):
        """更新界面状态"""
        # 连点按钮
        if self.clicker.is_running:
            self.btn_click.update_colors(RED)
            self.btn_click.text = "■ 停止连点 (F8)"
            self.btn_click._draw()
        else:
            self.btn_click.update_colors(ACCENT)
            self.btn_click.text = "▶ 开始连点 (F8)"
            self.btn_click._draw()

        # 录制按钮
        if self.macro.is_recording:
            self.btn_record.update_colors(RED_DARK)
            self.btn_record.text = "■ 停止录制 (F7)"
            self.btn_record._draw()
        else:
            self.btn_record.update_colors(RED)
            self.btn_record.text = "● 录制 (F7)"
            self.btn_record._draw()

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
            self.macro_status.config(text=f"状态: 录制中... ({n} 事件)", fg=RED)
        elif self.macro.is_playing:
            count_str = "无限" if getattr(self, '_replay_count', 1) == 0 else str(getattr(self, '_replay_count', 1))
            self.macro_status.config(text=f"状态: 回放中... ({count_str}轮)", fg=ACCENT)
        elif n > 0:
            self.macro_status.config(text=f"状态: 已录制 {n} 个事件{detail}", fg="#2ecc71")
        else:
            self.macro_status.config(text="状态: 未录制", fg=TEXT_HINT)

    def _flash_status(self, msg: str):
        """临时显示状态信息"""
        self.status_label.config(text=msg)
        self.root.after(3000, lambda: self.status_label.config(
            text="就绪 | F8连点 F7录制 F6回放 F9停止"))

    # ── 生命周期 ──────────────────────────────────────────

    def _on_close(self):
        """关闭时清理"""
        self._stop_all()
        if self._hotkey_listener:
            self._hotkey_listener.stop()
        self.root.destroy()

    def run(self):
        self.root.mainloop()
