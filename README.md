# Lighting Designer Workstation

## 舞台灯光设计工作站

专业级、模块化、独立可运行的舞台灯光设计工具箱。

类似 MA Lighting Tool Suite + Avolites Toolkit + ChamSys Utility Pack + Adobe Creative Suite 的灯光设计专业平台。

---

## 快速开始

```
双击 启动工作站.bat 打开工具启动器
或进入 Tools/ 子目录运行任意工具的 main.py
```

### 环境要求

- Windows 10/11 (64-bit)
- Python 3.10+
- PySide6 >= 6.6

### 安装依赖

```bash
pip install PySide6 numpy
```

### 一键打包为 EXE

```bash
build_all.bat
```

---

## 目录结构

```
D:\Lighting_Designer_Workstation\
│
├─ Common/                # 共享核心库（UI框架、项目管理、日志、主题）
│  ├─ ui/                 # 基础窗口类
│  ├─ widgets/            # 通用UI组件（DMX滑条、LED表、通道网格等）
│  ├─ themes/             # 主题系统（深色/浅色 QSS 生成）
│  ├─ project/            # 项目管理系统
│  ├─ config/             # 配置管理
│  ├─ logging/            # 统一日志系统
│  ├─ plugins/            # 插件加载框架
│  └─ utils/              # 工具函数
│
├─ Projects/              # 所有项目文件（JSON格式）
├─ Tools/                 # 所有独立工具
│  ├─ MusicAnalysis/      # 音乐分析工具
│  ├─ MIDI/               # MIDI工具
│  ├─ DMX/                # DMX/网络工具
│  ├─ LightingDesign/     # 灯光设计工具
│  ├─ VisualPreview/      # 视觉预演工具
│  ├─ Effects/            # 特效工具
│  ├─ Engineering/        # 工程计算工具
│  ├─ ShowManagement/     # 演出管理工具
│  └─ AI/                 # AI辅助工具
│
├─ Assets/                # 图标、GOBO、Fixture Profile 等资源
├─ Templates/             # 模板（Cue Sheet、Plot、技术骑手等）
├─ Libraries/             # 灯具库、Gel库、Gobo库、预设库
├─ Docs/                  # 帮助文档、使用手册
├─ Exports/               # 导出文件（PDF、CSV、MA Timecode等）
├─ Backups/               # 自动备份
├─ Plugins/               # 插件扩展目录
├─ Config/                # 全局配置、主题文件
│  └─ Themes/             # dark.json / light.json
├─ Logs/                  # 运行日志
└─ Releases/              # 打包输出
```

---

## 工具一览

### 🎵 音乐分析工具

| 工具 | 功能 | 状态 |
|------|------|------|
| BPMAnalyzer | BPM自动/实时检测、曲线显示、导出 | MVP |
| BeatDetector | 节拍/强拍/小节识别、自动打点 | Phase 3 |
| AudioSpectrum | 频谱/FFT/低频高频/峰值分析 | Phase 3 |
| MusicStructureAnalyzer | Intro/Verse/Chorus/Bridge/Drop/Outro识别 | Phase 3 |
| MoodAnalyzer | 情绪/能量曲线/高潮段分析、灯光建议 | Phase 3 |

### 🎹 MIDI工具

| 工具 | 功能 | 状态 |
|------|------|------|
| MIDIMonitor | MIDI监听、抓包、日志、实时显示 | MVP |
| MIDISender | MIDI发送、脚本、控制面板 (USB+Network) | MVP |
| MIDIMapper | MIDI学习、按钮/推子映射 | Phase 3 |
| MIDIRecorder | MIDI录制、回放、导出 | Phase 3 |
| TimecodeGenerator | SMPTE / MTC / LTC 时间码生成 | Phase 3 |
| TimecodeMonitor | 时间码监控、漂移检测、时钟同步 | Phase 3 |

### 💡 DMX/网络工具

| 工具 | 功能 | 状态 |
|------|------|------|
| DMXCalculator | 地址/通道/Universe计算 | MVP |
| FixturePatcher | 自动Patch表、Universe规划 | MVP |
| DMXTester | 通道测试、输出测试、故障检测 | Phase 3 |
| ArtNetMonitor | Art-Net协议监听与Universe监控 | Phase 3 |
| sACNMonitor | sACN协议监听与Universe分析 | Phase 3 |
| RDMTool | RDM发现、参数读写 | Phase 3 |

### 🔦 灯光设计工具

| 工具 | 功能 | 状态 |
|------|------|------|
| StagePlotDesigner | 灯位图/Truss图/舞台图绘制 (PDF/PNG/SVG) | MVP |
| FixtureLibrary | 完整灯具数据库、搜索、Profile管理 | MVP |
| BeamCalculator | 光束角/覆盖范围/投射距离计算 | Phase 3 |
| LuxCalculator | 照度计算、覆盖分析 | Phase 3 |
| ColorDesigner | RGB/CMY/色温/Gel调色板管理 | Phase 3 |
| GoboPreviewer | GOBO预览与旋转模拟 | Phase 3 |

### 🎬 视觉预演工具

| 工具 | 功能 | 状态 |
|------|------|------|
| VisualSimulator | 简易3D灯光模拟 (OBJ/FBX/GLTF) | Phase 4 |
| PixelMapper | LED矩阵Pixel Mapping设计 | Phase 4 |

### ✨ 特效与工程计算

| 工具 | 功能 | 状态 |
|------|------|------|
| LaserPlanner | 激光区域规划与安全计算 | Phase 3 |
| FXDesigner | 烟雾/CO2/火焰/冷焰火效果设计 | Phase 3 |
| PowerCalculator | 功率/电流计算 | Phase 3 |
| CableCalculator | 压降计算/线径推荐 | Phase 3 |
| DistributionPlanner | 配电规划/负载平衡 | Phase 3 |
| UPSCalculator | UPS续航计算 | Phase 3 |
| GeneratorCalculator | 发电机容量计算 | Phase 3 |

### 🎭 演出管理工具

| 工具 | 功能 | 状态 |
|------|------|------|
| ShowManager | 项目/场景/Cue总管理 | Phase 3 |
| CueDesigner | Cue/Chase/Effect设计 | Phase 3 |
| TimelineEditor | 时间轴编辑、音乐同步 | Phase 3 |
| CueSheetGenerator | Cue Sheet/节目单/操作表生成 | Phase 3 |
| EquipmentListGenerator | 灯具/配电/网络清单自动生成 | Phase 3 |
| BackupManager | 项目自动备份 | Phase 3 |

### 🤖 AI辅助工具

| 工具 | 功能 | 状态 |
|------|------|------|
| AILightingDesigner | 音乐+场地+灯具 → 灯位/Cue/颜色建议 | Phase 5 |
| AIProgrammingAssistant | 自动生成Chase/Effect/Cue流程 | Phase 5 |
| AIStageDesigner | 舞美/Truss/灯位布局辅助 | Phase 5 |
| AITroubleshooter | DMX/网络/灯具故障诊断 | Phase 5 |

---

## 开发阶段

```
Phase 1 ✅  基础框架     Common/ 核心库（UI/主题/项目/日志/配置/插件）
Phase 2 🔧  核心MVP     BPMAnalyzer / MIDIMonitor / MIDISender / DMXCalculator / FixtureLibrary / StagePlotDesigner
Phase 3 📋  高级工具     剩余音乐/MIDI/DMX/设计/管理工具
Phase 4 📋  视觉预演     VisualSimulator / PixelMapper
Phase 5 📋  AI模块       四个AI辅助工具
```

---

## UI规范

所有工具采用统一的 GrandMA3 风格深色主题：

- 深灰背景 `#1e1e1e`
- 橙色高亮 `#e8912d`
- 高对比度文字
- 扁平化专业控制台风格
- 支持深色/浅色主题切换
- 高DPI / 4K / 多显示器

主题配置位于 `Config/Themes/dark.json` 和 `Config/Themes/light.json`

---

## 项目格式

所有工具共享 `Projects/` 目录，使用统一 JSON 格式：

```json
{
  "name": "演唱会A",
  "author": "",
  "version": "1.0",
  "created_at": "2026-06-22T00:00:00",
  "modified_at": "2026-06-22T00:00:00",
  "venue": "",
  "fixtures": [],
  "cues": [],
  "scenes": [],
  "patch": [],
  "notes": []
}
```

---

## 数据格式

| 格式 | 用途 |
|------|------|
| JSON | 项目文件、配置、灯具Profile |
| CSV | 数据导出、Cue Sheet、设备清单 |
| SQLite | 灯具库、历史记录 |

---

## 插件系统

`Plugins/` 目录支持动态加载扩展插件。

每个插件结构：
```
Plugins/
└─ my_plugin/
   ├─ plugin.json    # 插件元数据
   └─ main.py        # 插件入口
```

计划支持：
MA2 · MA3 · Hog4 · Avolites · ChamSys · Resolume · QLab · TouchDesigner · Madrix · Capture · Depence

---

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+N | 新建项目 |
| Ctrl+O | 打开项目 |
| Ctrl+S | 保存项目 |
| Ctrl+Shift+S | 另存为 |
| Ctrl+L | 切换日志窗口 |
| Ctrl+P | 切换项目管理器 |
| F11 | 全屏 |
| Alt+F4 | 退出 |

---

## 技术栈

- Python 3.10+
- PySide6 (Qt6)
- NumPy (音频/信号处理)
- PyInstaller (打包)

---

## License

MIT License
