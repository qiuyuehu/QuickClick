<h1 align="center">⚡ QuickClick</h1>

<p align="center"><b>一款 Windows 平台的轻量工具，集「高速鼠标连点器」与「宏录制/回放」于一体，支持全局热键控制，游戏、办公、自动化场景通用。</b></p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.7+-blue?logo=python&logoColor=white" alt="Python 3.7+">
  <img src="https://img.shields.io/badge/Platform-Windows-0078d4?logo=windows&logoColor=white" alt="Windows">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  <img src="https://img.shields.io/github/stars/qiuyuehu/QuickClick?style=social" alt="Stars">
</p>

---

## 功能亮点

- **高速连点** — 最高 200 CPS（5ms 间隔），支持左键 / 右键切换
- **宏录制** — 一键录制鼠标点击操作，支持无限循环回放
- **全局热键** — 任何界面下都能用快捷键启停，无需切换窗口
- **轻量无依赖** — 纯 Python 实现，可直接运行或打包为单文件 EXE

## 界面预览

程序启动后显示简洁的单面板 GUI，分为「连点器」和「宏录制」两个独立区域，所有参数一目了然：

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

### 方式一：下载 EXE（免装 Python）

前往 [Releases](https://github.com/qiuyuehu/QuickClick/releases) 页面，下载最新版本的 `QuickClick.exe`，双击直接运行。

### 方式二：命令行运行

```bash
# 1. 克隆仓库
git clone https://github.com/qiuyuehu/QuickClick.git
cd QuickClick

# 2. 安装依赖
pip install pynput

# 3. 启动
python main.py
```

### 方式三：自行打包 EXE

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name QuickClick main.py
```

打包完成后，`dist/QuickClick.exe` 可独立运行，无需 Python 环境。

> **注意**：部分杀毒软件可能对 Python 打包的 EXE 误报，代码完全开源，可自行审计后添加信任。

## 快捷键

| 快捷键 | 功能 | 备注 |
|--------|------|------|
| `F8` | 开始 / 停止连点 | 切换连点启停状态 |
| `F7` | 开始 / 停止录制宏 | 录制期间记录所有鼠标点击操作 |
| `F6` | 回放宏 | 支持无限循环，按 `F9` 随时中断 |
| `F9` | 紧急停止 | 一键终止所有正在运行的任务 |

> 若热键与其他软件冲突，可直接编辑 `gui.py` 中的 `HOTKEY_*` 常量修改，无需改动核心逻辑。

## 配置说明

| 参数 | 位置 | 说明 |
|------|------|------|
| 热键绑定 | `gui.py` → `HOTKEY_*` 常量 | 修改为 `pynput` 支持的任意按键 |
| CPS 上限 | `gui.py` → 连点速度输入框 | 最小间隔 5ms（200 CPS） |
| 宏文件格式 | `core.py` → `MacroRecorder` | JSON 格式，可手动编辑 |

## 项目结构

```
QuickClick/
├── main.py       # 程序入口
├── core.py       # 连点器 + 宏录制核心引擎
├── gui.py        # GUI 界面 + 热键管理
├── start.bat     # Windows 一键启动脚本
├── LICENSE       # MIT 开源协议
└── README.md     # 项目文档
```

## 系统要求

- **操作系统**：Windows 10 / 11
- **Python**：3.7 及以上（直接运行时需要，打包后不需要）
- **依赖**：[pynput](https://pypi.org/project/pynput/)

## 常见问题

**Q：杀毒软件报毒怎么办？**
A：这是 Python 打包的常见误报。代码完全开源，可自行审计后添加白名单。

**Q：热键和其他软件冲突了？**
A：编辑 `gui.py` 中的 `HOTKEY_TOGGLE_CLICK`、`HOTKEY_TOGGLE_RECORD`、`HOTKEY_REPLAY`、`HOTKEY_STOP` 常量，改为 `pynput` 支持的任意按键即可。

**Q：连点速度上限是多少？**
A：理论上限 200 CPS（5ms 间隔），实际取决于系统负载。

**Q：宏录制支持键盘操作吗？**
A：当前版本仅支持鼠标点击录制，键盘操作暂不支持。

## 更新日志

### v1.0.0（2026-05-23）

- 初始发布
- 连点器功能（左键/右键，可调速度）
- 鼠标宏录制与无限循环回放
- 全局热键控制（F6-F9）
- 支持打包为独立 EXE

## 作者

**qiuyuehu** — [GitHub](https://github.com/qiuyuehu)

**凛 (Emperor Agent)** — 开发与设计

## License

[MIT](LICENSE)

---

<p align="center">
  如果觉得有用，点个 ⭐ Star 支持一下吧！
</p>
