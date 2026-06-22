# -*- coding: utf-8 -*-
"""
RDMTool - RDM (Remote Device Management) 管理工具
灯光设计工作站 - 设备发现、参数读写、识别控制
"""
import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QSplitter, QGroupBox,
    QHeaderView, QSpinBox, QComboBox, QProgressBar,
    QLineEdit, QFormLayout, QCheckBox, QTextEdit, QFrame,
    QAbstractItemView, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont

# 导入基类
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "Common"))
from ui.base_window import BaseToolWindow

from rdm_engine import RDMEngine, RDMMessage


class RDMTool(BaseToolWindow):
    """RDM 管理工具主窗口"""

    def __init__(self):
        super().__init__("RDMTool", "RDM管理工具", "1.0.0", 1200, 800)

        self.engine = RDMEngine()
        self._selected_uid = None
        self._log_max = 500

        self._init_ui()
        self._init_timers()

        self.logger.info("RDM管理工具已启动")

    def _init_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # === 顶部控制栏 ===
        top = QHBoxLayout()

        self._btn_discover = QPushButton("🔍 开始发现设备")
        self._btn_discover.setFixedWidth(150)
        self._btn_discover.clicked.connect(self._start_discovery)
        top.addWidget(self._btn_discover)

        top.addWidget(QLabel("Universe:"))
        self._cmb_universe = QComboBox()
        self._cmb_universe.setFixedWidth(100)
        for i in range(8):
            self._cmb_universe.addItem(f"U{i}")
        top.addWidget(self._cmb_universe)

        top.addWidget(QLabel("发现进度:"))
        self._progress = QProgressBar()
        self._progress.setFixedWidth(200)
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        top.addWidget(self._progress)

        self._lbl_device_count = QLabel("设备: 0")
        self._lbl_device_count.setStyleSheet("color: #aaa; font-weight: bold;")
        top.addWidget(self._lbl_device_count)

        top.addStretch()

        self._lbl_status = QLabel("● 就绪")
        self._lbl_status.setStyleSheet("color: #5f5; font-weight: bold;")
        top.addWidget(self._lbl_status)

        main_layout.addLayout(top)

        # === 中间主内容 ===
        splitter = QSplitter(Qt.Horizontal)

        # 左侧 - 设备表格
        table_group = QGroupBox("已发现设备")
        table_layout = QVBoxLayout(table_group)

        self._device_table = QTableWidget(0, 7)
        self._device_table.setHorizontalHeaderLabels([
            "UID", "设备标签", "型号ID", "固件版本", "DMX地址", "个性", "通道占用"
        ])
        self._device_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._device_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._device_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._device_table.setAlternatingRowColors(True)
        self._device_table.currentItemChanged.connect(self._on_device_selected)
        table_layout.addWidget(self._device_table)

        splitter.addWidget(table_group)

        # 右侧 - 参数面板
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # 只读参数区
        read_group = QGroupBox("设备参数 (只读)")
        read_form = QFormLayout(read_group)

        self._lbl_uid = QLabel("-")
        self._lbl_manufacturer = QLabel("-")
        self._lbl_model = QLabel("-")
        self._lbl_mode = QLabel("-")
        self._lbl_sensor = QLabel("-")
        self._lbl_fw = QLabel("-")
        self._lbl_personality = QLabel("-")
        self._lbl_footprint = QLabel("-")

        for lbl in [self._lbl_uid, self._lbl_manufacturer, self._lbl_model,
                     self._lbl_mode, self._lbl_sensor, self._lbl_fw,
                     self._lbl_personality, self._lbl_footprint]:
            lbl.setStyleSheet("color: #ddd;")

        read_form.addRow("UID:", self._lbl_uid)
        read_form.addRow("制造商:", self._lbl_manufacturer)
        read_form.addRow("型号:", self._lbl_model)
        read_form.addRow("工作模式:", self._lbl_mode)
        read_form.addRow("固件版本:", self._lbl_fw)
        read_form.addRow("个性索引:", self._lbl_personality)
        read_form.addRow("通道占用:", self._lbl_footprint)
        read_form.addRow("传感器数:", self._lbl_sensor)

        right_layout.addWidget(read_group)

        # 可写参数区
        write_group = QGroupBox("设置参数")
        write_form = QFormLayout(write_group)

        self._edit_label = QLineEdit()
        self._edit_label.setPlaceholderText("设备标签 (最多32字符)")
        write_form.addRow("设备标签:", self._edit_label)

        self._spin_dmx_addr = QSpinBox()
        self._spin_dmx_addr.setRange(1, 512)
        self._spin_dmx_addr.setValue(1)
        write_form.addRow("DMX地址:", self._spin_dmx_addr)

        self._chk_identify = QCheckBox("识别模式")
        write_form.addRow("识别:", self._chk_identify)

        btn_row = QHBoxLayout()
        self._btn_apply = QPushButton("📝 应用更改")
        self._btn_apply.clicked.connect(self._apply_changes)
        self._btn_apply.setEnabled(False)
        btn_row.addWidget(self._btn_apply)

        self._btn_read_all = QPushButton("📖 刷新参数")
        self._btn_read_all.clicked.connect(self._read_all_params)
        self._btn_read_all.setEnabled(False)
        btn_row.addWidget(self._btn_read_all)

        write_form.addRow(btn_row)

        right_layout.addWidget(write_group)
        right_layout.addStretch()

        # 固定宽度
        right_panel.setFixedWidth(280)
        splitter.addWidget(right_panel)

        splitter.setSizes([700, 280])
        main_layout.addWidget(splitter, 1)

        # === 底部消息日志 ===
        log_group = QGroupBox("RDM 消息日志")
        log_layout = QVBoxLayout(log_group)

        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setMaximumHeight(160)
        self._log_text.setFont(QFont("Consolas", 9))
        log_layout.addWidget(self._log_text)

        log_btn_row = QHBoxLayout()
        btn_clear = QPushButton("清空日志")
        btn_clear.setFixedWidth(80)
        btn_clear.clicked.connect(lambda: self._log_text.clear())
        log_btn_row.addStretch()
        log_btn_row.addWidget(btn_clear)
        log_layout.addLayout(log_btn_row)

        main_layout.addWidget(log_group)

        self.set_central_content(central)

    def _init_timers(self):
        # 发现进度定时器
        self._discovery_timer = QTimer(self)
        self._discovery_timer.timeout.connect(self._poll_discovery)
        self._discovery_timer.setInterval(300)

    # === 发现 ===
    def _start_discovery(self):
        if not self.engine.start_discovery():
            return

        self._device_table.setRowCount(0)
        self._progress.setValue(0)
        self._btn_discover.setEnabled(False)
        self._lbl_status.setText("● 正在发现设备...")
        self._lbl_status.setStyleSheet("color: #fa0; font-weight: bold;")
        self._log_message(">>> 开始 RDM 设备发现...")
        self._discovery_timer.start()
        self.logger.info("开始 RDM 设备发现")

    def _poll_discovery(self):
        progress, done = self.engine.advance_discovery()
        self._progress.setValue(progress)

        if done:
            self._discovery_timer.stop()
            self._btn_discover.setEnabled(True)
            devices = self.engine.get_devices()
            count = len(devices)
            self._lbl_device_count.setText(f"设备: {count}")
            self._lbl_status.setText(f"● 发现完成 ({count} 台设备)")
            self._lbl_status.setStyleSheet("color: #5f5; font-weight: bold;")
            self._log_message(f"<<< 发现完成: {count} 台设备在线")
            self._populate_table(devices)
            self.logger.info(f"RDM 发现完成: {count} 台设备")

    def _populate_table(self, devices):
        self._device_table.setRowCount(len(devices))
        for row, dev in enumerate(devices):
            self._device_table.setItem(row, 0, QTableWidgetItem(dev.uid))
            self._device_table.setItem(row, 1, QTableWidgetItem(dev.label))
            self._device_table.setItem(row, 2, QTableWidgetItem(f"{dev.model_id} ({dev.model_name})"))
            self._device_table.setItem(row, 3, QTableWidgetItem(dev.software_version))
            self._device_table.setItem(row, 4, QTableWidgetItem(str(dev.dmx_address)))
            self._device_table.setItem(row, 5, QTableWidgetItem(str(dev.personality)))
            self._device_table.setItem(row, 6, QTableWidgetItem(str(dev.footprint)))

        self._log_message(f"设备列表已更新: {len(devices)} 条记录")

    # === 设备选择 ===
    def _on_device_selected(self, current, _prev):
        if current is None:
            self._selected_uid = None
            self._btn_apply.setEnabled(False)
            self._btn_read_all.setEnabled(False)
            return

        row = current.row()
        uid_item = self._device_table.item(row, 0)
        if not uid_item:
            return

        self._selected_uid = uid_item.text()
        dev = self.engine.get_device(self._selected_uid)
        if dev:
            self._update_param_panel(dev)
            self._btn_apply.setEnabled(True)
            self._btn_read_all.setEnabled(True)
            self._log_message(f"> 选中设备: {dev.uid} ({dev.label})")

    def _update_param_panel(self, dev):
        self._lbl_uid.setText(dev.uid)
        self._lbl_manufacturer.setText(dev.manufacturer)
        self._lbl_model.setText(dev.model_name)
        self._lbl_mode.setText(dev.mode)
        self._lbl_sensor.setText(str(dev.sensor_count))
        self._lbl_fw.setText(dev.software_version)
        self._lbl_personality.setText(str(dev.personality))
        self._lbl_footprint.setText(str(dev.footprint))

        self._edit_label.setText(dev.label)
        self._spin_dmx_addr.setValue(dev.dmx_address)
        self._chk_identify.setChecked(dev.identify)

    def _read_all_params(self):
        if not self._selected_uid:
            return
        uid = self._selected_uid
        params = ['manufacturer', 'model', 'mode', 'dmx_start', 'sensor_count',
                  'label', 'software_version', 'identify']
        for pid_name in params:
            ok, val = self.engine.read_parameter(uid, pid_name)
            status = "OK" if ok else "FAIL"
            self._log_message(f"  GET {uid} PID={pid_name}: [{status}] {val}")

        # 刷新面板
        dev = self.engine.get_device(uid)
        if dev:
            self._update_param_panel(dev)
        self.logger.info(f"已读取设备 {uid} 所有参数")

    # === 设置参数 ===
    def _apply_changes(self):
        if not self._selected_uid:
            return
        uid = self._selected_uid
        dev = self.engine.get_device(uid)
        if not dev:
            return

        changes = []

        # 标签
        new_label = self._edit_label.text().strip()
        if new_label and new_label != dev.label:
            ok, msg = self.engine.set_parameter(uid, 'label', new_label)
            self._log_message(f"  SET label -> [{('OK' if ok else 'FAIL')}] {msg}")
            if ok:
                changes.append("标签")

        # DMX 地址
        new_addr = self._spin_dmx_addr.value()
        if new_addr != dev.dmx_address:
            ok, msg = self.engine.set_parameter(uid, 'dmx_address', new_addr)
            self._log_message(f"  SET dmx_address -> [{('OK' if ok else 'FAIL')}] {msg}")
            if ok:
                changes.append("DMX地址")

        # 识别模式
        new_ident = self._chk_identify.isChecked()
        if new_ident != dev.identify:
            ok, msg = self.engine.set_parameter(uid, 'identify', new_ident)
            self._log_message(f"  SET identify -> [{('OK' if ok else 'FAIL')}] {msg}")
            if ok:
                changes.append("识别模式")

        if changes:
            self._update_param_panel(dev)
            self._refresh_table_row(dev)
            self.logger.info(f"已更新设备 {uid}: {', '.join(changes)}")
        else:
            self._log_message("  没有需要更新的参数")

    def _refresh_table_row(self, dev):
        """更新表格中对应设备行"""
        for row in range(self._device_table.rowCount()):
            uid_item = self._device_table.item(row, 0)
            if uid_item and uid_item.text() == dev.uid:
                self._device_table.item(row, 1).setText(dev.label)
                self._device_table.item(row, 4).setText(str(dev.dmx_address))
                break

    # === 日志 ===
    def _log_message(self, text):
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self._log_text.append(f"[{ts}] {text}")
        # 限制日志行数
        doc = self._log_text.document()
        if doc.blockCount() > self._log_max:
            cursor = self._log_text.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.KeepAnchor,
                                doc.blockCount() - self._log_max)
            cursor.removeSelectedText()

    def closeEvent(self, event):
        self._discovery_timer.stop()
        self.logger.info("RDM管理工具已关闭")
        super().closeEvent(event)


def main():
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = RDMTool()
    window.show()
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
            QMessageBox.critical(None, "RDMTool - 启动错误",
                f"{type(_e).__name__}: {_e}\n\n请检查日志文件。")
        except Exception:
            pass
