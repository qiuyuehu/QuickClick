# -*- coding: utf-8 -*-
"""
gui.py — QuickClick v2.0 连点器 GUI
Author: 秋月 / 衾衾 (Hermes Agent)

严格对照 MAPPING.md 实现，不改进任何值。
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import os
import sys

from PIL import Image, ImageDraw, ImageTk
from pynput.keyboard import Listener as KeyboardListener, Key

from core import AutoClicker, MacroRecorder
from config import Config

# ── 热键 ──────────────────────────────────────────────────
HOTKEY_TOGGLE_CLICK = Key.f8
HOTKEY_TOGGLE_RECORD = Key.f7
HOTKEY_REPLAY = Key.f6
HOTKEY_STOP_ALL = Key.f9

# ── 配色（严格按 demo）────────────────────────────────────
BG = "#121212"
CARD_BG = "#1a1a1a"
TEXT_BODY = "#e0e0e0"
TEXT_HINT = "#888888"
LABEL_COLOR = "#999999"
SUFFIX_COLOR = "#666666"
SMALL_COLOR = "#555555"
FOOTER_COLOR = "#444444"
ACCENT = "#2563eb"
RED = "#dc2626"
RED_DARK = "#b91c1c"
GRAY = "#888888"
GHOST_BG = "#252525"
INPUT_BG = "#222222"

# ── 字体（Tkinter 比 HTML 小 2px）────────────────────────
FONT_SECTION = ("Microsoft YaHei UI", 10, "bold")   # demo 12px
FONT_BODY = ("Microsoft YaHei UI", 10)              # demo 12px
FONT_SMALL = ("Microsoft YaHei UI", 9)              # demo 11px
FONT_SUFFIX = ("Microsoft YaHei UI", 9)             # demo 11px
FONT_BTN = ("Microsoft YaHei UI", 10, "bold")       # demo 12px
FONT_BTN_LARGE = ("Microsoft YaHei UI", 11, "bold") # demo 13px
FONT_TITLE = ("Microsoft YaHei UI", 10, "bold")


# ══════════════════════════════════════════════════════════
# 自绘组件
# ══════════════════════════════════════════════════════════

class RoundRectCanvas(tk.Frame):
    """圆角矩形卡片容器（Frame + Canvas 背景）"""

    def __init__(self, parent, radius=8, bg_color=CARD_BG, **kwargs):
        super().__init__(parent, bg=parent["bg"], **kwargs)
        self._radius = radius
        self._bg_color = bg_color
        self._photo = None

        # Canvas 作为背景层
        self._canvas = tk.Canvas(self, highlightthickness=0, bg=parent["bg"])
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)

        # 内部 Frame 放内容（padding = radius）
        self._inner = tk.Frame(self, bg=bg_color)
        self._inner.pack(fill="both", expand=True, padx=radius, pady=radius)

        self.bind("<Configure>", self._draw_bg)

    def _draw_bg(self, event=None):
        self._canvas.delete("bg")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 2 or h < 2:
            return
        r = self._radius
        s = 4
        img = Image.new("RGBA", (w*s, h*s), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle([0, 0, w*s-1, h*s-1], radius=r*s, fill=self._bg_color)
        img = img.resize((w, h), Image.Resampling.LANCZOS)
        self._photo = ImageTk.PhotoImage(img)
        self._canvas.create_image(0, 0, anchor="nw", image=self._photo, tags="bg")
        self._canvas.tag_lower("bg")

    def inner(self):
        return self._inner


class PillButton(tk.Canvas):
    """圆角按钮（Pillow 抗锯齿）"""

    def __init__(self, parent, text, bg_color, fg_color="white",
                 width=120, height=30, radius=6, command=None, font=None, **kwargs):
        super().__init__(parent, width=width, height=height,
                         bg=parent["bg"], highlightthickness=0, **kwargs)
        self.command = command
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.text = text
        self.radius = radius
        self._font = font or FONT_BTN
        self._photo = None
        self._draw()
        self.bind("<ButtonRelease-1>", lambda e: self.command() if self.command else None)
        self.bind("<Configure>", lambda e: self._draw())

    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 2 or h < 2:
            return
        r = self.radius
        s = 4
        img = Image.new("RGBA", (w*s, h*s), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle([0, 0, w*s-1, h*s-1], radius=r*s, fill=self.bg_color)
        img = img.resize((w, h), Image.Resampling.LANCZOS)
        self._photo = ImageTk.PhotoImage(img)
        self.create_image(0, 0, anchor="nw", image=self._photo)
        self.create_text(w//2, h//2, text=self.text, fill=self.fg_color, font=self._font)

    def set_colors(self, bg, fg="white"):
        self.bg_color = bg
        self.fg_color = fg
        self._draw()


class RadioDot(tk.Canvas):
    """单选框圆点（12px）"""

    def __init__(self, parent, variable, value, **kwargs):
        super().__init__(parent, width=16, height=16, bg=parent["bg"],
                         highlightthickness=0, **kwargs)
        self.var = variable
        self.val = value
        self._draw()
        self.bind("<Button-1>", lambda e: self.var.set(self.val))
        self.var.trace_add("write", lambda *_: self._draw())

    def _draw(self):
        self.delete("all")
        sel = self.var.get() == self.val
        self.create_oval(2, 2, 14, 14, outline=ACCENT if sel else "#555555",
                         width=1.5, fill=CARD_BG)
        if sel:
            self.create_oval(5, 5, 11, 11, fill=ACCENT, outline=ACCENT)


class CheckDot(tk.Canvas):
    """复选框（14px 方形）"""

    def __init__(self, parent, variable, **kwargs):
        super().__init__(parent, width=16, height=16, bg=parent["bg"],
                         highlightthickness=0, **kwargs)
        self.var = variable
        self._draw()
        self.bind("<Button-1>", lambda e: self.var.set(not self.var.get()))
        self.var.trace_add("write", lambda *_: self._draw())

    def _draw(self):
        self.delete("all")
        c = self.var.get()
        self.create_polygon(3,2,13,2,15,4,15,12,13,14,3,14,1,12,1,4,
                            fill=ACCENT if c else CARD_BG,
                            outline=ACCENT if c else "#555555", width=1.5, smooth=True)
        if c:
            self.create_line([(5,8),(7,11),(12,4)], fill="white", width=1.5, capstyle="round")


# ══════════════════════════════════════════════════════════
# 自定义标题栏
# ══════════════════════════════════════════════════════════

class TitleBar(tk.Frame):
    def __init__(self, parent, title, on_min=None, on_close=None, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self._drag = {"x": 0, "y": 0}

        tk.Label(self, text=title, font=FONT_TITLE,
                 fg="#f0f0f0", bg=BG).pack(side="left", padx=10, pady=6)

        btns = tk.Frame(self, bg=BG)
        btns.pack(side="right", padx=6, pady=6)

        # 最小化
        min_btn = tk.Label(btns, text="─", font=("Microsoft YaHei UI", 10),
                           fg=TEXT_HINT, bg=BG, cursor="hand2", padx=4)
        min_btn.pack(side="left")
        min_btn.bind("<Button-1>", lambda e: on_min() if on_min else None)
        min_btn.bind("<Enter>", lambda e: min_btn.configure(fg=TEXT_BODY))
        min_btn.bind("<Leave>", lambda e: min_btn.configure(fg=TEXT_HINT))

        # 关闭
        cls_btn = tk.Label(btns, text="✕", font=("Microsoft YaHei UI", 10),
                           fg=TEXT_HINT, bg=BG, cursor="hand2", padx=4)
        cls_btn.pack(side="left")
        cls_btn.bind("<Button-1>", lambda e: on_close() if on_close else None)
        cls_btn.bind("<Enter>", lambda e: cls_btn.configure(fg=RED))
        cls_btn.bind("<Leave>", lambda e: cls_btn.configure(fg=TEXT_HINT))

        # 拖拽
        for w in [self]:
            w.bind("<Button-1>", self._start)
            w.bind("<B1-Motion>", self._drag_move)

    def _start(self, e):
        self._drag = {"x": e.x, "y": e.y}

    def _drag_move(self, e):
        x = self.winfo_toplevel().winfo_x() + (e.x - self._drag["x"])
        y = self.winfo_toplevel().winfo_y() + (e.y - self._drag["y"])
        self.winfo_toplevel().geometry(f"+{x}+{y}")


# ══════════════════════════════════════════════════════════
# 主应用
# ══════════════════════════════════════════════════════════

class App:
    def __init__(self):
        self.clicker = AutoClicker()
        self.macro = MacroRecorder()
        self._hotkey_listener = None
        self._tray_manager = None
        self._config = Config.load()

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.geometry("350x540")
        self.root.resizable(False, False)
        self.root.attributes('-topmost', True)
        self.root.configure(bg=BG)

        # 图标
        try:
            icon = os.path.join(sys._MEIPASS if getattr(sys, 'frozen', False)
                                else os.path.dirname(__file__), 'icon.ico')
            self.root.iconbitmap(icon)
        except:
            pass

        self._build()
        self._load_config()
        self._start_hotkeys()
        self._update_status()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def set_tray(self, tray):
        self._tray_manager = tray

    # ── 构建 UI ──────────────────────────────────────────

    def _build(self):
        # 标题栏
        self._titlebar = TitleBar(self.root, "QuickClick — 秋月",
                                  on_min=self._minimize, on_close=self._on_close)
        self._titlebar.pack(fill="x")

        # 内容区域（padding 16px）
        content = tk.Frame(self.root, bg=BG)
        content.pack(fill="both", expand=True, padx=16, pady=16)

        # ══ 连点设置卡片 ══
        card1 = RoundRectCanvas(content, radius=8)
        card1.pack(fill="x", pady=(0, 12))
        c1 = card1.inner()

        # 标题
        tk.Label(c1, text="连点设置", font=FONT_SECTION,
                 fg=TEXT_HINT, bg=CARD_BG).pack(anchor="w", padx=12, pady=(0, 10))

        # 按键行
        row = tk.Frame(c1, bg=CARD_BG)
        row.pack(fill="x", padx=12, pady=(0, 8))
        tk.Label(row, text="按键", font=FONT_BODY, fg=LABEL_COLOR,
                 bg=CARD_BG, width=4, anchor="w").pack(side="left")
        self.btn_var = tk.StringVar(value="left")
        for txt, val in [("左键","left"),("中键","middle"),("右键","right")]:
            f = tk.Frame(row, bg=CARD_BG)
            f.pack(side="left", padx=(6,2))
            RadioDot(f, self.btn_var, val).pack(side="left")
            tk.Label(f, text=txt, font=FONT_BODY, fg=TEXT_BODY,
                     bg=CARD_BG).pack(side="left", padx=(2,0))
        # 双击
        self.dbl_var = tk.BooleanVar(value=False)
        cf = tk.Frame(row, bg=CARD_BG)
        cf.pack(side="right")
        CheckDot(cf, self.dbl_var).pack(side="left")
        tk.Label(cf, text="双击", font=FONT_BODY, fg=TEXT_BODY,
                 bg=CARD_BG).pack(side="left", padx=(2,0))

        # 速度行
        row = tk.Frame(c1, bg=CARD_BG)
        row.pack(fill="x", padx=12, pady=(0, 8))
        tk.Label(row, text="速度", font=FONT_BODY, fg=LABEL_COLOR,
                 bg=CARD_BG, width=4, anchor="w").pack(side="left")
        self.cps_var = tk.StringVar(value="10")
        tk.Entry(row, textvariable=self.cps_var, width=6, justify="center",
                 font=FONT_BODY, bg=INPUT_BG, fg=TEXT_BODY,
                 insertbackground=TEXT_BODY, relief="flat", bd=0).pack(side="left", padx=(0,4))
        tk.Label(row, text="次/秒", font=FONT_SUFFIX, fg=SUFFIX_COLOR,
                 bg=CARD_BG).pack(side="left")

        # 坐标行
        row = tk.Frame(c1, bg=CARD_BG)
        row.pack(fill="x", padx=12, pady=(0, 12))
        tk.Label(row, text="坐标", font=FONT_BODY, fg=LABEL_COLOR,
                 bg=CARD_BG, width=4, anchor="w").pack(side="left")
        self.ax_var = tk.StringVar(value="")
        self.ay_var = tk.StringVar(value="")
        # X 输入框
        tk.Label(row, text="X", font=FONT_SUFFIX, fg=SUFFIX_COLOR,
                 bg=CARD_BG).pack(side="left")
        tk.Entry(row, textvariable=self.ax_var, width=5, justify="center",
                 font=FONT_BODY, bg=INPUT_BG, fg=TEXT_BODY,
                 insertbackground=TEXT_BODY, relief="flat", bd=0).pack(side="left", padx=(2,6))
        # Y 输入框
        tk.Label(row, text="Y", font=FONT_SUFFIX, fg=SUFFIX_COLOR,
                 bg=CARD_BG).pack(side="left")
        tk.Entry(row, textvariable=self.ay_var, width=5, justify="center",
                 font=FONT_BODY, bg=INPUT_BG, fg=TEXT_BODY,
                 insertbackground=TEXT_BODY, relief="flat", bd=0).pack(side="left", padx=(2,6))
        PillButton(row, "拾取", GHOST_BG, TEXT_BODY, 40, 24, 4,
                   command=self._pick).pack(side="left", padx=(0,4))
        tk.Label(row, text="空=跟随", font=("Microsoft YaHei UI", 8),
                 fg="#555555", bg=CARD_BG).pack(side="left")

        # ══ F8 按钮（height=20）══
        self.btn_click = PillButton(content, "▶ 开始连点 (F8)", ACCENT, "white",
                                    318, 20, 6, command=self._toggle_click, font=FONT_BTN_LARGE)
        self.btn_click.pack(pady=(0, 12))

        # ══ 鼠标宏卡片 ══
        card2 = RoundRectCanvas(content, radius=8)
        card2.pack(fill="x", pady=(0, 12))
        c2 = card2.inner()

        tk.Label(c2, text="鼠标宏", font=FONT_SECTION,
                 fg=TEXT_HINT, bg=CARD_BG).pack(anchor="w", padx=12, pady=(0, 6))

        # 状态
        self.status_lbl = tk.Label(c2, text="状态: 未录制", font=FONT_BODY,
                                   fg=TEXT_HINT, bg=CARD_BG)
        self.status_lbl.pack(anchor="w", padx=12, pady=(0, 8))

        # 回放+间隔
        row = tk.Frame(c2, bg=CARD_BG)
        row.pack(fill="x", padx=12, pady=(0, 8))
        for txt, name, default, suffix in [
            ("回放","replay_count_var","1","次 (0=无限)"),
            ("间隔","replay_interval_var","0","秒")
        ]:
            tk.Label(row, text=txt, font=FONT_BODY, fg=LABEL_COLOR,
                     bg=CARD_BG).pack(side="left")
            v = tk.StringVar(value=default)
            setattr(self, name, v)
            tk.Entry(row, textvariable=v, width=4, justify="center",
                     font=FONT_BODY, bg=INPUT_BG, fg=TEXT_BODY,
                     insertbackground=TEXT_BODY, relief="flat", bd=0).pack(side="left", padx=(0,4))
            tk.Label(row, text=suffix, font=FONT_SUFFIX, fg=SUFFIX_COLOR,
                     bg=CARD_BG).pack(side="left")

        # 录制/回放按钮（flex:1，不设固定 width）
        row = tk.Frame(c2, bg=CARD_BG)
        row.pack(fill="x", padx=12, pady=(0, 8))
        self.btn_rec = PillButton(row, "● 录制 (F7)", RED, "white",
                                  height=30, radius=6, command=self._toggle_rec)
        self.btn_rec.pack(side="left", padx=(0,6), fill="x", expand=True)
        self.btn_play = PillButton(row, "▶ 回放 (F6)", ACCENT, "white",
                                   height=30, radius=6, command=self._replay)
        self.btn_play.pack(side="left", fill="x", expand=True)

        # 文件按钮
        row = tk.Frame(c2, bg=CARD_BG)
        row.pack(fill="x", padx=12, pady=(0, 12))
        for txt, cmd in [("保存宏",self._save),("加载宏",self._load),("清空",self._clear)]:
            PillButton(row, txt, GHOST_BG, TEXT_BODY, width=0, height=26, radius=4,
                       command=cmd).pack(side="left", padx=(0,6), fill="x", expand=True)

        # ══ 状态栏 ══
        self.hint_lbl = tk.Label(content, text="就绪 | F8连点 F7录制 F6回放 F9停止",
                                 font=FONT_SMALL, fg=SMALL_COLOR, bg=BG)
        self.hint_lbl.pack(fill="x", pady=(0, 8))

        # ══ F9 按钮 ══
        self.btn_stop = PillButton(content, "■ 停止一切 (F9)", GHOST_BG, GRAY,
                                   318, 20, 6, command=self._stop_all, font=FONT_BTN_LARGE)
        self.btn_stop.pack(pady=(0, 8))

        # ══ 版本号 ══
        tk.Label(content, text="QuickClick v2.0", font=FONT_SMALL,
                 fg=FOOTER_COLOR, bg=BG).pack()

    # ── 窗口控制 ──────────────────────────────────────────

    def hide(self):
        self.root.withdraw()

    def show(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _minimize(self):
        self.root.overrideredirect(False)
        self.root.iconify()
        self.root.after(100, lambda: self.root.overrideredirect(True))

    def _on_close(self):
        self.hide()

    def quit(self):
        self._stop_all()
        if self._hotkey_listener:
            self._hotkey_listener.stop()
        if self._tray_manager:
            self._tray_manager.stop()
        self.root.destroy()

    # ── 热键 ──────────────────────────────────────────────

    def _start_hotkeys(self):
        def on_press(key):
            if key == HOTKEY_TOGGLE_CLICK:
                self.root.after(0, self._toggle_click)
            elif key == HOTKEY_TOGGLE_RECORD:
                self.root.after(0, self._toggle_rec)
            elif key == HOTKEY_REPLAY:
                self.root.after(0, self._replay)
            elif key == HOTKEY_STOP_ALL:
                self.root.after(0, self._stop_all)
        self._hotkey_listener = KeyboardListener(on_press=on_press)
        self._hotkey_listener.daemon = True
        self._hotkey_listener.start()

    # ── 逻辑 ──────────────────────────────────────────────

    def _apply(self):
        try:
            self.clicker.cps = max(1, min(int(self.cps_var.get()), 1000))
        except:
            self.clicker.cps = 10
            self.cps_var.set("10")
        from pynput.mouse import Button
        m = {"left":Button.left,"right":Button.right,"middle":Button.middle}
        self.clicker.button = m.get(self.btn_var.get(), Button.left)
        self.clicker.click_count = 2 if self.dbl_var.get() else 1
        try:
            x, y = self.ax_var.get().strip(), self.ay_var.get().strip()
            self.clicker.anchor_x = int(x) if x else None
            self.clicker.anchor_y = int(y) if y else None
        except:
            self.clicker.anchor_x = self.clicker.anchor_y = None
            self.ax_var.set(""); self.ay_var.set("")
        self._save_config()

    def _load_config(self):
        c = self._config
        self.cps_var.set(str(c.cps))
        self.btn_var.set(c.button)
        self.dbl_var.set(c.double_click)
        self.ax_var.set(str(c.anchor_x) if c.anchor_x is not None else "")
        self.ay_var.set(str(c.anchor_y) if c.anchor_y is not None else "")
        self.replay_count_var.set(str(c.replay_count))
        self.replay_interval_var.set(str(c.replay_interval))

    def _save_config(self):
        c = self._config
        try: c.cps = int(self.cps_var.get())
        except: c.cps = 10
        c.button = self.btn_var.get()
        c.double_click = self.dbl_var.get()
        try:
            x, y = self.ax_var.get().strip(), self.ay_var.get().strip()
            c.anchor_x = int(x) if x else None
            c.anchor_y = int(y) if y else None
        except: c.anchor_x = c.anchor_y = None
        try: c.replay_count = int(self.replay_count_var.get())
        except: c.replay_count = 1
        try: c.replay_interval = float(self.replay_interval_var.get())
        except: c.replay_interval = 0.0
        c.save()

    def _toggle_click(self):
        self._apply()
        self.clicker.toggle()
        self._update_status()
        self.hide() if self.clicker.is_running else self.show()

    def _pick(self):
        self._flash("3秒内点击鼠标左键拾取坐标...")
        from pynput.mouse import Listener as ML, Button
        def on_click(x, y, btn, pressed):
            if pressed and btn == Button.left:
                self.ax_var.set(str(x)); self.ay_var.set(str(y))
                self.root.after(0, lambda: self._flash(f"已拾取: ({x}, {y})"))
                return False
        l = ML(on_click=on_click); l.start()
        self.root.after(5000, lambda: l.stop() if l.running else None)

    def _toggle_rec(self):
        if self.macro.is_recording:
            n = self.macro.stop_recording()
            self._update_status(); self._flash(f"录制完成: {n} 个事件"); self.show()
        else:
            self.macro.start_recording(); self._update_status(); self.hide()

    def _replay(self):
        if self.macro.is_playing or not self.macro.events:
            if not self.macro.events: self._flash("没有可回放的宏")
            return
        try: count = max(0, int(self.replay_count_var.get()))
        except: count = 1; self.replay_count_var.set("1")
        try: interval = max(0, float(self.replay_interval_var.get()))
        except: interval = 0; self.replay_interval_var.set("0")
        def done():
            self.root.after(0, self._update_status)
            self.root.after(0, lambda: self._flash("回放完成"))
            self.root.after(0, self.show)
        def prog(cur, rem):
            t = f"回放中... 第{cur}轮 ({'无限' if rem==-1 else f'剩余{rem}次'})"
            self.root.after(0, lambda: self.status_lbl.config(text=t))
        self._rep_count = count
        self.macro.replay(count=count, interval=interval, speed=1.0,
                          callback=done, progress_callback=prog)
        self._update_status(); self.hide()

    def _stop_all(self):
        was = self.clicker.is_running or self.macro.is_recording or self.macro.is_playing
        self.clicker.stop(); self.macro.stop_recording(); self.macro.stop_replay()
        self._update_status(); self._flash("已停止")
        if was: self.show()

    def _save(self):
        if not self.macro.events: self._flash("没有可保存的宏"); return
        p = filedialog.asksaveasfilename(defaultextension=".json",
                                          filetypes=[("JSON","*.json")], title="保存鼠标宏")
        if p: self.macro.save(p); self._flash(f"已保存: {os.path.basename(p)}")

    def _load(self):
        p = filedialog.askopenfilename(filetypes=[("JSON","*.json")], title="加载鼠标宏")
        if p:
            try: n = self.macro.load(p); self._update_status(); self._flash(f"已加载: {n} 个事件")
            except Exception as e: messagebox.showerror("错误", f"加载失败: {e}")

    def _clear(self):
        self.macro.clear(); self._update_status()

    # ── 状态 ──────────────────────────────────────────────

    def _update_status(self):
        if self.clicker.is_running:
            self.btn_click.set_colors(RED, "white")
            self.btn_click.text = "■ 停止连点 (F8)"
        else:
            self.btn_click.set_colors(ACCENT, "white")
            self.btn_click.text = "▶ 开始连点 (F8)"
        self.btn_click._draw()

        if self.macro.is_recording:
            self.btn_rec.set_colors(RED_DARK, "white")
            self.btn_rec.text = "■ 停止录制 (F7)"
        else:
            self.btn_rec.set_colors(RED, "white")
            self.btn_rec.text = "● 录制 (F7)"
        self.btn_rec._draw()

        n = self.macro.event_count
        if self.macro.is_recording:
            self.status_lbl.config(text=f"状态: 录制中... ({n} 事件)", fg=RED)
        elif self.macro.is_playing:
            c = getattr(self, '_rep_count', 1)
            self.status_lbl.config(text=f"状态: 回放中... ({'无限' if c==0 else c}轮)", fg=ACCENT)
        elif n > 0:
            self.status_lbl.config(text=f"状态: 已录制 {n} 个事件", fg="#2ecc71")
        else:
            self.status_lbl.config(text="状态: 未录制", fg=TEXT_HINT)

    def _flash(self, msg):
        self.hint_lbl.config(text=msg)
        self.root.after(3000, lambda: self.hint_lbl.config(text="就绪 | F8连点 F7录制 F6回放 F9停止"))

    # ── 托盘 ──────────────────────────────────────────────

    def set_tray_manager(self, tray):
        self._tray_manager = tray

    def run(self):
        self.root.mainloop()
