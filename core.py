# -*- coding: utf-8 -*-
"""
core.py — QuickClick 连点器 + 鼠标宏 核心引擎
Author: qiuyuehu / 凛 (Emperor Agent)

功能：
1. AutoClicker — 连点（左键/右键，可调速度）
2. MacroRecorder — 鼠标宏录制与回放
"""

import time
import threading
import json
import os
from dataclasses import dataclass
from typing import List, Optional, Callable

from pynput.mouse import Controller as MouseController, Button, Listener as MouseListener
from pynput.keyboard import Controller as KeyboardController, Listener as KeyboardListener, Key


# ── 常量 ──

@dataclass
class MacroEvent:
    """一个宏事件"""
    event_type: str  # 'click' / 'key_press' / 'key_release'
    x: int
    y: int
    button: str = ''  # 'left' / 'right' / 'middle'
    pressed: bool = True  # True=按下, False=释放
    delay: float = 0.0  # 距上一个事件的延迟(秒)
    key_name: str = ''  # 键盘事件的键名


# ── 连点器 ──

class AutoClicker:
    """
    连点器引擎。
    在独立线程中循环发送鼠标点击。
    """

    def __init__(self):
        self._mouse = MouseController()
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False

        # 配置
        self.cps = 10  # 每秒点击次数
        self.button = Button.left
        self.click_count = 1  # 1=单击, 2=双击

        # 锚定坐标（None = 跟随鼠标）
        self.anchor_x: Optional[int] = None
        self.anchor_y: Optional[int] = None

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self):
        """开始连点"""
        if self._running:
            return
        self._stop_event.clear()
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """停止连点"""
        if not self._running:
            return
        self._stop_event.set()
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)
            self._thread = None

    def toggle(self):
        """切换开/关"""
        if self._running:
            self.stop()
        else:
            self.start()

    def _run(self):
        """连点循环"""
        interval = 1.0 / max(self.cps, 1)
        ax, ay = self.anchor_x, self.anchor_y
        anchored = ax is not None and ay is not None
        pos: tuple = (ax, ay)  # type: ignore
        if anchored:
            self._mouse.position = pos
        while not self._stop_event.is_set():
            if anchored:
                self._mouse.position = pos
            self._mouse.click(self.button, self.click_count)
            # 用 Event.wait 代替 time.sleep，可以被 stop() 立即中断
            self._stop_event.wait(interval)


# ── 鼠标宏 ──

class MacroRecorder:
    """
    鼠标+键盘宏录制与回放。
    录制：监听鼠标点击 + 键盘按键，记录事件和时间戳。
    回放：按原始时间间隔重现事件。
    """

    # 需要过滤的热键（不录进宏）
    _FILTERED_KEYS = {Key.f6, Key.f7, Key.f8, Key.f9}

    def __init__(self):
        self._mouse = MouseController()
        self._keyboard = KeyboardController()
        self._mouse_listener: Optional[MouseListener] = None
        self._kb_listener: Optional[KeyboardListener] = None
        self._replay_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._recording = False
        self._playing = False

        # 录制数据
        self.events: List[MacroEvent] = []
        self._last_event_time: float = 0
        self._last_move_time: float = 0  # 移动轨迹采样计时

    @property
    def is_recording(self) -> bool:
        return self._recording

    @property
    def is_playing(self) -> bool:
        return self._playing

    @property
    def event_count(self) -> int:
        return len(self.events)

    @property
    def mouse_event_count(self) -> int:
        return sum(1 for e in self.events if e.event_type == 'click')

    @property
    def move_event_count(self) -> int:
        return sum(1 for e in self.events if e.event_type == 'move')

    @property
    def key_event_count(self) -> int:
        return sum(1 for e in self.events if e.event_type in ('key_press', 'key_release'))

    def start_recording(self):
        """开始录制"""
        if self._recording:
            return
        self.events.clear()
        self._recording = True
        self._last_event_time = time.perf_counter()
        self._last_move_time = time.perf_counter()  # 初始化移动采样计时

        # 启动鼠标监听器
        self._mouse_listener = MouseListener(
            on_move=self._on_move,
            on_click=self._on_click,
            on_scroll=self._on_scroll,
        )
        self._mouse_listener.start()

        # 启动键盘监听器
        self._kb_listener = KeyboardListener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )
        self._kb_listener.start()

    def stop_recording(self) -> int:
        """停止录制，返回录制的事件数"""
        if not self._recording:
            return 0
        self._recording = False
        if self._mouse_listener:
            self._mouse_listener.stop()
            self._mouse_listener = None
        if self._kb_listener:
            self._kb_listener.stop()
            self._kb_listener = None
        return len(self.events)

    def _on_move(self, x, y):
        if not self._recording:
            return
        now = time.perf_counter()
        # 采样：每 150ms 记录一次鼠标位置（约7次/秒，平衡精度和性能）
        if now - self._last_move_time < 0.15:
            return
        self._last_move_time = now
        # 移动事件不更新 _last_event_time，避免干扰点击/键盘事件的延迟计算
        self.events.append(MacroEvent(
            event_type='move',
            x=x, y=y,
            delay=0.0,  # 移动事件延迟为0，回放时立即执行
        ))

    def _on_click(self, x, y, button, pressed):
        if not self._recording:
            return
        now = time.perf_counter()
        delay = now - self._last_event_time
        self._last_event_time = now
        self.events.append(MacroEvent(
            event_type='click',
            x=x, y=y,
            button=button.name if hasattr(button, 'name') else str(button),
            pressed=pressed,
            delay=delay,
        ))

    def _on_scroll(self, x, y, dx, dy):
        # 暂不支持滚轮
        pass

    @staticmethod
    def _key_to_name(key) -> str:
        """将 pynput key 对象转为可序列化的字符串"""
        if isinstance(key, Key):
            return key.name  # 特殊键: 'f8', 'shift', 'ctrl_l' 等
        elif hasattr(key, 'char') and key.char:
            return key.char  # 普通字符: 'a', '1', ' ' 等
        else:
            return str(key)

    def _on_key_press(self, key):
        if not self._recording:
            return
        # 过滤热键
        if key in self._FILTERED_KEYS:
            return
        now = time.perf_counter()
        delay = now - self._last_event_time
        self._last_event_time = now
        # 获取当前鼠标位置
        mx, my = self._mouse.position
        self.events.append(MacroEvent(
            event_type='key_press',
            x=mx, y=my,
            pressed=True,
            delay=delay,
            key_name=self._key_to_name(key),
        ))

    def _on_key_release(self, key):
        if not self._recording:
            return
        if key in self._FILTERED_KEYS:
            return
        now = time.perf_counter()
        delay = now - self._last_event_time
        self._last_event_time = now
        mx, my = self._mouse.position
        self.events.append(MacroEvent(
            event_type='key_release',
            x=mx, y=my,
            pressed=False,
            delay=delay,
            key_name=self._key_to_name(key),
        ))

    def replay(self, count: int = 1, interval: float = 0.0,
               speed: float = 1.0,
               callback: Optional[Callable] = None,
               progress_callback: Optional[Callable] = None):
        """回放录制的宏
        count: 回放次数（0=无限）
        interval: 每次回放之间的间隔（秒）
        speed: 速度倍率（1.0=原速，0.5=减速，2.0=加速）
        progress_callback: 进度回调函数 callback(current_round, remaining)
        """
        if self._playing or not self.events:
            return
        self._stop_event.clear()
        self._playing = True
        self._replay_thread = threading.Thread(
            target=self._replay_run, args=(count, interval, speed, callback, progress_callback), daemon=True
        )
        self._replay_thread.start()

    def stop_replay(self):
        """停止回放"""
        if not self._playing:
            return
        self._stop_event.set()
        self._playing = False
        if self._replay_thread:
            self._replay_thread.join(timeout=1)
            self._replay_thread = None

    def _replay_run(self, count, interval, speed, callback, progress_callback):
        """回放线程"""
        try:
            round_num = 0
            while True:
                if self._stop_event.is_set():
                    break

                round_num += 1
                
                # 调用进度回调
                if progress_callback:
                    remaining = count - round_num + 1 if count > 0 else -1
                    progress_callback(round_num, remaining)

                for evt in self.events:
                    if self._stop_event.is_set():
                        break

                    if evt.delay > 0:
                        adjusted_delay = evt.delay / speed  # 速度倍率
                        self._stop_event.wait(adjusted_delay)

                    if self._stop_event.is_set():
                        break

                    if evt.event_type == 'click' and evt.pressed:
                        self._mouse.position = (evt.x, evt.y)
                        btn_map = {'left': Button.left, 'right': Button.right, 'middle': Button.middle}
                        btn = btn_map.get(evt.button, Button.left)
                        self._mouse.click(btn)
                    elif evt.event_type == 'move':
                        self._mouse.position = (evt.x, evt.y)
                    elif evt.event_type == 'key_press':
                        self._mouse.position = (evt.x, evt.y)
                        try:
                            k = Key[evt.key_name] if evt.key_name in Key.__members__ else evt.key_name
                            self._keyboard.press(k)
                        except (KeyError, Exception):
                            pass
                    elif evt.event_type == 'key_release':
                        try:
                            k = Key[evt.key_name] if evt.key_name in Key.__members__ else evt.key_name
                            self._keyboard.release(k)
                        except (KeyError, Exception):
                            pass

                # 检查是否继续
                if count > 0 and round_num >= count:
                    break

                # 回放间隔
                if interval > 0 and not self._stop_event.is_set():
                    self._stop_event.wait(interval)
        finally:
            self._playing = False
            if callback:
                callback()

    def save(self, filepath: str):
        """保存宏到文件"""
        data = {
            "events": [
                {"type": e.event_type, "x": e.x, "y": e.y,
                 "button": e.button, "pressed": e.pressed, "delay": e.delay,
                 "key_name": e.key_name}
                for e in self.events
            ]
        }
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def load(self, filepath: str) -> int:
        """加载宏文件，返回事件数"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.events = []
        for e in data.get("events", []):
            try:
                self.events.append(MacroEvent(
                    event_type=e.get("type", "click"),
                    x=int(e.get("x", 0)), y=int(e.get("y", 0)),
                    button=e.get("button", "left"),
                    pressed=bool(e.get("pressed", True)),
                    delay=float(e.get("delay", 0)),
                    key_name=e.get("key_name", ""),
                ))
            except (ValueError, TypeError):
                continue  # 跳过损坏的事件
        return len(self.events)

    def clear(self):
        """清空录制"""
        self.events.clear()
