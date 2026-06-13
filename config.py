# -*- coding: utf-8 -*-
"""
config.py — QuickClick 配置持久化

保存/加载用户设置，下次启动自动恢复。
配置文件：quickclick_config.json（exe 同目录或 __file__ 同目录）
"""

import json
import os
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Config:
    """QuickClick 配置"""
    # 连点器
    cps: int = 10
    button: str = "left"
    double_click: bool = False
    anchor_x: Optional[int] = None
    anchor_y: Optional[int] = None

    # 宏回放
    replay_count: int = 1
    replay_interval: float = 0.0
    speed: str = "1"

    @classmethod
    def _config_path(cls) -> str:
        """配置文件路径"""
        if getattr(sys, 'frozen', False):
            # 打包后：exe 同目录
            base = os.path.dirname(sys.executable)
        else:
            # 开发时：__file__ 同目录
            base = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base, 'quickclick_config.json')

    def save(self):
        """保存配置到 JSON 文件"""
        path = self._config_path()
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(asdict(self), f, indent=2, ensure_ascii=False)
        except Exception:
            pass  # 保存失败不影响运行

    @classmethod
    def load(cls) -> 'Config':
        """从 JSON 文件加载配置，字段缺失用默认值兜底"""
        path = cls._config_path()
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # 只取 Config 有的字段，多余的忽略
            valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
            filtered = {k: v for k, v in data.items() if k in valid_keys}
            return cls(**filtered)
        except (FileNotFoundError, json.JSONDecodeError, TypeError, ValueError):
            return cls()  # 文件不存在或损坏，返回默认配置
