# QuickClick

Windows 连点器 + 鼠标宏录制回放工具。

## 功能

- **连点器** — 左键/右键自动点击，速度可调（CPS 上限 200）
- **宏录制** — 录制鼠标操作轨迹，支持无限循环回放
- **热键控制** — 全局热键，随时启停

## 热键

| 热键 | 功能 |
|------|------|
| F8 | 开始/停止连点 |
| F7 | 开始/停止录制宏 |
| F6 | 回放宏 |
| F9 | 停止一切 |

## 使用方式

### 直接运行

```
py -3.11 main.py
```

### 打包为 EXE

```
py -3.11 -m PyInstaller --onefile --windowed --name AutoClicker main.py
```

打包后生成 `dist/AutoClicker.exe`，可独立运行。

## 依赖

- Python 3.11
- pynput

安装依赖：

```
pip install pynput
```

## 截图

启动后显示主界面，选择连点器或宏录制模式，配置参数即可开始。
