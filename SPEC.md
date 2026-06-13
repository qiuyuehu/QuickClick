# QuickClick 项目规格文档

> 最后更新：2026-06-08 18:30
> 基于源码结构 + README + UPDATE_PLAN 梳理
> 当前版本：v2.0.0
> GitHub：qiuyuehu/QuickClick

---

## 一、项目简介

QuickClick 是一款 Windows 平台的轻量鼠标连点器 + 宏录制/回放工具，支持全局热键控制，适用于游戏、办公、自动化场景。

**技术栈：** Python 3.7+ + Tkinter + pynput + Pillow
**平台：** Windows 10/11
**定位：** 轻量桌面小工具（单文件 EXE，几 MB）

---

## 二、核心架构

双层结构：核心引擎 + GUI 层

```
┌─────────────────────────────────────────┐
│         main.py（入口）                   │
│  检查 pynput 依赖 → 创建 App → run()     │
├─────────────────────────────────────────┤
│         core.py（核心引擎，395行）         │
│  ┌──────────────┬──────────────────┐    │
│  │ AutoClicker  │ MacroRecorder    │    │
│  │ 连点器引擎    │ 宏录制/回放引擎   │    │
│  │ 独立线程      │ 独立线程          │    │
│  │ pynput.mouse │ pynput.mouse +   │    │
│  │              │ pynput.keyboard  │    │
│  └──────────────┴──────────────────┘    │
├─────────────────────────────────────────┤
│         gui.py（GUI + 热键，412行）       │
│  ┌──────────────┬──────────────────┐    │
│  │ App (Tkinter)│ KeyboardListener │    │
│  │ 单面板 GUI    │ 全局热键监听      │    │
│  │ 320×580 固定  │ F6/F7/F8/F9      │    │
│  └──────────────┴──────────────────┘    │
└─────────────────────────────────────────┘
```

**关键设计：**
- 核心引擎（core.py）与 GUI（gui.py）完全分离，引擎不依赖 Tkinter
- 连点器和宏录制各自独立，互不干扰
- 所有耗时操作在独立 daemon 线程中执行，不阻塞 GUI
- 使用 `threading.Event()` 实现优雅停止（比 time.sleep 可中断）
- 全局热键通过 pynput KeyboardListener 实现，用 `root.after(0, ...)` 线程安全回调

---

## 三、目录结构

```
QuickClick/
├── main.py              # 入口（31行）
├── core.py              # 核心引擎：AutoClicker + MacroRecorder（395行）
├── gui.py               # GUI 界面 + 热键管理（412行）
├── start.bat            # Windows 一键启动脚本
├── QuickClick.spec       # PyInstaller 打包配置
├── icon.ico             # 应用图标（v1.3.0 Pillow 生成，鼠标+闪电）
├── 鼠标连点器.png         # README 界面截图
├── UPDATE_PLAN.md       # v1.1 更新方案
├── UPDATE_PLAN_v1.2.md  # v1.2 更新方案
├── LICENSE              # MIT 开源协议
├── README.md            # 项目说明（含英文版）
├── dist/
│   └── QuickClick.exe   # 打包输出
└── build/               # PyInstaller 构建缓存
```

---

## 四、核心模块详解

### 4.1 AutoClicker（core.py）

连点器引擎，在独立线程中循环发送鼠标点击。

**配置属性：**
| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| cps | int | 10 | 每秒点击次数（上限 200，即 5ms 间隔） |
| button | Button | left | 鼠标按键（left/right/middle） |
| click_count | int | 1 | 点击次数（1=单击，2=双击） |
| anchor_x | int/None | None | 锚定 X 坐标（None=跟随鼠标） |
| anchor_y | int/None | None | 锚定 Y 坐标（None=跟随鼠标） |

**核心循环（_run）：**
```
interval = 1.0 / cps
while not stop_event:
    if anchored: mouse.position = (ax, ay)
    mouse.click(button, click_count)
    stop_event.wait(interval)  # 可被 stop() 立即中断
```

**关键细节：**
- 使用 `threading.Event.wait()` 代替 `time.sleep()`，stop 时立即响应
- 锚定模式下每次点击前都重设坐标（防止被其他程序移动）
- daemon 线程，主进程退出时自动结束

### 4.2 MacroRecorder（core.py）

鼠标+键盘宏录制与回放引擎。

**事件类型（MacroEvent）：**
| event_type | 字段 | 说明 |
|------------|------|------|
| click | x, y, button, pressed | 鼠标点击（按下+释放各记录一次） |
| move | x, y | 鼠标移动（150ms 采样，delay=0） |
| key_press | x, y, key_name, pressed=True | 键盘按下 |
| key_release | x, y, key_name, pressed=False | 键盘释放 |

**录制流程：**
```
start_recording()
  ├── 启动 MouseListener（on_move, on_click, on_scroll）
  └── 启动 KeyboardListener（on_press, on_release）
      ├── 过滤热键 F6-F9（不录进宏）
      └── 记录事件 + delay（距上一事件的时间差）

stop_recording()
  ├── 停止两个 Listener
  └── 返回事件总数
```

**移动轨迹采样：**
- 每 150ms 记录一次鼠标位置（约 7 次/秒）
- delay 设为 0，回放时立即执行（不干扰点击事件的时序）
- 不更新 `_last_event_time`（避免影响后续点击/键盘事件的 delay 计算）

**回放流程：**
```
replay(count, interval, speed, callback, progress_callback)
  └── _replay_run 线程:
      for round in range(count):  # 0=无限
          progress_callback(round, remaining)
          for event in events:
              wait(event.delay / speed)  # 速度倍率
              if click: set_position + click
              if move: set_position
              if key_press: set_position + press(key)
              if key_release: release(key)
          wait(interval)  # 轮次间隔
```

**宏文件格式（JSON）：**
```json
{
  "events": [
    {"type": "click", "x": 100, "y": 200, "button": "left",
     "pressed": true, "delay": 0.5, "key_name": ""},
    {"type": "key_press", "x": 100, "y": 200, "button": "",
     "pressed": true, "delay": 0.1, "key_name": "a"}
  ]
}
```
- 向后兼容：旧版缺少 `key_name` 字段时自动跳过
- 编码：UTF-8

### 4.3 App GUI（gui.py）

纯 tk 自绘界面，440×660 固定窗口，置顶显示。Win11 浅色风格，macOS 风格单选框/复选框。

**界面布局：**
```
┌──────────────────────────────────────┐
│ 连点器（标题，18px 加粗）              │
├──────────────────────────────────────┤
│ ┌ 连点设置 ─────────────────────────┐ │
│ │ 按键: ◉左键 ○中键 ○右键  ☑双击   │ │
│ │ 速度: [10] 次/秒                   │ │
│ │ [5] [10] [20] [50] 快捷            │ │
│ │ 坐标: [___] X [___] Y [拾取]       │ │
│ └────────────────────────────────────┘ │
│ [▶ 开始连点 (F8)]（蓝色圆角按钮）      │
├──────────────────────────────────────┤
│ ┌ 鼠标宏 ───────────────────────────┐ │
│ │ 状态: 未录制                       │ │
│ │ 回放: [1] 次 (0=无限)              │ │
│ │ 间隔: [0] 秒                       │ │
│ │ 速度: ◉0.5x ○1x ○2x ○4x ○8x      │ │
│ │ [● 录制] [▶ 回放]                  │ │
│ │ [保存宏] [加载宏] [清空]            │ │
│ └────────────────────────────────────┘ │
│ 就绪 | F8连点 F7录制 F6回放 F9停止     │
│ [■ 停止一切 (F9)]（灰色圆角按钮）      │
└──────────────────────────────────────┘
```

**技术实现：**
- 全部使用 tk 控件（tk.Button、tk.Label、tk.Entry、tk.Frame、tk.Canvas）
- 不使用 ttk（避免 vista 主题下的风格割裂）
- 单选框/复选框用 Canvas 自绘，macOS 风格（细边框、圆角方形、精致勾线）
- 主按钮用 Pillow 绘制抗锯齿圆角矩形（4x 超采样 + LANCZOS 缩放）
- 配色：Win11 蓝 (#0078d4) + 红 (#e81123) + 灰 (#6b7280)
- 背景：浅灰 (#f3f3f3) + 白色卡片 (#ffffff)
- 无 hover 效果
- 输入框文字颜色：纯黑 (#000000)

**热键管理：**
| 热键 | 常量 | 功能 |
|------|------|------|
| F8 | HOTKEY_TOGGLE_CLICK | 开始/停止连点 |
| F7 | HOTKEY_TOGGLE_RECORD | 开始/停止录制 |
| F6 | HOTKEY_REPLAY | 回放宏 |
| F9 | HOTKEY_STOP_ALL | 紧急停止一切 |

- 通过 pynput KeyboardListener 实现全局热键
- 回调通过 `root.after(0, ...)` 线程安全地调度到主线程
- 热键可编辑 gui.py 顶部常量修改

**坐标拾取：**
- 点击"拾取"按钮后，启动临时 MouseListener
- 3 秒内点击鼠标左键获取坐标填入输入框
- 5 秒超时自动停止监听

---

## 五、数据流

### 5.1 连点器数据流

```
GUI (cps_var, btn_var, double_click_var, anchor_x/y_var)
  ↓ _apply_settings()
AutoClicker (cps, button, click_count, anchor_x, anchor_y)
  ↓ _run() 线程
pynput MouseController → 系统鼠标事件
```

### 5.2 宏录制数据流

```
录制时:
  pynput MouseListener + KeyboardListener
    ↓ on_click / on_move / on_key_press / on_key_release
  MacroRecorder.events: List[MacroEvent]
    ↓ save()
  JSON 文件

回放时:
  JSON 文件
    ↓ load()
  MacroRecorder.events
    ↓ _replay_run() 线程
  pynput MouseController + KeyboardController → 系统事件
```

### 5.3 热键数据流

```
pynput KeyboardListener
  ↓ on_press(key)
  匹配 HOTKEY_* 常量
  ↓ root.after(0, callback)
  GUI 主线程执行操作
```

---

## 六、打包与发布

### 6.1 PyInstaller 打包

```bash
# 方式一：命令行
pyinstaller --onefile --windowed --name QuickClick main.py

# 方式二：使用 spec 文件
pyinstaller QuickClick.spec
```

输出：`dist/QuickClick.exe`（单文件，无需 Python 环境）

### 6.2 打包配置（QuickClick.spec）

- `--onefile`：单文件 EXE
- `--windowed`：无控制台窗口
- `console=False`：不显示命令行
- `upx=True`：启用 UPX 压缩
- `--hidden-import PIL`：确保 Pillow 被打包

### 6.3 注意事项

- pynput 依赖系统 API，打包后可能被杀毒软件误报
- Pillow 是新增依赖，打包时需要确保包含
- 代码签名可减少误报，但不是必须的
- 打包后图标需单独设置（spec 文件或 --icon 参数）

---

## 七、快捷键

| 快捷键 | 功能 | 可自定义 |
|--------|------|---------|
| F8 | 开始/停止连点 | ✅ 改 gui.py HOTKEY_TOGGLE_CLICK |
| F7 | 开始/停止录制 | ✅ 改 gui.py HOTKEY_TOGGLE_RECORD |
| F6 | 回放宏 | ✅ 改 gui.py HOTKEY_REPLAY |
| F9 | 紧急停止一切 | ✅ 改 gui.py HOTKEY_STOP_ALL |

热键值为 pynput Key 枚举，如 `Key.f8`、`Key.ctrl_l` 等。

---

## 八、已知限制与技术债务

| 编号 | 描述 | 优先级 |
|------|------|--------|
| 1 | 滚轮事件不支持录制（_on_scroll 为空） | 低 |
| 2 | 移动轨迹采样 150ms，高速移动可能丢失细节 | 低 |
| 3 | 无配置持久化（每次启动重置为默认值） | 中 |
| 4 | 热键冲突时需手动编辑代码 | 低 |
| 5 | core.py 署名还是旧的 "凛 (Emperor Agent)" | 低 |
| 6 | 无单元测试 | 中 |
| 7 | 宏回放不支持暂停/继续 | 低 |
| 8 | 新增 Pillow 依赖，打包体积会增大 | 低 |

---

## 九、版本历史

| 版本 | 日期 | 里程碑 |
|------|------|--------|
| v1.0.0 | 2026-05-23 | 初始发布：连点器 + 宏录制/回放 + 全局热键 |
| v1.1.0 | 2026-05-26 | 键盘录制、中键支持、锚定坐标、事件统计 |
|| v1.2.0 | 2026-05-27 | 双击功能、移动轨迹、回放速度调整、剩余次数显示 |
|| v1.3.0 | 2026-06-08 | UI 重写：Win11 浅色风格、纯 tk 自绘、Pillow 抗锯齿圆角按钮、macOS 风格单选框/复选框 |

---

## 十、开发流程记录

### v1.1 更新方案（UPDATE_PLAN.md）

3 项需求，6 步执行：
1. core.py — AutoClicker 增加 anchor 属性 + 中键逻辑
2. gui.py — 连点区域加中键 Radio + 锚定坐标 + 拾取按钮
3. core.py — MacroRecorder 增加键盘监听 + 键盘事件回放
4. gui.py — 宏状态显示区分鼠标/键盘事件
5. gui.py — 窗口尺寸调整（320×470 → 320×560）
6. README.md — 更新文档 → v1.1

### v1.2 更新方案（UPDATE_PLAN_v1.2.md）

4 项需求 + 5 项建议，8 步执行：
1. core.py — AutoClicker 增加 click_count
2. gui.py — 连点区域增加双击复选框
3. core.py — MacroRecorder 增加移动轨迹（采样 50ms→实际 150ms）
4. core.py — replay() 增加 speed 和 progress_callback
5. gui.py — 宏区域增加速度选择和剩余次数显示
6. gui.py — 状态显示更新（移动事件计数）
7. gui.py — 窗口尺寸调整（320×520 → 320×580）
8. README.md — 更新文档 → v1.2

**待实现建议（v1.2 方案中提出）：**
- 宏队列功能（多宏按顺序执行）
- 宏文件快速切换（最近 10 个）
- 回放暂停/继续（F5 热键）
- 坐标偏移（不同分辨率适配）
- 宏录制标记点

---

## 十一、文件路径速查

| 用途 | 路径 |
|------|------|
| 项目根目录（源码） | `C:\Agent\emperor-agent\projects\QuickClick\` |
| 项目根目录（桌面） | `C:\Users\秋月\Desktop\QuickClick\` |
| GitHub 仓库 | `https://github.com/qiuyuehu/QuickClick` |
| 打包输出 | `dist\QuickClick.exe` |

---

*基于源码结构、README、UPDATE_PLAN 梳理*
