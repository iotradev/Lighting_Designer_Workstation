#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""时间码生成器 - SMPTE时间码与MTC生成工具"""

import sys
import csv
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'Common'))
from ui.base_window import BaseToolWindow

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QFrame, QGridLayout
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor


class TimecodeDisplay(QFrame):
    """大字体时间码显示"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(2)
        self.setMinimumHeight(80)
        self._text = "00:00:00:00"

        layout = QHBoxLayout(self)
        self._label = QLabel(self._text)
        font = QFont("Consolas", 42, QFont.Bold)
        self._label.setFont(font)
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setStyleSheet("color: #00FF00; background-color: #1a1a1a;")
        layout.addWidget(self._label)

    def set_timecode(self, tc_str):
        self._text = tc_str
        self._label.setText(tc_str)

    def set_fps_label(self, fps_text):
        pass  # 可扩展


class TimecodeGenerator(BaseToolWindow):
    """时间码生成器"""

    def __init__(self):
        super().__init__('TimecodeGenerator', '时间码生成器', '1.0.0', 1000, 700)

        self._running = False
        self._fps = 25
        self._speed_multiplier = 1.0
        self._hours = 0
        self._minutes = 0
        self._seconds = 0
        self._frames = 0
        self._tc_log = []

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)

        self._build_ui()
        self.logger.info("时间码生成器已初始化")

    def _build_ui(self):
        central = QWidget()
        self.set_central_content(central)
        layout = QVBoxLayout(central)

        # 时间码显示
        self._tc_display = TimecodeDisplay()
        layout.addWidget(self._tc_display)

        # 设置面板
        settings_layout = QHBoxLayout()

        # FPS设置
        fps_group = QGroupBox("帧率 (FPS)")
        fps_layout = QVBoxLayout(fps_group)
        self._fps_combo = QComboBox()
        self._fps_combo.addItems(["24", "25", "30"])
        self._fps_combo.setCurrentText("25")
        self._fps_combo.currentTextChanged.connect(self._on_fps_changed)
        fps_layout.addWidget(self._fps_combo)
        settings_layout.addWidget(fps_group)

        # 速度控制
        speed_group = QGroupBox("播放速度")
        speed_layout = QVBoxLayout(speed_group)
        speed_btn_layout = QHBoxLayout()
        for label, mult in [("0.5x", 0.5), ("1x", 1.0), ("2x", 2.0)]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(mult == 1.0)
            btn.clicked.connect(lambda checked, m=mult: self._set_speed(m))
            speed_btn_layout.addWidget(btn)
            if mult == 1.0:
                self._speed_btns = []
            self._speed_btns.append(btn) if hasattr(self, '_speed_btns') else None
        speed_layout.addLayout(speed_btn_layout)
        settings_layout.addWidget(speed_group)

        # 手动设置时间码
        set_group = QGroupBox("设置时间码")
        set_layout = QGridLayout(set_group)
        self._set_h = QSpinBox(); self._set_h.setRange(0, 23); self._set_h.setPrefix("时 ")
        self._set_m = QSpinBox(); self._set_m.setRange(0, 59); self._set_m.setPrefix("分 ")
        self._set_s = QSpinBox(); self._set_s.setRange(0, 59); self._set_s.setPrefix("秒 ")
        self._set_f = QSpinBox(); self._set_f.setRange(0, 29); self._set_f.setPrefix("帧 ")
        set_layout.addWidget(self._set_h, 0, 0)
        set_layout.addWidget(self._set_m, 0, 1)
        set_layout.addWidget(self._set_s, 0, 2)
        set_layout.addWidget(self._set_f, 0, 3)
        set_btn = QPushButton("设置")
        set_btn.clicked.connect(self._on_set_timecode)
        set_layout.addWidget(set_btn, 0, 4)
        settings_layout.addWidget(set_group)

        layout.addLayout(settings_layout)

        # 播放控制
        ctrl_layout = QHBoxLayout()
        self._start_btn = QPushButton("▶ 开始")
        self._start_btn.setStyleSheet("font-size: 14px; padding: 8px 20px;")
        self._start_btn.clicked.connect(self._on_start)
        ctrl_layout.addWidget(self._start_btn)

        self._stop_btn = QPushButton("⏹ 停止")
        self._stop_btn.setStyleSheet("font-size: 14px; padding: 8px 20px;")
        self._stop_btn.clicked.connect(self._on_stop)
        self._stop_btn.setEnabled(False)
        ctrl_layout.addWidget(self._stop_btn)

        self._reset_btn = QPushButton("↺ 重置")
        self._reset_btn.setStyleSheet("font-size: 14px; padding: 8px 20px;")
        self._reset_btn.clicked.connect(self._on_reset)
        ctrl_layout.addWidget(self._reset_btn)

        export_btn = QPushButton("导出日志CSV")
        export_btn.clicked.connect(self._on_export)
        ctrl_layout.addWidget(export_btn)

        layout.addLayout(ctrl_layout)

        # MTC消息日志
        log_group = QGroupBox("MTC消息日志")
        log_layout = QVBoxLayout(log_group)
        self._log_table = QTableWidget(0, 4)
        self._log_table.setHorizontalHeaderLabels(["时间", "SMPTE", "MTC消息", "帧数"])
        self._log_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        log_layout.addWidget(self._log_table)
        layout.addWidget(log_group, 1)

        # 速度按钮引用
        self._speed_buttons = []

    def _on_fps_changed(self, text):
        self._fps = int(text)
        self._set_f.setRange(0, self._fps - 1)
        self.logger.info(f"帧率设置为: {self._fps} FPS")

    def _set_speed(self, mult):
        self._speed_multiplier = mult
        self.logger.info(f"速度设置为: {mult}x")

    def _on_set_timecode(self):
        self._hours = self._set_h.value()
        self._minutes = self._set_m.value()
        self._seconds = self._set_s.value()
        self._frames = self._set_f.value()
        self._update_display()

    def _on_start(self):
        self._running = True
        self._start_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        interval = max(1, int(1000 / self._fps / self._speed_multiplier))
        self._timer.setInterval(interval)
        self._timer.start()
        self.logger.info("时间码生成已启动")

    def _on_stop(self):
        self._running = False
        self._timer.stop()
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self.logger.info("时间码生成已停止")

    def _on_reset(self):
        self._on_stop()
        self._hours = self._minutes = self._seconds = self._frames = 0
        self._update_display()

    def _on_tick(self):
        self._frames += 1
        if self._frames >= self._fps:
            self._frames = 0
            self._seconds += 1
            if self._seconds >= 60:
                self._seconds = 0
                self._minutes += 1
                if self._minutes >= 60:
                    self._minutes = 0
                    self._hours = (self._hours + 1) % 24

        self._update_display()
        self._log_timecode()

    def _update_display(self):
        tc = f"{self._hours:02d}:{self._minutes:02d}:{self._seconds:02d}:{self._frames:02d}"
        self._tc_display.set_timecode(tc)

    def _log_timecode(self):
        tc = f"{self._hours:02d}:{self._minutes:02d}:{self._seconds:02d}:{self._frames:02d}"
        total_frames = (self._hours * 3600 + self._minutes * 60 + self._seconds) * self._fps + self._frames

        # MTC消息格式
        mtc_msg = self._generate_mtc_message()

        row = self._log_table.rowCount()
        self._log_table.insertRow(row)
        now = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self._log_table.setItem(row, 0, QTableWidgetItem(now))
        self._log_table.setItem(row, 1, QTableWidgetItem(tc))
        self._log_table.setItem(row, 2, QTableWidgetItem(mtc_msg))
        self._log_table.setItem(row, 3, QTableWidgetItem(str(total_frames)))

        self._tc_log.append({
            'timestamp': now,
            'smpte': tc,
            'mtc': mtc_msg,
            'frames': total_frames
        })

        # 保持日志大小
        if self._log_table.rowCount() > 500:
            self._log_table.removeRow(0)
            self._tc_log.pop(0)

    def _generate_mtc_message(self):
        """生成MTC消息字符串"""
        # MTC quarter frame messages (8 parts)
        hh = self._hours
        mm = self._minutes
        ss = self._seconds
        ff = self._frames
        fps_type = {24: 0, 25: 1, 30: 3}.get(self._fps, 1)

        msg = f"F1:{(fps_type << 5) | (hh & 0x1F):02X} "
        msg += f"F2:{mm:02X} F3:{ss:02X} F4:{ff:02X}"
        return msg

    def _on_export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "导出时间码日志", "timecode_log.csv", "CSV文件 (*.csv)"
        )
        if path:
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=['timestamp', 'smpte', 'mtc', 'frames'])
                writer.writeheader()
                writer.writerows(self._tc_log)
            self.logger.info(f"日志已导出: {path}")


# ─── 入口 ────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = TimecodeGenerator()
    window.show()
    sys.exit(app.exec())
