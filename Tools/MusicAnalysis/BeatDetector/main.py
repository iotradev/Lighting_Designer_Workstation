"""
节拍检测工具 - BeatDetector
音频WAV文件节拍检测、强弱拍分析、小节划分、时间戳导出
"""
import sys
import os
from pathlib import Path

# 添加Common目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'Common'))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QGroupBox, QSpinBox, QDoubleSpinBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QSplitter, QComboBox, QMessageBox,
    QProgressBar, QSizePolicy, QScrollArea
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QLinearGradient, QBrush

from ui.base_window import BaseToolWindow
from beat_engine import BeatEngine, BeatAnalysisResult, Beat


class BeatAnalysisThread(QThread):
    """后台分析线程"""
    finished = Signal(object)  # BeatAnalysisResult
    error = Signal(str)
    progress = Signal(int)

    def __init__(self, filepath, beats_per_bar, sensitivity):
        super().__init__()
        self.filepath = filepath
        self.beats_per_bar = beats_per_bar
        self.sensitivity = sensitivity

    def run(self):
        try:
            self.progress.emit(10)
            engine = BeatEngine()
            self.progress.emit(30)
            result = engine.detect_beats(
                self.filepath,
                beats_per_bar=self.beats_per_bar,
                sensitivity=self.sensitivity
            )
            self.progress.emit(100)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class BeatTimelineCanvas(QWidget):
    """节拍时间线画布 - 用QPainter绘制节拍可视化"""

    def __init__(self):
        super().__init__()
        self.result: BeatAnalysisResult = None
        self.setMinimumHeight(200)
        self.setMinimumWidth(400)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._scroll_offset = 0.0  # 秒

    def set_result(self, result: BeatAnalysisResult):
        self.result = result
        self._scroll_offset = 0.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # 背景
        painter.fillRect(0, 0, w, h, QColor(30, 30, 40))

        if not self.result or not self.result.beats:
            painter.setPen(QColor(120, 120, 120))
            painter.setFont(QFont("Microsoft YaHei", 11))
            painter.drawText(0, 0, w, h, Qt.AlignCenter, "请加载音频文件并开始分析")
            painter.end()
            return

        beats = self.result.beats
        duration = self.result.duration
        if duration <= 0:
            duration = beats[-1].timestamp + 0.5

        # 时间范围 (显示全部)
        time_start = 0.0
        time_end = duration
        time_range = time_end - time_start if time_end > time_start else 1.0

        margin_left = 60
        margin_right = 20
        margin_top = 30
        margin_bottom = 40
        draw_w = w - margin_left - margin_right
        draw_h = h - margin_top - margin_bottom

        if draw_w <= 0 or draw_h <= 0:
            painter.end()
            return

        def time_to_x(t):
            return margin_left + int((t - time_start) / time_range * draw_w)

        # 绘制时间轴
        axis_y = margin_top + draw_h
        painter.setPen(QPen(QColor(100, 100, 120), 1))
        painter.drawLine(margin_left, axis_y, margin_left + draw_w, axis_y)

        # 时间刻度
        tick_interval = 1.0
        if time_range > 60:
            tick_interval = 10.0
        elif time_range > 20:
            tick_interval = 5.0
        elif time_range > 5:
            tick_interval = 1.0
        else:
            tick_interval = 0.5

        painter.setPen(QColor(150, 150, 170))
        painter.setFont(QFont("Consolas", 8))
        t = 0.0
        while t <= time_end:
            x = time_to_x(t)
            if margin_left <= x <= margin_left + draw_w:
                painter.drawLine(x, axis_y, x, axis_y + 5)
                label = f"{t:.1f}s"
                painter.drawText(x - 15, axis_y + 8, 30, 15, Qt.AlignCenter, label)
            t += tick_interval

        # 绘制小节背景 (交替色)
        current_bar = -1
        bar_start_x = margin_left
        for beat in beats:
            if beat.bar_number != current_bar:
                if current_bar != -1 and current_bar % 2 == 0:
                    bx = time_to_x(beat.timestamp)
                    painter.fillRect(bar_start_x, margin_top, bx - bar_start_x, draw_h,
                                     QColor(35, 35, 48))
                bar_start_x = time_to_x(beat.timestamp)
                current_bar = beat.bar_number
        # 最后一个小节
        if current_bar != -1 and current_bar % 2 == 0:
            painter.fillRect(bar_start_x, margin_top,
                             margin_left + draw_w - bar_start_x, draw_h,
                             QColor(35, 35, 48))

        # 绘制节拍竖线 (高度=强度)
        for beat in beats:
            x = time_to_x(beat.timestamp)
            if x < margin_left or x > margin_left + draw_w:
                continue

            # 高度 = 强度
            line_h = int(draw_h * beat.strength * 0.85)
            y_top = axis_y - line_h

            if beat.is_downbeat:
                # 强拍 - 暖色粗线
                color = QColor(255, 180, 50)
                pen_width = 3
            else:
                # 弱拍 - 冷色细线
                color = QColor(80, 180, 255)
                pen_width = 1

            pen = QPen(color, pen_width)
            painter.setPen(pen)
            painter.drawLine(x, y_top, x, axis_y)

            # 强拍标记数字
            if beat.is_downbeat:
                painter.setPen(QColor(255, 220, 100))
                painter.setFont(QFont("Consolas", 7))
                painter.drawText(x - 8, margin_top - 2, 16, 12, Qt.AlignCenter,
                                 str(beat.bar_number))

        # 图例
        legend_x = margin_left + 10
        legend_y = margin_top + 5
        painter.setPen(QPen(QColor(255, 180, 50), 3))
        painter.drawLine(legend_x, legend_y + 6, legend_x + 20, legend_y + 6)
        painter.setPen(QColor(200, 200, 200))
        painter.setFont(QFont("Microsoft YaHei", 8))
        painter.drawText(legend_x + 25, legend_y, 60, 14, Qt.AlignLeft, "强拍")

        painter.setPen(QPen(QColor(80, 180, 255), 1))
        painter.drawLine(legend_x + 85, legend_y + 6, legend_x + 105, legend_y + 6)
        painter.setPen(QColor(200, 200, 200))
        painter.drawText(legend_x + 110, legend_y, 60, 14, Qt.AlignLeft, "弱拍")

        painter.end()


class BeatDetectorWindow(BaseToolWindow):
    """节拍检测工具主窗口"""

    def __init__(self):
        super().__init__(
            tool_name="beat_detector",
            tool_title="节拍检测工具",
            version="1.0.0",
            width=1100,
            height=750
        )

        self.result: BeatAnalysisResult = None
        self.current_file: str = ""
        self.analysis_thread: BeatAnalysisThread = None

        self._build_ui()

    def _build_ui(self):
        """构建界面"""
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(6)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # ===== 顶部: 文件加载区 =====
        file_group = QGroupBox("音频文件")
        file_layout = QHBoxLayout(file_group)

        self.file_label = QLabel("未加载文件")
        self.file_label.setStyleSheet("color: #aaa; padding: 4px;")
        file_layout.addWidget(self.file_label, 1)

        self.btn_load = QPushButton("📂 加载WAV文件")
        self.btn_load.setMinimumWidth(120)
        self.btn_load.clicked.connect(self._on_load_file)
        file_layout.addWidget(self.btn_load)

        main_layout.addWidget(file_group)

        # ===== 分析参数 =====
        param_group = QGroupBox("分析参数")
        param_layout = QHBoxLayout(param_group)

        param_layout.addWidget(QLabel("每小节拍数:"))
        self.spin_bpb = QSpinBox()
        self.spin_bpb.setRange(2, 8)
        self.spin_bpb.setValue(4)
        self.spin_bpb.setMinimumWidth(60)
        param_layout.addWidget(self.spin_bpb)

        param_layout.addSpacing(15)
        param_layout.addWidget(QLabel("灵敏度:"))
        self.spin_sensitivity = QDoubleSpinBox()
        self.spin_sensitivity.setRange(0.1, 1.0)
        self.spin_sensitivity.setValue(0.5)
        self.spin_sensitivity.setSingleStep(0.1)
        self.spin_sensitivity.setMinimumWidth(70)
        param_layout.addWidget(self.spin_sensitivity)

        param_layout.addSpacing(15)
        self.btn_analyze = QPushButton("▶ 开始分析")
        self.btn_analyze.setMinimumWidth(100)
        self.btn_analyze.setStyleSheet("QPushButton { background-color: #2a6; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px; } QPushButton:hover { background-color: #3b7; }")
        self.btn_analyze.clicked.connect(self._on_analyze)
        self.btn_analyze.setEnabled(False)
        param_layout.addWidget(self.btn_analyze)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(150)
        self.progress_bar.setMaximumHeight(18)
        self.progress_bar.setVisible(False)
        param_layout.addWidget(self.progress_bar)

        param_layout.addStretch()
        main_layout.addWidget(param_group)

        # ===== 中部: 节拍可视化 + 统计面板 =====
        splitter = QSplitter(Qt.Horizontal)

        # 节拍画布
        canvas_group = QGroupBox("节拍时间线")
        canvas_layout = QVBoxLayout(canvas_group)
        self.canvas = BeatTimelineCanvas()
        canvas_layout.addWidget(self.canvas)
        splitter.addWidget(canvas_group)

        # 右侧统计面板
        stats_widget = QWidget()
        stats_layout = QVBoxLayout(stats_widget)
        stats_layout.setContentsMargins(4, 4, 4, 4)

        stats_group = QGroupBox("分析统计")
        sg_layout = QVBoxLayout(stats_group)

        self.lbl_bpm = self._stat_label("BPM", "--")
        self.lbl_beat_count = self._stat_label("节拍数", "--")
        self.lbl_bar_count = self._stat_label("小节数", "--")
        self.lbl_duration = self._stat_label("时长", "--")
        self.lbl_time_sig = self._stat_label("拍号", "--")
        self.lbl_downbeats = self._stat_label("强拍数", "--")

        sg_layout.addWidget(self.lbl_bpm)
        sg_layout.addWidget(self.lbl_beat_count)
        sg_layout.addWidget(self.lbl_bar_count)
        sg_layout.addWidget(self.lbl_downbeats)
        sg_layout.addWidget(self.lbl_duration)
        sg_layout.addWidget(self.lbl_time_sig)
        sg_layout.addStretch()

        stats_layout.addWidget(stats_group)

        # 导出按钮
        export_group = QGroupBox("导出")
        eg_layout = QVBoxLayout(export_group)

        self.btn_export_csv = QPushButton("📄 导出CSV")
        self.btn_export_csv.setEnabled(False)
        self.btn_export_csv.clicked.connect(self._export_csv)
        eg_layout.addWidget(self.btn_export_csv)

        self.btn_export_ma = QPushButton("🎭 导出MA时间码")
        self.btn_export_ma.setEnabled(False)
        self.btn_export_ma.clicked.connect(self._export_ma)
        eg_layout.addWidget(self.btn_export_ma)

        stats_layout.addWidget(export_group)
        stats_layout.addStretch()

        splitter.addWidget(stats_widget)
        splitter.setSizes([700, 250])

        main_layout.addWidget(splitter, 1)

        # ===== 底部: 节拍表格 =====
        table_group = QGroupBox("节拍详情")
        table_layout = QVBoxLayout(table_group)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["序号", "时间戳(秒)", "强度", "小节", "类型"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setMaximumHeight(200)
        table_layout.addWidget(self.table)

        main_layout.addWidget(table_group)

        self.set_central_content(main_widget)

    def _stat_label(self, name, value):
        """创建统计标签"""
        label = QLabel(f"<b>{name}:</b> {value}")
        label.setStyleSheet("font-size: 13px; padding: 3px 0;")
        return label

    def _on_load_file(self):
        """加载WAV文件"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "选择音频文件", "",
            "音频文件 (*.wav *.mp3 *.flac *.ogg *.aac);;所有文件 (*)"
        )
        if filepath:
            self.current_file = filepath
            filename = os.path.basename(filepath)
            self.file_label.setText(f"📎 {filename}")
            self.file_label.setStyleSheet("color: #4af; padding: 4px;")
            self.btn_analyze.setEnabled(True)

    def _on_analyze(self):
        """开始分析"""
        if not self.current_file:
            return

        self.btn_analyze.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.analysis_thread = BeatAnalysisThread(
            self.current_file,
            self.spin_bpb.value(),
            self.spin_sensitivity.value()
        )
        self.analysis_thread.progress.connect(self.progress_bar.setValue)
        self.analysis_thread.finished.connect(self._on_analysis_done)
        self.analysis_thread.error.connect(self._on_analysis_error)
        self.analysis_thread.start()

    def _on_analysis_done(self, result: BeatAnalysisResult):
        """分析完成"""
        self.result = result
        self.progress_bar.setVisible(False)
        self.btn_analyze.setEnabled(True)

        # 更新统计
        self.lbl_bpm.setText(f"<b>BPM:</b> {result.bpm}")
        self.lbl_beat_count.setText(f"<b>节拍数:</b> {result.beat_count}")
        self.lbl_bar_count.setText(f"<b>小节数:</b> {result.bar_count}")
        self.lbl_duration.setText(f"<b>时长:</b> {result.duration:.2f}秒")
        ts = result.time_signature
        self.lbl_time_sig.setText(f"<b>拍号:</b> {ts[0]}/{ts[1]}")
        downbeats = sum(1 for b in result.beats if b.is_downbeat)
        self.lbl_downbeats.setText(f"<b>强拍数:</b> {downbeats}")

        # 更新画布
        self.canvas.set_result(result)

        # 更新表格
        self._fill_table(result.beats)

        # 启用导出
        has_data = len(result.beats) > 0
        self.btn_export_csv.setEnabled(has_data)
        self.btn_export_ma.setEnabled(has_data)

        if result.beats:
            self.logger.info(f"分析完成: {result.bpm} BPM, {result.beat_count} 个节拍, {result.bar_count} 个小节")
        else:
            QMessageBox.warning(self, "分析结果", "未检测到节拍，请尝试调整灵敏度。")

    def _on_analysis_error(self, error_msg: str):
        """分析出错"""
        self.progress_bar.setVisible(False)
        self.btn_analyze.setEnabled(True)
        QMessageBox.critical(self, "分析错误", f"节拍检测失败:\n{error_msg}")
        self.logger.error(f"分析失败: {error_msg}")

    def _fill_table(self, beats):
        """填充节拍表格"""
        self.table.setRowCount(len(beats))
        for i, beat in enumerate(beats):
            self.table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.table.setItem(i, 1, QTableWidgetItem(f"{beat.timestamp:.4f}"))

            # 强度用百分比显示
            item = QTableWidgetItem(f"{beat.strength * 100:.1f}%")
            if beat.is_downbeat:
                item.setBackground(QColor(100, 80, 20, 100))
            self.table.setItem(i, 2, item)

            self.table.setItem(i, 3, QTableWidgetItem(str(beat.bar_number)))

            type_item = QTableWidgetItem("强拍" if beat.is_downbeat else "弱拍")
            if beat.is_downbeat:
                type_item.setForeground(QColor(255, 180, 50))
            else:
                type_item.setForeground(QColor(80, 180, 255))
            self.table.setItem(i, 4, type_item)

    def _export_csv(self):
        """导出CSV"""
        if not self.result or not self.result.beats:
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self, "导出CSV", "beats.csv",
            "CSV文件 (*.csv)"
        )
        if not filepath:
            return

        try:
            with open(filepath, 'w', encoding='utf-8-sig') as f:
                f.write("beat_number,timestamp,strength,bar_number,is_downbeat\n")
                for i, beat in enumerate(self.result.beats):
                    f.write(f"{i+1},{beat.timestamp:.4f},{beat.strength:.4f},"
                            f"{beat.bar_number},{1 if beat.is_downbeat else 0}\n")
            QMessageBox.information(self, "导出成功", f"已导出到:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", str(e))

    def _export_ma(self):
        """导出MA时间码格式"""
        if not self.result or not self.result.beats:
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self, "导出MA时间码", "beats_ma.txt",
            "文本文件 (*.txt)"
        )
        if not filepath:
            return

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# MA Timecode - BPM: {self.result.bpm}\n")
                f.write(f"# Time Signature: {self.result.time_signature[0]}/{self.result.time_signature[1]}\n")
                f.write(f"# Duration: {self.result.duration:.2f}s\n")
                f.write(f"# Beats: {self.result.beat_count}, Bars: {self.result.bar_count}\n")
                f.write("#\n")
                f.write("# Format: TC | Bar.Beat | Strength | Type\n")
                f.write("#" + "=" * 60 + "\n")

                for beat in self.result.beats:
                    # 转换为 MA 时间码格式 (HH:MM:SS:FF @ 30fps)
                    tc = self._seconds_to_timecode(beat.timestamp)
                    beat_type = "DOWN" if beat.is_downbeat else "    "
                    f.write(f"{tc}  {beat.bar_number:3d}.{beat.beat_number}  "
                            f"{beat.strength:5.1%}  {beat_type}\n")

            QMessageBox.information(self, "导出成功", f"已导出MA时间码到:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", str(e))

    def closeEvent(self, event):
        """关闭窗口时清理线程"""
        if self.analysis_thread and self.analysis_thread.isRunning():
            self.analysis_thread.terminate()
            self.analysis_thread.wait(2000)
        super().closeEvent(event)

    @staticmethod
    def _seconds_to_timecode(seconds: float, fps: int = 30) -> str:
        """秒数转时间码 HH:MM:SS:FF"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        f = int((seconds % 1) * fps)
        return f"{h:02d}:{m:02d}:{s:02d}:{f:02d}"


def main():
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 深色主题
    from PySide6.QtGui import QPalette, QColor
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(45, 45, 55))
    palette.setColor(QPalette.WindowText, QColor(220, 220, 220))
    palette.setColor(QPalette.Base, QColor(35, 35, 45))
    palette.setColor(QPalette.AlternateBase, QColor(45, 45, 55))
    palette.setColor(QPalette.Text, QColor(220, 220, 220))
    palette.setColor(QPalette.Button, QColor(55, 55, 65))
    palette.setColor(QPalette.ButtonText, QColor(220, 220, 220))
    palette.setColor(QPalette.Highlight, QColor(60, 120, 200))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)

    win = BeatDetectorWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    import traceback
    try:

        main()
    except Exception as _e:
        traceback.print_exc()
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            _app = QApplication.instance() or QApplication([])
            QMessageBox.critical(None, "BeatDetector - 启动错误",
                f"{type(_e).__name__}: {_e}\n\n请检查日志文件。")
        except Exception:
            pass
