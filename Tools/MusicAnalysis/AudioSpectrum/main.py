"""
AudioSpectrum - 音频频谱分析工具
实时FFT频谱显示、瀑布图、频段能量监测
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'Common'))
from ui.base_window import BaseToolWindow

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog,
    QLabel, QComboBox, QGroupBox, QSlider, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QLinearGradient, QFont

from spectrum_engine import SpectrumEngine, FREQUENCY_BANDS


# 频段颜色
BAND_COLORS = [
    QColor(128, 0, 255),    # Sub-bass - 紫
    QColor(0, 0, 255),      # Bass - 蓝
    QColor(0, 200, 255),    # Low-mid - 青
    QColor(0, 255, 0),      # Mid - 绿
    QColor(255, 255, 0),    # High-mid - 黄
    QColor(255, 128, 0),    # High - 橙
    QColor(255, 0, 0),      # Ultra-high - 红
]


class SpectrumCanvas(QWidget):
    """频谱显示画布"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(200)
        self._frequencies = None
        self._magnitudes = None
        self._peak_freq = 0.0
        self._min_db = -80
        self._max_db = 0

    def update_spectrum(self, frequencies, magnitudes, peak_freq):
        self._frequencies = frequencies
        self._magnitudes = magnitudes
        self._peak_freq = peak_freq
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        # 背景
        painter.fillRect(0, 0, w, h, QColor(20, 20, 30))

        if self._frequencies is None or self._magnitudes is None:
            painter.setPen(QColor(100, 100, 100))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "请加载音频文件")
            painter.end()
            return

        freqs = self._frequencies
        mags = self._magnitudes
        n = len(freqs)

        # 绘制网格线
        painter.setPen(QPen(QColor(50, 50, 60), 1))
        for db in range(self._min_db, self._max_db + 1, 10):
            y = h - int((db - self._min_db) / (self._max_db - self._min_db) * h)
            painter.drawLine(0, y, w, y)
            painter.drawText(4, y - 2, f"{db}dB")

        # 频谱条
        bar_width = max(1, w / n * 2)
        gradient = QLinearGradient(0, h, 0, 0)
        gradient.setColorAt(0.0, QColor(0, 100, 255))
        gradient.setColorAt(0.5, QColor(0, 255, 100))
        gradient.setColorAt(1.0, QColor(255, 50, 50))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(gradient)

        # 只绘制可听频段 (20Hz~20kHz)
        for i in range(1, n):
            if freqs[i] < 20 or freqs[i] > 20000:
                continue
            # 对数频率映射
            import math
            log_min = math.log10(20)
            log_max = math.log10(20000)
            log_freq = math.log10(max(freqs[i], 20))
            x = int((log_freq - log_min) / (log_max - log_min) * w)

            db = max(self._min_db, min(self._max_db, mags[i]))
            bar_h = int((db - self._min_db) / (self._max_db - self._min_db) * h)

            painter.drawRect(x, h - bar_h, max(2, int(bar_width)), bar_h)

        # 峰值频率标注
        painter.setPen(QPen(QColor(255, 255, 0), 1))
        painter.setFont(QFont("Arial", 10))
        painter.drawText(10, 16, f"峰值频率: {self._peak_freq:.1f} Hz")

        painter.end()


class WaterfallCanvas(QWidget):
    """频谱瀑布图画布"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(150)
        self._waterfall_data = None
        self._sample_rate = 44100
        self._fft_size = 2048

    def update_waterfall(self, waterfall_data, sample_rate, fft_size):
        self._waterfall_data = waterfall_data
        self._sample_rate = sample_rate
        self._fft_size = fft_size
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        w, h = self.width(), self.height()
        painter.fillRect(0, 0, w, h, QColor(10, 10, 20))

        if self._waterfall_data is None or len(self._waterfall_data) == 0:
            painter.setPen(QColor(100, 100, 100))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "等待音频数据...")
            painter.end()
            return

        data = self._waterfall_data
        rows, cols = data.shape

        import math
        log_min = math.log10(20)
        log_max = math.log10(20000)
        freqs = [i * self._sample_rate / self._fft_size for i in range(cols)]

        # 逐行绘制
        row_h = max(1, h / rows)
        for r in range(rows):
            y = int(r * row_h)
            for c in range(1, cols):
                f = freqs[c]
                if f < 20 or f > 20000:
                    continue
                log_f = math.log10(max(f, 20))
                x = int((log_f - log_min) / (log_max - log_min) * w)

                # dB -> 颜色映射
                db = data[r, c]
                norm = max(0, min(1, (db + 80) / 80))  # -80~0dB -> 0~1

                # 冷->暖 颜色映射
                if norm < 0.25:
                    color = QColor(0, 0, int(norm * 4 * 200))
                elif norm < 0.5:
                    t = (norm - 0.25) * 4
                    color = QColor(0, int(t * 255), 200)
                elif norm < 0.75:
                    t = (norm - 0.5) * 4
                    color = QColor(int(t * 255), 255, int((1 - t) * 200))
                else:
                    t = (norm - 0.75) * 4
                    color = QColor(255, int((1 - t) * 200), 0)

                painter.fillRect(x, y, max(2, int(w / cols * 1.5)), max(1, int(row_h)), color)

        # 坐标标注
        painter.setPen(QColor(150, 150, 150))
        painter.setFont(QFont("Arial", 8))
        for freq in [50, 100, 200, 500, 1000, 2000, 5000, 10000]:
            if 20 <= freq <= 20000:
                x = int((math.log10(freq) - log_min) / (log_max - log_min) * w)
                painter.drawText(x, h - 4, f"{freq}")

        painter.end()


class BandMetersPanel(QWidget):
    """频段能量仪表面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(180)
        self._band_energies = [0.0] * 7

    def update_energies(self, energies):
        self._band_energies = energies
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        painter.fillRect(0, 0, w, h, QColor(25, 25, 35))

        n_bands = len(FREQUENCY_BANDS)
        margin = 10
        bar_w = max(20, (w - margin * 2) // n_bands - 6)
        gap = 6
        total_w = n_bands * bar_w + (n_bands - 1) * gap
        start_x = (w - total_w) // 2

        for i, (name, f_low, f_high) in enumerate(FREQUENCY_BANDS):
            x = start_x + i * (bar_w + gap)
            energy = self._band_energies[i] if i < len(self._band_energies) else 0.0
            energy = max(0.0, min(1.0, energy))

            bar_h = int(energy * (h - 40))
            y_top = h - 20 - bar_h

            # 柱体渐变
            grad = QLinearGradient(x, h - 20, x, y_top)
            c = BAND_COLORS[i]
            grad.setColorAt(0.0, QColor(c.red() // 3, c.green() // 3, c.blue() // 3))
            grad.setColorAt(1.0, c)
            painter.setBrush(grad)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(x, y_top, bar_w, bar_h)

            # 能量值
            painter.setPen(QColor(200, 200, 200))
            painter.setFont(QFont("Arial", 7))
            painter.drawText(x, y_top - 4, bar_w, 12,
                             Qt.AlignmentFlag.AlignCenter, f"{energy:.0%}")

            # 频段名称
            painter.setPen(QColor(150, 150, 150))
            painter.setFont(QFont("Arial", 7))
            painter.drawText(x, h - 18, bar_w, 16,
                             Qt.AlignmentFlag.AlignCenter, name)

        painter.end()


class AudioSpectrumWindow(BaseToolWindow):
    """音频频谱分析工具主窗口"""

    def __init__(self):
        super().__init__(
            tool_name="AudioSpectrum",
            tool_title="音频频谱分析",
            version="1.0.0",
            width=1200,
            height=900,
        )

        self.engine = SpectrumEngine(fft_size=2048)
        self.is_playing = False

        # 定时器驱动分析循环 (~30fps)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)

        self._build_ui()
        self.logger.info("音频频谱分析工具初始化完成")

    def _build_ui(self):
        """构建主界面"""
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # ---- 工具栏 ----
        toolbar = QHBoxLayout()

        self.btn_load = QPushButton("📂 加载音频")
        self.btn_load.setFixedWidth(100)
        self.btn_load.clicked.connect(self._on_load)
        toolbar.addWidget(self.btn_load)

        self.btn_play = QPushButton("▶ 播放")
        self.btn_play.setFixedWidth(80)
        self.btn_play.clicked.connect(self._on_play_toggle)
        toolbar.addWidget(self.btn_play)

        self.btn_stop = QPushButton("⏹ 停止")
        self.btn_stop.setFixedWidth(80)
        self.btn_stop.clicked.connect(self._on_stop)
        toolbar.addWidget(self.btn_stop)

        toolbar.addWidget(QLabel("  FFT大小:"))
        self.combo_fft = QComboBox()
        self.combo_fft.addItems(["1024", "2048", "4096"])
        self.combo_fft.setCurrentIndex(1)
        self.combo_fft.currentTextChanged.connect(self._on_fft_changed)
        toolbar.addWidget(self.combo_fft)

        self.lbl_file = QLabel("  未加载文件")
        self.lbl_file.setStyleSheet("color: #aaa;")
        toolbar.addWidget(self.lbl_file)

        toolbar.addStretch()

        self.lbl_peak = QLabel("峰值: -- Hz")
        self.lbl_peak.setStyleSheet("color: #ff0; font-weight: bold;")
        toolbar.addWidget(self.lbl_peak)

        layout.addLayout(toolbar)

        # ---- 频谱画布 ----
        spec_group = QGroupBox("频谱显示")
        spec_layout = QVBoxLayout(spec_group)
        self.spectrum_canvas = SpectrumCanvas()
        spec_layout.addWidget(self.spectrum_canvas)
        layout.addWidget(spec_group, stretch=3)

        # ---- 瀑布图 ----
        waterfall_group = QGroupBox("频谱瀑布图")
        waterfall_layout = QVBoxLayout(waterfall_group)
        self.waterfall_canvas = WaterfallCanvas()
        waterfall_layout.addWidget(self.waterfall_canvas)
        layout.addWidget(waterfall_group, stretch=2)

        # ---- 频段能量仪表 ----
        meters_group = QGroupBox("频段能量")
        meters_layout = QVBoxLayout(meters_group)
        self.band_meters = BandMetersPanel()
        meters_layout.addWidget(self.band_meters)
        layout.addWidget(meters_group, stretch=1)

        self.set_central_content(root)

    def _on_load(self):
        """加载WAV文件"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "选择音频文件", "", "音频文件 (*.wav *.mp3 *.flac *.ogg *.aac);;WAV文件 (*.wav);;所有文件 (*)"
        )
        if not filepath:
            return
        try:
            info = self.engine.load_audio(filepath)
            name = Path(filepath).name
            dur = info["duration"]
            self.lbl_file.setText(
                f"  {name} | {info['sample_rate']}Hz | {dur:.1f}s"
            )
            self.spectrum_canvas.update_spectrum(None, None, 0)
            self.waterfall_canvas.update_waterfall(None, 0, 0)
            self.band_meters.update_energies([0] * 7)
            self.logger.info(f"已加载: {name} ({info['sample_rate']}Hz, {dur:.1f}s)")
        except Exception as e:
            self.logger.error(f"加载失败: {e}")

    def _on_play_toggle(self):
        """播放/暂停切换"""
        if self.engine.audio_data is None:
            return
        if self.is_playing:
            self.is_playing = False
            self._timer.stop()
            self.btn_play.setText("▶ 播放")
        else:
            self.is_playing = True
            self._timer.start(33)  # ~30fps
            self.btn_play.setText("⏸ 暂停")

    def _on_stop(self):
        """停止播放"""
        self.is_playing = False
        self._timer.stop()
        self.engine.reset()
        self.btn_play.setText("▶ 播放")
        self.lbl_peak.setText("峰值: -- Hz")
        self.spectrum_canvas.update_spectrum(None, None, 0)
        self.waterfall_canvas.update_waterfall(None, 0, 0)
        self.band_meters.update_energies([0] * 7)

    def _on_fft_changed(self, text):
        """FFT大小变更"""
        try:
            size = int(text)
            self.engine.set_fft_size(size)
            self.waterfall_canvas._fft_size = size
            self.logger.info(f"FFT大小已设为 {size}")
        except ValueError:
            pass

    def _on_tick(self):
        """分析定时回调"""
        frame = self.engine.process_frame()
        if frame is None:
            return

        # 更新频谱画布
        self.spectrum_canvas.update_spectrum(
            frame.frequencies, frame.magnitudes, frame.peak_frequency
        )

        # 更新峰值显示
        self.lbl_peak.setText(f"峰值: {frame.peak_frequency:.0f} Hz")

        # 更新瀑布图
        wf = self.engine.get_waterfall_data()
        self.waterfall_canvas.update_waterfall(
            wf, self.engine.sample_rate, self.engine.fft_size
        )

        # 更新频段能量
        self.band_meters.update_energies(frame.band_energies)

    def closeEvent(self, event):
        """关闭窗口时停止定时器"""
        self._timer.stop()
        super().closeEvent(event)


if __name__ == "__main__":
    import traceback
    try:

        from PySide6.QtWidgets import QApplication
        app = QApplication(sys.argv)
        win = AudioSpectrumWindow()
        win.show()
        sys.exit(app.exec())
    except Exception as _e:
        traceback.print_exc()
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            _app = QApplication.instance() or QApplication([])
            QMessageBox.critical(None, "AudioSpectrum - 启动错误",
                f"{type(_e).__name__}: {_e}\n\n请检查日志文件。")
        except Exception:
            pass
