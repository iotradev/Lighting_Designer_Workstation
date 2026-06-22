# DMX测试器 (DMXTester) v1.0.0

512通道DMX输出测试工具，用于舞台灯光DMX信号测试与故障排查。

## 功能

### 通道测试
- 单通道设置 (1-512, 值 0-255)
- 通道范围批量设置
- 全部归零 (Blackout) / 全部满值 (Full)

### 自动测试
- **Chase测试**: 逐通道顺序扫描，可调速度 (10-1000ms)
- **Ramp测试**: 单通道渐变 0→255→0，可调速度 (5-200ms)

### Universe视图
- 512通道 16×32 网格实时显示
- 颜色编码: 绿(低值)→黄(中值)→红(高值)
- 10Hz 自动刷新

### 故障检测
- 自动执行: 全部255 → 全部0 → 检测卡死通道
- 结果表格显示故障通道号、卡死值

## 运行

```bash
cd Tools/DMX/DMXTester
pip install -r requirements.txt
python main.py
```

## 依赖

- Python 3.9+
- PySide6 6.5.0+
- Lighting Designer Workstation Common 模块
