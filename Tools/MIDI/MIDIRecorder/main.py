"""MIDI录制器 - 录制、回放和导出MIDI消息"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'Common'))
from ui.base_window import BaseToolWindow

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QSpinBox, QComboBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from engine import MIDIEngine


class MainWindow(BaseToolWindow):
    def __init__(self):
        super().__init__('MIDIRecorder', 'MIDI录制器', '1.0.0', 1200, 800)
        self.engine = MIDIEngine()
        self.playback_index = 0
        self.playback_start_time = 0.0
        self._playback_timer = QTimer()
        self._playback_timer.timeout.connect(self._on_playback_tick)
        self._time_timer = QTimer()
        self._time_timer.timeout.connect(self._update_time_display)
        self._recording_start = 0.0
        self._build_ui()
        self._init_device()

    def _build_ui(self):
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # 设备信息栏
        device_bar = QHBoxLayout()
        self.lbl_device = QLabel("MIDI设备: 检测中...")
        self.lbl_device.setStyleSheet("color: #aaa; font-size: 12px;")
        device_bar.addWidget(self.lbl_device)
        device_bar.addStretch()
        layout.addLayout(device_bar)

        # 控制面板
        ctrl_group = QGroupBox("控制面板")
        ctrl_group.setStyleSheet("QGroupBox { color: #ddd; font-weight: bold; }")
        ctrl_layout = QHBoxLayout(ctrl_group)

        self.btn_record = QPushButton("⏺ 录制")
        self.btn_record.setFixedSize(100, 40)
        self.btn_record.setStyleSheet("""
            QPushButton { background: #555; color: #fff; font-size: 14px; font-weight: bold; border-radius: 4px; }
            QPushButton:hover { background: #666; }
        """)
        self.btn_record.clicked.connect(self._on_record)

        self.btn_stop = QPushButton("⏹ 停止")
        self.btn_stop.setFixedSize(100, 40)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet("""
            QPushButton { background: #555; color: #fff; font-size: 14px; font-weight: bold; border-radius: 4px; }
            QPushButton:hover { background: #666; }
            QPushButton:disabled { background: #333; color: #666; }
        """)
        self.btn_stop.clicked.connect(self._on_stop)

        self.btn_play = QPushButton("▶ 播放")
        self.btn_play.setFixedSize(100, 40)
        self.btn_play.setEnabled(False)
        self.btn_play.setStyleSheet("""
            QPushButton { background: #555; color: #fff; font-size: 14px; font-weight: bold; border-radius: 4px; }
            QPushButton:hover { background: #666; }
            QPushButton:disabled { background: #333; color: #666; }
        """)
        self.btn_play.clicked.connect(self._on_play)

        self.btn_pause = QPushButton("⏸ 暂停")
        self.btn_pause.setFixedSize(100, 40)
        self.btn_pause.setEnabled(False)
        self.btn_pause.setStyleSheet("""
            QPushButton { background: #555; color: #fff; font-size: 14px; font-weight: bold; border-radius: 4px; }
            QPushButton:hover { background: #666; }
            QPushButton:disabled { background: #333; color: #666; }
        """)
        self.btn_pause.clicked.connect(self._on_pause)

        # 时间显示
        self.lbl_time = QLabel("00:00.000")
        self.lbl_time.setFont(QFont("Consolas", 20, QFont.Bold))
        self.lbl_time.setStyleSheet("color: #00ff88; background: #111; padding: 8px 20px; border-radius: 4px;")

        # 消息计数
        self.lbl_count = QLabel("消息: 0")
        self.lbl_count.setStyleSheet("color: #aaa; font-size: 12px;")

        ctrl_layout.addWidget(self.btn_record)
        ctrl_layout.addWidget(self.btn_stop)
        ctrl_layout.addWidget(self.btn_play)
        ctrl_layout.addWidget(self.btn_pause)
        ctrl_layout.addSpacing(20)
        ctrl_layout.addWidget(self.lbl_time)
        ctrl_layout.addSpacing(20)
        ctrl_layout.addWidget(self.lbl_count)
        ctrl_layout.addStretch()
        layout.addWidget(ctrl_group)

        # 导出按钮栏
        export_bar = QHBoxLayout()
        self.btn_export_csv = QPushButton("📄 导出CSV")
        self.btn_export_csv.setFixedHeight(32)
        self.btn_export_csv.setEnabled(False)
        self.btn_export_csv.clicked.connect(self._export_csv)

        self.btn_export_midi = QPushButton("🎵 导出MIDI")
        self.btn_export_midi.setFixedHeight(32)
        self.btn_export_midi.setEnabled(False)
        self.btn_export_midi.clicked.connect(self._export_midi)

        self.btn_clear = QPushButton("🗑 清空")
        self.btn_clear.setFixedHeight(32)
        self.btn_clear.setEnabled(False)
        self.btn_clear.clicked.connect(self._clear)

        self.spin_bpm = QSpinBox()
        self.spin_bpm.setRange(20, 300)
        self.spin_bpm.setValue(120)
        self.spin_bpm.setPrefix("BPM: ")
        self.spin_bpm.setFixedWidth(100)

        export_bar.addWidget(self.btn_export_csv)
        export_bar.addWidget(self.btn_export_midi)
        export_bar.addWidget(self.spin_bpm)
        export_bar.addWidget(self.btn_clear)
        export_bar.addStretch()
        layout.addLayout(export_bar)

        # 消息表格
        table_group = QGroupBox("录制消息")
        table_group.setStyleSheet("QGroupBox { color: #ddd; font-weight: bold; }")
        tbl_layout = QVBoxLayout(table_group)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["#", "时间戳", "状态", "数据", "消息类型"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setStyleSheet("""
            QTableWidget { background: #1e1e1e; color: #ddd; gridline-color: #333; font-family: Consolas; }
            QHeaderView::section { background: #2d2d2d; color: #ddd; padding: 5px; }
        """)
        tbl_layout.addWidget(self.table)
        layout.addWidget(table_group, 1)

        self.set_central_content(main_widget)

    def _init_device(self):
        """初始化MIDI设备"""
        device_name = self.engine.try_open_input()
        if device_name:
            self.lbl_device.setText(f"MIDI设备: {device_name} ✓")
            self.lbl_device.setStyleSheet("color: #00ff88; font-size: 12px;")
            self.engine.set_callback(self._on_midi_received)
        else:
            self.lbl_device.setText("MIDI设备: 未检测到设备（支持手动模拟输入）")
            self.lbl_device.setStyleSheet("color: #ff8800; font-size: 12px;")

    def _on_midi_received(self, status, data1, data2):
        """收到MIDI消息回调"""
        # 在UI线程中更新表格
        pass  # 消息已在引擎中存储，通过定时器刷新UI

    def _on_record(self):
        """开始录制"""
        self.engine.start_record()
        self._recording_start = time.time()
        self._time_timer.start(50)

        self.btn_record.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_play.setEnabled(False)
        self.btn_pause.setEnabled(False)
        self.btn_export_csv.setEnabled(False)
        self.btn_export_midi.setEnabled(False)
        self.btn_clear.setEnabled(False)
        self.table.setRowCount(0)
        self.lbl_count.setText("录制中...")
        self.lbl_count.setStyleSheet("color: #ff4444; font-size: 12px;")

        # 启动刷新定时器
        self._refresh_timer = QTimer()
        self._refresh_timer.timeout.connect(self._refresh_table)
        self._refresh_timer.start(200)

        self.logger.info("开始录制MIDI")

    def _on_stop(self):
        """停止录制或播放"""
        if self.engine.is_recording:
            self.engine.stop_record()
            self._refresh_table()  # 最终刷新
            if hasattr(self, '_refresh_timer'):
                self._refresh_timer.stop()

        if self.engine.is_playing:
            self.engine.is_playing = False
            self._playback_timer.stop()

        self._time_timer.stop()

        self.btn_record.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_play.setEnabled(len(self.engine.messages) > 0)
        self.btn_pause.setEnabled(False)

        has_msgs = len(self.engine.messages) > 0
        self.btn_export_csv.setEnabled(has_msgs)
        self.btn_export_midi.setEnabled(has_msgs)
        self.btn_clear.setEnabled(has_msgs)

        count = len(self.engine.messages)
        self.lbl_count.setText(f"消息: {count}")
        self.lbl_count.setStyleSheet("color: #aaa; font-size: 12px;")

        self.logger.info(f"停止录制，共 {count} 条消息")

    def _on_play(self):
        """播放录制的消息"""
        if not self.engine.messages:
            return

        self.engine.is_playing = True
        self.engine.is_paused = False
        self.playback_index = 0
        self.playback_start_time = time.time()
        self._playback_timer.start(10)

        self.btn_record.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_play.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.lbl_count.setStyleSheet("color: #4488ff; font-size: 12px;")
        self.lbl_count.setText("播放中...")

        self.logger.info("开始播放MIDI")

    def _on_pause(self):
        """暂停/继续播放"""
        if self.engine.is_playing:
            if self.engine.is_paused:
                # 继续播放
                self.engine.is_paused = False
                self.playback_start_time = time.time() - self.engine.messages[self.playback_index].timestamp
                self._playback_timer.start(10)
                self.btn_pause.setText("⏸ 暂停")
                self._time_timer.start(50)
            else:
                # 暂停
                self.engine.is_paused = True
                self._playback_timer.stop()
                self._time_timer.stop()
                self.btn_pause.setText("▶ 继续")

    def _on_playback_tick(self):
        """播放定时器回调"""
        if not self.engine.is_playing or self.engine.is_paused:
            return

        current_time = time.time() - self.playback_start_time

        while self.playback_index < len(self.engine.messages):
            msg = self.engine.messages[self.playback_index]
            if msg.timestamp <= current_time:
                self.playback_index += 1
            else:
                break

        # 高亮当前行
        if self.playback_index > 0:
            self.table.selectRow(self.playback_index - 1)

        # 播放完成
        if self.playback_index >= len(self.engine.messages):
            self._on_stop()
            self.logger.info("播放完成")

    def _refresh_table(self):
        """刷新消息表格"""
        msgs = self.engine.messages
        if self.table.rowCount() != len(msgs):
            self.table.setRowCount(len(msgs))
            for i in range(self.table.rowCount() - 20, len(msgs)):
                if i < 0:
                    continue
                msg = msgs[i]
                self.table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
                self.table.setItem(i, 1, QTableWidgetItem(f"{msg.timestamp:.4f}"))
                self.table.setItem(i, 2, QTableWidgetItem(f"0x{msg.status:02X}"))
                self.table.setItem(i, 3, QTableWidgetItem(f"{msg.data1}, {msg.data2}"))
                self.table.setItem(i, 4, QTableWidgetItem(msg.message_type))

            self.lbl_count.setText(f"录制中: {len(msgs)} 条")

    def _update_time_display(self):
        """更新时间显示"""
        if self.engine.is_recording:
            elapsed = time.time() - self._recording_start
        elif self.engine.is_playing and not self.engine.is_paused:
            elapsed = time.time() - self.playback_start_time
        else:
            return

        minutes = int(elapsed // 60)
        seconds = elapsed % 60
        self.lbl_time.setText(f"{minutes:02d}:{seconds:06.3f}")

    def _export_csv(self):
        """导出CSV"""
        path, _ = QFileDialog.getSaveFileName(
            self, "导出CSV", "midi_recording.csv", "CSV文件 (*.csv)"
        )
        if path:
            try:
                self.engine.export_csv(path)
                QMessageBox.information(self, "成功", f"已导出到:\n{path}")
                self.logger.info(f"导出CSV: {path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败:\n{str(e)}")

    def _export_midi(self):
        """导出MIDI文件"""
        path, _ = QFileDialog.getSaveFileName(
            self, "导出MIDI", "midi_recording.mid", "MIDI文件 (*.mid)"
        )
        if path:
            try:
                bpm = self.spin_bpm.value()
                self.engine.export_midi(path, bpm=bpm)
                QMessageBox.information(self, "成功", f"已导出到:\n{path}\n(BPM: {bpm})")
                self.logger.info(f"导出MIDI: {path} (BPM: {bpm})")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败:\n{str(e)}")

    def _clear(self):
        """清空所有录制"""
        reply = QMessageBox.question(
            self, "确认", "确定要清空所有录制的消息吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.engine.clear()
            self.table.setRowCount(0)
            self.lbl_count.setText("消息: 0")
            self.lbl_time.setText("00:00.000")
            self.btn_play.setEnabled(False)
            self.btn_export_csv.setEnabled(False)
            self.btn_export_midi.setEnabled(False)
            self.btn_clear.setEnabled(False)
            self.logger.info("已清空所有录制")

    def closeEvent(self, event):
        """关闭时清理资源"""
        self.engine.close_input()
        super().closeEvent(event)


if __name__ == '__main__':
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
        QSpinBox { background: #2d2d2d; color: #ddd; border: 1px solid #555; border-radius: 3px; padding: 3px; }
    """)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
