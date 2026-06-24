"""情绪分析器 - 分析音频情绪特征并生成灯光建议"""

import sys
from pathlib import Path

try:
    import path_setup
except ImportError:
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location('path_setup', str(Path(__file__).resolve().parent.parent.parent.parent / 'path_setup.py'))
    _mod = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_mod); import sys; sys.modules['path_setup'] = _mod; path_setup = _mod
path_setup.ensure_common_path(__file__)
from ui.base_window import BaseToolWindow

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QGroupBox, QSplitter, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QBrush

from engine import MoodEngine, MoodZone, MOOD_COLORS


class EnergyCurveWidget(QWidget):
    """能量曲线可视化（QPainter绘制）"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.frames = []
        self.setMinimumHeight(200)

    def set_data(self, frames):
        self.frames = frames
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if not self.frames:
            painter.setPen(QColor(150, 150, 150))
            painter.setFont(QFont("Microsoft YaHei", 10))
            painter.drawText(self.rect(), Qt.AlignCenter, "等待加载音频文件...")
            painter.end()
            return

        w = self.width() - 40
        h = self.height() - 60
        x_off = 30
        y_off = 10

        # 绘制背景
        painter.fillRect(x_off, y_off, w, h, QColor(30, 30, 30))

        # 绘制网格线
        painter.setPen(QPen(QColor(60, 60, 60), 1, Qt.DotLine))
        for i in range(5):
            y = y_off + int(i * h / 4)
            painter.drawLine(x_off, y, x_off + w, y)

        # 计算数据范围
        max_e = max(f.rms_energy for f in self.frames) if self.frames else 1.0
        if max_e == 0:
            max_e = 1.0

        # 绘制能量曲线
        points = []
        for i, f in enumerate(self.frames):
            x = x_off + int(i / len(self.frames) * w)
            y = y_off + h - int(f.rms_energy / max_e * h)
            points.append((x, y))

        # 按情绪区间着色绘制
        if len(points) > 1:
            for i in range(len(points) - 1):
                zone = self.frames[i].mood_zone
                color = MOOD_COLORS.get(zone, (128, 128, 128))
                pen = QPen(QColor(*color), 2)
                painter.setPen(pen)
                painter.drawLine(points[i][0], points[i][1],
                                 points[i + 1][0], points[i + 1][1])

        # 绘制X轴标签
        painter.setPen(QColor(150, 150, 150))
        painter.setFont(QFont("Microsoft YaHei", 8))
        total_time = self.frames[-1].time if self.frames else 0
        for i in range(6):
            t = total_time * i / 5
            x = x_off + int(i / 5 * w)
            painter.drawText(x - 15, y_off + h + 15, f"{t:.1f}s")

        # 绘制Y轴标签
        painter.drawText(5, y_off + 10, f"{max_e:.3f}")
        painter.drawText(5, y_off + h, "0.000")

        # 绘制图例
        legend_y = y_off + h + 30
        legend_x = x_off
        for zone in MoodZone:
            color = MOOD_COLORS.get(zone, (128, 128, 128))
            painter.setBrush(QBrush(QColor(*color)))
            painter.setPen(Qt.NoPen)
            painter.drawRect(legend_x, legend_y, 12, 12)
            painter.setPen(QColor(180, 180, 180))
            painter.setFont(QFont("Microsoft YaHei", 8))
            painter.drawText(legend_x + 16, legend_y + 11, zone.value)
            legend_x += 80

        painter.end()


class MainWindow(BaseToolWindow):
    def __init__(self):
        super().__init__('MoodAnalyzer', '情绪分析器', '1.0.0', 1200, 800)
        self.engine = MoodEngine()
        self._build_ui()

    def _build_ui(self):
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # 工具栏
        toolbar = QHBoxLayout()
        self.btn_load = QPushButton("📂 加载音频")
        self.btn_load.setFixedHeight(36)
        self.btn_load.clicked.connect(self._load_audio)

        self.btn_analyze = QPushButton("🔍 分析情绪")
        self.btn_analyze.setFixedHeight(36)
        self.btn_analyze.setEnabled(False)
        self.btn_analyze.clicked.connect(self._analyze)

        self.btn_export = QPushButton("💾 导出CSV")
        self.btn_export.setFixedHeight(36)
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self._export_csv)

        self.lbl_info = QLabel("请加载WAV音频文件")
        self.lbl_info.setStyleSheet("color: #aaa; font-size: 12px;")

        toolbar.addWidget(self.btn_load)
        toolbar.addWidget(self.btn_analyze)
        toolbar.addWidget(self.btn_export)
        toolbar.addStretch()
        toolbar.addWidget(self.lbl_info)
        layout.addLayout(toolbar)

        # 能量曲线
        curve_group = QGroupBox("能量曲线 / 情绪分布")
        curve_group.setStyleSheet("QGroupBox { color: #ddd; font-weight: bold; }")
        cl_layout = QVBoxLayout(curve_group)
        self.energy_curve = EnergyCurveWidget()
        cl_layout.addWidget(self.energy_curve)
        layout.addWidget(curve_group)

        # 统计信息
        self.lbl_stats = QLabel("")
        self.lbl_stats.setStyleSheet("color: #ccc; font-size: 11px; padding: 5px;")
        layout.addWidget(self.lbl_stats)

        # 分割器：表格 + 建议
        splitter = QSplitter(Qt.Horizontal)

        # 段落表格
        table_group = QGroupBox("情绪段落详情")
        table_group.setStyleSheet("QGroupBox { color: #ddd; font-weight: bold; }")
        tbl_layout = QVBoxLayout(table_group)
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["情绪区间", "开始时间", "结束时间", "持续时间", "灯光建议"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setStyleSheet("""
            QTableWidget { background: #1e1e1e; color: #ddd; gridline-color: #333; }
            QHeaderView::section { background: #2d2d2d; color: #ddd; padding: 5px; }
        """)
        tbl_layout.addWidget(self.table)
        splitter.addWidget(table_group)

        # 灯光建议面板
        suggest_group = QGroupBox("灯光设计建议")
        suggest_group.setStyleSheet("QGroupBox { color: #ddd; font-weight: bold; }")
        sug_layout = QVBoxLayout(suggest_group)
        self.suggest_scroll = QScrollArea()
        self.suggest_scroll.setWidgetResizable(True)
        self.suggest_content = QLabel("分析后将在此显示灯光设计建议...")
        self.suggest_content.setWordWrap(True)
        self.suggest_content.setStyleSheet("color: #ccc; padding: 10px; font-size: 12px;")
        self.suggest_content.setAlignment(Qt.AlignTop)
        self.suggest_scroll.setWidget(self.suggest_content)
        sug_layout.addWidget(self.suggest_scroll)
        splitter.addWidget(suggest_group)

        splitter.setSizes([600, 400])
        layout.addWidget(splitter, 1)

        self.set_central_content(main_widget)

    def _load_audio(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择音频文件", "", "音频文件 (*.wav *.mp3 *.flac *.ogg *.aac)"
        )
        if not path:
            return
        try:
            info = self.engine.load_audio(path)
            self.lbl_info.setText(
                f"文件: {Path(path).name} | "
                f"时长: {info['duration']:.1f}秒 | "
                f"采样率: {info['sample_rate']}Hz"
            )
            self.btn_analyze.setEnabled(True)
            self.logger.info(f"已加载音频: {path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载音频失败:\n{str(e)}")

    def _analyze(self):
        try:
            frames = self.engine.analyze()
            self.energy_curve.set_data(frames)

            # 显示统计
            summary = self.engine.get_mood_summary()
            stats_parts = [f"{k}: {v}%" for k, v in summary.items()]
            self.lbl_stats.setText("情绪分布统计: " + " | ".join(stats_parts))

            # 填充表格
            segments = self.engine.get_mood_segments()
            self.table.setRowCount(len(segments))
            for i, seg in enumerate(segments):
                zone = seg["zone"]
                color = MOOD_COLORS.get(zone, (128, 128, 128))
                dur = seg["end_time"] - seg["start_time"]

                self.table.setItem(i, 0, QTableWidgetItem(zone.value))
                self.table.setItem(i, 1, QTableWidgetItem(f"{seg['start_time']:.2f}s"))
                self.table.setItem(i, 2, QTableWidgetItem(f"{seg['end_time']:.2f}s"))
                self.table.setItem(i, 3, QTableWidgetItem(f"{dur:.2f}s"))
                self.table.setItem(i, 4, QTableWidgetItem(seg["suggestion"]))

                for col in range(5):
                    item = self.table.item(i, col)
                    item.setBackground(QColor(*color))

            # 生成建议
            self._generate_suggestions(segments)
            self.btn_export.setEnabled(True)
            self.logger.info(f"情绪分析完成，共 {len(segments)} 个情绪段落")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"分析失败:\n{str(e)}")
            self.logger.error(f"情绪分析失败: {e}")

    def _generate_suggestions(self, segments):
        html = "<div style='color: #ccc; line-height: 1.8;'>"
        html += "<h3 style='color: #ffcc00;'>灯光设计方案</h3>"
        for seg in segments:
            zone = seg["zone"]
            color = MOOD_COLORS.get(zone, (128, 128, 128))
            color_hex = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
            dur = seg["end_time"] - seg["start_time"]
            html += f"""
            <div style='margin: 8px 0; padding: 8px; background: rgba(255,255,255,0.05); border-left: 4px solid {color_hex}; border-radius: 4px;'>
                <b style='color: {color_hex};'>{zone.value}</b>
                <span style='color: #888;'> ({seg['start_time']:.1f}s - {seg['end_time']:.1f}s, {dur:.1f}s)</span><br/>
                <span>{seg['suggestion']}</span>
            </div>
            """
        html += "</div>"
        self.suggest_content.setText(html)

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "导出CSV", "mood_timeline.csv", "CSV文件 (*.csv)"
        )
        if path:
            try:
                self.engine.export_csv(path)
                QMessageBox.information(self, "成功", f"已导出到:\n{path}")
                self.logger.info(f"导出CSV: {path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败:\n{str(e)}")


if __name__ == '__main__':
    import traceback
    try:

        import sys
        from PySide6.QtWidgets import QApplication
        app = QApplication(sys.argv)
        app.setStyleSheet("""
        QMainWindow { background: #1e1e1e; }
        QWidget { background: #1e1e1e; color: #ddd; }
        QPushButton { background: #333; color: #ddd; border: 1px solid #555; border-radius: 4px; padding: 6px 16px; }
        QPushButton:hover { background: #444; }
        QPushButton:disabled { background: #2a2a2a; color: #666; }
        QGroupBox { border: 1px solid #444; border-radius: 4px; margin-top: 10px; padding-top: 15px; }
        """)
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as _e:
        traceback.print_exc()
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            _app = QApplication.instance() or QApplication([])
            QMessageBox.critical(None, "MoodAnalyzer - 启动错误",
                f"{type(_e).__name__}: {_e}\n\n请检查日志文件。")
        except Exception:
            pass
