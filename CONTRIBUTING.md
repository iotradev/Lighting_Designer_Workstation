# 贡献指南

感谢你对 Lighting Designer Workstation 的关注！

## 开发环境

1. 克隆仓库
2. 运行 `scripts\bootstrap.ps1` 初始化环境
3. 使用 `.venv\Scripts\python.exe launcher.py` 启动

## 代码规范

- 使用中文注释
- 遵循 PEP 8
- 提交前运行 `ruff check .`

## 提交规范

- 类型: feat/fix/docs/refactor/test/chore
- 示例: `feat: 新增灯具库搜索功能`

## 测试

运行 `pytest tests/` 执行基础测试。
