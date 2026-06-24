# 贡献指南

感谢你对 Lighting Designer Workstation 的关注！

## 开发环境

```bash
# 1. 克隆仓库
git clone https://github.com/lighting-designer/workstation.git
cd workstation

# 2. 初始化环境
powershell -ExecutionPolicy Bypass -File scripts\bootstrap.ps1

# 3. 启动
.\.venv\Scripts\python.exe launcher.py
```

## 项目约定

- 使用中文注释和提交信息
- 遵循 PEP 8 代码规范
- 每个工具位于 `Tools/<分类>/<工具名>/main.py`
- 继承 `BaseToolWindow` 作为工具窗口基类
- 使用 `import path_setup; path_setup.ensure_common_path(__file__)` 初始化路径

## 提交规范

```
类型: 简短描述

类型: feat / fix / docs / refactor / test / chore
示例: feat: 新增灯具库搜索功能
```

## 测试

```bash
# 运行全部测试
pytest tests/ -v

# 语法检查
python scripts/check_tools.py
```
