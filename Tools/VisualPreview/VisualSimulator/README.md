# 视觉模拟器 (VisualSimulator)

3D 舞台灯光视觉模拟工具，用于预览灯具布置和光束效果。

## 功能特性

- **多种视图模式**: 俯视图、侧视图、等轴测视图
- **舞台建模**: 绘制舞台地板、桁架结构、灯具位置
- **光束模拟**: 彩色锥体光束，带雾气渐变效果
- **灯具控制**: 选择灯具、设置 RGB 颜色、亮度、Pan/Tilt 角度
- **场景管理**: 保存/加载场景为 JSON 格式
- **交互操作**: 鼠标拖拽灯具、滚轮缩放、中键平移

## 界面布局

| 区域 | 内容 |
|------|------|
| 左侧 | 灯具列表（添加/删除/颜色选择/亮度控制） |
| 中央 | 3D 画布（QPainter 坐标变换渲染） |
| 右侧 | 属性面板（颜色 RGB、Pan/Tilt、亮度、光束参数） |
| 工具栏 | 视图切换、网格/光束/雾气开关、缩放、保存/加载 |

## 运行

```bash
cd Tools/VisualPreview/VisualSimulator
pip install -r requirements.txt
python main.py
```

## 文件说明

- `main.py` - 主窗口 UI、交互逻辑、画布渲染
- `simulator_engine.py` - 舞台/灯具数据模型、坐标变换、光束计算
- `requirements.txt` - Python 依赖
