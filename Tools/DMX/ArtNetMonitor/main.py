# -*- coding: utf-8 -*-
"""
ArtNetMonitor - Art-Net 监听器
灯光设计工作站 - 网络 DMX 数据监听与分析
"""
import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QLabel, QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QSplitter, QGroupBox, QHeaderView, QGridLayout, QFrame, QSpinBox,
    QAbstractItemView
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QFont

# 导入基类
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "Common"))
from ui.base_window import BaseToolWindow

from artnet_engine import ArtnetListener


class DMXChannelGrid(QWidget):
    """DMX 通道值网格显示 - 16列 x 32行 柱状图"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = bytearray(512)
        self.setMinimumSize(600, 400)

    def update_data(self, data: bytes):
        length = min(len(data), 512)
        self._data[:length] = data[:length]
        if len(data) < 512:
            self._data[len(data):] = b"\x00" * (512 - len(data))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()

        # 背景
        painter.fillRect(0, 0, w, h, QColor(25, 25, 30))

        cols = 32
        rows = 16
        cell_w = w / cols
        cell_h = h / rows
        margin = 1

        for idx in range(512):
            col = idx % cols
            row = idx // cols
            val = self._data[idx]

            x = col * cell_w + margin
            y = row * cell_h + margin
            bar_w = cell_w - margin * 2
            bar_h = cell_h - margin * 2

            # 柱状图：从底部向上
            fill_h = bar_h * (val / 255) if val > 0 else 0
            fill_y = y + bar_h - fill_h

            # 颜色：低值蓝 → 中值绿 → 高值红
            if val < 85:
                color = QColor(30, int(30 + val * 2.5), 200)
            elif val < 170:
                color = QColor(30, 200, int(200 - (val - 85) * 2))
            else:
                color = QColor(int((val - 170) * 3), 200, 30)

            if val > 0:
                painter.fillRect(int(x), int(fill_y), int(bar_w), int(fill_h), color)

            # 边框
            painter.setPen(QPen(QColor(50, 50, 55), 0.5))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(int(x), int(y), int(bar_w), int(bar_h))

        painter.end()


class ArtNetMonitor(BaseToolWindow):
    """Art-Net 监听器主窗口"""

    def __init__(self):
        super().__init__("ArtNetMonitor", "Art-Net 监听器", "1.0.0", 1300, 850)

        self._listener: ArtnetListener | None = None
        self._selected_universe: int | None = None
        self._log_max = 200

        self._init_ui()
        self._init_timer()

        self.logger.info("ArtNetMonitor 已启动")

    def _init_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # === 顶部控制栏 ===
        top = QHBoxLayout()
        self._btn_start = QPushButton("▶ 开始监听")
        self._btn_start.setFixedWidth(120)
        self._btn_start.clicked.connect(self._toggle_listen)

        top.addWidget(QLabel("绑定地址:"))
        self._input_addr = QLineEdit("0.0.0.0")
        self._input_addr.setFixedWidth(120)
        top.addWidget(self._input_addr)

        top.addWidget(QLabel("端口:"))
        self._input_port = QSpinBox()
        self._input_port.setRange(1, 65535)
        self._input_port.setValue(6454)
        self._input_port.setFixedWidth(80)
        top.addWidget(self._input_port)

        self._btn_poll = QPushButton("🔍 发送 ArtPoll")
        self._btn_poll.setFixedWidth(130)
        self._btn_poll.clicked.connect(self._send_poll)
        self._btn_poll.setEnabled(False)
        top.addWidget(self._btn_poll)

        top.addStretch()

        self._lbl_status = QLabel("● 未连接")
        self._lbl_status.setStyleSheet("color: #888; font-weight: bold;")
        top.addWidget(self._lbl_status)

        main_layout.addLayout(top)

        # === 中间内容 ===
        splitter = QSplitter(Qt.Horizontal)

        # 左侧 - Universe 列表
        left_group = QGroupBox("活跃 Universe")
        left_layout = QVBoxLayout(left_group)

        self._universe_list = QListWidget()
        self._universe_list.currentItemChanged.connect(self._on_universe_selected)
        left_layout.addWidget(self._universe_list)

        self._lbl_rate = QLabel("速率: - 包/秒")
        left_layout.addWidget(self._lbl_rate)

        splitter.addWidget(left_group)

        # 中间 - DMX 网格
        center_group = QGroupBox("DMX 通道数据 (16×32)")
        center_layout = QVBoxLayout(center_group)
        self._dmx_grid = DMXChannelGrid()
        center_layout.addWidget(self._dmx_grid)

        self._lbl_universe_info = QLabel("请选择 Universe")
        center_layout.addWidget(self._lbl_universe_info)

        splitter.addWidget(center_group)

        splitter.setSizes([250, 700])
        main_layout.addWidget(splitter, 1)

        # === 底部日志表 ===
        log_group = QGroupBox("数据包日志")
        log_layout = QVBoxLayout(log_group)

        self._log_table = QTableWidget(0, 4)
        self._log_table.setHorizontalHeaderLabels(["时间", "Universe", "数据长度", "序列号"])
        self._log_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._log_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._log_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._log_table.setMaximumHeight(180)
        log_layout.addWidget(self._log_table)

        main_layout.addWidget(log_group)

        self.set_central_content(central)

    def _init_timer(self):
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_display)
        self._refresh_timer.start(200)  # 5 Hz 刷新

    def _toggle_listen(self):
        if self._listener and self._listener.isRunning():
            self._stop_listen()
        else:
            self._start_listen()

    def _start_listen(self):
        addr = self._input_addr.text().strip() or "0.0.0.0"
        port = self._input_port.value()

        self._listener = ArtnetListener(addr, port, self)
        self._listener.packet_received.connect(self._on_packet)
        self._listener.log_entry.connect(self._on_log)
        self._listener.node_found.connect(self._on_node_found)
        self._listener.error_occurred.connect(self._on_error)
        self._listener.status_changed.connect(self._on_status_changed)
        self._listener.start()

        self._btn_start.setText("■ 停止监听")
        self._btn_poll.setEnabled(True)
        self._input_addr.setEnabled(False)
        self._input_port.setEnabled(False)
        self.logger.info(f"开始监听 Art-Net: {addr}:{port}")

    def _stop_listen(self):
        if self._listener:
            self._listener.stop()
            self._listener.wait(3000)
            self._listener = None

        self._btn_start.setText("▶ 开始监听")
        self._btn_poll.setEnabled(False)
        self._input_addr.setEnabled(True)
        self._input_port.setEnabled(True)
        self._lbl_status.setText("● 未连接")
        self._lbl_status.setStyleSheet("color: #888; font-weight: bold;")
        self.logger.info("停止监听 Art-Net")

    def _send_poll(self):
        if self._listener:
            self._listener.send_poll()
            self.logger.info("已发送 ArtPoll")

    def _on_packet(self, universe_key: int, seq: int, data_len: int, rate: float):
        # 更新 universe list（延迟到 _refresh_display 批量处理）
        pass

    def _on_log(self, ts: str, universe: int, size: int, seq: int):
        table = self._log_table
        if table.rowCount() >= self._log_max:
            table.removeRow(0)
        row = table.rowCount()
        table.insertRow(row)
        table.setItem(row, 0, QTableWidgetItem(ts))
        table.setItem(row, 1, QTableWidgetItem(f"U{universe}"))
        table.setItem(row, 2, QTableWidgetItem(str(size)))
        table.setItem(row, 3, QTableWidgetItem(str(seq)))
        table.scrollToBottom()

    def _on_node_found(self, ip: str, name: str):
        self.logger.info(f"发现 Art-Net 节点: {ip} ({name})")

    def _on_error(self, msg: str):
        self._lbl_status.setText(f"● 错误: {msg}")
        self._lbl_status.setStyleSheet("color: #f55; font-weight: bold;")
        self.logger.error(msg)

    def _on_status_changed(self, msg: str):
        if "已连接" in msg:
            self._lbl_status.setText(f"● {msg}")
            self._lbl_status.setStyleSheet("color: #5f5; font-weight: bold;")
        else:
            self._lbl_status.setText(f"● {msg}")
            self._lbl_status.setStyleSheet("color: #888; font-weight: bold;")

    def _on_universe_selected(self, current: QListWidgetItem, _prev):
        if current:
            self._selected_universe = current.data(Qt.UserRole)
        else:
            self._selected_universe = None

    def _refresh_display(self):
        if not self._listener or not self._listener.isRunning():
            return

        # 刷新 universe 列表（保持选中状态）
        selected_key = self._selected_universe
        universes = self._listener.get_active_universes()
        self._universe_list.blockSignals(True)
        self._universe_list.clear()
        restore_item = None
        for key, rate, count in universes:
            display_key = f"U{key}"
            item = QListWidgetItem(f"{display_key}  |  {rate:.1f} pkt/s  |  共 {count}")
            item.setData(Qt.UserRole, key)
            self._universe_list.addItem(item)
            if key == selected_key:
                restore_item = item
        if restore_item:
            self._universe_list.setCurrentItem(restore_item)
        elif self._universe_list.count() > 0 and selected_key is None:
            self._universe_list.setCurrentRow(0)
        self._universe_list.blockSignals(False)

        # 刷新 DMX 网格
        if self._selected_universe is not None:
            udata = self._listener.get_universe_data(self._selected_universe)
            if udata:
                self._dmx_grid.update_data(bytes(udata.channels))
                self._lbl_universe_info.setText(
                    f"Universe {self._selected_universe}  |  "
                    f"序列: {udata.sequence}  |  物理: {udata.physical}  |  "
                    f"速率: {udata.rate:.1f} pkt/s  |  总计: {udata.packet_count}"
                )
                self._lbl_rate.setText(f"速率: {udata.rate:.1f} 包/秒")
                return
        self._lbl_rate.setText("速率: - 包/秒")

    def closeEvent(self, event):
        self._stop_listen()
        super().closeEvent(event)


def main():
    import sys
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = ArtNetMonitor()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
