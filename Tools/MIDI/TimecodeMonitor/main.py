#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""时间码监视器 - SMPTE/MTC时间码监视与漂移检测工具"""

import sys
import time
import math
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'Common'))
from ui.base_window import BaseToolWindow

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QGridLayout, QProgressBar, QTextEdit
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor, QPalette


class StatusIndicator(QFrame):
    """同步状态指示灯"""

    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        self._dot = QLabel("●")
        self._dot.setFixedWidth(20)
        self._dot.setAlignment(Qt.AlignCenter)
        self._label = QLabel(label_text)
        layout.addWidget(self._dot)
        layout.addWidget(self._label)
        self.set_status("offline")

    def set_status(self, status):
        colors = {
            "synced": "#00FF00",
            "drift": "#FFFF00",
            "lost": "#FF0000",
            "offline": "#666666"
        }
        color = colors.get(status, "#666666")
        self._dot.setStyleSheet(f"color: {color}; font-size: 16px;")


class TimecodeMonitor(BaseToolWindow):
    """时间码监视器"""

    def __init__(self):
        super().__init__('TimecodeMonitor', '时间码监视器', '1.0.0', 1000, 700)

        self._simulated_h = 0
        self._simulated_m = 0
        self._simulated_s = 0
        self._simulated_f = 0
        self._sim_fps = 25
        self._sim_running = False

        self._ref_h = 0
        self._ref_m = 0
        self._ref_s = 0
        self._ref_f = 0

        self._history = []
        self._drift_ms = 0.0

        self._build_ui()

        # 模拟时钟定时器
        self._sim_timer = QTimer(self)
        self._sim_timer.timeout.connect(self._on_sim_tick)

        # 参考时钟定时器
        self._ref_timer = QTimer(self)
        self._ref_timer.timeout.connect(self._on_ref_tick)
        self._ref_timer.setInterval(1000 // 25)

        # UI更新定时器
        self._ui_timer = QTimer(self)
        self._ui_timer.timeout.connect(self._update_ui)
        self._ui_timer.setInterval(100)

        self.logger.info("时间码监视器已初始化")

    def _build_ui(self):
        central = QWidget()
        self.set_central_content(central)
        layout = QVBoxLayout(central)

        # 时间码显示区
        tc_layout = QHBoxLayout()

        # 输入时间码
        in_group = QGroupBox("输入时间码")
        in_layout = QVBoxLayout(in_group)
        self._input_tc_label = QLabel("00:00:00:00")
        self._input_tc_label.setFont(QFont("Consolas", 36, QFont.Bold))
        self._input_tc_label.setAlignment(Qt.AlignCenter)
        self._input_tc_label.setStyleSheet("color: #00FF00; background: #1a1a1a; padding: 10px;")
        in_layout.addWidget(self._input_tc_label)
        self._input_type_label = QLabel("类型: SMPTE | FPS: 25")
        self._input_type_label.setAlignment(Qt.AlignCenter)
        in_layout.addWidget(self._input_type_label)
        tc_layout.addWidget(in_group)

        # 参考时间码
        ref_group = QGroupBox("参考时钟")
        ref_layout = QVBoxLayout(ref_group)
        self._ref_tc_label = QLabel("00:00:00:00")
        self._ref_tc_label.setFont(QFont("Consolas", 36, QFont.Bold))
        self._ref_tc_label.setAlignment(Qt.AlignCenter)
        self._ref_tc_label.setStyleSheet("color: #00AAFF; background: #1a1a1a; padding: 10px;")
        ref_layout.addWidget(self._ref_tc_label)
        self._ref_type_label = QLabel("内部参考")
        self._ref_type_label.setAlignment(Qt.AlignCenter)
        ref_layout.addWidget(self._ref_type_label)
        tc_layout.addWidget(ref_group)

        layout.addLayout(tc_layout)

        # 状态面板
        status_layout = QHBoxLayout()

        # 同步状态
        sync_group = QGroupBox("同步状态")
        sync_layout = QVBoxLayout(sync_group)
        self._sync_indicator = StatusIndicator("时钟同步")
        sync_layout.addWidget(self._sync_indicator)
        self._drift_label = QLabel("漂移: 0.0 ms")
        self._drift_label.setFont(QFont("Consolas", 12))
        sync_layout.addWidget(self._drift_label)
        self._drift_bar = QProgressBar()
        self._drift_bar.setRange(-100, 100)
        self._drift_bar.setValue(0)
        self._drift_bar.setFormat("漂移")
        sync_layout.addWidget(self._drift_bar)
        status_layout.addWidget(sync_group)

        # 信号状态
        signal_group = QGroupBox("信号状态")
        signal_layout = QVBoxLayout(signal_group)
        self._signal_indicator = StatusIndicator("信号锁定")
        signal_layout.addWidget(self._signal_indicator)
        self._signal_quality_label = QLabel("质量: --")
        signal_layout.addWidget(self._signal_quality_label)
        self._packet_count_label = QLabel("数据包: 0")
        signal_layout.addWidget(self._packet_count_label)
        status_layout.addWidget(signal_group)

        layout.addLayout(status_layout)

        # 模拟控制
        sim_group = QGroupBox("模拟时间码输入 (演示)")
        sim_layout = QHBoxLayout(sim_group)

        self._sim_start_btn = QPushButton("▶ 开始模拟")
        self._sim_start_btn.clicked.connect(self._on_sim_start)
        sim_layout.addWidget(self._sim_start_btn)

        self._sim_stop_btn = QPushButton("⏹ 停止")
        self._sim_stop_btn.clicked.connect(self._on_sim_stop)
        self._sim_stop_btn.setEnabled(False)
        sim_layout.addWidget(self._sim_stop_btn)

        self._sim_reset_btn = QPushButton("↺ 重置")
        self._sim_reset_btn.clicked.connect(self._on_sim_reset)
        sim_layout.addWidget(self._sim_reset_btn)

        drift_btn = QPushButton("模拟漂移")
        drift_btn.setCheckable(True)
        drift_btn.toggled.connect(self._on_drift_toggle)
        sim_layout.addWidget(drift_btn)
        self._drift_btn = drift_btn

        layout.addWidget(sim_group)

        # 历史日志
        log_group = QGroupBox("时间码历史日志")
        log_layout = QVBoxLayout(log_group)
        self._log_table = QTableWidget(0, 5)
        self._log_table.setHorizontalHeaderLabels(["时间", "输入时间码", "参考时间码", "漂移(ms)", "状态"])
        self._log_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        log_layout.addWidget(self._log_table)
        layout.addWidget(log_group, 1)

    def _on_sim_start(self):
        self._sim_running = True
        self._sim_start_btn.setEnabled(False)
        self._sim_stop_btn.setEnabled(True)
        self._sim_timer.setInterval(1000 // self._sim_fps)
        self._sim_timer.start()
        self._ref_timer.start()
        self._ui_timer.start()
        self._signal_indicator.set_status("synced")
        self._sync_indicator.set_status("synced")
        self.logger.info("模拟时间码已启动")

    def _on_sim_stop(self):
        self._sim_running = False
        self._sim_timer.stop()
        self._ref_timer.stop()
        self._ui_timer.stop()
        self._sim_start_btn.setEnabled(True)
        self._sim_stop_btn.setEnabled(False)
        self._signal_indicator.set_status("offline")
        self._sync_indicator.set_status("offline")
        self.logger.info("模拟时间码已停止")

    def _on_sim_reset(self):
        self._on_sim_stop()
        self._simulated_h = self._simulated_m = self._simulated_s = self._simulated_f = 0
        self._ref_h = self._ref_m = self._ref_s = self._ref_f = 0
        self._drift_ms = 0.0
        self._history.clear()
        self._log_table.setRowCount(0)
        self._input_tc_label.setText("00:00:00:00")
        self._ref_tc_label.setText("00:00:00:00")
        self._drift_label.setText("漂移: 0.0 ms")
        self._drift_bar.setValue(0)

    def _on_drift_toggle(self, checked):
        if checked:
            self._drift_btn.setText("漂移已启用")
            self.logger.info("模拟漂移已启用")
        else:
            self._drift_btn.setText("模拟漂移")
            self.logger.info("模拟漂移已禁用")

    def _on_sim_tick(self):
        self._simulated_f += 1
        if self._simulated_f >= self._sim_fps:
            self._simulated_f = 0
            self._simulated_s += 1
            if self._simulated_s >= 60:
                self._simulated_s = 0
                self._simulated_m += 1
                if self._simulated_m >= 60:
                    self._simulated_m = 0
                    self._simulated_h = (self._simulated_h + 1) % 24

    def _on_ref_tick(self):
        self._ref_f += 1
        if self._ref_f >= self._sim_fps:
            self._ref_f = 0
            self._ref_s += 1
            if self._ref_s >= 60:
                self._ref_s = 0
                self._ref_m += 1
                if self._ref_m >= 60:
                    self._ref_m = 0
                    self._ref_h = (self._ref_h + 1) % 24

    def _update_ui(self):
        input_tc = f"{self._simulated_h:02d}:{self._simulated_m:02d}:{self._simulated_s:02d}:{self._simulated_f:02d}"
        ref_tc = f"{self._ref_h:02d}:{self._ref_m:02d}:{self._ref_s:02d}:{self._ref_f:02d}"

        self._input_tc_label.setText(input_tc)
        self._ref_tc_label.setText(ref_tc)

        # 计算漂移
        input_total = (self._simulated_h * 3600 + self._simulated_m * 60 + self._simulated_s) + self._simulated_f / self._sim_fps
        ref_total = (self._ref_h * 3600 + self._ref_m * 60 + self._ref_s) + self._ref_f / self._sim_fps

        if self._drift_btn.isChecked():
            self._drift_ms = (input_total - ref_total) * 1000 + 15.0  # 模拟15ms漂移
        else:
            self._drift_ms = (input_total - ref_total) * 1000

        self._drift_label.setText(f"漂移: {self._drift_ms:+.1f} ms")
        self._drift_bar.setValue(max(-100, min(100, int(self._drift_ms))))

        # 更新同步状态
        if abs(self._drift_ms) < 5:
            self._sync_indicator.set_status("synced")
        elif abs(self._drift_ms) < 50:
            self._sync_indicator.set_status("drift")
        else:
            self._sync_indicator.set_status("lost")

        # 更新数据包计数
        total = len(self._history)
        self._packet_count_label.setText(f"数据包: {total}")
        self._signal_quality_label.setText(f"质量: {'优' if abs(self._drift_ms) < 5 else '良' if abs(self._drift_ms) < 50 else '差'}")

        # 记录历史
        now = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        if len(self._history) == 0 or (self._history[-1]['input'] != input_tc):
            status = "同步" if abs(self._drift_ms) < 5 else "漂移" if abs(self._drift_ms) < 50 else "失锁"
            self._history.append({
                'time': now, 'input': input_tc, 'ref': ref_tc,
                'drift': f"{self._drift_ms:+.1f}", 'status': status
            })

            row = self._log_table.rowCount()
            self._log_table.insertRow(row)
            self._log_table.setItem(row, 0, QTableWidgetItem(now))
            self._log_table.setItem(row, 1, QTableWidgetItem(input_tc))
            self._log_table.setItem(row, 2, QTableWidgetItem(ref_tc))
            self._log_table.setItem(row, 3, QTableWidgetItem(f"{self._drift_ms:+.1f}"))
            status_item = QTableWidgetItem(status)
            if status == "同步":
                status_item.setForeground(QColor("#00FF00"))
            elif status == "漂移":
                status_item.setForeground(QColor("#FFFF00"))
            else:
                status_item.setForeground(QColor("#FF0000"))
            self._log_table.setItem(row, 4, status_item)
            self._log_table.scrollToBottom()

            if self._log_table.rowCount() > 500:
                self._log_table.removeRow(0)
                self._history.pop(0)


# ─── 入口 ────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import traceback
    try:

        from PySide6.QtWidgets import QApplication
        app = QApplication(sys.argv)
        window = TimecodeMonitor()
        window.show()
        sys.exit(app.exec())
    except Exception as _e:
        traceback.print_exc()
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            _app = QApplication.instance() or QApplication([])
            QMessageBox.critical(None, "TimecodeMonitor - 启动错误",
                f"{type(_e).__name__}: {_e}\n\n请检查日志文件。")
        except Exception:
            pass
