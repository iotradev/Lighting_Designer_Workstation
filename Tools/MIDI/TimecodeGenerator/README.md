# 时间码生成器 (TimecodeGenerator)

SMPTE时间码与MIDI时间码(MTC)生成工具。

## 功能

- 生成SMPTE时间码 (HH:MM:SS:FF)
- 可配置帧率: 24/25/30 FPS
- 生成MTC (MIDI Timecode) 消息
- 大字体运行时间码显示
- 开始/停止/设置控制
- 速度控制 (1x, 0.5x, 2x)
- 导出时间码日志到CSV

## 使用

```bash
python main.py
```

## 依赖

- Python 3.9+
- PySide6
