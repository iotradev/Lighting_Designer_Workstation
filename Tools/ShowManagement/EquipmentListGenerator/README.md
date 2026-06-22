# 设备清单生成器 (EquipmentListGenerator)

灯光项目设备清单管理与导出工具。

## 功能

- 从项目加载灯具或手动添加
- 生成灯具清单（名称、数量、模式、Universe、地址）
- 生成电力分配清单（总功率、按回路分布）
- 生成网络清单（IP地址、ArtNet/sACN节点）
- 导出到CSV和HTML
- 汇总统计（灯具总数、总功率、总重量）

## 使用

```bash
python main.py
```

## 依赖

- Python 3.9+
- PySide6
