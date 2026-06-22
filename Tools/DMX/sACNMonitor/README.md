# sACNMonitor - sACN (E1.31) 数据包监听器

## 功能特性
- 监听 sACN (E1.31) 多播数据包 (UDP 5568)
- 解析 sACN 完整协议层: Root Layer / Framing Layer / DMP Layer
- 显示数据源名称、Universe、优先级、序列号
- DMX 512通道数据可视化 (16x32 条形图 + 数值表格)
- 活跃数据源列表，按优先级显示
- 实时数据包速率计数器
- 数据包日志记录

## 界面布局
- **顶部**: 开始/停止按钮 + Universe选择 + 多播地址 + 状态指示灯 + 速率
- **左侧**: 活跃数据源列表 (源名称, Universe, 优先级)
- **中间**: DMX通道数据网格 (16x32 条形图) + 通道数值表
- **底部**: 数据包日志 (时间戳, 数据源, Universe, 优先级, 序列号)

## 使用方法
```bash
python main.py
```

选择 Universe 编号后点击 "开始监听"，工具将自动加入对应的多播组接收 sACN 数据包。

## 协议说明
sACN (streaming ACN) 基于 E1.31 标准，使用 UDP 多播传输 DMX512 数据。
多播地址范围: 239.255.x.x (由 Universe 编号计算)
端口: 5568

## 依赖
- PySide6 >= 6.5.0
