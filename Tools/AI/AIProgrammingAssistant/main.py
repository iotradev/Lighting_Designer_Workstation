#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""AI编程助手 - 基于规则的灯光效果/Chase模式生成工具"""

import sys
import json
import math
import random
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
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QComboBox, QPushButton, QSpinBox, QDoubleSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter,
    QTabWidget, QCheckBox, QFileDialog, QMessageBox,
    QSlider, QScrollArea, QFrame, QGridLayout
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QBrush, QPen, QFont


# ── 模式生成引擎 ──────────────────────────────────────────────────────────────

COLOR_SCHEMES = {
    "红色系": ["#FF0000", "#CC0000", "#990000", "#FF3333", "#FF6666"],
    "蓝色系": ["#0000FF", "#0044CC", "#0066FF", "#3399FF", "#66CCFF"],
    "绿色系": ["#00FF00", "#00CC00", "#009900", "#33FF33", "#66FF66"],
    "暖色调": ["#FF0000", "#FF6600", "#FFCC00", "#FF3300", "#FF9900"],
    "冷色调": ["#0000FF", "#0066FF", "#00CCCC", "#6633FF", "#0099CC"],
    "彩虹": ["#FF0000", "#FF7700", "#FFFF00", "#00FF00", "#0000FF", "#8B00FF"],
    "黑白": ["#FFFFFF", "#CCCCCC", "#999999", "#666666", "#333333"],
    "紫粉": ["#FF00FF", "#CC00CC", "#FF33CC", "#FF66FF", "#990099"],
    "青蓝": ["#00FFFF", "#00CCCC", "#0099FF", "#33CCFF", "#66FFFF"],
    "金色": ["#FFD700", "#FFC200", "#FFB300", "#FFAA00", "#FF9500"]
}


class PatternGenerator:
    """效果/Chase模式生成引擎"""
    
    def generate_chase(self, num_steps, num_channels, colors, direction="forward"):
        """生成Chase效果"""
        steps = []
        color_list = colors if colors else ["#FFFFFF"]
        
        for step in range(num_steps):
            dmx = [0] * num_channels
            if direction == "forward":
                active = step % num_channels
            elif direction == "backward":
                active = (num_channels - 1 - step % num_channels)
            else:  # bounce
                cycle = num_channels * 2 - 2
                pos = step % cycle
                active = pos if pos < num_channels else cycle - pos
            
            ci = step % len(color_list)
            r, g, b = self._hex_to_rgb(color_list[ci])
            
            if active < num_channels:
                dmx[active] = min(255, 200 + (step % 56))
            # 辅助通道有微弱光
            for ch in range(max(0, active-1), min(num_channels, active+2)):
                if ch != active:
                    dmx[ch] = 50
            
            steps.append({"step": step + 1, "dmx_values": dmx, "active_channel": active, "color": color_list[ci]})
        
        return steps
    
    def generate_bounce(self, num_steps, num_channels, colors):
        """生成来回弹跳效果"""
        return self.generate_chase(num_steps, num_channels, colors, direction="bounce")
    
    def generate_random(self, num_steps, num_channels, colors, active_count=3):
        """生成随机效果"""
        steps = []
        color_list = colors if colors else ["#FFFFFF"]
        
        for step in range(num_steps):
            dmx = [0] * num_channels
            active_channels = random.sample(range(num_channels), min(active_count, num_channels))
            
            for ch in active_channels:
                ci = random.randint(0, len(color_list) - 1)
                dmx[ch] = random.randint(100, 255)
            
            steps.append({
                "step": step + 1,
                "dmx_values": dmx,
                "active_channel": active_channels,
                "color": color_list[step % len(color_list)]
            })
        
        return steps
    
    def generate_wave(self, num_steps, num_channels, colors, wave_width=3):
        """生成波浪效果"""
        steps = []
        color_list = colors if colors else ["#FFFFFF"]
        
        for step in range(num_steps):
            dmx = [0] * num_channels
            phase = (step / num_steps) * 2 * math.pi
            
            for ch in range(num_channels):
                offset = ch / num_channels * 2 * math.pi
                value = (math.sin(phase + offset) + 1) / 2  # 0-1
                dmx[ch] = int(value * 255)
            
            steps.append({
                "step": step + 1,
                "dmx_values": dmx,
                "active_channel": "wave",
                "color": color_list[step % len(color_list)]
            })
        
        return steps
    
    def generate_fade(self, num_steps, num_channels, colors):
        """生成渐变效果"""
        steps = []
        color_list = colors if colors else ["#FFFFFF"]
        
        for step in range(num_steps):
            dmx = [0] * num_channels
            progress = step / max(1, num_steps - 1)
            
            for ch in range(num_channels):
                ch_offset = ch / num_channels
                phase = (progress + ch_offset) % 1.0
                value = int((math.sin(phase * math.pi) * 255))
                dmx[ch] = min(255, max(0, value))
            
            steps.append({
                "step": step + 1,
                "dmx_values": dmx,
                "active_channel": "fade",
                "color": color_list[step % len(color_list)]
            })
        
        return steps
    
    def generate_strobe(self, num_steps, num_channels, colors, on_ratio=0.3):
        """生成频闪效果"""
        steps = []
        color_list = colors if colors else ["#FFFFFF"]
        
        for step in range(num_steps):
            dmx = [0] * num_channels
            is_on = (step % max(1, int(1 / on_ratio))) == 0
            
            for ch in range(num_channels):
                dmx[ch] = 255 if is_on else 0
            
            steps.append({
                "step": step + 1,
                "dmx_values": dmx,
                "active_channel": "all" if is_on else "none",
                "color": color_list[step % len(color_list)]
            })
        
        return steps
    
    def _hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


class PreviewGridWidget(QWidget):
    """DMX通道预览网格"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dmx_values = []
        self.num_channels = 16
        self.cell_size = 28
        self.setMinimumHeight(200)
    
    def set_data(self, dmx_values, num_channels):
        self.dmx_values = dmx_values
        self.num_channels = num_channels
        self.update()
    
    def paintEvent(self, event):
        if not self.dmx_values:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        cols = min(16, self.num_channels)
        rows = max(1, (self.num_channels + cols - 1) // cols)
        
        for ch in range(self.num_channels):
            row = ch // cols
            col = ch % cols
            x = 10 + col * (self.cell_size + 4)
            y = 10 + row * (self.cell_size + 4)
            
            value = self.dmx_values[ch] if ch < len(self.dmx_values) else 0
            intensity = value / 255.0
            
            color = QColor.fromRgbF(intensity, intensity * 0.3, 0.1, max(0.2, intensity))
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor("#555555"), 1))
            painter.drawRoundedRect(x, y, self.cell_size, self.cell_size, 3, 3)
            
            painter.setPen(QColor("#FFFFFF" if intensity > 0.5 else "#AAAAAA"))
            font = QFont("Consolas", 7)
            painter.setFont(font)
            painter.drawText(x, y, self.cell_size, self.cell_size, Qt.AlignmentFlag.AlignCenter, str(ch + 1))
            
            # 显示DMX值
            painter.setPen(QColor("#CCCCCC"))
            font2 = QFont("Consolas", 6)
            painter.setFont(font2)
            painter.drawText(x, y + self.cell_size - 10, self.cell_size, 10,
                           Qt.AlignmentFlag.AlignCenter, str(value))
        
        painter.end()
        
        self.setMinimumSize(
            10 + cols * (self.cell_size + 4) + 10,
            10 + rows * (self.cell_size + 4) + 10
        )


class AIProgrammingAssistant(BaseToolWindow):
    def __init__(self):
        super().__init__('AIProgrammingAssistant', 'AI编程助手', '1.0.0', 1200, 800)
        self.generator = PatternGenerator()
        self.current_cues = []
        self.animation_timer = QTimer()
        self.animation_step = 0
        self.is_animating = False
        self._build_ui()
        self._connect_signals()
        self.logger.info("AI编程助手已初始化")
    
    def _build_ui(self):
        central = QWidget()
        main_layout = QHBoxLayout(central)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧控制面板
        control_panel = self._build_control_panel()
        splitter.addWidget(control_panel)
        
        # 右侧结果面板
        result_panel = self._build_result_panel()
        splitter.addWidget(result_panel)
        
        splitter.setSizes([350, 850])
        main_layout.addWidget(splitter)
        
        self.set_central_content(central)
    
    def _build_control_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 模式类型
        group_pattern = QGroupBox("效果模式")
        pat_layout = QVBoxLayout(group_pattern)
        
        pat_layout.addWidget(QLabel("模式类型:"))
        self.pattern_combo = QComboBox()
        self.pattern_combo.addItems(["Chase(追逐)", "Bounce(弹跳)", "Random(随机)",
                                      "Wave(波浪)", "Fade(渐变)", "Strobe(频闪)"])
        pat_layout.addWidget(self.pattern_combo)
        
        pat_layout.addWidget(QLabel("步数:"))
        self.steps_spin = QSpinBox()
        self.steps_spin.setRange(4, 128)
        self.steps_spin.setValue(16)
        pat_layout.addWidget(self.steps_spin)
        
        pat_layout.addWidget(QLabel("通道数:"))
        self.channels_spin = QSpinBox()
        self.channels_spin.setRange(1, 512)
        self.channels_spin.setValue(16)
        pat_layout.addWidget(self.channels_spin)
        
        layout.addWidget(group_pattern)
        
        # 颜色方案
        group_color = QGroupBox("颜色方案")
        color_layout = QVBoxLayout(group_color)
        
        color_layout.addWidget(QLabel("颜色方案:"))
        self.color_combo = QComboBox()
        self.color_combo.addItems(list(COLOR_SCHEMES.keys()))
        color_layout.addWidget(self.color_combo)
        
        self.color_preview = QWidget()
        self.color_preview.setFixedHeight(30)
        self.color_preview.paintEvent = self._paint_color_preview
        color_layout.addWidget(self.color_preview)
        
        layout.addWidget(group_color)
        
        # 速度设置
        group_speed = QGroupBox("速度设置")
        speed_layout = QVBoxLayout(group_speed)
        
        speed_layout.addWidget(QLabel("动画速度 (ms/步):"))
        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(50, 2000)
        self.speed_spin.setValue(200)
        self.speed_spin.setSingleStep(50)
        speed_layout.addWidget(self.speed_spin)
        
        layout.addWidget(group_speed)
        
        # 生成按钮
        self.btn_generate = QPushButton("▶ 生成效果序列")
        self.btn_generate.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 10px; font-size: 13px; font-weight: bold; border-radius: 4px; } QPushButton:hover { background-color: #388E3C; }")
        layout.addWidget(self.btn_generate)
        
        # 预览按钮
        preview_layout = QHBoxLayout()
        self.btn_preview = QPushButton("▶ 播放预览")
        self.btn_preview.setEnabled(False)
        self.btn_stop = QPushButton("■ 停止")
        self.btn_stop.setEnabled(False)
        preview_layout.addWidget(self.btn_preview)
        preview_layout.addWidget(self.btn_stop)
        layout.addLayout(preview_layout)
        
        # 导出
        self.btn_export = QPushButton("导出到JSON")
        layout.addWidget(self.btn_export)
        
        layout.addStretch()
        return panel
    
    def _build_result_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        self.result_tabs = QTabWidget()
        
        # 预览标签页
        self.preview_tab = QWidget()
        preview_layout = QVBoxLayout(self.preview_tab)
        
        self.preview_label = QLabel("生成效果后点击播放预览")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(self.preview_label)
        
        scroll = QScrollArea()
        self.preview_grid = PreviewGridWidget()
        scroll.setWidget(self.preview_grid)
        scroll.setWidgetResizable(True)
        preview_layout.addWidget(scroll)
        
        self.step_label = QLabel("步骤: 0/0")
        self.step_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(self.step_label)
        
        self.result_tabs.addTab(self.preview_tab, "预览")
        
        # CUE列表标签页
        self.cue_tab = QWidget()
        cue_layout = QVBoxLayout(self.cue_tab)
        self.cue_table = QTableWidget()
        self.cue_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        cue_layout.addWidget(self.cue_table)
        self.result_tabs.addTab(self.cue_tab, "CUE列表")
        
        # DMX值标签页
        self.dmx_tab = QWidget()
        dmx_layout = QVBoxLayout(self.dmx_tab)
        self.dmx_table = QTableWidget()
        self.dmx_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        dmx_layout.addWidget(self.dmx_table)
        self.result_tabs.addTab(self.dmx_tab, "DMX值表")
        
        layout.addWidget(self.result_tabs)
        return panel
    
    def _paint_color_preview(self, event):
        painter = QPainter(self.color_preview)
        scheme_name = self.color_combo.currentText()
        colors = COLOR_SCHEMES.get(scheme_name, ["#FFFFFF"])
        w = self.color_preview.width() / len(colors) if colors else self.color_preview.width()
        for i, c in enumerate(colors):
            painter.setBrush(QBrush(QColor(c)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(int(i * w), 0, int(w) + 1, self.color_preview.height())
        painter.end()
    
    def _connect_signals(self):
        self.btn_generate.clicked.connect(self._on_generate)
        self.btn_preview.clicked.connect(self._on_preview)
        self.btn_stop.clicked.connect(self._on_stop_preview)
        self.btn_export.clicked.connect(self._on_export)
        self.color_combo.currentTextChanged.connect(lambda: self.color_preview.update())
        self.animation_timer.timeout.connect(self._on_animation_tick)
    
    def _on_generate(self):
        pattern = self.pattern_combo.currentText()
        num_steps = self.steps_spin.value()
        num_channels = self.channels_spin.value()
        scheme_name = self.color_combo.currentText()
        colors = COLOR_SCHEMES.get(scheme_name, ["#FFFFFF"])
        
        if "Chase" in pattern:
            self.current_cues = self.generator.generate_chase(num_steps, num_channels, colors)
        elif "Bounce" in pattern:
            self.current_cues = self.generator.generate_bounce(num_steps, num_channels, colors)
        elif "Random" in pattern:
            self.current_cues = self.generator.generate_random(num_steps, num_channels, colors)
        elif "Wave" in pattern:
            self.current_cues = self.generator.generate_wave(num_steps, num_channels, colors)
        elif "Fade" in pattern:
            self.current_cues = self.generator.generate_fade(num_steps, num_channels, colors)
        elif "Strobe" in pattern:
            self.current_cues = self.generator.generate_strobe(num_steps, num_channels, colors)
        
        self._display_cues(self.current_cues, num_channels)
        self.btn_preview.setEnabled(True)
        self.logger.info(f"生成{pattern}: {num_steps}步, {num_channels}通道")
    
    def _display_cues(self, cues, num_channels):
        # CUE表格
        self.cue_table.setRowCount(len(cues))
        self.cue_table.setColumnCount(4)
        self.cue_table.setHorizontalHeaderLabels(["步骤", "活动通道", "颜色", "DMX预览"])
        
        for i, cue in enumerate(cues):
            self.cue_table.setItem(i, 0, QTableWidgetItem(str(cue["step"])))
            active = cue["active_channel"]
            if isinstance(active, list):
                active_str = ", ".join(str(a + 1) for a in active)
            else:
                active_str = str(active)
            self.cue_table.setItem(i, 1, QTableWidgetItem(active_str))
            self.cue_table.setItem(i, 2, QTableWidgetItem(cue.get("color", "")))
            # 简化DMX预览
            dmx_preview = ",".join(str(v) for v in cue["dmx_values"][:8])
            if len(cue["dmx_values"]) > 8:
                dmx_preview += "..."
            self.cue_table.setItem(i, 3, QTableWidgetItem(dmx_preview))
        
        # DMX值表格
        self.dmx_table.setRowCount(len(cues))
        self.dmx_table.setColumnCount(min(num_channels, 32) + 1)
        headers = ["步骤"] + [f"CH{i+1}" for i in range(min(num_channels, 32))]
        self.dmx_table.setHorizontalHeaderLabels(headers)
        
        for i, cue in enumerate(cues):
            self.dmx_table.setItem(i, 0, QTableWidgetItem(str(cue["step"])))
            for ch in range(min(num_channels, 32)):
                val = cue["dmx_values"][ch] if ch < len(cue["dmx_values"]) else 0
                self.dmx_table.setItem(i, ch + 1, QTableWidgetItem(str(val)))
    
    def _on_preview(self):
        if not self.current_cues:
            return
        self.is_animating = True
        self.animation_step = 0
        self.btn_preview.setEnabled(False)
        self.btn_stop.setEnabled(True)
        num_channels = self.channels_spin.value()
        self.preview_grid.set_data([], num_channels)
        self.animation_timer.start(self.speed_spin.value())
    
    def _on_animation_tick(self):
        if self.animation_step >= len(self.current_cues):
            self.animation_step = 0  # 循环播放
        
        cue = self.current_cues[self.animation_step]
        num_channels = self.channels_spin.value()
        self.preview_grid.set_data(cue["dmx_values"], num_channels)
        self.step_label.setText(f"步骤: {cue['step']}/{len(self.current_cues)}")
        self.animation_step += 1
    
    def _on_stop_preview(self):
        self.animation_timer.stop()
        self.is_animating = False
        self.btn_preview.setEnabled(True)
        self.btn_stop.setEnabled(False)
    
    def _on_export(self):
        if not self.current_cues:
            QMessageBox.warning(self, "提示", "请先生成效果序列")
            return
        
        path, _ = QFileDialog.getSaveFileName(self, "导出JSON", "pattern_cues.json", "JSON文件 (*.json)")
        if path:
            export_data = {
                "pattern_type": self.pattern_combo.currentText(),
                "steps": len(self.current_cues),
                "channels": self.channels_spin.value(),
                "color_scheme": self.color_combo.currentText(),
                "speed_ms": self.speed_spin.value(),
                "cues": self.current_cues
            }
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
                QMessageBox.information(self, "成功", f"已导出到: {path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", str(e))

    def closeEvent(self, event):
        """关闭窗口时停止动画定时器"""
        if self.animation_timer.isActive():
            self.animation_timer.stop()
        super().closeEvent(event)


if __name__ == '__main__':
    from launcher_utils import run_tool
    run_tool(AIProgrammingAssistant, "AIProgrammingAssistant - 启动错误")