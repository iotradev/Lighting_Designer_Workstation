#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""AI灯光设计助手 - 基于规则的灯光设计建议工具"""

import sys
import json
import csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'Common'))
from ui.base_window import BaseToolWindow

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QComboBox, QTextEdit, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter,
    QTabWidget, QScrollArea, QFrame, QFileDialog, QMessageBox,
    QPlainTextEdit, QListWidget, QListWidgetItem, QGridLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QBrush, QPen, QFont


# ── 规则引擎数据 ──────────────────────────────────────────────────────────────

VENUE_DEFAULTS = {
    "剧院": {
        "positions": ["台口上方", "两侧耳光", "天幕后", "观众席上方", "舞台地面"],
        "fixtures": ["电脑摇头灯×12", "LED染色灯×16", "成像灯×8", "追光灯×2"],
        "default_mood": "庄重典雅"
    },
    "演唱会": {
        "positions": ["主舞台上方", "舞台两侧", "观众区后方", "T台上方", "舞台地面边缘"],
        "fixtures": ["电脑摇头灯×24", "LED染色灯×32", "激光灯×4", "频闪灯×8", "追光灯×4"],
        "default_mood": "热情奔放"
    },
    "会议室": {
        "positions": ["天花板均匀分布", "讲台上方", "屏幕两侧"],
        "fixtures": ["LED面板灯×8", "筒灯×12", "面光灯×4"],
        "default_mood": "明亮清晰"
    },
    "宴会厅": {
        "positions": ["天花板均匀分布", "舞台上方", "入口两侧", "舞池上方"],
        "fixtures": ["电脑摇头灯×8", "LED染色灯×12", "星空幕布×1", "激光灯×2"],
        "default_mood": "温馨浪漫"
    },
    "户外音乐节": {
        "positions": ["主舞台桁架", "副舞台", "音响塔", "观众区后方高塔"],
        "fixtures": ["电脑摇头灯×32", "LED染色灯×48", "激光灯×8", "频闪灯×16", "追光灯×6"],
        "default_mood": "震撼动感"
    },
    "演播室": {
        "positions": ["顶部网格", "侧面", "背景", "地面反射"],
        "fixtures": ["LED面板灯×16", "聚光灯×8", "柔光灯×8", "背景灯×4"],
        "default_mood": "专业明亮"
    }
}

MOOD_COLORS = {
    "热情奔放": {"primary": "#FF3333", "secondary": "#FF6600", "accent": "#FFCC00", "wash": "#FF4444"},
    "温馨浪漫": {"primary": "#FF69B4", "secondary": "#FF1493", "accent": "#FFB6C1", "wash": "#FFC0CB"},
    "庄重典雅": {"primary": "#4169E1", "secondary": "#191970", "accent": "#FFD700", "wash": "#6A5ACD"},
    "神秘梦幻": {"primary": "#8A2BE2", "secondary": "#4B0082", "accent": "#00CED1", "wash": "#9370DB"},
    "震撼动感": {"primary": "#FF0000", "secondary": "#00FF00", "accent": "#0000FF", "wash": "#FF00FF"},
    "明亮清晰": {"primary": "#FFFFFF", "secondary": "#F0F0F0", "accent": "#E0E0E0", "wash": "#FFFFF0"},
    "忧郁深沉": {"primary": "#2F4F4F", "secondary": "#1C1C3C", "accent": "#483D8B", "wash": "#363652"},
    "活力四射": {"primary": "#FF4500", "secondary": "#FF8C00", "accent": "#ADFF2F", "wash": "#FF6347"},
    "宁静祥和": {"primary": "#87CEEB", "secondary": "#4682B4", "accent": "#98FB98", "wash": "#B0E0E6"},
    "科技未来": {"primary": "#00FFFF", "secondary": "#0080FF", "accent": "#FF00FF", "wash": "#00CED1"},
    "自然清新": {"primary": "#32CD32", "secondary": "#228B22", "accent": "#98FB98", "wash": "#90EE90"},
    "复古怀旧": {"primary": "#DAA520", "secondary": "#B8860B", "accent": "#CD853F", "wash": "#DEB887"}
}

ENERGY_TIMING = {
    "慢速抒情": {"fade_in": 5.0, "hold": 8.0, "fade_out": 5.0, "crossfade": 3.0},
    "中速平稳": {"fade_in": 3.0, "hold": 5.0, "fade_out": 3.0, "crossfade": 2.0},
    "快速激昂": {"fade_in": 0.5, "hold": 2.0, "fade_out": 0.5, "crossfade": 0.5},
    "极快节奏": {"fade_in": 0.2, "hold": 0.8, "fade_out": 0.2, "crossfade": 0.2},
    "渐进变化": {"fade_in": 8.0, "hold": 10.0, "fade_out": 8.0, "crossfade": 5.0}
}

MOOD_ENERGY_MAP = {
    "热情奔放": "快速激昂",
    "温馨浪漫": "慢速抒情",
    "庄重典雅": "中速平稳",
    "神秘梦幻": "渐进变化",
    "震撼动感": "极快节奏",
    "明亮清晰": "中速平稳",
    "忧郁深沉": "慢速抒情",
    "活力四射": "快速激昂",
    "宁静祥和": "慢速抒情",
    "科技未来": "快速激昂",
    "自然清新": "中速平稳",
    "复古怀旧": "中速平稳"
}

CUE_TEMPLATES = {
    "开场": {"intensity": 60, "description": "开场亮灯，吸引观众注意"},
    "渐亮": {"intensity": 80, "description": "逐渐增加亮度"},
    "全亮": {"intensity": 100, "description": "全场最亮"},
    "渐暗": {"intensity": 30, "description": "逐渐降低亮度"},
    "暗场": {"intensity": 0, "description": "完全熄灭"},
    "追光": {"intensity": 90, "description": "追光灯跟踪主角"},
    "染色": {"intensity": 70, "description": "全场染色效果"},
    "闪烁": {"intensity": 85, "description": "快速闪烁效果"},
    "扫描": {"intensity": 75, "description": "光束扫描全场"},
    "聚焦": {"intensity": 95, "description": "聚焦舞台中心"}
}


class RuleEngine:
    """基于规则的灯光设计引擎"""
    
    def analyze_mood(self, mood_text):
        """从文本中提取最匹配的情绪"""
        if not mood_text.strip():
            return "明亮清晰", "中速平稳"
        
        mood_text = mood_text.lower()
        best_match = "明亮清晰"
        best_score = 0
        
        keywords = {
            "热情奔放": ["热情", "奔放", "热烈", "激昂", "活力", "欢快", "high"],
            "温馨浪漫": ["温馨", "浪漫", "柔和", "温暖", "甜蜜", "love", "warm"],
            "庄重典雅": ["庄重", "典雅", "正式", "严肃", "高贵", "formal", "elegant"],
            "神秘梦幻": ["神秘", "梦幻", "魔幻", "奇幻", "虚幻", "magic", "dream"],
            "震撼动感": ["震撼", "动感", "摇滚", "电子", "狂野", "rock", "edm"],
            "明亮清晰": ["明亮", "清晰", "干净", "简约", "专业", "bright", "clean"],
            "忧郁深沉": ["忧郁", "深沉", "悲伤", "沉重", "暗淡", "sad", "dark"],
            "活力四射": ["活力", "四射", "青春", "朝气", "跳跃", "energy", "fun"],
            "宁静祥和": ["宁静", "祥和", "平静", "安详", "放松", "calm", "peace"],
            "科技未来": ["科技", "未来", "赛博", "电子", "科幻", "cyber", "future"],
            "自然清新": ["自然", "清新", "田园", "森林", "绿色", "nature", "fresh"],
            "复古怀旧": ["复古", "怀旧", "古典", "经典", "老式", "retro", "vintage"]
        }
        
        for mood, words in keywords.items():
            score = sum(1 for w in words if w in mood_text)
            if score > best_score:
                best_score = score
                best_match = mood
        
        energy = MOOD_ENERGY_MAP.get(best_match, "中速平稳")
        return best_match, energy
    
    def generate_suggestions(self, venue_type, mood_text, fixtures_text):
        """生成灯光设计方案"""
        venue_info = VENUE_DEFAULTS.get(venue_type, VENUE_DEFAULTS["剧院"])
        mood, energy = self.analyze_mood(mood_text)
        colors = MOOD_COLORS.get(mood, MOOD_COLORS["明亮清晰"])
        timing = ENERGY_TIMING.get(energy, ENERGY_TIMING["中速平稳"])
        
        # 生成颜色面板
        color_palette = self._build_color_palette(colors)
        
        # 生成CUE序列
        cue_sequence = self._build_cue_sequence(mood, energy, timing, venue_type)
        
        # 生成灯位建议
        beam_positions = self._build_beam_positions(venue_info, fixtures_text)
        
        return {
            "venue": venue_type,
            "mood": mood,
            "energy": energy,
            "color_palette": color_palette,
            "cue_sequence": cue_sequence,
            "beam_positions": beam_positions,
            "fixture_suggestions": venue_info["fixtures"],
            "timing": timing
        }
    
    def _build_color_palette(self, colors):
        return [
            {"name": "主色", "hex": colors["primary"], "usage": "主光、追光"},
            {"name": "副色", "hex": colors["secondary"], "usage": "侧面染色"},
            {"name": "强调色", "hex": colors["accent"], "usage": "重点照明、效果"},
            {"name": "环境色", "hex": colors["wash"], "usage": "全场铺光、背景"}
        ]
    
    def _build_cue_sequence(self, mood, energy, timing, venue):
        cues = []
        
        if venue in ["演唱会", "户外音乐节"]:
            cue_order = ["暗场", "渐亮", "追光", "染色", "扫描", "全亮", "闪烁", "聚焦", "渐暗", "暗场"]
        elif venue in ["剧院", "演播室"]:
            cue_order = ["暗场", "渐亮", "追光", "染色", "聚焦", "渐暗", "暗场"]
        elif venue in ["会议室"]:
            cue_order = ["暗场", "渐亮", "全亮", "聚焦", "渐暗"]
        else:
            cue_order = ["暗场", "渐亮", "染色", "追光", "扫描", "渐暗", "暗场"]
        
        current_time = 0.0
        for i, cue_name in enumerate(cue_order):
            template = CUE_TEMPLATES[cue_name]
            if i == 0:
                dur = 0.5
            elif cue_name in ["暗场", "渐暗"]:
                dur = timing["fade_out"]
            elif cue_name in ["渐亮", "染色"]:
                dur = timing["fade_in"]
            elif cue_name in ["闪烁", "扫描"]:
                dur = timing["hold"] * 0.5
            else:
                dur = timing["hold"]
            
            cues.append({
                "cue_number": i + 1,
                "name": cue_name,
                "time": round(current_time, 1),
                "duration": round(dur, 1),
                "intensity": template["intensity"],
                "description": template["description"]
            })
            current_time += dur
        
        return cues
    
    def _build_beam_positions(self, venue_info, fixtures_text):
        positions = []
        for i, pos in enumerate(venue_info["positions"]):
            angle_h = 15 + (i * 25) % 90
            angle_v = 30 + (i * 15) % 45
            positions.append({
                "name": pos,
                "horizontal_angle": angle_h,
                "vertical_angle": angle_v,
                "suggested_gobo": "无" if i % 3 == 0 else ["棱镜", "光栅", "水纹"][i % 3],
                "priority": "高" if i < 2 else "中" if i < 4 else "低"
            })
        return positions


class ColorSwatchWidget(QWidget):
    """颜色色块显示控件"""
    def __init__(self, color_hex, label="", parent=None):
        super().__init__(parent)
        self.color = QColor(color_hex)
        self.label = label
        self.setFixedSize(80, 60)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(self.color))
        painter.setPen(QPen(QColor("#333333"), 1))
        painter.drawRoundedRect(2, 2, self.width()-4, self.height()-22, 6, 6)
        painter.setPen(QColor("#CCCCCC"))
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        painter.drawText(0, self.height()-18, self.width(), 16, Qt.AlignmentFlag.AlignCenter, self.label)


class AILightingDesigner(BaseToolWindow):
    def __init__(self):
        super().__init__('AILightingDesigner', 'AI灯光设计助手', '1.0.0', 1300, 850)
        self.engine = RuleEngine()
        self.current_suggestions = None
        self._build_ui()
        self._connect_signals()
        self.logger.info("AI灯光设计助手已初始化")
    
    def _build_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout(central)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧输入面板
        input_panel = self._build_input_panel()
        splitter.addWidget(input_panel)
        
        # 右侧结果面板
        result_panel = self._build_result_panel()
        splitter.addWidget(result_panel)
        
        splitter.setSizes([400, 900])
        main_layout.addWidget(splitter)
        
        self.set_central_content(central)
    
    def _build_input_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 场地类型
        group_venue = QGroupBox("场地设置")
        venue_layout = QVBoxLayout(group_venue)
        
        venue_layout.addWidget(QLabel("场地类型:"))
        self.venue_combo = QComboBox()
        self.venue_combo.addItems(list(VENUE_DEFAULTS.keys()))
        venue_layout.addWidget(self.venue_combo)
        
        venue_layout.addWidget(QLabel("情绪描述 (可输入关键词):"))
        self.mood_input = QLineEdit()
        self.mood_input.setPlaceholderText("如: 热情、浪漫、震撼、科技感...")
        venue_layout.addWidget(self.mood_input)
        
        venue_layout.addWidget(QLabel("预设情绪:"))
        self.mood_preset = QComboBox()
        self.mood_preset.addItems(list(MOOD_COLORS.keys()))
        venue_layout.addWidget(self.mood_preset)
        
        layout.addWidget(group_venue)
        
        # 灯具列表
        group_fixtures = QGroupBox("灯具清单")
        fixture_layout = QVBoxLayout(group_fixtures)
        
        self.fixture_input = QPlainTextEdit()
        self.fixture_input.setPlaceholderText("输入当前可用灯具，每行一个\n如:\n电脑摇头灯×12\nLED染色灯×16\n成像灯×8")
        self.fixture_input.setMaximumHeight(150)
        fixture_layout.addWidget(self.fixture_input)
        
        self.btn_load_default = QPushButton("加载场地默认灯具")
        fixture_layout.addWidget(self.btn_load_default)
        
        layout.addWidget(group_fixtures)
        
        # 生成按钮
        self.btn_generate = QPushButton("▶ 生成灯光设计方案")
        self.btn_generate.setStyleSheet("QPushButton { background-color: #2196F3; color: white; padding: 12px; font-size: 14px; font-weight: bold; border-radius: 4px; } QPushButton:hover { background-color: #1976D2; }")
        layout.addWidget(self.btn_generate)
        
        # 导出按钮
        export_layout = QHBoxLayout()
        self.btn_export_json = QPushButton("导出JSON")
        self.btn_export_csv = QPushButton("导出CSV")
        export_layout.addWidget(self.btn_export_json)
        export_layout.addWidget(self.btn_export_csv)
        layout.addLayout(export_layout)
        
        layout.addStretch()
        return panel
    
    def _build_result_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        self.result_tabs = QTabWidget()
        
        # 颜色面板标签页
        self.color_tab = QWidget()
        self.color_layout = QVBoxLayout(self.color_tab)
        self.color_grid_widget = QWidget()
        self.color_grid = QGridLayout(self.color_grid_widget)
        self.color_layout.addWidget(self.color_grid_widget)
        self.color_info = QLabel("选择情绪后生成颜色建议")
        self.color_info.setWordWrap(True)
        self.color_layout.addWidget(self.color_info)
        self.color_layout.addStretch()
        self.result_tabs.addTab(self.color_tab, "颜色面板")
        
        # CUE序列标签页
        self.cue_tab = QWidget()
        cue_layout = QVBoxLayout(self.cue_tab)
        self.cue_table = QTableWidget()
        self.cue_table.setColumnCount(6)
        self.cue_table.setHorizontalHeaderLabels(["CUE", "名称", "时间(秒)", "持续(秒)", "亮度%", "说明"])
        self.cue_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        cue_layout.addWidget(self.cue_table)
        self.result_tabs.addTab(self.cue_tab, "CUE序列")
        
        # 灯位建议标签页
        self.position_tab = QWidget()
        pos_layout = QVBoxLayout(self.position_tab)
        self.position_table = QTableWidget()
        self.position_table.setColumnCount(5)
        self.position_table.setHorizontalHeaderLabels(["位置名称", "水平角度", "俯仰角度", "建议图案", "优先级"])
        self.position_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        pos_layout.addWidget(self.position_table)
        self.result_tabs.addTab(self.position_tab, "灯位建议")
        
        # 灯具建议标签页
        self.fixture_tab = QWidget()
        fix_layout = QVBoxLayout(self.fixture_tab)
        self.fixture_list_widget = QListWidget()
        fix_layout.addWidget(self.fixture_list_widget)
        self.fixture_suggestion_label = QLabel("")
        self.fixture_suggestion_label.setWordWrap(True)
        fix_layout.addWidget(self.fixture_suggestion_label)
        self.result_tabs.addTab(self.fixture_tab, "灯具建议")
        
        layout.addWidget(self.result_tabs)
        return panel
    
    def _connect_signals(self):
        self.btn_generate.clicked.connect(self._on_generate)
        self.btn_load_default.clicked.connect(self._on_load_default)
        self.btn_export_json.clicked.connect(self._on_export_json)
        self.btn_export_csv.clicked.connect(self._on_export_csv)
        self.venue_combo.currentTextChanged.connect(self._on_venue_changed)
    
    def _on_venue_changed(self, venue):
        venue_info = VENUE_DEFAULTS.get(venue, {})
        if venue_info:
            self.mood_input.setPlaceholderText(f"默认情绪: {venue_info.get('default_mood', '')}")
    
    def _on_load_default(self):
        venue = self.venue_combo.currentText()
        venue_info = VENUE_DEFAULTS.get(venue, {})
        fixtures = venue_info.get("fixtures", [])
        self.fixture_input.setPlainText("\n".join(fixtures))
    
    def _on_generate(self):
        venue = self.venue_combo.currentText()
        mood_text = self.mood_input.text().strip()
        if not mood_text:
            mood_text = self.mood_preset.currentText()
        
        fixtures_text = self.fixture_input.toPlainText().strip()
        
        self.current_suggestions = self.engine.generate_suggestions(venue, mood_text, fixtures_text)
        self._display_results(self.current_suggestions)
        self.logger.info(f"生成方案: 场地={venue}, 情绪={self.current_suggestions['mood']}")
    
    def _display_results(self, suggestions):
        self._display_colors(suggestions["color_palette"], suggestions["mood"])
        self._display_cues(suggestions["cue_sequence"])
        self._display_positions(suggestions["beam_positions"])
        self._display_fixtures(suggestions["fixture_suggestions"])
    
    def _display_colors(self, palette, mood):
        # 清理旧的色块
        while self.color_grid.count():
            item = self.color_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        for i, color_info in enumerate(palette):
            swatch = ColorSwatchWidget(color_info["hex"], color_info["name"])
            self.color_grid.addWidget(swatch, 0, i)
        
        info_text = f"情绪: {mood}\n\n"
        for c in palette:
            info_text += f"• {c['name']}: {c['hex']} — {c['usage']}\n"
        self.color_info.setText(info_text)
    
    def _display_cues(self, cues):
        self.cue_table.setRowCount(len(cues))
        for i, cue in enumerate(cues):
            self.cue_table.setItem(i, 0, QTableWidgetItem(str(cue["cue_number"])))
            self.cue_table.setItem(i, 1, QTableWidgetItem(cue["name"]))
            self.cue_table.setItem(i, 2, QTableWidgetItem(str(cue["time"])))
            self.cue_table.setItem(i, 3, QTableWidgetItem(str(cue["duration"])))
            self.cue_table.setItem(i, 4, QTableWidgetItem(str(cue["intensity"])))
            self.cue_table.setItem(i, 5, QTableWidgetItem(cue["description"]))
    
    def _display_positions(self, positions):
        self.position_table.setRowCount(len(positions))
        for i, pos in enumerate(positions):
            self.position_table.setItem(i, 0, QTableWidgetItem(pos["name"]))
            self.position_table.setItem(i, 1, QTableWidgetItem(str(pos["horizontal_angle"]) + "°"))
            self.position_table.setItem(i, 2, QTableWidgetItem(str(pos["vertical_angle"]) + "°"))
            self.position_table.setItem(i, 3, QTableWidgetItem(pos["suggested_gobo"]))
            self.position_table.setItem(i, 4, QTableWidgetItem(pos["priority"]))
    
    def _display_fixtures(self, fixtures):
        self.fixture_list_widget.clear()
        for f in fixtures:
            self.fixture_list_widget.addItem(QListWidgetItem(f"  • {f}"))
        self.fixture_suggestion_label.setText(f"共建议 {len(fixtures)} 类灯具，请根据实际库存调整数量。")
    
    def _on_export_json(self):
        if not self.current_suggestions:
            QMessageBox.warning(self, "提示", "请先生成设计方案")
            return
        
        path, _ = QFileDialog.getSaveFileName(self, "导出JSON", "lighting_design.json", "JSON文件 (*.json)")
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(self.current_suggestions, f, ensure_ascii=False, indent=2)
                QMessageBox.information(self, "成功", f"已导出到: {path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", str(e))
    
    def _on_export_csv(self):
        if not self.current_suggestions:
            QMessageBox.warning(self, "提示", "请先生成设计方案")
            return
        
        path, _ = QFileDialog.getSaveFileName(self, "导出CSV", "lighting_design.csv", "CSV文件 (*.csv)")
        if path:
            try:
                with open(path, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["类型", "编号", "名称/位置", "参数1", "参数2", "参数3", "说明"])

                    for i, cue in enumerate(self.current_suggestions["cue_sequence"]):
                        writer.writerow(["CUE", cue["cue_number"], cue["name"],
                                       f"时间:{cue['time']}s", f"持续:{cue['duration']}s",
                                       f"亮度:{cue['intensity']}%", cue["description"]])

                    for pos in self.current_suggestions["beam_positions"]:
                        writer.writerow(["灯位", "", pos["name"],
                                       f"H:{pos['horizontal_angle']}°", f"V:{pos['vertical_angle']}°",
                                       pos["suggested_gobo"], f"优先级:{pos['priority']}"])

                    for c in self.current_suggestions["color_palette"]:
                        writer.writerow(["颜色", c["name"], c["hex"], "", "", "", c["usage"]])

                QMessageBox.information(self, "成功", f"已导出到: {path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", str(e))


if __name__ == '__main__':
    import traceback
    try:

        from PySide6.QtWidgets import QApplication
        app = QApplication(sys.argv)
        window = AILightingDesigner()
        window.show()
        sys.exit(app.exec())
    except Exception as _e:
        traceback.print_exc()
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            _app = QApplication.instance() or QApplication([])
            QMessageBox.critical(None, "AILightingDesigner - 启动错误",
                f"{type(_e).__name__}: {_e}\n\n请检查日志文件。")
        except Exception:
            pass
