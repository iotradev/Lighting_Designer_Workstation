# ArtNetMonitor - Art-Net 监听器

灯光设计工作站 - Art-Net 网络 DMX 数据监听与分析工具。

## 功能

- 监听 Art-Net 数据包（UDP 端口 6454）
- 解析 ArtDmx 数据包（opcode 0x5000）：ProtVer, Sequence, Physical, SubUni, Net, Data
- 显示活跃 Universe 列表
- 选中 Universe 查看 512 通道 DMX 数据（16×32 柱状图网格）
- 每个 Universe 的数据包速率统计（包/秒）
- 网络状态指示（绑定地址、端口、错误信息）
- 自动发现网络上的 Art-Net 节点（ArtPoll）
- 数据包日志记录

## 使用

```bash
python main.py
```

## 依赖

- PySide6 >= 6.5.0
- Python >= 3.10

## Art-Net 协议

Art-Net 是用于传输 DMX512 数据的以太网协议，基于 UDP 广播。
本工具监听 UDP 端口 6454（Art-Net 标准端口），解析符合 Art-Net IV 规范的数据包。
