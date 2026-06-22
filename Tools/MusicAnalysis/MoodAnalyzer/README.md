# 情绪分析器 (MoodAnalyzer)

## 功能
- 加载WAV音频文件
- 分析音频特征：RMS能量曲线、频谱质心（亮度）、过零率
- 基于能量阈值分类情绪区间：平静/中等/高能量
- QPainter绘制能量曲线图表
- 为每个情绪区间生成灯光设计建议
- 导出情绪时间线到CSV

## 使用方法
1. 点击"加载音频"选择WAV文件
2. 点击"分析情绪"进行分析
3. 查看能量曲线、情绪段落详情和灯光建议
4. 点击"导出CSV"保存结果

## 情绪分类
- **平静 (Calm)**: 低能量，柔和灯光
- **中等 (Medium)**: 中等能量，暖色调流动
- **高能量 (High Energy)**: 高能量，快速变化效果

## 依赖
- Python 3.9+
- PySide6
- NumPy

## 安装
```bash
pip install -r requirements.txt
```

## 运行
```bash
python main.py
```
