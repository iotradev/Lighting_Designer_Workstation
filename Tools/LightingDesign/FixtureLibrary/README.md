# 灯具库管理工具 (FixtureLibrary)

灯光设计师专用的灯具资料库管理工具，内置20+常见灯具的DMX通道配置。

## 功能特性

- **内置数据库**: 包含 Clay Paky、Robe、Martin、Chauvet、ADJ 等品牌灯具
- **分类浏览**: 按灯具类型分类 - 摇头灯、染色灯、光束灯、图案灯、LED PAR、激光、追光灯
- **搜索过滤**: 支持按名称、制造商、类型搜索
- **完整编辑**: 添加、编辑、删除灯具及其通道模式
- **通道可视化**: 彩色条形图显示通道分配，直观明了
- **导入导出**: JSON格式导入导出，方便数据交换

## 灯具类型

| 类别 | 说明 |
|------|------|
| 摇头灯(Moving Head) | 通用摇头灯 |
| 染色灯(Wash) | 洗墙/染色灯具 |
| 光束灯(Beam) | 光束效果灯 |
| 图案灯(Spot) | 图案投影灯 |
| LED PAR | LED帕灯 |
| 激光(Laser) | 激光投影设备 |
| 追光灯(Follow Spot) | 追光灯 |

## 使用方法

```bash
cd Tools/LightingDesign/FixtureLibrary
python main.py
```

## 通道颜色编码

- 红/绿/蓝/白: RGBW色彩通道
- 青/品红/黄: CMY色彩通道
- Pan/Tilt: 水平/垂直运动
- 调光: 亮度控制
- CTO: 色温调节
- 棱镜/雾化/变焦: 效果通道

## 文件说明

- `main.py` - 主应用程序
- `fixture_data.py` - 内置灯具数据库
- `user_fixtures.json` - 用户自定义灯具（自动生成）
- `requirements.txt` - 依赖项

## 依赖

- Python 3.8+
- PySide6
- Common 库 (ui.base_window.BaseToolWindow)
