# -*- coding: utf-8 -*-
"""
sACNMonitor - sACN (E1.31) 数据包监听器
监听sACN多播数据，显示DMX数据和数据源信息
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'Common'))
from ui.base_window import BaseToolWindow

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QSplitter, QGroupBox, QSpinBox, QScrollArea, QFrame,
    QHeaderView, QAbstractItemView, QGridLayout, QProgressBar
)
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QColor, QPainter, QFont, QPen, QBrush

from sacn_engine import SACNEngine, get_multicast_address


class DMXChannelGrid(QWidget):
    """DMX通道网格 - 16x32条形图显示"""
    def __init__(self, channels=512, parent=None):
        super().__init__(parent)
        self._data = bytearray(512)
        self._channels = channels
        self.setMinimumHeight(300)

    def set_data(self, data):
        if isinstance(data, (bytes, bytearray)):
            self._data = bytearray(data[:512])
        else:
            self._data = bytearray(data)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        w = self.width()
        h = self.height()

        cols = 32
        rows = 16
        cell_w = w / cols
        cell_h = h / rows
        margin = 1

        for ch in range(self._channels):
            col = ch % cols
            row = ch // cols
            x = col * cell_w + margin
            y = row * cell_h + margin
            bar_w = cell_w - 2 * margin
            bar_h = cell_h - 2 * margin

            val = self._data[ch]
            fill_h = bar_h * val / 255.0

            # Background
            painter.fillRect(int(x), int(y), int(bar_w), int(bar_h),
                           QColor(40, 40, 40))

            # Bar
            if val > 0:
                if val > 200:
                    color = QColor(0, 220, 0)
                elif val > 100:
                    color = QColor(200, 200, 0)
                else:
                    color = QColor(0, 140, 220)
                painter.fillRect(
                    int(x), int(y + bar_h - fill_h),
                    int(bar_w), int(fill_h), color
                )

            # Channel number on first row
            if row == 0:
                painter.setPen(QPen(QColor(120, 120, 120)))
                painter.setFont(QFont("Consolas", 6))
                painter.drawText(int(x), int(y + 8), str(ch + 1))

        painter.end()


class SACNMonitorWindow(BaseToolWindow):
    """sACN监听器主窗口"""

    def __init__(self):
        super().__init__('sACNMonitor', 'sACN监听器', '1.0.0', 1200, 800)
        self._engine = SACNEngine(self)
        self._connect_signals()
        self._build_ui()
        self._listening = False
        self._source_display_items = {}  # key -> QListWidgetItem

    def _connect_signals(self):
        self._engine.packet_rate_updated.connect(self._on_rate_update)
        self._engine.source_updated.connect(self._on_source_update)
        self._engine.dmx_data_updated.connect(self._on_dmx_update)
        self._engine.log_message.connect(self._on_log)
        self._engine.status_changed.connect(self._on_status)

    def _build_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # === 顶部控制栏 ===
        top_bar = QHBoxLayout()
        self._btn_start = QPushButton("▶ 开始监听")
        self._btn_start.setFixedWidth(120)
        self._btn_start.clicked.connect(self._toggle_listening)
        top_bar.addWidget(self._btn_start)

        top_bar.addWidget(QLabel("Universe:"))
        self._spin_universe = QSpinBox()
        self._spin_universe.setRange(1, 63999)
        self._spin_universe.setValue(1)
        self._spin_universe.setFixedWidth(80)
        self._spin_universe.valueChanged.connect(self._on_universe_changed)
        top_bar.addWidget(self._spin_universe)

        self._lbl_mcast = QLabel("多播地址: 239.255.0.1:5568")
        self._lbl_mcast.setStyleSheet("color: #aaa;")
        top_bar.addWidget(self._lbl_mcast)

        top_bar.addStretch()

        self._lbl_status = QLabel("● 已停止")
        self._lbl_status.setStyleSheet("color: #888; font-weight: bold;")
        top_bar.addWidget(self._lbl_status)

        self._lbl_rate = QLabel("速率: 0 pps")
        self._lbl_rate.setStyleSheet("color: #0af;")
        top_bar.addWidget(self._lbl_rate)

        main_layout.addLayout(top_bar)

        # === 主体区域 ===
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧 - 活跃数据源列表
        left_group = QGroupBox("活跃数据源")
        left_layout = QVBoxLayout(left_group)
        self._source_list = QListWidget()
        self._source_list.setStyleSheet("QListWidget { font-family: Consolas; font-size: 11px; }")
        self._source_list.currentItemChanged.connect(self._on_source_selected)
        left_layout.addWidget(self._source_list)
        splitter.addWidget(left_group)

        # 中间 - DMX数据区
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # DMX条形图
        dmx_group = QGroupBox("DMX 通道数据 (512)")
        dmx_layout = QVBoxLayout(dmx_group)
        self._dmx_grid = DMXChannelGrid(512)
        dmx_layout.addWidget(self._dmx_grid)

        # 通道值表格 (16x32)
        self._ch_table = QTableWidget(16, 32)
        self._ch_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._ch_table.setFont(QFont("Consolas", 8))
        self._ch_table.horizontalHeader().setVisible(False)
        self._ch_table.verticalHeader().setVisible(False)
        self._ch_table.setMaximumHeight(200)
        self._ch_table.setShowGrid(False)
        for r in range(16):
            for c in range(32):
                ch = r * 32 + c
                item = QTableWidgetItem(f"{ch+1}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QColor(100, 100, 100))
                self._ch_table.setItem(r, c, item)
        # Uniform cell size
        for c in range(32):
            self._ch_table.setColumnWidth(c, 30)
        for r in range(16):
            self._ch_table.setRowHeight(r, 12)
        dmx_layout.addWidget(self._ch_table)
        right_layout.addWidget(dmx_group)

        splitter.addWidget(right_widget)
        splitter.setSizes([250, 950])
        main_layout.addWidget(splitter, 1)

        # === 底部日志 ===
        log_group = QGroupBox("数据包日志")
        log_layout = QVBoxLayout(log_group)
        self._log_table = QTableWidget(0, 6)
        self._log_table.setHorizontalHeaderLabels(
            ["时间", "数据源", "Universe", "优先级", "序列号", "数据长度"]
        )
        self._log_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._log_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._log_table.setFont(QFont("Consolas", 9))
        self._log_table.setMaximumHeight(160)
        log_layout.addWidget(self._log_table)
        main_layout.addWidget(log_group)

        self.set_central_content(central)

        # 初始状态更新
        self._update_mcast_label()

    def _update_mcast_label(self):
        uni = self._spin_universe.value()
        addr = get_multicast_address(uni)
        self._lbl_mcast.setText(f"多播地址: {addr}:5568")

    def _on_universe_changed(self, val):
        self._update_mcast_label()

    def _toggle_listening(self):
        if self._listening:
            self._engine.stop_listening()
            self._btn_start.setText("▶ 开始监听")
            self._lbl_status.setText("● 已停止")
            self._lbl_status.setStyleSheet("color: #888; font-weight: bold;")
            self._listening = False
            self.logger.info("停止监听")
        else:
            uni = self._spin_universe.value()
            self._engine.start_listening(uni)
            self._btn_start.setText("■ 停止监听")
            self._lbl_status.setText("● 监听中")
            self._lbl_status.setStyleSheet("color: #0f0; font-weight: bold;")
            self._listening = True
            self.logger.info(f"开始监听 Universe {uni}")

    @Slot(float)
    def _on_rate_update(self, rate):
        self._lbl_rate.setText(f"速率: {rate:.0f} pps")

    @Slot(str, int, int, str, int)
    def _on_source_selected(self, current, previous):
        """数据源选择变更"""
        if current:
            self._update_dmx_display()
    def _on_source_update(self, name, universe, priority, cid_short, seq):
        key = f"{cid_short}_{universe}"
        display = f"{name[:24]}  U{universe}  优先级:{priority}  序列:{seq}"
        if key in self._source_display_items:
            self._source_display_items[key].setText(display)
        else:
            item = QListWidgetItem(display)
            self._source_list.addItem(item)
            self._source_display_items[key] = item

        # 添加日志行
        from datetime import datetime
        now = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        row = self._log_table.rowCount()
        self._log_table.insertRow(row)
        vals = [now, name[:30], str(universe), str(priority), str(seq), "512"]
        for col, v in enumerate(vals):
            item = QTableWidgetItem(v)
            self._log_table.setItem(row, col, item)
        # 限制日志行数
        if self._log_table.rowCount() > 500:
            self._log_table.removeRow(0)

    @Slot(int, object)
    def _on_dmx_update(self, universe, dmx_data):
        self._dmx_grid.set_data(dmx_data)
        # 更新表格
        for r in range(16):
            for c in range(32):
                ch = r * 32 + c
                if ch < len(dmx_data):
                    val = dmx_data[ch]
                    item = self._ch_table.item(r, c)
                    if item:
                        item.setText(str(val))
                        if val > 200:
                            item.setForeground(QColor(0, 220, 0))
                        elif val > 100:
                            item.setForeground(QColor(200, 200, 0))
                        elif val > 0:
                            item.setForeground(QColor(0, 140, 220))
                        else:
                            item.setForeground(QColor(80, 80, 80))

    @Slot(str)
    def _on_log(self, msg):
        self.logger.info(msg)

    @Slot(str)
    def _on_status(self, status):
        if "监听中" in status:
            self._lbl_status.setText(f"● {status}")
            self._lbl_status.setStyleSheet("color: #0f0; font-weight: bold;")
        else:
            self._lbl_status.setText(f"● {status}")

    def closeEvent(self, event):
        if self._listening:
            self._engine.stop_listening()
        super().closeEvent(event)


def main():
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = SACNMonitorWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
