# -*- coding: utf-8 -*-
"""
core.py — QuickClick 连点器 + 鼠标宏 核心引擎
Author: qiuyuehu / 凛

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


# ── 常量 ──

@dataclass
class MacroEvent:
    """一个宏事件"""
    event_type: str  # 'click' / 'move'
    x: int
    y: int
    button: str = ''  # 'left' / 'right'
    pressed: bool = True  # True=按下, False=释放
    delay: float = 0.0  # 距上一个事件的延迟(秒)


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
        while not self._stop_event.is_set():
            self._mouse.click(self.button)
            # 用 Event.wait 代替 time.sleep，可以被 stop() 立即中断
            self._stop_event.wait(interval)


# ── 鼠标宏 ──

class MacroRecorder:
    """
    鼠标宏录制与回放。
    录制：监听鼠标移动 + 点击，记录事件和时间戳。
    回放：按原始时间间隔重现事件。
    """

    def __init__(self):
        self._mouse = MouseController()
        self._listener: Optional[MouseListener] = None
        self._replay_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._recording = False
        self._playing = False

        # 录制数据
        self.events: List[MacroEvent] = []
        self._last_event_time: float = 0

    @property
    def is_recording(self) -> bool:
        return self._recording

    @property
    def is_playing(self) -> bool:
        return self._playing

    @property
    def event_count(self) -> int:
        return len(self.events)

    def start_recording(self):
        """开始录制"""
        if self._recording:
            return
        self.events.clear()
        self._recording = True
        self._last_event_time = time.perf_counter()

        # 启动鼠标监听器
        self._listener = MouseListener(
            on_move=self._on_move,
            on_click=self._on_click,
            on_scroll=self._on_scroll,
        )
        self._listener.start()

    def stop_recording(self) -> int:
        """停止录制，返回录制的事件数"""
        if not self._recording:
            return 0
        self._recording = False
        if self._listener:
            self._listener.stop()
            self._listener = None
        return len(self.events)

    def _on_move(self, x, y):
        # 不更新 _last_event_time — 移动不是事件，不应重置计时
        pass

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

    def replay(self, count: int = 1, interval: float = 0.0,
               callback: Optional[Callable] = None):
        """回放录制的宏
        count: 回放次数（0=无限）
        interval: 每次回放之间的间隔（秒）
        """
        if self._playing or not self.events:
            return
        self._stop_event.clear()
        self._playing = True
        self._replay_thread = threading.Thread(
            target=self._replay_run, args=(count, interval, callback), daemon=True
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

    def _replay_run(self, count, interval, callback):
        """回放线程"""
        try:
            round_num = 0
            while True:
                if self._stop_event.is_set():
                    break

                round_num += 1

                for evt in self.events:
                    if self._stop_event.is_set():
                        break

                    if evt.delay > 0:
                        self._stop_event.wait(evt.delay)

                    if self._stop_event.is_set():
                        break

                    if evt.event_type == 'click' and evt.pressed:
                        self._mouse.position = (evt.x, evt.y)
                        btn = Button.left if evt.button in ('left', 'Button.left') else Button.right
                        self._mouse.click(btn)

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
                 "button": e.button, "pressed": e.pressed, "delay": e.delay}
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
                ))
            except (ValueError, TypeError):
                continue  # 跳过损坏的事件
        return len(self.events)

    def clear(self):
        """清空录制"""
        self.events.clear()
