# 舞台平面图设计器 (StagePlotDesigner)

## 概述
舞台平面图设计器是一款基于 PySide6 (Qt) 的专业舞台灯光布局设计工具，提供直观的画布编辑界面，支持多种舞台元素的创建、编辑和导出。

## 功能特性
- **画布设计**: 基于 QGraphicsScene/QGraphicsView 的矢量画布
- **多种元素**: 舞台矩形、桁架线、灯具位置、观众区域、侧幕区域、文本标签、自由线条
- **拖放操作**: 支持元素拖放移动
- **属性编辑**: 实时编辑选中元素的位置、尺寸、旋转、标签和颜色
- **网格与吸附**: 可切换的网格背景和网格吸附功能
- **缩放平移**: 鼠标滚轮缩放、中键平移
- **导出功能**: 导出为 PNG/SVG 格式
- **存档功能**: 保存/加载布局为 JSON 文件

## 界面布局
```
+----------------+---------------------------+------------------+
|   元素面板     |        画布区域           |   属性编辑器     |
|                |                           |                  |
| [添加舞台]     |      (网格背景)           | X: [___]         |
| [添加桁架]     |                           | Y: [___]         |
| [添加灯具]     |      舞台元素可拖拽       | 宽度: [___]      |
| [文本标签]     |      缩放、平移            | 高度: [___]      |
| [添加线条]     |                           | 旋转: [___]      |
| [观众区域]     |                           | 标签: [___]      |
| [侧幕区域]     |                           | 颜色: [选择]     |
+----------------+---------------------------+------------------+
```

## 工具栏
- 🔍+ 放大 / 🔍- 缩小
- ⬜ 适应视图
- ▦ 网格 (开关)
- 🧲 吸附 (开关)
- 📷 导出PNG
- 📄 导出SVG
- 📂 打开布局
- 💾 保存布局
- 🗑 删除选中

## 快捷键
- `+` / `=`: 放大
- `-`: 缩小
- `Delete`: 删除选中元素
- 中键拖拽: 平移画布
- 滚轮: 缩放

## 文件结构
```
StagePlotDesigner/
├── main.py              # 主程序 (继承 BaseToolWindow)
├── stage_elements.py    # 舞台元素类定义
├── requirements.txt     # 依赖列表
└── README.md            # 本文档
```

## 元素类型
| 类型 | 类 | 描述 |
|------|------|------|
| stage | StageElement | 舞台矩形 (QGraphicsRectItem) |
| truss | TrussElement | 桁架线 (QGraphicsLineItem) |
| fixture | FixtureElement | 灯具位置 (QGraphicsEllipseItem) |
| text | TextElement | 文本标签 (QGraphicsTextItem) |
| line | LineElement | 自由线条 (QGraphicsLineItem) |
| audience | AudienceElement | 观众区域 (QGraphicsRectItem) |
| wing | WingElement | 侧幕区域 (QGraphicsRectItem) |

## 依赖
- PySide6 >= 6.5.0
- PySide6-Addons >= 6.5.0 (SVG 导出支持)

## 启动
```bash
python main.py
```
