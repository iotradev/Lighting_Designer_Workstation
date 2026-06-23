# Lighting Designer Workstation

舞台灯光设计工作站 — 42个专业灯光工具，GrandMA3 风格深色主题

## 快速启动

```bash
python launcher.py
# 或双击 启动工作站.bat
```

## 依赖

```bash
pip install PySide6 numpy miniaudio python-rtmidi
```

## 工具分类 (42个)

| 分类 | 工具数 | 说明 |
|------|--------|------|
| 🎵 音乐分析 | 5 | BPM检测、频谱分析、情绪分析 |
| 🎹 MIDI工具 | 6 | 监听、发送、映射、录制、时间码 |
| 🌐 DMX/网络 | 6 | DMX计算、Art-Net、sACN、RDM |
| 🔦 灯光设计 | 6 | 舞台平面图、灯具库、光束计算 |
| 🎬 视觉预演 | 2 | 3D模拟、像素映射 |
| ✅ 特效工程 | 7 | 激光、功率、线缆、配电计算 |
| 🎭 演出管理 | 6 | Cue设计、时间轴、节目单 |
| 🤖 AI辅助 | 4 | AI灯光/编程/舞美/故障诊断 |

## 快捷键

- `Ctrl+K` — 搜索工具
- `Ctrl+B` — 切换侧栏抽屉
- `Ctrl+Q` — 退出

## 项目结构

```
├── launcher.py          # 图形启动器
├── Common/              # 共享库 (ui, themes, widgets, utils)
├── Tools/               # 42个工具
├── Config/              # 配置和主题
├── Libraries/           # 灯具库、颜色库、GOBO库
└── tests/               # 单元测试
```

## 版本

v2.0.0 — 详见 [CHANGELOG.md](CHANGELOG.md)
