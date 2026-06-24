# Changelog

## v2.1.0 (2026-06-24)

### Bug 修复
- **BPM分析器**: 修复 `_load_worker` / `_analyze_worker` / `_curve_worker` 未初始化导致首次使用崩溃
- **启动器**: 修复 Signal 在类外赋值，移至 CategoryCard 类体内声明
- **启动器**: 修复损坏的中文注释 (编码问题 `??????` → `高DPI适配`)
- **启动器**: 统一 BPMAnalyzer 的 `__main__` 入口为 `launcher_utils.run_tool` 模式

### 架构改进
- **path_setup.py**: 重写为统一的 `ensure_common_path()` 工具，42 个工具共用
- **42 个工具**: 消除重复的 `sys.path.insert(Path(...).parent.parent.parent.parent / 'Common')` 模板
- **ConfigManager**: 所有读写操作加 `_lock` 保护，修复多线程数据竞争
- **BaseToolWindow**: 移除未实现的撤销/重做菜单 stub；新增自动备份定时器
- **Common/__init__.py**: 添加去重守卫，避免 sys.path 重复插入

### 部署修复
- **启动工作站.bat**: 依赖安装从 `pip install PySide6 numpy` 改为 `pip install -r requirements.txt`
- **启动工作站.vbs**: 窗口改为可见 (style=1)，错误时暂停显示而非静默失败

### 项目清理
- 删除死代码 `path_setup.py`（已重写为实用工具）

## v2.0.0 (2026-06-23)

### 启动器 (launcher.py)
- 侧栏抽屉化：Ctrl+B 切换展开/收起，只显示图标
- 侧栏分类过滤：点击分类只显示该分类，再点恢复全部
- 底部栏从蓝色改为深色主题
- 工具栏默认隐藏（菜单栏已有功能）
- 卡片等高显示，统一字号
- 全局样式表优化（间距、圆角、颜色）

### 时间码生成器 (TimecodeGenerator)
- 布局重构：上下排列，每行不拥挤
- SpinBox 宽度优化，箭头样式修复
- 音频播放修复：generator prime + 按需返回 framecount
- 播放进度条：可拖动 seek，实时时间显示
- MTC 日志改为终端风格彩色 HTML 显示
- 支持音频 + MTC 同时运行

### 全局样式 (stylesheet.py)
- SpinBox 上下箭头样式：明确按钮区域、hover 效果
- 状态栏从蓝色改为深色
- 所有控件间距优化
- 滚动条更细 (12px → 10px)

### 主题 (Config/Themes/dark.json)
- 背景色统一为 #18181b
- 边框色统一为 #2a2a2d
- 输入框背景统一为 #222225
- 状态栏背景改为 #1a1a1d

### 项目清理
- 删除 53 个 __pycache__ 目录
- 删除构建文件、测试文件、旧安装包
- Releases/ 清空
- 项目大小 284MB → 32MB
