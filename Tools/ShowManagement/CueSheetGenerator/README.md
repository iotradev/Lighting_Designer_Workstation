# 节目单生成器 (CueSheetGenerator)

**版本:** 1.0.0

## 功能

- 输入演出信息：名称、日期、场地、灯光设计
- 模板化Cue Sheet：Cue编号、页码、动作、灯光状态描述、时机/渐变、备注
- 可编辑表格：添加、删除、上移、下移Cue行
- 从ShowManager项目文件加载Cue数据
- 预览面板：实时查看格式化输出
- 导出为CSV、HTML（可打印）和纯文本格式

## 使用方法

```bash
python main.py
```

## 导出格式

- **CSV**: 带表头的CSV文件，可用Excel打开
- **HTML**: 带样式的网页文件，可直接打印
- **TXT**: 纯文本对齐格式

## 依赖

- Python 3.10+
- PySide6 >= 6.5.0
