# Changelog

All notable changes to Lighting Designer Workstation will be documented in this file.

## [1.0.0] - 2026-06-22

### Added
- Phase 1: 完整基础框架 (Common/)
  - GrandMA3 风格深色主题系统 (dark.json / light.json)
  - 统一主窗口基类 (BaseToolWindow)
    - 菜单栏、工具栏、状态栏、日志窗口、项目管理器
    - 窗口布局记忆、自动保存、拖放支持
  - 项目管理系统 (JSON格式)
  - 统一日志系统 (文件+窗口输出)
  - 配置管理系统 (settings.json)
  - 通用UI组件库 (DMX滑条、LED表、通道网格、颜色色块、搜索框等)
  - 插件加载框架
- Phase 2: 核心MVP工具
  - BPMAnalyzer - BPM自动检测与实时分析
  - MIDIMonitor - MIDI监听与日志
  - MIDISender - MIDI发送与控制面板
  - DMXCalculator - DMX地址/通道/Universe计算
  - FixtureLibrary - 灯具数据库管理
  - StagePlotDesigner - 灯位图绘制
- 一键打包脚本 (build_all.bat / build_all.ps1)
- 工具启动器
- 根目录 README.md
