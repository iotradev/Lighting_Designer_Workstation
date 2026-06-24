#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""AI舞美助手 - 基于规则的舞台布局建议工具"""

import sys
import json
import math
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
    QTabWidget, QFileDialog, QMessageBox, QScrollArea, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QBrush, QPen, QFont


# ── 舞台布局规则引擎 ──────────────────────────────────────────────────────────

STAGE_PRESETS = {
    "演唱会": {
        "description": "大型演唱会舞台，需要强烈的视觉冲击",
        "truss_layout": [
            {"name": "主桁架", "type": "straight", "x": 50, "y": 10, "width": 700, "height": 20},
            {"name": "左侧面桁架", "type": "straight", "x": 30, "y": 10, "width": 20, "height": 400},
            {"name": "右侧面桁架", "type": "straight", "x": 750, "y": 10, "width": 20, "height": 400},
            {"name": "后桁架", "type": "straight", "x": 50, "y": 420, "width": 700, "height": 20},
            {"name": "T台桁架", "type": "straight", "x": 350, "y": 430, "width": 100, "height": 200}
        ],
        "fixtures": [
            {"type": "电脑摇头灯", "count": 24, "positions": "main_truss", "spacing": 30},
            {"type": "LED染色灯", "count": 32, "positions": "all_truss", "spacing": 25},
            {"type": "频闪灯", "count": 8, "positions": "main_truss", "spacing": 90},
            {"type": "追光灯", "count": 4, "positions": "corners", "spacing": 0},
            {"type": "激光灯", "count": 4, "positions": "side_truss", "spacing": 0}
        ]
    },
    "话剧/戏剧": {
        "description": "戏剧舞台，注重层次和氛围营造",
        "truss_layout": [
            {"name": "前区桁架", "type": "straight", "x": 100, "y": 10, "width": 600, "height": 15},
            {"name": "中区桁架", "type": "straight", "x": 100, "y": 200, "width": 600, "height": 15},
            {"name": "后区桁架", "type": "straight", "x": 100, "y": 380, "width": 600, "height": 15},
            {"name": "左侧耳光", "type": "straight", "x": 60, "y": 50, "width": 15, "height": 300},
            {"name": "右侧耳光", "type": "straight", "x": 725, "y": 50, "width": 15, "height": 300}
        ],
        "fixtures": [
            {"type": "成像灯", "count": 16, "positions": "all_truss", "spacing": 40},
            {"type": "聚光灯", "count": 8, "positions": "main_truss", "spacing": 80},
            {"type": "柔光灯", "count": 12, "positions": "all_truss", "spacing": 50},
            {"type": "染色灯", "count": 16, "positions": "all_truss", "spacing": 40},
            {"type": "追光灯", "count": 2, "positions": "corners", "spacing": 0}
        ]
    },
    "企业会议": {
        "description": "商务会议/发布会，简洁专业",
        "truss_layout": [
            {"name": "主桁架", "type": "straight", "x": 100, "y": 10, "width": 600, "height": 15},
            {"name": "背景桁架", "type": "straight", "x": 100, "y": 350, "width": 600, "height": 15}
        ],
        "fixtures": [
            {"type": "LED面板灯", "count": 12, "positions": "main_truss", "spacing": 50},
            {"type": "筒灯", "count": 16, "positions": "ceiling", "spacing": 100},
            {"type": "面光灯", "count": 8, "positions": "main_truss", "spacing": 80},
            {"type": "背景灯", "count": 8, "positions": "back_truss", "spacing": 75}
        ]
    },
    "舞蹈演出": {
        "description": "舞蹈演出，需要均匀的舞台覆盖",
        "truss_layout": [
            {"name": "前区桁架", "type": "straight", "x": 80, "y": 10, "width": 640, "height": 15},
            {"name": "中区桁架", "type": "straight", "x": 80, "y": 180, "width": 640, "height": 15},
            {"name": "后区桁架", "type": "straight", "x": 80, "y": 350, "width": 640, "height": 15},
            {"name": "左侧桁架", "type": "straight", "x": 50, "y": 10, "width": 15, "height": 380},
            {"name": "右侧桁架", "type": "straight", "x": 735, "y": 10, "width": 15, "height": 380}
        ],
        "fixtures": [
            {"type": "LED染色灯", "count": 24, "positions": "all_truss", "spacing": 30},
            {"type": "聚光灯", "count": 12, "positions": "all_truss", "spacing": 55},
            {"type": "地排灯", "count": 8, "positions": "floor_back", "spacing": 80},
            {"type": "追光灯", "count": 2, "positions": "corners", "spacing": 0}
        ]
    },
    "时装秀": {
        "description": "时装秀T台布局",
        "truss_layout": [
            {"name": "主舞台桁架", "type": "straight", "x": 150, "y": 10, "width": 500, "height": 15},
            {"name": "T台桁架", "type": "straight", "x": 350, "y": 25, "width": 100, "height": 500},
            {"name": "T台终端桁架", "type": "straight", "x": 300, "y": 530, "width": 200, "height": 15}
        ],
        "fixtures": [
            {"type": "LED染色灯", "count": 20, "positions": "all_truss", "spacing": 30},
            {"type": "成像灯", "count": 16, "positions": "runway_truss", "spacing": 35},
            {"type": "频闪灯", "count": 6, "positions": "main_truss", "spacing": 90},
            {"type": "追光灯", "count": 3, "positions": "corners", "spacing": 0}
        ]
    }
}


class StageLayoutEngine:
    """舞台布局建议引擎"""
    
    def suggest_layout(self, stage_type, width, depth):
        preset = STAGE_PRESETS.get(stage_type, STAGE_PRESETS["演唱会"])
        
        # 按比例缩放桁架
        scale_x = width / 800
        scale_y = depth / 600
        
        truss = []
        for t in preset["truss_layout"]:
            truss.append({
                "name": t["name"],
                "type": t["type"],
                "x": int(t["x"] * scale_x),
                "y": int(t["y"] * scale_y),
                "width": int(t["width"] * scale_x),
                "height": int(t["height"] * scale_y)
            })
        
        # 生成灯具位置
        fixtures = self._place_fixtures(preset["fixtures"], truss, width, depth, scale_x, scale_y)
        
        return {
            "stage_type": stage_type,
            "stage_size": {"width": width, "depth": depth},
            "description": preset["description"],
            "truss_layout": truss,
            "fixtures": fixtures
        }
    
    def _place_fixtures(self, fixture_defs, truss_list, stage_w, stage_d, sx, sy):
        result = []
        fixture_id = 1
        
        for fd in fixture_defs:
            target_truss = self._get_target_truss(fd["positions"], truss_list)
            
            if fd["positions"] == "corners":
                # 角落位置
                corners = [
                    (20, 20), (stage_w - 20, 20),
                    (20, stage_d - 20), (stage_w - 20, stage_d - 20)
                ]
                for i in range(min(fd["count"], len(corners))):
                    result.append({
                        "id": fixture_id,
                        "type": fd["type"],
                        "x": corners[i][0],
                        "y": corners[i][1],
                        "truss": "角落支架"
                    })
                    fixture_id += 1
            elif fd["positions"] == "ceiling":
                # 天花板均匀分布
                cols = max(1, int(math.sqrt(fd["count"])))
                rows = max(1, (fd["count"] + cols - 1) // cols)
                for i in range(fd["count"]):
                    r = i // cols
                    c = i % cols
                    x = int(stage_w * (c + 1) / (cols + 1))
                    y = int(stage_d * (r + 1) / (rows + 1))
                    result.append({
                        "id": fixture_id, "type": fd["type"],
                        "x": x, "y": y, "truss": "天花板"
                    })
                    fixture_id += 1
            elif fd["positions"] == "floor_back":
                for i in range(fd["count"]):
                    x = int(stage_w * (i + 1) / (fd["count"] + 1))
                    y = stage_d - 15
                    result.append({
                        "id": fixture_id, "type": fd["type"],
                        "x": x, "y": y, "truss": "地面"
                    })
                    fixture_id += 1
            else:
                # 在桁架上分布
                placed = 0
                for t in target_truss:
                    if placed >= fd["count"]:
                        break
                    spacing = max(1, fd.get("spacing", 30))
                    if t["width"] > t["height"]:  # 水平桁架
                        count_on_truss = min(fd["count"] - placed, max(1, t["width"] // spacing))
                        for i in range(count_on_truss):
                            x = t["x"] + int(t["width"] * (i + 0.5) / count_on_truss)
                            y = t["y"] + t["height"] + 5
                            result.append({
                                "id": fixture_id, "type": fd["type"],
                                "x": x, "y": y, "truss": t["name"]
                            })
                            fixture_id += 1
                            placed += 1
                    else:  # 垂直桁架
                        count_on_truss = min(fd["count"] - placed, max(1, t["height"] // spacing))
                        for i in range(count_on_truss):
                            x = t["x"] + t["width"] + 5
                            y = t["y"] + int(t["height"] * (i + 0.5) / count_on_truss)
                            result.append({
                                "id": fixture_id, "type": fd["type"],
                                "x": x, "y": y, "truss": t["name"]
                            })
                            fixture_id += 1
                            placed += 1
        
        return result
    
    def _get_target_truss(self, positions, truss_list):
        if positions == "main_truss":
            return [t for t in truss_list if "主" in t["name"] or "前" in t["name"]][:1]
        elif positions == "all_truss":
            return truss_list
        elif positions == "back_truss":
            return [t for t in truss_list if "后" in t["name"] or "背景" in t["name"]]
        elif positions == "side_truss":
            return [t for t in truss_list if "侧" in t["name"] or "左" in t["name"] or "右" in t["name"]]
        elif positions == "runway_truss":
            return [t for t in truss_list if "T台" in t["name"]]
        return truss_list[:1]


class StageCanvas(QWidget):
    """舞台布局可视化画布"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout_data = None
        self.setMinimumSize(600, 450)
    
    def set_layout(self, data):
        self.layout_data = data
        self.update()
    
    def paintEvent(self, event):
        if not self.layout_data:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制舞台边界
        painter.setPen(QPen(QColor("#888888"), 2))
        painter.setBrush(QBrush(QColor("#1a1a2e")))
        painter.drawRect(10, 10, self.width() - 20, self.height() - 60)
        
        # 舞台标签
        painter.setPen(QColor("#666666"))
        painter.setFont(QFont("Microsoft YaHei", 8))
        painter.drawText(15, self.height() - 45, f"舞台 {self.layout_data['stage_size']['width']}m × {self.layout_data['stage_size']['depth']}m")
        
        scale_x = (self.width() - 40) / max(1, 800)
        scale_y = (self.height() - 80) / max(1, 600)
        
        # 绘制桁架
        for truss in self.layout_data.get("truss_layout", []):
            x = 20 + int(truss["x"] * scale_x)
            y = 20 + int(truss["y"] * scale_y)
            w = max(5, int(truss["width"] * scale_x))
            h = max(5, int(truss["height"] * scale_y))
            
            painter.setPen(QPen(QColor("#FFD700"), 2))
            painter.setBrush(QBrush(QColor(255, 215, 0, 60)))
            painter.drawRect(x, y, w, h)
            
            painter.setPen(QColor("#FFD700"))
            painter.setFont(QFont("Microsoft YaHei", 7))
            painter.drawText(x + 2, y + h + 12, truss["name"])
        
        # 绘制灯具
        color_map = {
            "电脑摇头灯": "#FF4444", "LED染色灯": "#44FF44", "LED面板灯": "#44FF44",
            "成像灯": "#4488FF", "聚光灯": "#FFFF44", "柔光灯": "#FF88FF",
            "频闪灯": "#FFFFFF", "追光灯": "#FF8800", "激光灯": "#00FFFF",
            "筒灯": "#AAAAAA", "面光灯": "#FFAA44", "背景灯": "#8844FF",
            "地排灯": "#44FFAA", "染色灯": "#44FF44"
        }
        
        for fix in self.layout_data.get("fixtures", []):
            x = 20 + int(fix["x"] * scale_x)
            y = 20 + int(fix["y"] * scale_y)
            
            color = QColor(color_map.get(fix["type"], "#FFFFFF"))
            painter.setPen(QPen(color, 1))
            painter.setBrush(QBrush(color.darker(200)))
            painter.drawEllipse(x - 4, y - 4, 8, 8)
        
        # 图例
        legend_y = self.height() - 40
        painter.setPen(QColor("#CCCCCC"))
        painter.setFont(QFont("Microsoft YaHei", 7))
        legend_x = 20
        for ftype, color_hex in list(color_map.items())[:6]:
            painter.setBrush(QBrush(QColor(color_hex)))
            painter.setPen(QPen(QColor(color_hex), 1))
            painter.drawEllipse(legend_x, legend_y, 8, 8)
            painter.setPen(QColor("#CCCCCC"))
            painter.drawText(legend_x + 12, legend_y + 8, ftype)
            legend_x += 100
        
        painter.end()


class AIStageDesigner(BaseToolWindow):
    def __init__(self):
        super().__init__('AIStageDesigner', 'AI舞美助手', '1.0.0', 1200, 800)
        self.engine = StageLayoutEngine()
        self.current_layout = None
        self._build_ui()
        self._connect_signals()
        self.logger.info("AI舞美助手已初始化")
    
    def _build_ui(self):
        central = QWidget()
        main_layout = QHBoxLayout(central)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧控制面板
        control_panel = self._build_control_panel()
        splitter.addWidget(control_panel)
        
        # 右侧显示面板
        display_panel = self._build_display_panel()
        splitter.addWidget(display_panel)
        
        splitter.setSizes([300, 900])
        main_layout.addWidget(splitter)
        
        self.set_central_content(central)
    
    def _build_control_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 舞台类型
        group_type = QGroupBox("舞台类型")
        type_layout = QVBoxLayout(group_type)
        
        type_layout.addWidget(QLabel("演出类型:"))
        self.stage_combo = QComboBox()
        self.stage_combo.addItems(list(STAGE_PRESETS.keys()))
        type_layout.addWidget(self.stage_combo)
        
        self.stage_desc = QLabel("")
        self.stage_desc.setWordWrap(True)
        type_layout.addWidget(self.stage_desc)
        
        layout.addWidget(group_type)
        
        # 舞台尺寸
        group_size = QGroupBox("舞台尺寸 (米)")
        size_layout = QVBoxLayout(group_size)
        
        size_layout.addWidget(QLabel("宽度:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(5, 100)
        self.width_spin.setValue(20)
        self.width_spin.setSuffix(" m")
        size_layout.addWidget(self.width_spin)
        
        size_layout.addWidget(QLabel("深度:"))
        self.depth_spin = QSpinBox()
        self.depth_spin.setRange(3, 80)
        self.depth_spin.setValue(15)
        self.depth_spin.setSuffix(" m")
        size_layout.addWidget(self.depth_spin)
        
        size_layout.addWidget(QLabel("高度:"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(3, 30)
        self.height_spin.setValue(8)
        self.height_spin.setSuffix(" m")
        size_layout.addWidget(self.height_spin)
        
        layout.addWidget(group_size)
        
        # 生成按钮
        self.btn_generate = QPushButton("▶ 生成舞台布局")
        self.btn_generate.setStyleSheet("QPushButton { background-color: #FF9800; color: white; padding: 10px; font-size: 13px; font-weight: bold; border-radius: 4px; } QPushButton:hover { background-color: #F57C00; }")
        layout.addWidget(self.btn_generate)
        
        # 导出按钮
        self.btn_export = QPushButton("导出布局到JSON")
        layout.addWidget(self.btn_export)
        
        layout.addStretch()
        return panel
    
    def _build_display_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        self.display_tabs = QTabWidget()
        
        # 可视化标签页
        self.canvas_tab = QWidget()
        canvas_layout = QVBoxLayout(self.canvas_tab)
        self.canvas = StageCanvas()
        canvas_layout.addWidget(self.canvas)
        self.display_tabs.addTab(self.canvas_tab, "舞台视图")
        
        # 桁架详情标签页
        self.truss_tab = QWidget()
        truss_layout = QVBoxLayout(self.truss_tab)
        self.truss_table = QTableWidget()
        self.truss_table.setColumnCount(5)
        self.truss_table.setHorizontalHeaderLabels(["名称", "X", "Y", "宽度", "高度"])
        self.truss_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        truss_layout.addWidget(self.truss_table)
        self.display_tabs.addTab(self.truss_tab, "桁架布局")
        
        # 灯具详情标签页
        self.fixture_tab = QWidget()
        fix_layout = QVBoxLayout(self.fixture_tab)
        self.fixture_table = QTableWidget()
        self.fixture_table.setColumnCount(5)
        self.fixture_table.setHorizontalHeaderLabels(["编号", "类型", "X", "Y", "所属桁架"])
        self.fixture_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        fix_layout.addWidget(self.fixture_table)
        self.fixture_summary = QLabel("")
        self.fixture_summary.setWordWrap(True)
        fix_layout.addWidget(self.fixture_summary)
        self.display_tabs.addTab(self.fixture_tab, "灯具布局")
        
        layout.addWidget(self.display_tabs)
        return panel
    
    def _connect_signals(self):
        self.btn_generate.clicked.connect(self._on_generate)
        self.btn_export.clicked.connect(self._on_export)
        self.stage_combo.currentTextChanged.connect(self._on_stage_changed)
        self._on_stage_changed(self.stage_combo.currentText())
    
    def _on_stage_changed(self, stage_type):
        preset = STAGE_PRESETS.get(stage_type, {})
        self.stage_desc.setText(preset.get("description", ""))
    
    def _on_generate(self):
        stage_type = self.stage_combo.currentText()
        width = self.width_spin.value()
        depth = self.depth_spin.value()
        
        self.current_layout = self.engine.suggest_layout(stage_type, width, depth)
        
        self.canvas.set_layout(self.current_layout)
        self._display_truss(self.current_layout["truss_layout"])
        self._display_fixtures(self.current_layout["fixtures"])
        
        self.logger.info(f"生成舞台布局: {stage_type}, {width}×{depth}m")
    
    def _display_truss(self, truss_list):
        self.truss_table.setRowCount(len(truss_list))
        for i, t in enumerate(truss_list):
            self.truss_table.setItem(i, 0, QTableWidgetItem(t["name"]))
            self.truss_table.setItem(i, 1, QTableWidgetItem(str(t["x"])))
            self.truss_table.setItem(i, 2, QTableWidgetItem(str(t["y"])))
            self.truss_table.setItem(i, 3, QTableWidgetItem(str(t["width"])))
            self.truss_table.setItem(i, 4, QTableWidgetItem(str(t["height"])))
    
    def _display_fixtures(self, fixtures):
        self.fixture_table.setRowCount(len(fixtures))
        for i, f in enumerate(fixtures):
            self.fixture_table.setItem(i, 0, QTableWidgetItem(str(f["id"])))
            self.fixture_table.setItem(i, 1, QTableWidgetItem(f["type"]))
            self.fixture_table.setItem(i, 2, QTableWidgetItem(str(f["x"])))
            self.fixture_table.setItem(i, 3, QTableWidgetItem(str(f["y"])))
            self.fixture_table.setItem(i, 4, QTableWidgetItem(f["truss"]))
        
        # 统计
        type_counts = {}
        for f in fixtures:
            type_counts[f["type"]] = type_counts.get(f["type"], 0) + 1
        summary = "灯具统计: " + ", ".join(f"{t}×{c}" for t, c in type_counts.items())
        summary += f"\n总计: {len(fixtures)} 台灯具"
        self.fixture_summary.setText(summary)
    
    def _on_export(self):
        if not self.current_layout:
            QMessageBox.warning(self, "提示", "请先生成舞台布局")
            return
        
        path, _ = QFileDialog.getSaveFileName(self, "导出JSON", "stage_layout.json", "JSON文件 (*.json)")
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(self.current_layout, f, ensure_ascii=False, indent=2)
                QMessageBox.information(self, "成功", f"已导出到: {path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", str(e))


if __name__ == '__main__':
    from launcher_utils import run_tool
    run_tool(AIStageDesigner, "AIStageDesigner - 启动错误")