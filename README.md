# Lighting Designer Workstation

舞台灯光设计工作站 — 42 个专业灯光工具，GrandMA3 风格深色主题

## 快速启动

```bash
# 安装依赖
pip install -r requirements.txt

# 启动
python launcher.py
```

或双击 `启动工作站.bat`（首次运行自动安装依赖）。

## 工具分类 (42 个)

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

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+K` | 搜索工具 |
| `Ctrl+B` | 切换侧栏抽屉 |
| `Ctrl+Q` | 退出 |

## 项目结构

```
├── launcher.py          # 图形启动器
├── path_setup.py        # 统一 sys.path 初始化
├── Common/              # 共享库
│   ├── ui/              #   基础窗口框架
│   ├── themes/          #   主题与样式表
│   ├── widgets/         #   通用控件
│   ├── utils/           #   工具函数
│   ├── config/          #   配置管理
│   ├── log_system/      #   日志系统
│   └── project/         #   项目管理
├── Tools/               # 42 个工具 (9 个分类)
├── Config/              # 主题配置
├── Libraries/           # 灯具库、颜色库、GOBO库
├── Assets/              # 图标、音效等资源
├── Templates/           # 项目模板
├── tests/               # 单元测试
└── scripts/             # 辅助脚本
```

## 开发

```bash
# 初始化开发环境
powershell -ExecutionPolicy Bypass -File scripts\bootstrap.ps1

# 运行测试
pytest tests/ -v

# 语法检查
python scripts/check_tools.py
```

## 依赖

| 包 | 版本 | 用途 |
|----|------|------|
| PySide6 | >=6.5,<7 | Qt6 GUI 框架 |
| numpy | >=1.26,<2 | 音频信号处理 |
| miniaudio | >=1.55,<2 | 多格式音频解码 |
| python-rtmidi | >=1.5,<2 | MIDI I/O |

## 版本

v2.1.0 — 详见 [CHANGELOG.md](CHANGELOG.md)

## 许可证

[MIT License](LICENSE)
