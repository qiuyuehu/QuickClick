<h1 align="center">⚡ QuickClick</h1>

<p align="center">Windows 桌面连点器 + 鼠标宏录制回放工具</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white" alt="Python 3.11">
  <img src="https://img.shields.io/badge/Platform-Windows-0078d4?logo=windows&logoColor=white" alt="Windows">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  <img src="https://img.shields.io/github/stars/qiuyuehu/QuickClick?style=social" alt="Stars">
</p>

---

## 它能做什么？

| 功能 | 说明 |
|------|------|
| **高速连点** | 左键 / 右键自动点击，CPS 最高 200 次/秒 |
| **宏录制** | 录制你的鼠标点击操作，一键回放 |
| **循环回放** | 宏支持无限循环，按停止键随时中断 |
| **全局热键** | 任何界面下都能用快捷键控制，无需切窗口 |

## 截图

> 启动后显示简洁的 GUI 面板，分为「连点器」和「宏录制」两个区域，参数一目了然。

```
┌─────────────────────────────────┐
│         ⚡ QuickClick           │
├─────────────────────────────────┤
│  连点器                         │
│  按钮: [左键] [右键]            │
│  速度: [____] ms                │
│                                 │
│  宏录制                         │
│  [录制] [回放] [清除]           │
│  状态: ● 空闲                   │
│                                 │
│  F8连点 F7录制 F6回放 F9停止    │
└─────────────────────────────────┘
```

## 快速开始

### 方式一：直接运行（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/qiuyuehu/QuickClick.git
cd QuickClick

# 2. 安装依赖
pip install pynput

# 3. 启动
python main.py
```

### 方式二：打包为 EXE

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name QuickClick main.py
```

打包完成后，`dist/QuickClick.exe` 可独立运行，无需 Python 环境。

## 快捷键

| 快捷键 | 功能 | 备注 |
|--------|------|------|
| `F8` | 开始 / 停止连点 | 切换模式 |
| `F7` | 开始 / 停止录制宏 | 录制期间记录所有鼠标点击 |
| `F6` | 回放宏 | 支持无限循环，按 `F9` 停止 |
| `F9` | 停止一切 | 紧急停止，连点和回放全部中断 |

## 系统要求

- **操作系统**：Windows 10 / 11
- **Python**：3.11（直接运行时需要）
- **依赖**：[pynput](https://pypi.org/project/pynput/)

## 常见问题

**Q：杀毒软件报毒怎么办？**
> 这是 Python 打包的常见误报。代码完全开源，可自行审计后添加白名单。

**Q：热键和其他软件冲突了？**
> 当前热键为固定值（F6-F9），如需修改可编辑 `gui.py` 中的 `HOTKEY_*` 常量。

**Q：连点速度上限是多少？**
> 理论上限 200 CPS（5ms 间隔），实际取决于系统负载。

## 项目结构

```
QuickClick/
├── main.py       # 程序入口
├── core.py       # 连点器 + 宏录制核心引擎
├── gui.py        # GUI 界面 + 热键管理
├── start.bat     # Windows 一键启动脚本
└── README.md     # 就是这个文件
```

## License

[MIT](LICENSE)

---

<p align="center">
  如果觉得有用，点个 ⭐ Star 支持一下吧！
</p>
