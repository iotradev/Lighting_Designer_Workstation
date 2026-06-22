# -*- coding: utf-8 -*-
"""
DMX测试器 - DMXTester v1.0.0
512通道DMX输出测试工具
支持单通道测试、自动Chase/Ramp测试、Universe视图、故障检测
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QSpinBox, QSlider, QLabel, QPushButton, QGroupBox,
    QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QSplitter, QScrollArea, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QLinearGradient

# 导入基类
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'Common'))
from ui.base_window import BaseToolWindow

# 导入引擎
from dmx_test_engine import DMXTestEngine


# ===== 自定义Widget: DMX值显示条 =====
class DMXBar(QWidget):
    """单个DMX通道值显示条"""

    def __init__(self, channel: int = 1, parent=None):
        super().__init__(parent)
        self.channel = channel
        self.value = 0
        self.setMinimumSize(28, 50)
        self.setMaximumWidth(36)

    def set_value(self, value: int):
        self.value = max(0, min(255, value))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        w = self.width()
        h = self.height()

        # 背景
        painter.fillRect(0, 0, w, h, QColor(30, 30, 30))

        # 值条 - 从底部向上
        bar_h = int(self.value / 255.0 * (h - 14))
        if bar_h > 0:
            # 颜色渐变: 绿->黄->红
            if self.value < 128:
                color = QColor(0, int(self.value * 2), 0)
            else:
                color = QColor(int((self.value - 128) * 2), 255 - int((self.value - 128) * 2), 0)
            painter.fillRect(2, h - 14 - bar_h, w - 4, bar_h, color)

        # 边框
        painter.setPen(QColor(80, 80, 80))
        painter.drawRect(1, 1, w - 2, h - 14)

        # 通道号
        painter.setPen(QColor(180, 180, 180))
        painter.drawText(0, h - 12, w, 12, Qt.AlignCenter, str(self.channel))


# ===== 自定义Widget: Universe网格 =====
class UniverseGrid(QWidget):
    """512通道16x32网格显示"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bars = []
        self.setMinimumSize(900, 450)
        layout = QGridLayout(self)
        layout.setSpacing(1)
        layout.setContentsMargins(2, 2, 2, 2)

        for row in range(16):
            for col in range(32):
                ch = row * 32 + col + 1
                bar = DMXBar(ch)
                self.bars.append(bar)
                layout.addWidget(bar, row, col)

    def update_all(self, channels):
        """更新所有通道显示"""
        for i, bar in enumerate(self.bars):
            if i < len(channels):
                bar.set_value(channels[i])


# ===== Tab 1: 通道测试 =====
class ChannelTestTab(QWidget):
    def __init__(self, engine: DMXTestEngine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 通道选择组
        ch_group = QGroupBox("通道设置")
        ch_layout = QGridLayout(ch_group)

        ch_layout.addWidget(QLabel("通道号 (1-512):"), 0, 0)
        self.ch_spin = QSpinBox()
        self.ch_spin.setRange(1, 512)
        self.ch_spin.setValue(1)
        ch_layout.addWidget(self.ch_spin, 0, 1)

        ch_layout.addWidget(QLabel("通道值 (0-255):"), 1, 0)
        self.val_slider = QSlider(Qt.Horizontal)
        self.val_slider.setRange(0, 255)
        self.val_slider.setValue(0)
        self.val_label = QLabel("0")
        self.val_label.setMinimumWidth(40)
        self.val_slider.valueChanged.connect(lambda v: self.val_label.setText(str(v)))
        ch_layout.addWidget(self.val_slider, 1, 1)
        ch_layout.addWidget(self.val_label, 1, 2)

        # DMX值显示条
        self.dmx_bar = DMXBar(1)
        self.dmx_bar.setFixedHeight(200)
        ch_layout.addWidget(self.dmx_bar, 0, 3, 2, 1)

        layout.addWidget(ch_group)

        # 范围设置组
        range_group = QGroupBox("范围设置")
        range_layout = QGridLayout(range_group)

        range_layout.addWidget(QLabel("起始通道:"), 0, 0)
        self.range_start = QSpinBox()
        self.range_start.setRange(1, 512)
        range_layout.addWidget(self.range_start, 0, 1)

        range_layout.addWidget(QLabel("结束通道:"), 0, 2)
        self.range_end = QSpinBox()
        self.range_end.setRange(1, 512)
        self.range_end.setValue(16)
        range_layout.addWidget(self.range_end, 0, 3)

        range_layout.addWidget(QLabel("设置值:"), 1, 0)
        self.range_val = QSpinBox()
        self.range_val.setRange(0, 255)
        range_layout.addWidget(self.range_val, 1, 1)

        range_btn = QPushButton("设置范围")
        range_btn.clicked.connect(self._set_range)
        range_layout.addWidget(range_btn, 1, 2, 1, 2)

        layout.addWidget(range_group)

        # 操作按钮
        btn_layout = QHBoxLayout()

        set_btn = QPushButton("设置通道")
        set_btn.clicked.connect(self._set_channel)
        btn_layout.addWidget(set_btn)

        all0_btn = QPushButton("全部归零 (Blackout)")
        all0_btn.clicked.connect(self._all_zero)
        btn_layout.addWidget(all0_btn)

        all255_btn = QPushButton("全部满值 (Full)")
        all255_btn.clicked.connect(self._all_full)
        btn_layout.addWidget(all255_btn)

        layout.addLayout(btn_layout)
        layout.addStretch()

        # 滑块联动
        self.val_slider.valueChanged.connect(self._on_slider_changed)
        self.ch_spin.valueChanged.connect(self._on_channel_changed)

    def _on_slider_changed(self, value):
        ch = self.ch_spin.value()
        self.engine.set_channel(ch, value)
        self.dmx_bar.channel = ch
        self.dmx_bar.set_value(value)

    def _on_channel_changed(self, ch):
        self.dmx_bar.channel = ch
        val = self.engine.get_channel(ch)
        self.val_slider.blockSignals(True)
        self.val_slider.setValue(val)
        self.val_slider.blockSignals(False)
        self.dmx_bar.set_value(val)

    def _set_channel(self):
        ch = self.ch_spin.value()
        val = self.val_slider.value()
        self.engine.set_channel(ch, val)
        self.dmx_bar.set_value(val)

    def _set_range(self):
        start = self.range_start.value()
        end = self.range_end.value()
        val = self.range_val.value()
        self.engine.set_range(start, end, val)

    def _all_zero(self):
        self.engine.blackout()
        self.val_slider.setValue(0)

    def _all_full(self):
        self.engine.full_on()
        self.val_slider.setValue(255)


# ===== Tab 2: 自动测试 =====
class AutoTestTab(QWidget):
    def __init__(self, engine: DMXTestEngine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Chase测试组
        chase_group = QGroupBox("Chase测试 (逐通道扫描)")
        chase_layout = QGridLayout(chase_group)

        chase_layout.addWidget(QLabel("扫描速度 (ms):"), 0, 0)
        self.chase_speed = QSlider(Qt.Horizontal)
        self.chase_speed.setRange(10, 1000)
        self.chase_speed.setValue(100)
        self.chase_speed_label = QLabel("100ms")
        self.chase_speed.valueChanged.connect(
            lambda v: self.chase_speed_label.setText(f"{v}ms"))
        chase_layout.addWidget(self.chase_speed, 0, 1)
        chase_layout.addWidget(self.chase_speed_label, 0, 2)

        chase_btn_layout = QHBoxLayout()
        self.chase_start_btn = QPushButton("▶ 启动Chase")
        self.chase_start_btn.clicked.connect(self._start_chase)
        chase_btn_layout.addWidget(self.chase_start_btn)

        self.chase_stop_btn = QPushButton("⏹ 停止Chase")
        self.chase_stop_btn.clicked.connect(self._stop_chase)
        self.chase_stop_btn.setEnabled(False)
        chase_btn_layout.addWidget(self.chase_stop_btn)
        chase_layout.addLayout(chase_btn_layout, 1, 0, 1, 3)

        self.chase_status = QLabel("状态: 未运行")
        chase_layout.addWidget(self.chase_status, 2, 0, 1, 3)

        layout.addWidget(chase_group)

        # Ramp测试组
        ramp_group = QGroupBox("Ramp测试 (渐变 0→255→0)")
        ramp_layout = QGridLayout(ramp_group)

        ramp_layout.addWidget(QLabel("目标通道:"), 0, 0)
        self.ramp_channel = QSpinBox()
        self.ramp_channel.setRange(1, 512)
        ramp_layout.addWidget(self.ramp_channel, 0, 1)

        ramp_layout.addWidget(QLabel("渐变速度 (ms):"), 1, 0)
        self.ramp_speed = QSlider(Qt.Horizontal)
        self.ramp_speed.setRange(5, 200)
        self.ramp_speed.setValue(20)
        self.ramp_speed_label = QLabel("20ms")
        self.ramp_speed.valueChanged.connect(
            lambda v: self.ramp_speed_label.setText(f"{v}ms"))
        ramp_layout.addWidget(self.ramp_speed, 1, 1)
        ramp_layout.addWidget(self.ramp_speed_label, 1, 2)

        ramp_btn_layout = QHBoxLayout()
        self.ramp_start_btn = QPushButton("▶ 启动Ramp")
        self.ramp_start_btn.clicked.connect(self._start_ramp)
        ramp_btn_layout.addWidget(self.ramp_start_btn)

        self.ramp_stop_btn = QPushButton("⏹ 停止Ramp")
        self.ramp_stop_btn.clicked.connect(self._stop_ramp)
        self.ramp_stop_btn.setEnabled(False)
        ramp_btn_layout.addWidget(self.ramp_stop_btn)
        ramp_layout.addLayout(ramp_btn_layout, 2, 0, 1, 3)

        self.ramp_status = QLabel("状态: 未运行")
        self.ramp_value_label = QLabel("当前值: 0")
        ramp_layout.addWidget(self.ramp_status, 3, 0, 1, 3)
        ramp_layout.addWidget(self.ramp_value_label, 4, 0, 1, 3)

        # Ramp值进度条
        self.ramp_progress = QProgressBar()
        self.ramp_progress.setRange(0, 255)
        self.ramp_progress.setValue(0)
        ramp_layout.addWidget(self.ramp_progress, 5, 0, 1, 3)

        layout.addWidget(ramp_group)

        # 全部停止
        stop_all_btn = QPushButton("⏹ 停止所有测试 + Blackout")
        stop_all_btn.clicked.connect(self._stop_all)
        layout.addWidget(stop_all_btn)

        layout.addStretch()

    def _start_chase(self):
        speed = self.chase_speed.value()
        self.engine.start_chase(speed, self._on_chase_step)
        self.chase_start_btn.setEnabled(False)
        self.chase_stop_btn.setEnabled(True)
        self.chase_status.setText("状态: Chase运行中...")

    def _stop_chase(self):
        self.engine.stop_chase()
        self.chase_start_btn.setEnabled(True)
        self.chase_stop_btn.setEnabled(False)
        self.chase_status.setText("状态: 已停止")

    def _on_chase_step(self, ch):
        self.chase_status.setText(f"状态: Chase运行中 - 通道 {ch}")

    def _start_ramp(self):
        ch = self.ramp_channel.value()
        speed = self.ramp_speed.value()
        self.engine.start_ramp(ch, speed, self._on_ramp_step)
        self.ramp_start_btn.setEnabled(False)
        self.ramp_stop_btn.setEnabled(True)
        self.ramp_status.setText(f"状态: Ramp运行中 (通道 {ch})")

    def _stop_ramp(self):
        self.engine.stop_ramp()
        self.ramp_start_btn.setEnabled(True)
        self.ramp_stop_btn.setEnabled(False)
        self.ramp_status.setText("状态: 已停止")
        self.ramp_progress.setValue(0)
        self.ramp_value_label.setText("当前值: 0")

    def _on_ramp_step(self, value):
        self.ramp_progress.setValue(value)
        self.ramp_value_label.setText(f"当前值: {value}")

    def _stop_all(self):
        self.engine.stop_all_tests()
        self._stop_chase()
        self._stop_ramp()


# ===== Tab 3: Universe视图 =====
class UniverseViewTab(QWidget):
    def __init__(self, engine: DMXTestEngine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 信息标签
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel("Universe 0 - 512通道 (16×32 网格)"))
        info_layout.addStretch()
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.refresh)
        info_layout.addWidget(self.refresh_btn)
        layout.addLayout(info_layout)

        # 网格
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.grid = UniverseGrid()
        scroll.setWidget(self.grid)
        layout.addWidget(scroll)

        # 定时刷新
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(100)  # 10Hz刷新

    def refresh(self):
        self.grid.update_all(self.engine.channels)


# ===== Tab 4: 故障检测 =====
class FaultDetectionTab(QWidget):
    def __init__(self, engine: DMXTestEngine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 控制区
        ctrl_group = QGroupBox("故障检测")
        ctrl_layout = QVBoxLayout(ctrl_group)

        desc = QLabel(
            "检测流程：将所有通道设为255，然后设为0，检测是否有通道卡死（无法归零）。"
        )
        desc.setWordWrap(True)
        ctrl_layout.addWidget(desc)

        btn_layout = QHBoxLayout()
        self.run_btn = QPushButton("▶ 开始检测")
        self.run_btn.clicked.connect(self._run_test)
        btn_layout.addWidget(self.run_btn)

        self.stop_btn = QPushButton("⏹ 停止")
        self.stop_btn.clicked.connect(self._stop_test)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_btn)
        ctrl_layout.addLayout(btn_layout)

        self.status_label = QLabel("状态: 就绪")
        ctrl_layout.addWidget(self.status_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        ctrl_layout.addWidget(self.progress)

        layout.addWidget(ctrl_group)

        # 结果表格
        result_group = QGroupBox("检测结果")
        result_layout = QVBoxLayout(result_group)

        self.result_table = QTableWidget()
        self.result_table.setColumnCount(3)
        self.result_table.setHorizontalHeaderLabels(["通道", "卡死值", "状态"])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.result_table.setEditTriggers(QTableWidget.NoEditTriggers)
        result_layout.addWidget(self.result_table)

        self.result_summary = QLabel("共检测 0 个通道，发现 0 个故障")
        result_layout.addWidget(self.result_summary)

        layout.addWidget(result_group)

    def _run_test(self):
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("状态: 正在检测...")
        self.progress.setVisible(True)
        self.result_table.setRowCount(0)

        import threading
        def _do_test():
            results = self.engine.run_fault_detection(
                callback=lambda msg: self.status_label.setText(f"状态: {msg}")
            )
            # 回到主线程更新UI
            from PySide6.QtCore import QMetaObject, Qt as QTC
            QTimer.singleShot(0, lambda: self._show_results(results))

        threading.Thread(target=_do_test, daemon=True).start()

    def _stop_test(self):
        self.engine.stop_all_tests()
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("状态: 已停止")
        self.progress.setVisible(False)

    def _show_results(self, results):
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress.setVisible(False)

        self.result_table.setRowCount(len(results))
        for i, r in enumerate(results):
            self.result_table.setItem(i, 0, QTableWidgetItem(str(r['channel'])))
            self.result_table.setItem(i, 1, QTableWidgetItem(str(r['stuck_value'])))
            self.result_table.setItem(i, 2, QTableWidgetItem(r['status']))

        self.result_summary.setText(
            f"共检测 512 个通道，发现 {len(results)} 个故障"
        )
        if results:
            self.status_label.setText(f"状态: 检测完成 - 发现 {len(results)} 个故障通道!")
        else:
            self.status_label.setText("状态: 检测完成 - 所有通道正常 ✓")


# ===== 主窗口 =====
class DMXTesterWindow(BaseToolWindow):
    """DMX测试器主窗口"""

    def __init__(self, parent=None):
        super().__init__(
            tool_name='DMXTester',
            tool_title='DMX测试器',
            version='1.0.0',
            width=1200,
            height=800,
            parent=parent
        )

        # 初始化引擎
        self.engine = DMXTestEngine()
        self.engine.set_update_callback(self._on_engine_update)

        # 构建中心内容
        self._build_ui()

        self.logger.info("DMX测试器初始化完成")

    def _build_ui(self):
        """构建主UI"""
        tabs = QTabWidget()

        # Tab 1: 通道测试
        self.channel_tab = ChannelTestTab(self.engine)
        tabs.addTab(self.channel_tab, "通道测试")

        # Tab 2: 自动测试
        self.auto_tab = AutoTestTab(self.engine)
        tabs.addTab(self.auto_tab, "自动测试")

        # Tab 3: Universe视图
        self.universe_tab = UniverseViewTab(self.engine)
        tabs.addTab(self.universe_tab, "Universe视图")

        # Tab 4: 故障检测
        self.fault_tab = FaultDetectionTab(self.engine)
        tabs.addTab(self.fault_tab, "故障检测")

        self.set_central_content(tabs)

    def _on_engine_update(self):
        """引擎数据更新回调"""
        pass  # Universe视图有自己的定时刷新

    def closeEvent(self, event):
        """关闭时清理"""
        self.engine.stop_all_tests()
        super().closeEvent(event)


# ===== 入口 =====
def main():
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = DMXTesterWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
