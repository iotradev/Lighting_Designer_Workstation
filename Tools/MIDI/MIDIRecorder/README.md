# MIDI录制器 (MIDIRecorder)

## 功能
- 从MIDI输入设备录制MIDI消息（支持自动检测设备）
- 实时显示录制的消息列表（表格形式）
- 播放/暂停/停止回放录制的消息
- 导出为CSV格式
- 导出为标准MIDI文件(.mid)
- 时间显示（分:秒.毫秒）
- Record/Stop/Play/Pause 控制按钮

## 使用方法
1. 连接MIDI设备（软件会自动检测）
2. 点击"录制"开始录制MIDI消息
3. 点击"停止"结束录制
4. 点击"播放"回放录制的消息
5. 点击"导出CSV"或"导出MIDI"保存文件

## MIDI消息类型支持
- Note On / Note Off
- Control Change
- Program Change
- Pitch Bend

## 依赖
- Python 3.9+
- PySide6
- python-rtmidi（可选，用于MIDI设备输入）

## 安装
```bash
pip install -r requirements.txt
```

## 运行
```bash
python main.py
```
