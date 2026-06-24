"""音乐结构分析器 - 分析音频段落结构并生成灯光建议"""

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
    QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QSplitter, QScrollArea, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QBrush

from engine import MusicStructureEngine, SegmentType, SEGMENT_COLORS


class StructureTimelineWidget(QWidget):
    """结构时间线可视化组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.segments = []
        self.setMinimumHeight(120)

    def set_segments(self, segments):
        self.segments = segments
        self.update()

    def paintEvent(self, event):
        if not self.segments:
            painter = QPainter(self)
            painter.setPen(QColor(150, 150, 150))
            painter.setFont(QFont("Microsoft YaHei", 10))
            painter.drawText(self.rect(), Qt.AlignCenter, "等待加载音频文件...")
            painter.end()
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width() - 20
        h = self.height() - 40
        x_offset = 10
        y_offset = 20

        total_time = self.segments[-1].end_time

        # 绘制标题
        painter.setPen(QColor(200, 200, 200))
        painter.setFont(QFont("Microsoft YaHei", 9, QFont.Bold))
        painter.drawText(x_offset, 15, "结构时间线")

        for seg in self.segments:
            color = SEGMENT_COLORS.get(seg.segment_type, (128, 128, 128))
            x = x_offset + int(seg.start_time / total_time * w)
            seg_w = max(2, int(seg.duration / total_time * w))

            # 绘制色块
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(*color)))
            painter.drawRoundedRect(x, y_offset, seg_w, h - 20, 3, 3)

            # 绘制标签（如果宽度足够）
            if seg_w > 40:
                painter.setPen(QColor(0, 0, 0))
                painter.setFont(QFont("Microsoft YaHei", 8))
                label = f"{seg.segment_type.value}\n{seg.start_time:.1f}s"
                painter.drawText(QRect(x + 2, y_offset + 5, seg_w - 4, h - 30),
                                 Qt.AlignCenter | Qt.TextWordWrap, label)

        painter.end()


class MainWindow(BaseToolWindow):
    def __init__(self):
        super().__init__('MusicStructureAnalyzer', '音乐结构分析器', '1.0.0', 1300, 850)
        self.engine = MusicStructureEngine()
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

        self.btn_analyze = QPushButton("🔍 分析结构")
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

        # 时间线可视化
        timeline_group = QGroupBox("结构时间线")
        timeline_group.setStyleSheet("QGroupBox { color: #ddd; font-weight: bold; }")
        tl_layout = QVBoxLayout(timeline_group)
        self.timeline = StructureTimelineWidget()
        tl_layout.addWidget(self.timeline)
        layout.addWidget(timeline_group)

        # 分割器：左侧表格，右侧灯光建议
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：段落表格
        table_group = QGroupBox("段落详情")
        table_group.setStyleSheet("QGroupBox { color: #ddd; font-weight: bold; }")
        tbl_layout = QVBoxLayout(table_group)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["段落类型", "开始时间", "结束时间", "持续时间", "能量水平", "灯光建议"]
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

        # 右侧：灯光建议
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

        splitter.setSizes([700, 400])
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
            self.logger.error(f"加载音频失败: {e}")

    def _analyze(self):
        try:
            segments = self.engine.analyze_structure()
            self.timeline.set_segments(segments)
            self._populate_table(segments)
            self._generate_suggestions(segments)
            self.btn_export.setEnabled(True)
            self.logger.info(f"分析完成，共 {len(segments)} 个段落")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"分析失败:\n{str(e)}")
            self.logger.error(f"分析失败: {e}")

    def _populate_table(self, segments):
        self.table.setRowCount(len(segments))
        for i, seg in enumerate(segments):
            color = SEGMENT_COLORS.get(seg.segment_type, (128, 128, 128))
            color_str = f"rgb({color[0]},{color[1]},{color[2]})"

            self.table.setItem(i, 0, QTableWidgetItem(seg.segment_type.value))
            self.table.setItem(i, 1, QTableWidgetItem(f"{seg.start_time:.2f}s"))
            self.table.setItem(i, 2, QTableWidgetItem(f"{seg.end_time:.2f}s"))
            self.table.setItem(i, 3, QTableWidgetItem(f"{seg.duration:.2f}s"))
            self.table.setItem(i, 4, QTableWidgetItem(f"{seg.energy_level:.4f}"))
            self.table.setItem(i, 5, QTableWidgetItem(seg.lighting_suggestion))

            for col in range(6):
                item = self.table.item(i, col)
                item.setBackground(QColor(*color))

    def _generate_suggestions(self, segments):
        html = "<div style='color: #ccc; line-height: 1.8;'>"
        html += "<h3 style='color: #ffcc00;'>灯光设计方案</h3>"
        for i, seg in enumerate(segments):
            color = SEGMENT_COLORS.get(seg.segment_type, (128, 128, 128))
            color_hex = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
            html += f"""
            <div style='margin: 8px 0; padding: 8px; background: rgba(255,255,255,0.05); border-left: 4px solid {color_hex}; border-radius: 4px;'>
                <b style='color: {color_hex};'>{seg.segment_type.value}</b>
                <span style='color: #888;'> ({seg.start_time:.1f}s - {seg.end_time:.1f}s)</span><br/>
                <span>{seg.lighting_suggestion}</span>
            </div>
            """
        html += "</div>"
        self.suggest_content.setText(html)

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "导出CSV", "structure_map.csv", "CSV文件 (*.csv)"
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
            QMessageBox.critical(None, "MusicStructureAnalyzer - 启动错误",
                f"{type(_e).__name__}: {_e}\n\n请检查日志文件。")
        except Exception:
            pass
