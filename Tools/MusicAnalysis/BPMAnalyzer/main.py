# -*- coding: utf-8 -*-
"""
BPM分析器 - 音乐节拍检测工具
支持WAV文件的BPM自动检测、波形显示、BPM曲线分析
"""
import sys
from pathlib import Path

# 添加Common库路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'Common'))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QCheckBox, QGroupBox, QGridLayout, QSplitter, QSizePolicy, QSpinBox,
    QDoubleSpinBox, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QLinearGradient, QDragEnterEvent, QDropEvent

from ui.base_window import BaseToolWindow
from bpm_engine import BPMEngine


class WaveformWidget(QWidget):
    """波形显示组件 - 使用QPainter绘制"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.waveform_data = []
        self.onset_times = []
        self.duration = 0.0
        self.sample_rate = 0
        self.setMinimumHeight(120)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
    def set_data(self, waveform_data, onset_times=None, duration=0.0, sample_rate=0):
        """设置波形数据"""
        self.waveform_data = waveform_data or []
        self.onset_times = onset_times or []
        self.duration = duration
        self.sample_rate = sample_rate
        self.update()
    
    def paintEvent(self, event):
        """绘制波形"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        # 背景
        painter.fillRect(0, 0, w, h, QColor(25, 25, 30))
        
        # 绘制网格线
        painter.setPen(QPen(QColor(60, 60, 70), 1))
        # 水平中心线
        painter.drawLine(0, h // 2, w, h // 2)
        # 垂直网格
        for i in range(1, 10):
            x = int(w * i / 10)
            painter.drawLine(x, 0, x, h)
        
        # 水平网格
        for i in range(1, 4):
            y = int(h * i / 4)
            painter.drawLine(0, y, w, y)
        
        if not self.waveform_data:
            painter.setPen(QColor(120, 120, 130))
            font = QFont("Microsoft YaHei", 12)
            painter.setFont(font)
            painter.drawText(0, 0, w, h, Qt.AlignmentFlag.AlignCenter, "请加载音频文件")
            painter.end()
            return
        
        # 绘制波形
        n = len(self.waveform_data)
        pen = QPen(QColor(0, 200, 100), 1.5)
        painter.setPen(pen)
        
        mid_y = h // 2
        scale_y = (h // 2) * 0.85
        
        points = []
        for i, val in enumerate(self.waveform_data):
            x = int(i * w / n)
            y = int(mid_y - val * scale_y)
            points.append((x, y))
        
        # 连线绘制
        for i in range(len(points) - 1):
            painter.drawLine(points[i][0], points[i][1], points[i+1][0], points[i+1][1])
        
        # 绘制镜像
        pen_mirror = QPen(QColor(0, 150, 80, 100), 1)
        painter.setPen(pen_mirror)
        for i in range(len(points) - 1):
            y1 = 2 * mid_y - points[i][1]
            y2 = 2 * mid_y - points[i+1][1]
            painter.drawLine(points[i][0], y1, points[i+1][0], y2)
        
        # 绘制起始点标记
        if self.onset_times and self.duration > 0:
            pen_onset = QPen(QColor(255, 80, 80, 180), 1.5)
            painter.setPen(pen_onset)
            for t in self.onset_times:
                x = int(t / self.duration * w)
                painter.drawLine(x, 0, x, h)
        
        # 绘制时间刻度
        painter.setPen(QColor(150, 150, 160))
        font = QFont("Consolas", 8)
        painter.setFont(font)
        if self.duration > 0:
            for i in range(0, int(self.duration) + 1, max(1, int(self.duration / 10))):
                x = int(i / self.duration * w)
                painter.drawText(x + 2, h - 4, f"{i}s")
        
        painter.end()


class BPMCurveWidget(QWidget):
    """BPM曲线显示组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.times = []
        self.bpms = []
        self.setMinimumHeight(100)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    
    def set_data(self, times, bpms):
        """设置BPM曲线数据"""
        self.times = times or []
        self.bpms = bpms or []
        self.update()
    
    def paintEvent(self, event):
        """绘制BPM曲线"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        # 背景
        painter.fillRect(0, 0, w, h, QColor(25, 25, 30))
        
        if not self.bpms or len(self.bpms) < 2:
            painter.setPen(QColor(120, 120, 130))
            font = QFont("Microsoft YaHei", 10)
            painter.setFont(font)
            painter.drawText(0, 0, w, h, Qt.AlignmentFlag.AlignCenter, "BPM曲线将在分析后显示")
            painter.end()
            return
        
        # 计算范围
        min_bpm = max(0, min(self.bpms) - 10)
        max_bpm = max(self.bpms) + 10
        min_t = self.times[0]
        max_t = self.times[-1]
        
        if max_t == min_t:
            max_t = min_t + 1
        
        bpm_range = max_bpm - min_bpm if max_bpm > min_bpm else 1
        
        margin = 40
        
        # 绘制网格
        painter.setPen(QPen(QColor(50, 50, 60), 1))
        font = QFont("Consolas", 8)
        painter.setFont(font)
        
        # BPM刻度
        for bpm_val in range(int(min_bpm), int(max_bpm) + 1, 10):
            y = int(h - margin - (bpm_val - min_bpm) / bpm_range * (h - margin * 2))
            painter.drawLine(margin, y, w - margin, y)
            painter.setPen(QColor(150, 150, 160))
            painter.drawText(2, y + 4, f"{bpm_val}")
            painter.setPen(QPen(QColor(50, 50, 60), 1))
        
        # 绘制曲线
        pen = QPen(QColor(255, 180, 0), 2)
        painter.setPen(pen)
        
        for i in range(len(self.times) - 1):
            x1 = int(margin + (self.times[i] - min_t) / (max_t - min_t) * (w - margin * 2))
            y1 = int(h - margin - (self.bpms[i] - min_bpm) / bpm_range * (h - margin * 2))
            x2 = int(margin + (self.times[i+1] - min_t) / (max_t - min_t) * (w - margin * 2))
            y2 = int(h - margin - (self.bpms[i+1] - min_bpm) / bpm_range * (h - margin * 2))
            painter.drawLine(x1, y1, x2, y2)
        
        # 绘制数据点
        painter.setPen(QPen(QColor(255, 220, 100), 1))
        painter.setBrush(QBrush(QColor(255, 180, 0)))
        for i in range(len(self.times)):
            x = int(margin + (self.times[i] - min_t) / (max_t - min_t) * (w - margin * 2))
            y = int(h - margin - (self.bpms[i] - min_bpm) / bpm_range * (h - margin * 2))
            painter.drawEllipse(x - 3, y - 3, 6, 6)
        
        # 时间刻度
        painter.setPen(QColor(150, 150, 160))
        painter.setFont(font)
        step = max(1, int((max_t - min_t) / 8))
        for t_val in range(int(min_t), int(max_t) + 1, step):
            x = int(margin + (t_val - min_t) / (max_t - min_t) * (w - margin * 2))
            painter.drawText(x - 10, h - 8, f"{t_val}s")
        
        painter.end()


class BPMDisplayWidget(QWidget):
    """BPM大数字显示组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bpm_value = 0.0
        self.confidence = 0.0
        self.setMinimumWidth(200)
        self.setMinimumHeight(200)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
    
    def set_bpm(self, bpm, confidence=0.0):
        """设置BPM值"""
        self.bpm_value = bpm
        self.confidence = confidence
        self.update()
    
    def paintEvent(self, event):
        """绘制BPM显示"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        # 渐变背景
        gradient = QLinearGradient(0, 0, 0, h)
        gradient.setColorAt(0.0, QColor(30, 30, 40))
        gradient.setColorAt(1.0, QColor(20, 20, 28))
        painter.fillRect(0, 0, w, h, gradient)
        
        # BPM数字
        if self.bpm_value > 0:
            # BPM值
            font = QFont("Consolas", 48, QFont.Weight.Bold)
            painter.setFont(font)
            painter.setPen(QColor(0, 220, 130))
            painter.drawText(0, 0, w, h // 2 + 20, Qt.AlignmentFlag.AlignCenter, f"{self.bpm_value:.1f}")
            
            # "BPM" 标签
            font_small = QFont("Microsoft YaHei", 16)
            painter.setFont(font_small)
            painter.setPen(QColor(180, 180, 190))
            painter.drawText(0, h // 2 + 10, w, 30, Qt.AlignmentFlag.AlignCenter, "BPM")
            
            # 置信度指示
            if self.confidence > 0:
                conf_color = QColor(0, int(200 * self.confidence), 0) if self.confidence > 0.5 else QColor(200, 200, 0)
                bar_w = int((w - 40) * self.confidence)
                painter.fillRect(20, h - 40, w - 40, 12, QColor(40, 40, 50))
                painter.fillRect(20, h - 40, bar_w, 12, conf_color)
                
                font_tiny = QFont("Consolas", 8)
                painter.setFont(font_tiny)
                painter.setPen(QColor(150, 150, 160))
                painter.drawText(20, h - 45, f"置信度: {self.confidence * 100:.0f}%")
        else:
            font = QFont("Microsoft YaHei", 14)
            painter.setFont(font)
            painter.setPen(QColor(100, 100, 110))
            painter.drawText(0, 0, w, h, Qt.AlignmentFlag.AlignCenter, "等待\n分析...")
        
        painter.end()


class BPMAnalyzerWindow(BaseToolWindow):
    """BPM分析器主窗口"""
    
    def __init__(self):
        super().__init__(
            tool_name="BPMAnalyzer",
            tool_title="BPM分析器",
            version="1.0.0",
            width=1200,
            height=800
        )
        
        # BPM引擎
        self.engine = BPMEngine()
        self.current_file = None
        self.realtime_mode = False
        self.realtime_timer = QTimer(self)
        self.realtime_timer.timeout.connect(self._realtime_tick)
        
        # 构建UI
        self._build_ui()
        
        # 添加工具栏按钮
        self.toolbar.addSeparator()
        self.toolbar.addAction("🎵 加载音频", self._load_file)
        self.toolbar.addAction("📊 分析BPM", self._analyze)
        self.toolbar.addAction("📈 BPM曲线", self._compute_bpm_curve)
        self.toolbar.addAction("💾 导出CSV", self._export_csv)
        
        self.logger.info("BPM分析器已就绪")
    
    def _build_ui(self):
        """构建UI布局"""
        central = QWidget()
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(6)
        main_layout.setContentsMargins(8, 8, 8, 8)
        
        # === 顶部控制区 ===
        top_group = QGroupBox("控制面板")
        top_layout = QHBoxLayout(top_group)
        
        btn_load = QPushButton("📂 加载音频文件")
        btn_load.setMinimumHeight(36)
        btn_load.clicked.connect(self._load_file)
        top_layout.addWidget(btn_load)
        
        self.file_label = QLabel("未加载文件")
        self.file_label.setStyleSheet("color: #aaa; padding: 4px;")
        top_layout.addWidget(self.file_label, 1)
        
        top_layout.addSpacing(20)
        
        # 分析参数
        top_layout.addWidget(QLabel("最小BPM:"))
        self.min_bpm_spin = QSpinBox()
        self.min_bpm_spin.setRange(30, 100)
        self.min_bpm_spin.setValue(60)
        self.min_bpm_spin.valueChanged.connect(lambda v: setattr(self.engine, 'min_bpm', v))
        top_layout.addWidget(self.min_bpm_spin)
        
        top_layout.addWidget(QLabel("最大BPM:"))
        self.max_bpm_spin = QSpinBox()
        self.max_bpm_spin.setRange(100, 300)
        self.max_bpm_spin.setValue(200)
        self.max_bpm_spin.valueChanged.connect(lambda v: setattr(self.engine, 'max_bpm', v))
        top_layout.addWidget(self.max_bpm_spin)
        
        btn_analyze = QPushButton("🔍 分析BPM")
        btn_analyze.setMinimumHeight(36)
        btn_analyze.clicked.connect(self._analyze)
        top_layout.addWidget(btn_analyze)
        
        self.realtime_check = QCheckBox("实时分析")
        self.realtime_check.toggled.connect(self._toggle_realtime)
        top_layout.addWidget(self.realtime_check)
        
        main_layout.addWidget(top_group)
        
        # === 中间区域 ===
        mid_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧: 波形显示
        left_group = QGroupBox("波形显示")
        left_layout = QVBoxLayout(left_group)
        self.waveform_widget = WaveformWidget()
        left_layout.addWidget(self.waveform_widget)
        mid_splitter.addWidget(left_group)
        
        # 右侧: BPM显示 + 统计
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # BPM显示
        bpm_group = QGroupBox("BPM 检测结果")
        bpm_layout = QVBoxLayout(bpm_group)
        self.bpm_display = BPMDisplayWidget()
        bpm_layout.addWidget(self.bpm_display)
        right_layout.addWidget(bpm_group, 2)
        
        # 统计信息
        stats_group = QGroupBox("统计信息")
        stats_layout = QGridLayout(stats_group)
        
        self.stats_labels = {}
        labels = ['平均BPM', '最小BPM', '最大BPM', '标准差', '分析次数']
        for i, name in enumerate(labels):
            stats_layout.addWidget(QLabel(f"{name}:"), i, 0)
            lbl = QLabel("--")
            lbl.setStyleSheet("color: #00dc82; font-weight: bold;")
            stats_layout.addWidget(lbl, i, 1)
            self.stats_labels[name] = lbl
        
        right_layout.addWidget(stats_group, 1)
        mid_splitter.addWidget(right_widget)
        
        mid_splitter.setStretchFactor(0, 3)
        mid_splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(mid_splitter, 1)
        
        # === 底部: BPM曲线 + 导出 ===
        bottom_group = QGroupBox("BPM 变化曲线")
        bottom_layout = QVBoxLayout(bottom_group)
        
        self.bpm_curve_widget = BPMCurveWidget()
        bottom_layout.addWidget(self.bpm_curve_widget)
        
        btn_row = QHBoxLayout()
        btn_curve = QPushButton("📈 计算BPM曲线")
        btn_curve.clicked.connect(self._compute_bpm_curve)
        btn_row.addWidget(btn_curve)
        
        btn_export = QPushButton("💾 导出CSV")
        btn_export.clicked.connect(self._export_csv)
        btn_row.addWidget(btn_export)
        
        btn_row.addStretch()
        bottom_layout.addLayout(btn_row)
        
        bottom_group.setMaximumHeight(250)
        main_layout.addWidget(bottom_group)
        
        self.set_central_content(central)
    
    def _load_file(self):
        """加载音频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择音频文件",
            str(Path.home()),
            "音频文件 (*.wav *.mp3 *.flac *.aac);;WAV文件 (*.wav);;所有文件 (*)"
        )
        if file_path:
            self._do_load(file_path)
    
    def _do_load(self, file_path):
        """执行加载"""
        self.logger.info(f"加载文件: {file_path}")
        self.status_ready.setText("正在加载...")
        
        result = self.engine.load_audio(file_path)
        
        if result['success']:
            self.current_file = file_path
            self.file_label.setText(f"✓ {Path(file_path).name} ({result['duration']:.1f}秒, {result['sample_rate']}Hz)")
            self.file_label.setStyleSheet("color: #00dc82; padding: 4px;")
            
            # 显示波形
            waveform = self.engine.get_waveform_data(4000)
            self.waveform_widget.set_data(waveform, duration=result['duration'], sample_rate=result['sample_rate'])
            
            self.status_ready.setText("文件已加载")
            self.logger.info(f"加载成功: {result['samples_count']} 采样点, {result['duration']:.2f}秒")
        else:
            self.file_label.setText(f"✗ 加载失败")
            self.file_label.setStyleSheet("color: #ff5050; padding: 4px;")
            QMessageBox.warning(self, "加载失败", result['message'])
            self.logger.error(result['message'])
            self.status_ready.setText("加载失败")
    
    def _analyze(self):
        """分析BPM"""
        if not self.current_file:
            QMessageBox.information(self, "提示", "请先加载音频文件")
            return
        
        self.logger.info("开始BPM分析...")
        self.status_ready.setText("正在分析...")
        
        result = self.engine.detect_bpm()
        
        if result['bpm'] > 0:
            self.bpm_display.set_bpm(result['bpm'], result['confidence'])
            self.logger.info(f"BPM检测结果: {result['bpm']} (置信度: {result['confidence'] * 100:.0f}%)")
            
            # 更新波形上的起始点标记
            waveform = self.engine.get_waveform_data(4000)
            self.waveform_widget.set_data(
                waveform,
                onset_times=result.get('onset_times', []),
                duration=self.engine.duration,
                sample_rate=self.engine.sample_rate
            )
            
            self.status_ready.setText(f"BPM: {result['bpm']}")
        else:
            self.bpm_display.set_bpm(0, 0)
            self.logger.warning("BPM检测失败，未能找到足够的节拍点")
            self.status_ready.setText("分析失败")
    
    def _compute_bpm_curve(self):
        """计算BPM曲线"""
        if not self.current_file:
            QMessageBox.information(self, "提示", "请先加载音频文件")
            return
        
        self.logger.info("计算BPM变化曲线...")
        self.status_ready.setText("正在计算BPM曲线...")
        
        result = self.engine.compute_bpm_curve(window_sec=5.0, hop_sec=1.0)
        
        self.bpm_curve_widget.set_data(result['times'], result['bpms'])
        
        # 更新统计
        stats = self.engine.get_statistics()
        self.stats_labels['平均BPM'].setText(f"{stats['avg']}")
        self.stats_labels['最小BPM'].setText(f"{stats['min']}")
        self.stats_labels['最大BPM'].setText(f"{stats['max']}")
        self.stats_labels['标准差'].setText(f"{stats['std']}")
        self.stats_labels['分析次数'].setText(f"{stats['count']}")
        
        self.status_ready.setText(f"BPM曲线已计算 ({stats['count']}个点)")
        self.logger.info(f"BPM曲线: 平均{stats['avg']}, 范围{stats['min']}-{stats['max']}")
    
    def _export_csv(self):
        """导出CSV"""
        if not self.engine.current_bpm and not self.engine.bpm_history:
            QMessageBox.information(self, "提示", "请先进行BPM分析")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出BPM数据",
            str(Path.home() / "bpm_analysis.csv"),
            "CSV文件 (*.csv)"
        )
        if file_path:
            msg = self.engine.export_csv(file_path)
            self.logger.info(msg)
            self.status_ready.setText("已导出CSV")
    
    def _toggle_realtime(self, checked):
        """切换实时分析模式"""
        self.realtime_mode = checked
        if checked:
            if not self.current_file:
                self.realtime_check.setChecked(False)
                QMessageBox.information(self, "提示", "请先加载音频文件")
                return
            self.realtime_timer.start(2000)  # 每2秒分析一次
            self.logger.info("实时分析模式已开启")
            self.status_ready.setText("实时分析中...")
        else:
            self.realtime_timer.stop()
            self.logger.info("实时分析模式已关闭")
            self.status_ready.setText("就绪")
    
    def _realtime_tick(self):
        """实时分析定时回调"""
        if not self.current_file or self.engine.samples is None:
            return
        
        import random
        # 模拟滑动窗口分析
        t = random.uniform(0, max(0, self.engine.duration - 5))
        result = self.engine.detect_bpm(t, t + 5.0)
        
        if result['bpm'] > 0:
            self.bpm_display.set_bpm(result['bpm'], result['confidence'])
            self.status_ready.setText(f"实时BPM: {result['bpm']}")
    
    def _handle_dropped_file(self, path):
        """处理拖放文件"""
        ext = Path(path).suffix.lower()
        if ext in ['.wav', '.mp3', '.flac', '.aac']:
            self._do_load(path)
        else:
            self.logger.warning(f"不支持的文件格式: {ext}")
            QMessageBox.warning(self, "不支持", f"不支持的文件格式: {ext}\n支持: WAV, MP3, FLAC, AAC")

    def closeEvent(self, event):
        """关闭窗口时停止定时器"""
        self.realtime_timer.stop()
        super().closeEvent(event)


def main():
    """应用入口"""
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    app.setApplicationName("BPM分析器")
    app.setOrganizationName("LightingDesignerWorkstation")
    
    window = BPMAnalyzerWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    import traceback
    try:

        main()
    except Exception as _e:
        traceback.print_exc()
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            _app = QApplication.instance() or QApplication([])
            QMessageBox.critical(None, "BPMAnalyzer - 启动错误",
                f"{type(_e).__name__}: {_e}\n\n请检查日志文件。")
        except Exception:
            pass
