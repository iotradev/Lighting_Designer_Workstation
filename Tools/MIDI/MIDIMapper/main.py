# -*- coding: utf-8 -*-
"""
MIDI映射器 - MIDI信号到灯光控制的映射工具
支持MIDI Learn、映射表管理、配置文件保存/加载
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'Common'))
from ui.base_window import BaseToolWindow

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QPushButton, QLabel, QCheckBox,
    QGroupBox, QTextEdit, QSplitter, QFileDialog,
    QMessageBox, QAbstractItemView, QLineEdit, QSpinBox, QFrame
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QColor

from mapper_engine import MapperEngine, MIDIMessage, MappingEntry

# 列索引常量
COL_INPUT_TYPE = 0
COL_INPUT_CH = 1
COL_INPUT_NUM = 2
COL_OUTPUT_ACTION = 3
COL_OUTPUT_PARAM = 4
COL_ENABLED = 5
COL_COUNT = 6

INPUT_TYPES = ["CC", "NoteOn", "NoteOff", "PitchBend"]
OUTPUT_ACTIONS = ["DMX通道", "场景触发", "宏命令", "无"]
CHANNELS = [f"CH{i}" for i in range(1, 17)]


class MIDIMapperWindow(BaseToolWindow):
    def __init__(self):
        super().__init__(
            tool_name="midi_mapper",
            tool_title="MIDI映射器",
            version="1.0.0",
            width=1100,
            height=750
        )
        self.engine = MapperEngine(self)
        self.engine.midi_received.connect(self._on_midi_received)
        self.engine.mapping_triggered.connect(self._on_mapping_triggered)
        self._learn_pending = False
        self._build_ui()
        self._refresh_devices()

    def _build_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)

        # --- 顶部：设备选择 + Learn ---
        top = QHBoxLayout()
        top.addWidget(QLabel("MIDI输入设备:"))
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(250)
        self.device_combo.currentTextChanged.connect(self._on_device_changed)
        top.addWidget(self.device_combo)
        self.btn_refresh = QPushButton("🔄 刷新")
        self.btn_refresh.clicked.connect(self._refresh_devices)
        top.addWidget(self.btn_refresh)
        top.addSpacing(20)
        self.learn_check = QCheckBox("🎹 MIDI Learn模式")
        self.learn_check.setStyleSheet("font-weight:bold; color:#ff6600;")
        self.learn_check.toggled.connect(self._on_learn_toggled)
        top.addWidget(self.learn_check)
        top.addStretch()
        self.btn_test = QPushButton("🧪 测试映射")
        self.btn_test.clicked.connect(self._on_test_mapping)
        top.addWidget(self.btn_test)
        main_layout.addLayout(top)

        # --- 中间：映射表 + 右侧按钮 ---
        mid_layout = QHBoxLayout()

        # 映射表
        self.table = QTableWidget(0, COL_COUNT)
        self.table.setHorizontalHeaderLabels(
            ["输入类型", "输入通道", "输入编号", "输出动作", "输出参数", "启用"]
        )
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(COL_INPUT_TYPE, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COL_INPUT_CH, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COL_INPUT_NUM, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COL_OUTPUT_ACTION, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(COL_OUTPUT_PARAM, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(COL_ENABLED, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.cellChanged.connect(self._on_cell_changed)
        mid_layout.addWidget(self.table, 1)

        # 右侧按钮
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(8)
        self.btn_add = QPushButton("➕ 添加映射")
        self.btn_add.clicked.connect(self._add_mapping)
        btn_layout.addWidget(self.btn_add)
        self.btn_remove = QPushButton("➖ 删除选中")
        self.btn_remove.clicked.connect(self._remove_mapping)
        btn_layout.addWidget(self.btn_remove)
        self.btn_clear = QPushButton("🗑 清空全部")
        self.btn_clear.clicked.connect(self._clear_mappings)
        btn_layout.addWidget(self.btn_clear)
        btn_layout.addSpacing(16)
        btn_layout.addWidget(self._separator())
        btn_layout.addSpacing(8)
        self.btn_save = QPushButton("💾 保存配置")
        self.btn_save.clicked.connect(self._save_profile)
        btn_layout.addWidget(self.btn_save)
        self.btn_load = QPushButton("📂 加载配置")
        self.btn_load.clicked.connect(self._load_profile)
        btn_layout.addWidget(self.btn_load)
        btn_layout.addStretch()

        # 映射统计
        self.lbl_count = QLabel("映射数: 0")
        self.lbl_count.setStyleSheet("color:#888;")
        btn_layout.addWidget(self.lbl_count)

        mid_layout.addLayout(btn_layout)
        main_layout.addLayout(mid_layout, 1)

        # --- 底部：MIDI实时输入显示 ---
        bottom_group = QGroupBox("📡 MIDI实时输入 (Learn模式下自动捕获)")
        bottom_layout = QVBoxLayout(bottom_group)
        self.midi_log = QTextEdit()
        self.midi_log.setReadOnly(True)
        self.midi_log.setMaximumHeight(140)
        self.midi_log.setFont(QFont("Consolas", 9))
        self.midi_log.setStyleSheet("background-color:#1e1e1e; color:#00ff88;")
        bottom_layout.addWidget(self.midi_log)
        main_layout.addWidget(bottom_group)

        self.set_central_content(central)
        self._update_count()

    def _separator(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        return line

    # ===== 设备 =====
    def _refresh_devices(self):
        self.device_combo.blockSignals(True)
        self.device_combo.clear()
        devices = self.engine.get_input_devices()
        self.device_combo.addItems(devices)
        self.device_combo.blockSignals(False)
        if devices:
            self._on_device_changed(devices[0])

    def _on_device_changed(self, name):
        if not name:
            return
        ok = self.engine.open_input(name)
        status = "已连接" if ok else "连接失败"
        self.logger.info(f"MIDI设备: {name} - {status}")

    # ===== Learn模式 =====
    def _on_learn_toggled(self, checked):
        if checked:
            self.engine.start_learn(self._on_learn_capture)
            self.midi_log.append(">>> Learn模式已开启 - 请操作MIDI控制器 <<<")
            self._learn_pending = True
        else:
            self.engine.stop_learn()
            self.midi_log.append(">>> Learn模式已关闭 <<<")
            self._learn_pending = False

    def _on_learn_capture(self, msg: MIDIMessage):
        """Learn模式捕获到消息，自动添加映射"""
        self._learn_pending = False
        entry = MappingEntry(
            input_type=msg.msg_type,
            input_channel=msg.channel,
            input_number=msg.number,
            output_action="DMX通道",
            output_param=f"{msg.number + 1}/255",
            enabled=True
        )
        self.engine.add_mapping(entry)
        self._refresh_table()
        self.midi_log.append(f"✓ 已映射: {msg.display_text()} → DMX通道 {msg.number + 1}")
        self.logger.info(f"Learn捕获映射: {entry.display_input()}")
        # 重置learn以便捕获下一个
        QTimer.singleShot(500, lambda: setattr(self, '_learn_pending', True))

    # ===== MIDI事件 =====
    def _on_midi_received(self, msg: MIDIMessage):
        self.midi_log.append(msg.display_text())
        # 限制日志行数
        doc = self.midi_log.document()
        if doc.blockCount() > 200:
            cursor = self.midi_log.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.KeepAnchor, 50)
            cursor.removeSelectedText()

    def _on_mapping_triggered(self, entry: MappingEntry, msg: MIDIMessage):
        self.logger.info(f"映射触发: {entry.display_input()} → {entry.output_action} {entry.output_param}")

    # ===== 映射表操作 =====
    def _add_mapping(self):
        entry = MappingEntry()
        self.engine.add_mapping(entry)
        self._refresh_table()
        # 选中新行
        row = self.table.rowCount() - 1
        self.table.selectRow(row)
        self.table.editItem(self.table.item(row, COL_INPUT_TYPE))

    def _remove_mapping(self):
        rows = sorted(set(idx.row() for idx in self.table.selectedIndexes()), reverse=True)
        for row in rows:
            self.engine.remove_mapping(row)
        self._refresh_table()

    def _clear_mappings(self):
        if QMessageBox.question(self, "确认", "确定清空所有映射？") == QMessageBox.StandardButton.Yes:
            self.engine.clear_mappings()
            self._refresh_table()

    def _refresh_table(self):
        self.table.blockSignals(True)
        mappings = self.engine.get_mappings()
        self.table.setRowCount(len(mappings))
        for i, m in enumerate(mappings):
            # 输入类型
            combo = QComboBox()
            combo.addItems(INPUT_TYPES)
            combo.setCurrentText(m.input_type)
            combo.currentTextChanged.connect(lambda t, row=i: self._on_type_changed(row, t))
            self.table.setCellWidget(i, COL_INPUT_TYPE, combo)

            # 输入通道
            ch_combo = QComboBox()
            ch_combo.addItems(CHANNELS)
            ch_combo.setCurrentIndex(m.input_channel)
            ch_combo.currentIndexChanged.connect(lambda idx, row=i: self._on_ch_changed(row, idx))
            self.table.setCellWidget(i, COL_INPUT_CH, ch_combo)

            # 输入编号
            num_spin = QSpinBox()
            num_spin.setRange(0, 127)
            num_spin.setValue(m.input_number)
            num_spin.valueChanged.connect(lambda val, row=i: self._on_num_changed(row, val))
            self.table.setCellWidget(i, COL_INPUT_NUM, num_spin)

            # 输出动作
            act_combo = QComboBox()
            act_combo.addItems(OUTPUT_ACTIONS)
            act_combo.setCurrentText(m.output_action)
            act_combo.currentTextChanged.connect(lambda t, row=i: self._on_action_changed(row, t))
            self.table.setCellWidget(i, COL_OUTPUT_ACTION, act_combo)

            # 输出参数
            param_item = QTableWidgetItem(m.output_param)
            self.table.setItem(i, COL_OUTPUT_PARAM, param_item)

            # 启用
            chk = QCheckBox()
            chk.setChecked(m.enabled)
            chk.stateChanged.connect(lambda state, row=i: self._on_enabled_changed(row, state))
            chk_widget = QWidget()
            chk_layout = QHBoxLayout(chk_widget)
            chk_layout.addWidget(chk)
            chk_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chk_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(i, COL_ENABLED, chk_widget)

        self.table.blockSignals(False)
        self._update_count()

    def _on_type_changed(self, row, text):
        if 0 <= row < len(self.engine.mappings):
            self.engine.mappings[row].input_type = text

    def _on_ch_changed(self, row, idx):
        if 0 <= row < len(self.engine.mappings):
            self.engine.mappings[row].input_channel = idx

    def _on_num_changed(self, row, val):
        if 0 <= row < len(self.engine.mappings):
            self.engine.mappings[row].input_number = val

    def _on_action_changed(self, row, text):
        if 0 <= row < len(self.engine.mappings):
            self.engine.mappings[row].output_action = text

    def _on_enabled_changed(self, row, state):
        if 0 <= row < len(self.engine.mappings):
            self.engine.mappings[row].enabled = (state == Qt.CheckState.Checked.value)

    def _on_cell_changed(self, row, col):
        if col == COL_OUTPUT_PARAM and 0 <= row < len(self.engine.mappings):
            item = self.table.item(row, col)
            if item:
                self.engine.mappings[row].output_param = item.text()

    def _update_count(self):
        n = len(self.engine.mappings)
        active = sum(1 for m in self.engine.mappings if m.enabled)
        self.lbl_count.setText(f"映射数: {n} (启用: {active})")

    # ===== 配置文件 =====
    def _save_profile(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "保存MIDI映射配置", "", "JSON文件 (*.json)"
        )
        if path:
            self.engine.save_profile(path)
            self.logger.info(f"映射配置已保存: {path}")

    def _load_profile(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "加载MIDI映射配置", "", "JSON文件 (*.json)"
        )
        if path:
            try:
                self.engine.load_profile(path)
                self._refresh_table()
                self.logger.info(f"映射配置已加载: {path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载失败:\n{e}")

    # ===== 测试 =====
    def _on_test_mapping(self):
        """发送测试消息验证当前映射"""
        rows = sorted(set(idx.row() for idx in self.table.selectedIndexes()))
        if not rows:
            QMessageBox.information(self, "提示", "请先选中一行映射进行测试")
            return
        for row in rows:
            if row < len(self.engine.mappings):
                m = self.engine.mappings[row]
                test_msg = MIDIMessage(
                    msg_type=m.input_type,
                    channel=m.input_channel,
                    number=m.input_number,
                    value=64
                )
                self.engine.send_test_message(test_msg)
                self.midi_log.append(f"[测试] {test_msg.display_text()}")

    def closeEvent(self, event):
        self.engine.close_input()
        super().closeEvent(event)


def main():
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MIDIMapperWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
