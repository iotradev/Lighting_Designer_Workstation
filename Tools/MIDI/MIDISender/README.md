# MIDI发送器 (MIDISender)

MIDI消息发送工具，支持音符发送、CC控制、自定义消息构建和脚本执行。

## 功能特性

- **音符发送**: 可视化钢琴键盘，支持Note On/Off，可调力度和通道
- **CC控制**: 16个CC滑块（CC0-CC15），实时控制
- **消息构建**: 手动输入十六进制MIDI消息，预设库快速发送
- **脚本执行**: 批量发送MIDI消息序列，支持延时控制

## 界面布局

- **Note发送**: 钢琴键盘 + 力度滑块 + 通道选择
- **CC控制**: 16个垂直滑块，对应CC0-CC15
- **消息构建**: 十六进制输入 + 预设下拉菜单 + 解析预览
- **脚本**: 脚本编辑器 + 执行/停止按钮

## 快捷操作

- **Panic**: 紧急关闭所有通道所有音符
- **All Notes Off**: 关闭当前通道所有音符
- **重置CC**: 将所有CC滑块归位到64

## 脚本格式

每行一条MIDI命令：
```
note_on <通道> <音符> <力度>
note_off <通道> <音符> [力度]
cc <通道> <CC号> <值>
program_change <通道> <程序号>
raw <十六进制字节...>
sleep <秒数>
# 这是注释
```

示例脚本：
```midi
# C大调音阶
note_on 1 60 100
sleep 0.3
note_off 1 60
sleep 0.1
note_on 1 62 100
sleep 0.3
note_off 1 62
```

## 依赖

- Python 3.8+
- PySide6
- python-rtmidi (可选，无则使用日志桩模式)

## 安装

```bash
pip install -r requirements.txt
```

## 使用

```bash
python main.py
```

## 注意事项

- 如未安装python-rtmidi，工具仍可运行，但MIDI消息仅记录到日志
- 点击钢琴键盘发送Note On，松开发送Note Off
- Panic按钮会发送全通道全音符的Note Off和All Sound Off
- 脚本执行在后台线程，不会阻塞UI
