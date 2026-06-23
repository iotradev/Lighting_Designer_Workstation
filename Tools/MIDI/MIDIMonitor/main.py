# -*- coding: utf-8 -*-
"""
MIDI Monitor - MIDI 信号监控工具
实时监控 MIDI 输入设备，显示并分析 MIDI 消息。
"""
import sys
import time
import threading
from pathlib import Path

# 将 Common 目录加入模块路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'Common'))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QCheckBox, QLabel, QGroupBox,
    QProgressBar, QLineEdit, QHeaderView, QSplitter, QFrame,
    QGridLayout, QScrollArea, QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QColor, QFont, QBrush

from ui.base_window import BaseToolWindow
from midi_engine import MIDIEngine, MIDIMessage, RTMIDI_AVAILABLE


# ===== 消息类型颜色映射 =====
MSG_COLORS = {
    0x90: QColor(80, 200, 80),     # 音符开启 - 绿色
    0x80: QColor(220, 70, 70),     # 音符关闭 - 红色
    0xB0: QColor(240, 160, 40),    # 控制变化 - 橙色
    0xC0: QColor(100, 160, 240),   # 程序变化 - 蓝色
    0xA0: QColor(200, 130, 255),   # 触后压力 - 紫色
    0xD0: QColor(255, 200, 80),    # 通道压力 - 黄色
    0xE0: QColor(80, 220, 220),    # 弯音     - 青色
    0xF0: QColor(180, 180, 180),   # 系统消息 - 灰色
}

# 可过滤的消息类型
FILTER_TYPES = {
    "音符开启": 0x90,
    "音符关闭": 0x80,
    "控制变化": 0xB0,
    "程序变化": 0xC0,
    "触后压力": 0xA0,
    "通道压力": 0xD0,
    "弯音":     0xE0,
}


class NoteIndicator(QWidget):
    """单个音符指示灯"""

    def __init__(self, note_num: int, parent=None):
        super().__init__(parent)
        self.note_num = note_num
        self._active = False
        self._velocity = 0
        self.setFixedSize(28, 36)

    def set_active(self, active: bool, velocity: int = 0):
        self._active = active
        self._velocity = velocity
        self.update()

    def paintEvent(self, event):
        from PySide6.QtGui import QPainter
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 白键 / 黑键
        black_keys = {1, 3, 6, 8, 10}
        is_black = (self.note_num % 12) in black_keys

        if self._active:
            intensity = min(255, 60 + self._velocity * 2)
            bg = QColor(intensity, intensity // 2, 40)
        elif is_black:
            bg = QColor(50, 50, 50)
        else:
            bg = QColor(200, 200, 200)

        painter.setBrush(bg)
        painter.setPen(QColor(100, 100, 100))
        painter.drawRoundedRect(1, 1, self.width() - 2, self.height() - 2, 3, 3)
        painter.end()


class ActiveNotesPanel(QWidget):
    """活动音符显示面板 - 两个八度键盘"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setSpacing(1)
        layout.setContentsMargins(2, 2, 2, 2)

        self.notes: dict[int, NoteIndicator] = {}
        # 显示 C3-B4 (MIDI 48-71)
        for n in range(48, 72):
            indicator = NoteIndicator(n)
            self.notes[n] = indicator
            layout.addWidget(indicator)

    def update_notes(self, active_notes: dict):
        # 重置全部
        for n, ind in self.notes.items():
            ind.set_active(False)
        # 激活
        for (ch, note), vel in active_notes.items():
            if note in self.notes:
                self.notes[note].set_active(True, vel)


class CCMeter(QWidget):
    """单个 CC 值仪表"""

    def __init__(self, cc_num: int, parent=None):
        super().__init__(parent)
        self.cc_num = cc_num
        self._value = 0
        self.setFixedSize(20, 60)

    def set_value(self, v: int):
        self._value = v
        self.update()

    def paintEvent(self, event):
        from PySide6.QtGui import QPainter
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # 背景
        p.setBrush(QColor(40, 40, 40))
        p.setPen(QColor(80, 80, 80))
        p.drawRoundedRect(1, 1, self.width() - 2, self.height() - 2, 2, 2)
        # 填充
        fill_h = int((self._value / 127) * (self.height() - 4))
        if fill_h > 0:
            ratio = self._value / 127
            c = QColor.fromHsv(int(120 - ratio * 120), 200, 200)
            p.setBrush(c)
            p.setPen(Qt.PenStyle.NoPen)
            y = self.height() - 2 - fill_h
            p.drawRoundedRect(2, y, self.width() - 4, fill_h, 2, 2)
        p.end()


class CCMetersPanel(QWidget):
    """CC 仪表面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QGridLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)
        self.meters: dict[int, CCMeter] = {}
        # 显示 CC 1-8
        for i, cc in enumerate(range(1, 9)):
            meter = CCMeter(cc)
            lbl = QLabel(f"C{cc}")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("font-size:8px; color:#aaa;")
            layout.addWidget(meter, 0, i)
            layout.addWidget(lbl, 1, i)
            self.meters[cc] = meter

    def update_cc(self, cc_values: dict):
        for cc, meter in self.meters.items():
            # 任意通道同 CC 取最新
            val = 0
            for (ch, c), v in cc_values.items():
                if c == cc:
                    val = v
            meter.set_value(val)


# ======================================================================
# 主界面
# ======================================================================
class MIDIMonitorWindow(BaseToolWindow):
    """MIDI 监控工具主窗口"""

    def __init__(self):
        super().__init__(
            tool_name="MIDIMonitor",
            tool_title="MIDI 信号监控",
            version="1.0.0",
            width=1200,
            height=800,
        )

        self._engine = MIDIEngine(callback=self._on_midi_message)
        self._max_rows = 2000
        self._active_filters: set[int] = set(FILTER_TYPES.values())
        self._message_queue: list[MIDIMessage] = []
        self._queue_lock = threading.Lock()

        self._build_ui()
        self._refresh_devices()

        # UI 刷新定时器（批量更新避免卡顿）
        self._ui_timer = QTimer(self)
        self._ui_timer.timeout.connect(self._flush_messages)
        self._ui_timer.start(50)

        self.logger.info("MIDI 监控工具就绪")

    # ------------------------------------------------------------------
    # 构建 UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        root = QWidget()
        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(4, 4, 4, 4)

        # ----- 顶部控制栏 -----
        top_bar = QHBoxLayout()

        top_bar.addWidget(QLabel("MIDI 输入设备:"))
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(250)
        top_bar.addWidget(self.device_combo)

        self.btn_refresh = QPushButton("刷新")
        self.btn_refresh.clicked.connect(self._refresh_devices)
        top_bar.addWidget(self.btn_refresh)

        self.btn_start = QPushButton("▶ 开始监听")
        self.btn_start.setStyleSheet("QPushButton{background:#2a6e2a; padding:4px 14px;}")
        self.btn_start.clicked.connect(self._start_listening)
        top_bar.addWidget(self.btn_start)

        self.btn_stop = QPushButton("■ 停止")
        self.btn_stop.setStyleSheet("QPushButton{background:#6e2a2a; padding:4px 14px;}")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop_listening)
        top_bar.addWidget(self.btn_stop)

        self.btn_clear = QPushButton("清除")
        self.btn_clear.clicked.connect(self._clear_messages)
        top_bar.addWidget(self.btn_clear)

        top_bar.addStretch()
        main_layout.addLayout(top_bar)

        # ----- 过滤复选框 -----
        filter_bar = QHBoxLayout()
        filter_bar.addWidget(QLabel("消息过滤:"))
        self.filter_checks: dict[str, QCheckBox] = {}
        for name, code in FILTER_TYPES.items():
            cb = QCheckBox(name)
            cb.setChecked(True)
            cb.toggled.connect(lambda checked, c=code: self._toggle_filter(c, checked))
            color = MSG_COLORS.get(code, QColor(200, 200, 200))
            cb.setStyleSheet(f"QCheckBox{{color:{color.name()};}}")
            filter_bar.addWidget(cb)
            self.filter_checks[name] = cb
        filter_bar.addStretch()
        main_layout.addLayout(filter_bar)

        # ----- 中心: 消息表 + 右侧统计 -----
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 消息表格
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["时间戳", "状态", "通道", "数据1", "数据2", "类型"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        splitter.addWidget(self.table)

        # 右侧面板
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(4, 4, 4, 4)

        # 统计信息
        stats_group = QGroupBox("统计信息")
        stats_layout = QVBoxLayout(stats_group)
        self.lbl_total = QLabel("总消息数: 0")
        self.lbl_rate = QLabel("消息速率: 0 /秒")
        self.lbl_active = QLabel("活动音符: 0")
        self.lbl_type_stats = QLabel("")
        self.lbl_type_stats.setWordWrap(True)
        for lbl in (self.lbl_total, self.lbl_rate, self.lbl_active, self.lbl_type_stats):
            lbl.setStyleSheet("font-size:11px; color:#ddd;")
            stats_layout.addWidget(lbl)
        right_layout.addWidget(stats_group)

        # 活动音符
        notes_group = QGroupBox("活动音符 (C3-B4)")
        notes_layout = QVBoxLayout(notes_group)
        self.notes_panel = ActiveNotesPanel()
        notes_layout.addWidget(self.notes_panel)
        right_layout.addWidget(notes_group)

        # CC 仪表
        cc_group = QGroupBox("控制变化 (CC 1-8)")
        cc_layout = QVBoxLayout(cc_group)
        self.cc_panel = CCMetersPanel()
        cc_layout.addWidget(self.cc_panel)
        right_layout.addWidget(cc_group)

        right_layout.addStretch()
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

        # ----- 底部搜索/过滤栏 -----
        bottom_bar = QHBoxLayout()
        bottom_bar.addWidget(QLabel("搜索:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入关键字过滤消息...")
        self.search_input.textChanged.connect(self._on_search_changed)
        bottom_bar.addWidget(self.search_input)
        main_layout.addLayout(bottom_bar)

        self.set_central_content(root)

        # 速率计算
        self._rate_counter = 0
        self._rate_timer = QTimer(self)
        self._rate_timer.timeout.connect(self._update_rate)
        self._rate_timer.start(1000)

    # ------------------------------------------------------------------
    # 设备
    # ------------------------------------------------------------------
    def _refresh_devices(self):
        self.device_combo.clear()
        devices = self._engine.get_input_devices()
        self.device_combo.addItems(devices)
        if not RTMIDI_AVAILABLE:
            self.device_combo.addItem("[演示] 模拟 MIDI 输入")
        self.logger.info(f"发现 {len(devices)} 个 MIDI 设备")

    # ------------------------------------------------------------------
    # 监听控制
    # ------------------------------------------------------------------
    def _start_listening(self):
        device = self.device_combo.currentText()
        self._engine.start(device_name=device)
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.device_combo.setEnabled(False)
        self.status_ready.setText("监听中...")
        self.logger.info(f"开始监听: {device}")

    def _stop_listening(self):
        self._engine.stop()
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.device_combo.setEnabled(True)
        self.status_ready.setText("就绪")
        self.logger.info("已停止监听")

    # ------------------------------------------------------------------
    # MIDI 消息处理
    # ------------------------------------------------------------------
    @Slot(object)
    def _on_midi_message(self, msg: MIDIMessage):
        """从引擎线程接收消息（线程安全，存入队列）"""
        with self._queue_lock:
            self._message_queue.append(msg)

    def _flush_messages(self):
        """定时将队列中的消息刷新到 UI"""
        with self._queue_lock:
            if not self._message_queue:
                return
            messages = self._message_queue
            self._message_queue = []

        for msg in messages:
            # 过滤
            if msg.msg_type not in self._active_filters:
                continue
            # 搜索过滤
            keyword = self.search_input.text().strip().lower()
            if keyword:
                text = f"{msg.msg_type_name} {msg.channel} {msg.data1} {msg.data2}".lower()
                if keyword not in text:
                    continue

            self._add_table_row(msg)
            self._rate_counter += 1

        # 更新统计（通过快照避免数据竞争）
        stats = self._engine.get_stats_snapshot()
        self.lbl_total.setText(f"总消息数: {stats['msg_count']}")
        self.lbl_active.setText(f"活动音符: {len(stats['active_notes'])}")
        self.notes_panel.update_notes(stats['active_notes'])
        self.cc_panel.update_cc(stats['cc_values'])

        # 类型统计
        parts = []
        for name, cnt in stats['msg_type_counts'].items():
            parts.append(f"{name}: {cnt}")
        self.lbl_type_stats.setText("\n".join(parts) if parts else "")

    def _add_table_row(self, msg: MIDIMessage):
        row = self.table.rowCount()
        if row >= self._max_rows:
            batch = self._max_rows // 4
            self.table.removeRows(0, batch)
            row = self.table.rowCount()

        self.table.insertRow(row)

        ts_str = time.strftime("%H:%M:%S", time.localtime(msg.timestamp))
        ts_ms = f".{int(msg.timestamp * 1000) % 1000:03d}"

        items = [
            f"{ts_str}{ts_ms}",
            f"0x{msg.status:02X}",
            str(msg.channel),
            str(msg.data1),
            str(msg.data2),
            msg.msg_type_name,
        ]

        color = MSG_COLORS.get(msg.msg_type, QColor(200, 200, 200))

        for col, text in enumerate(items):
            item = QTableWidgetItem(text)
            item.setForeground(QBrush(color))
            self.table.setItem(row, col, item)

        self.table.scrollToBottom()

    # ------------------------------------------------------------------
    # 过滤
    # ------------------------------------------------------------------
    def _toggle_filter(self, msg_type: int, checked: bool):
        if checked:
            self._active_filters.add(msg_type)
        else:
            self._active_filters.discard(msg_type)

    def _on_search_changed(self, text: str):
        pass  # 搜索在 _flush_messages 中生效

    # ------------------------------------------------------------------
    # 速率
    # ------------------------------------------------------------------
    def _update_rate(self):
        self.lbl_rate.setText(f"消息速率: {self._rate_counter} /秒")
        self._rate_counter = 0

    # ------------------------------------------------------------------
    # 清除
    # ------------------------------------------------------------------
    def _clear_messages(self):
        self.table.setRowCount(0)
        self._message_queue.clear()
        self.logger.info("已清除消息列表")

    # ------------------------------------------------------------------
    # 关闭
    # ------------------------------------------------------------------
    def closeEvent(self, event):
        self._engine.stop()
        super().closeEvent(event)


# ======================================================================
# 入口
# ======================================================================
def main():
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MIDIMonitorWindow()
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
            QMessageBox.critical(None, "MIDIMonitor - 启动错误",
                f"{type(_e).__name__}: {_e}\n\n请检查日志文件。")
        except Exception:
            pass
