# AI编程助手 (AIProgrammingAssistant)

## 版本
1.0.0

## 简介
基于规则的灯光效果/Chase模式生成工具。快速生成各种DMX灯光效果序列，并提供实时动画预览。

## 功能特性
- **多种效果模式**: Chase(追逐)、Bounce(弹跳)、Random(随机)、Wave(波浪)、Fade(渐变)、Strobe(频闪)
- **参数配置**: 可设置步数、通道数、速度
- **颜色方案**: 10种预设颜色方案（红色系、蓝色系、彩虹等）
- **动画预览**: 实时显示DMX通道值变化的网格动画
- **CUE列表**: 生成的完整CUE序列表格
- **DMX值表**: 每步每个通道的精确DMX值
- **导出功能**: 导出为JSON格式

## 效果模式说明
| 模式 | 说明 |
|------|------|
| Chase | 单灯依次点亮，经典追逐效果 |
| Bounce | 从头到尾再从尾到头来回 |
| Random | 随机点亮指定数量的通道 |
| Wave | 正弦波形效果，平滑过渡 |
| Fade | 全通道渐变效果 |
| Strobe | 全通道同步频闪 |

## 使用方法
```bash
python main.py
```

## 依赖
- Python 3.8+
- PySide6 >= 6.5.0
- Common/ui/base_window.py (BaseToolWindow)

## 目录结构
```
AIProgrammingAssistant/
├── main.py          # 主程序
├── requirements.txt # 依赖
└── README.md        # 说明文档
```
