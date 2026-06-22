# 音乐结构分析器 (MusicStructureAnalyzer)

## 功能
- 加载WAV音频文件
- 基于能量和频谱特征分析音乐结构段落
- 识别 Intro/Verse/Chorus/Bridge/Drop/Outro 段落类型
- 可视化显示结构时间线（彩色色块）
- 为每个段落生成灯光设计建议
- 导出结构分析结果到CSV

## 使用方法
1. 点击"加载音频"选择WAV文件
2. 点击"分析结构"进行分析
3. 查看时间线、段落详情和灯光建议
4. 点击"导出CSV"保存结果

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
