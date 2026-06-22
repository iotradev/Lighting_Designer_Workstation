# DMX计算器

DMX地址计算、Universe规划与冲突检测工具，为舞台灯光设计师提供便捷的DMX地址管理方案。

## 功能特性

### 地址计算
- 输入起始地址 (1-512) 和通道数量
- 自动计算结束地址、所属 Universe
- 检测跨 Universe 溢出警告

### Universe规划
- 灯具列表管理：添加/移除灯具（名称、起始通道、通道数）
- 16×32 可视化通道网格（512通道）
- 颜色编码：绿色=空闲，橙色=已占用，红色=冲突
- 支持切换查看不同 Universe

### 快速转换
- 全局地址 → Universe + 通道：输入全局地址 (1-32768)，转换为 Universe 和通道号
- Universe + 通道 → 全局地址：输入 Universe 和通道号，转换为全局地址

## 运行方式

```bash
cd D:/Lighting_Designer_Workstation/Tools/DMX/DMXCalculator
python main.py
```

## 依赖

- Python 3.10+
- PySide6
- Lighting Designer Workstation Common 库

## DMX 基础知识

- 每个 Universe 最多 512 个通道
- 全局地址 = Universe × 512 + 通道
- Universe 编号从 0 开始
- 通道编号从 1 开始

## 版本

v1.0.0
