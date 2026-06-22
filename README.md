# Lighting Designer Workstation

## 舞台灯光设计工作站

专业级、模块化、独立可运行的舞台灯光设计工具箱。

类似 MA Lighting Tool Suite + Avolites Toolkit + ChamSys Utility Pack + Adobe Creative Suite 的灯光设计专业平台。

---

## 快速开始

```
双击 启动工作站.bat 打开工具启动器，或进入 Tools/ 子目录运行任意工具的 main.py
```

### 环境要求

- Windows 10/11 (64-bit)
- Python 3.10+
- PySide6 >= 6.5

### 安装依赖

```bash
pip install -r requirements.txt
```

### 一键初始化开发环境

```powershell
scripts\bootstrap.ps1
```

### 一键打包为 EXE

```powershell
build_all.ps1
```

---

## 目录结构

```
D:\Lighting_Designer_Workstation\
├─ Common/                # 共享核心库（UI框架、项目管理、日志、主题）
│  ├─ ui/                 # 基础窗口类
│  ├─ widgets/            # 通用UI组件
│  ├─ themes/             # 主题系统（深色/浅色 QSS）
│  ├─ project/            # 项目管理系统
│  ├─ config/             # 配置管理
│  ├─ log_system/         # 统一日志系统
│  ├─ plugins/            # 插件加载框架
│  └─ utils/              # 工具函数
├─ Projects/              # 所有项目文件（JSON格式）
├─ Tools/                 # 所有独立工具
│  ├─ MusicAnalysis/      # 音乐分析工具（5个）
│  ├─ MIDI/               # MIDI工具（6个）
│  ├─ DMX/                # DMX/网络工具（6个）
│  ├─ LightingDesign/     # 灯光设计工具（6个）
│  ├─ VisualPreview/      # 视觉预演工具（2个）
│  ├─ Effects/            # 特效工具（2个）
│  ├─ Engineering/        # 工程计算工具（5个）
│  ├─ ShowManagement/     # 演出管理工具（6个）
│  └─ AI/                 # AI辅助工具（4个）
├─ Assets/                # 图标、GOBO、Fixture Profile 等资源
├─ Templates/             # 模板（Cue Sheet、Plot、技术骑手等）
├─ Libraries/             # 灯具库、Gel库、Gobo库、预设库
├─ Config/                # 全局配置、主题文件、版本号
├─ Logs/                  # 运行日志
├─ tests/                 # 基础测试
├─ scripts/               # 开发脚本
├─ CONTRIBUTING.md        # 贡献指南
├─ requirements.txt       # 依赖声明
└─ pyproject.toml         # 项目元数据
```

---

## 工具一览（共 42 个）

### 🎵 音乐分析（5个）
| 工具 | 功能 |
|------|------|
| BPMAnalyzer | BPM自动/实时检测、曲线显示、导出 |
| BeatDetector | 节拍/强拍/小节识别、自动打点 |
| AudioSpectrum | 频谱/FFT/低频高频/峰值分析 |
| MusicStructureAnalyzer | Intro/Verse/Chorus/Bridge/Drop/Outro识别 |
| MoodAnalyzer | 情绪/能量曲线/高潮段分析、灯光建议 |

### 🎹 MIDI工具（6个）
| 工具 | 功能 |
|------|------|
| MIDIMonitor | MIDI监听、抓包、日志、实时显示 |
| MIDISender | MIDI发送、脚本、控制面板 (USB+Network) |
| MIDIMapper | MIDI学习、按钮映射、CC映射 |
| MIDIRecorder | MIDI录制、回放、导出 |
| TimecodeGenerator | SMPTE/MTC/LTC时间码生成 |
| TimecodeMonitor | 时间码漂移检测、同步监视 |

### 🌐 DMX/网络（6个）
| 工具 | 功能 |
|------|------|
| DMXCalculator | DMX地址/通道计算 |
| FixturePatcher | Patch表规划、灯具配接 |
| DMXTester | DMX通道测试、故障检测 |
| ArtNetMonitor | Art-Net协议监听 |
| sACNMonitor | sACN Universe分析 |
| RDMTool | RDM设备发现、参数读写 |

### 🔦 灯光设计（6个）
| 工具 | 功能 |
|------|------|
| StagePlotDesigner | 舞台平面图、灯位图绘制 |
| FixtureLibrary | 灯具数据库搜索/管理 |
| BeamCalculator | 光束角度/覆盖计算 |
| LuxCalculator | 照度/覆盖分析 |
| ColorDesigner | RGB/CMY/Gel色彩设计 |
| GoboPreviewer | GOBO预览/旋转模拟 |

### 🎬 视觉预演（2个）
| 工具 | 功能 |
|------|------|
| VisualSimulator | 3D灯光模拟 |
| PixelMapper | LED矩阵/像素映射设计 |

### ✅ 特效工程（7个）
| 工具 | 功能 |
|------|------|
| LaserPlanner | 激光区域/安全计算 |
| FXDesigner | 烟雾/CO2/焰火特效设计 |
| PowerCalculator | 功率/电流计算 |
| CableCalculator | 线缆压降/线径计算 |
| DistributionPlanner | 配电负载平衡规划 |
| UPSCalculator | UPS续航计算 |
| GeneratorCalculator | 发电机容量计算 |

### 🎭 演出管理（6个）
| 工具 | 功能 |
|------|------|
| ShowManager | 项目/场景/Cue管理 |
| CueDesigner | Cue/Chase/效果设计 |
| TimelineEditor | 时间轴/音乐同步编辑 |
| CueSheetGenerator | 节目单/Cue Sheet生成 |
| EquipmentListGenerator | 设备清单生成 |
| BackupManager | 自动备份管理 |

### 🤖 AI辅助（4个）
| 工具 | 功能 |
|------|------|
| AILightingDesigner | AI灯光设计建议 |
| AIProgrammingAssistant | AI编程助手（Chase/效果） |
| AIStageDesigner | AI舞美/布局建议 |
| AITroubleshooter | AI故障诊断 |

---

## 开发指南

### 运行测试
```bash
python -m pytest tests/ -v
```

### 代码风格
- 使用中文注释
- 遵循 PEP 8
- 提交前检查语法：`python -m py_compile <file>`

### 版本管理
- 版本号统一在 `Config/version.json` 管理
- 构建脚本和启动器自动读取此文件

---

## 许可证

MIT License