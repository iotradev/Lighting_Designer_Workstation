# -*- coding: utf-8 -*-
"""
FixtureLibrary - 灯具库管理工具
管理灯具配置文件，包含内置灯具数据库，支持自定义灯具添加和编辑
"""

import sys
import json
import os
from pathlib import Path

# 添加Common库路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'Common'))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTreeWidget, QTreeWidgetItem,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QTextEdit,
    QPushButton, QToolBar, QFileDialog, QMessageBox, QFormLayout, QGroupBox,
    QComboBox, QSpinBox, QDoubleSpinBox, QDialog, QDialogButtonBox, QFrame,
    QAbstractItemView, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QFont, QIcon, QAction, QPainter

from ui.base_window import BaseToolWindow
from fixture_data import (
    BUILTIN_FIXTURES, FIXTURE_CATEGORIES, CATEGORY_TYPE_MAP, TYPE_CATEGORY_MAP
)

# 频道颜色映射
CHANNEL_COLORS = {
    "调光": QColor(255, 255, 180), "Dimmer": QColor(255, 255, 180),
    "频闪": QColor(200, 200, 200), "Strobe": QColor(200, 200, 200),
    "红": QColor(255, 50, 50), "R": QColor(255, 50, 50),
    "绿": QColor(50, 255, 50), "G": QColor(50, 255, 50),
    "蓝": QColor(80, 120, 255), "B": QColor(80, 120, 255),
    "白": QColor(255, 255, 255), "W": QColor(255, 255, 255),
    "青": QColor(0, 255, 255), "品红": QColor(255, 0, 255),
    "黄": QColor(255, 255, 0), "CTO": QColor(255, 180, 100),
    "Pan": QColor(100, 180, 255), "Tilt": QColor(100, 255, 180),
    "速度": QColor(200, 200, 255), "功能": QColor(220, 220, 220),
    "复位": QColor(220, 220, 220), "光圈": QColor(255, 200, 150),
    "变焦": QColor(180, 255, 200), "对焦": QColor(200, 255, 220),
    "棱镜": QColor(200, 200, 255), "雾化": QColor(200, 230, 255),
    "图案": QColor(255, 200, 255), "色轮": QColor(255, 220, 180),
    "效果": QColor(230, 200, 255), "宏": QColor(230, 230, 200),
}


def get_channel_color(name: str) -> QColor:
    """根据频道名称返回对应颜色"""
    for key, color in CHANNEL_COLORS.items():
        if key in name:
            return color
    return QColor(180, 180, 180)


class ChannelBarWidget(QWidget):
    """频道模式显示组件 - 以彩色条形显示通道分配"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.channels = []
        self.setMinimumHeight(60)

    def set_channels(self, channels: list):
        self.channels = channels or []
        self.update()

    def paintEvent(self, event):
        if not self.channels:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()
        n = len(self.channels)
        if n == 0:
            return
        bar_w = max(2, (w - (n - 1) * 2) / n)
        for i, ch in enumerate(self.channels):
            x = int(i * (bar_w + 2))
            bw = int(bar_w)
            color = get_channel_color(ch["name"])
            painter.setBrush(color)
            painter.setPen(QColor(60, 60, 60))
            painter.drawRoundedRect(x, 0, bw, h - 20, 3, 3)
            painter.setPen(QColor(220, 220, 220) if color.lightness() < 140 else QColor(40, 40, 40))
            font = QFont()
            font.setPixelSize(max(8, min(11, int(bar_w / len(ch["name"]) * 1.8))))
            painter.setFont(font)
            # 偏移编号
            painter.drawText(x, h - 18, bw, 18, Qt.AlignCenter, str(ch["offset"]))
            # 名称（竖排或截断）
            name = ch["name"]
            if len(name) > 4:
                name = name[:4] + "…"
            painter.drawText(x, h - 38, bw, 18, Qt.AlignCenter, name)
        painter.end()


class FixtureEditDialog(QDialog):
    """灯具编辑对话框"""

    def __init__(self, fixture=None, parent=None):
        super().__init__(parent)
        self.fixture = fixture or {}
        self.setWindowTitle("编辑灯具" if fixture else "添加灯具")
        self.setMinimumSize(600, 500)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # 基本信息
        info_group = QGroupBox("基本信息")
        form = QFormLayout()
        self.name_edit = QLineEdit(self.fixture.get("name", ""))
        self.mfr_edit = QLineEdit(self.fixture.get("manufacturer", ""))
        self.type_combo = QComboBox()
        for cat in FIXTURE_CATEGORIES:
            self.type_combo.addItem(cat["name"])
        if self.fixture.get("type"):
            idx = self.type_combo.findText(self.fixture["type"])
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
        self.weight_spin = QDoubleSpinBox()
        self.weight_spin.setRange(0, 500)
        self.weight_spin.setValue(self.fixture.get("weight", 0))
        self.weight_spin.setSuffix(" kg")
        self.power_spin = QSpinBox()
        self.power_spin.setRange(0, 50000)
        self.power_spin.setValue(self.fixture.get("power", 0))
        self.power_spin.setSuffix(" W")
        self.desc_edit = QTextEdit(self.fixture.get("description", ""))
        self.desc_edit.setMaximumHeight(60)

        form.addRow("名称:", self.name_edit)
        form.addRow("制造商:", self.mfr_edit)
        form.addRow("类型:", self.type_combo)
        form.addRow("重量:", self.weight_spin)
        form.addRow("功率:", self.power_spin)
        form.addRow("描述:", self.desc_edit)
        info_group.setLayout(form)
        layout.addWidget(info_group)

        # 通道模式
        mode_group = QGroupBox("通道模式")
        mode_layout = QVBoxLayout()
        mode_toolbar = QHBoxLayout()
        self.add_mode_btn = QPushButton("添加模式")
        self.add_mode_btn.clicked.connect(self._add_mode)
        self.del_mode_btn = QPushButton("删除模式")
        self.del_mode_btn.clicked.connect(self._del_mode)
        self.add_ch_btn = QPushButton("添加通道")
        self.add_ch_btn.clicked.connect(self._add_channel)
        self.del_ch_btn = QPushButton("删除通道")
        self.del_ch_btn.clicked.connect(self._del_channel)
        mode_toolbar.addWidget(self.add_mode_btn)
        mode_toolbar.addWidget(self.del_mode_btn)
        mode_toolbar.addWidget(self.add_ch_btn)
        mode_toolbar.addWidget(self.del_ch_btn)
        mode_toolbar.addStretch()
        mode_layout.addLayout(mode_toolbar)

        self.mode_tabs = QComboBox()
        self.mode_tabs.currentIndexChanged.connect(self._on_mode_changed)
        mode_layout.addWidget(self.mode_tabs)

        self.ch_table = QTableWidget()
        self.ch_table.setColumnCount(3)
        self.ch_table.setHorizontalHeaderLabels(["偏移", "通道名称", "颜色预览"])
        self.ch_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.ch_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        mode_layout.addWidget(self.ch_table)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # 频道颜色预览
        self.bar_widget = ChannelBarWidget()
        self.ch_table.itemChanged.connect(self._update_bar)
        mode_layout.addWidget(self.bar_widget)

        # 按钮
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

        # 加载模式数据
        self.modes = [dict(m) for m in self.fixture.get("modes", [])]
        if self.modes:
            for m in self.modes:
                self.mode_tabs.addItem(m["name"])
            self._load_mode_channels(0)
        else:
            self._add_mode()

    def _add_mode(self):
        idx = len(self.modes)
        mode = {"name": f"模式 {idx + 1} (0CH)", "channels": []}
        self.modes.append(mode)
        self.mode_tabs.addItem(mode["name"])
        self.mode_tabs.setCurrentIndex(len(self.modes) - 1)

    def _del_mode(self):
        idx = self.mode_tabs.currentIndex()
        if idx >= 0 and len(self.modes) > 1:
            self.modes.pop(idx)
            self.mode_tabs.removeItem(idx)

    def _add_channel(self):
        m_idx = self.mode_tabs.currentIndex()
        if m_idx < 0:
            return
        mode = self.modes[m_idx]
        chs = mode["channels"]
        offset = chs[-1]["offset"] + 1 if chs else 1
        chs.append({"name": f"通道{offset}", "offset": offset})
        mode["name"] = mode["name"].split("(")[0].strip() + f" ({len(chs)}CH)"
        self.mode_tabs.setItemText(m_idx, mode["name"])
        self._load_mode_channels(m_idx)

    def _del_channel(self):
        m_idx = self.mode_tabs.currentIndex()
        if m_idx < 0:
            return
        mode = self.modes[m_idx]
        row = self.ch_table.currentRow()
        if 0 <= row < len(mode["channels"]):
            mode["channels"].pop(row)
            mode["name"] = mode["name"].split("(")[0].strip() + f" ({len(mode['channels'])}CH)"
            self.mode_tabs.setItemText(m_idx, mode["name"])
            self._load_mode_channels(m_idx)

    def _on_mode_changed(self, idx):
        if 0 <= idx < len(self.modes):
            self._load_mode_channels(idx)

    def _load_mode_channels(self, mode_idx):
        self.ch_table.blockSignals(True)
        mode = self.modes[mode_idx]
        channels = mode["channels"]
        self.ch_table.setRowCount(len(channels))
        for i, ch in enumerate(channels):
            self.ch_table.setItem(i, 0, QTableWidgetItem(str(ch["offset"])))
            self.ch_table.setItem(i, 1, QTableWidgetItem(ch["name"]))
            color = get_channel_color(ch["name"])
            color_item = QTableWidgetItem()
            color_item.setBackground(color)
            color_item.setFlags(Qt.ItemIsEnabled)
            self.ch_table.setItem(i, 2, color_item)
        self.ch_table.blockSignals(False)
        self.bar_widget.set_channels(channels)

    def _update_bar(self):
        m_idx = self.mode_tabs.currentIndex()
        if 0 <= m_idx < len(self.modes):
            # 读取表格更新通道
            channels = []
            for row in range(self.ch_table.rowCount()):
                offset_item = self.ch_table.item(row, 0)
                name_item = self.ch_table.item(row, 1)
                if offset_item and name_item:
                    try:
                        offset = int(offset_item.text())
                    except ValueError:
                        offset = row + 1
                    channels.append({"name": name_item.text(), "offset": offset})
            self.modes[m_idx]["channels"] = channels
            self.bar_widget.set_channels(channels)

    def get_fixture_data(self) -> dict:
        return {
            "name": self.name_edit.text(),
            "manufacturer": self.mfr_edit.text(),
            "type": self.type_combo.currentText(),
            "weight": self.weight_spin.value(),
            "power": self.power_spin.value(),
            "description": self.desc_edit.toPlainText(),
            "modes": self.modes,
        }


class FixtureLibrary(BaseToolWindow):
    """灯具库管理工具主窗口"""

    def __init__(self):
        super().__init__(
            tool_name="fixture_library",
            tool_title="灯具库管理",
            version="1.0.0",
            width=1100,
            height=750
        )
        self.all_fixtures = []
        self.filtered_fixtures = []
        self._load_data()
        self._build_ui()
        self._populate_tree()
        self._filter_fixtures()

    def _load_data(self):
        """加载内置灯具数据，同时加载用户自定义灯具"""
        self.all_fixtures = list(BUILTIN_FIXTURES)
        user_file = Path(__file__).parent / "user_fixtures.json"
        if user_file.exists():
            try:
                with open(user_file, "r", encoding="utf-8") as f:
                    user_data = json.load(f)
                    self.all_fixtures.extend(user_data)
                self.logger.info(f"加载用户灯具 {len(user_data)} 个")
            except Exception as e:
                self.logger.warning(f"加载用户灯具失败: {e}")

    def _save_user_fixtures(self):
        """保存用户自定义灯具"""
        builtins = {json.dumps(f, ensure_ascii=False, sort_keys=True) for f in BUILTIN_FIXTURES}
        user_fixtures = [f for f in self.all_fixtures if json.dumps(f, ensure_ascii=False, sort_keys=True) not in builtins]
        user_file = Path(__file__).parent / "user_fixtures.json"
        try:
            with open(user_file, "w", encoding="utf-8") as f:
                json.dump(user_fixtures, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存用户灯具失败: {e}")

    def _build_ui(self):
        """构建主界面"""
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(4, 4, 4, 4)

        # 工具栏
        toolbar = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 搜索灯具名称、制造商...")
        self.search_edit.textChanged.connect(self._filter_fixtures)
        self.search_edit.setMinimumWidth(200)

        self.add_btn = QPushButton("➕ 添加灯具")
        self.add_btn.clicked.connect(self._add_fixture)
        self.edit_btn = QPushButton("✏️ 编辑灯具")
        self.edit_btn.clicked.connect(self._edit_fixture)
        self.del_btn = QPushButton("🗑️ 删除灯具")
        self.del_btn.clicked.connect(self._delete_fixture)
        self.export_btn = QPushButton("📤 导出JSON")
        self.export_btn.clicked.connect(self._export_json)
        self.import_btn = QPushButton("📥 导入文件")
        self.import_btn.clicked.connect(self._import_file)

        toolbar.addWidget(QLabel("搜索:"))
        toolbar.addWidget(self.search_edit, 1)
        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.edit_btn)
        toolbar.addWidget(self.del_btn)
        toolbar.addWidget(self.export_btn)
        toolbar.addWidget(self.import_btn)
        main_layout.addLayout(toolbar)

        # 主分割器
        splitter = QSplitter(Qt.Horizontal)

        # 左侧 - 分类树
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QLabel("灯具分类"))
        self.category_tree = QTreeWidget()
        self.category_tree.setHeaderHidden(True)
        self.category_tree.currentItemChanged.connect(self._on_category_changed)
        left_layout.addWidget(self.category_tree)
        left_panel.setMinimumWidth(180)
        left_panel.setMaximumWidth(250)
        splitter.addWidget(left_panel)

        # 右侧 - 列表和详情
        right_splitter = QSplitter(Qt.Vertical)

        # 灯具列表
        list_panel = QWidget()
        list_layout = QVBoxLayout(list_panel)
        list_layout.setContentsMargins(0, 0, 0, 0)
        self.fixture_label = QLabel("灯具列表")
        list_layout.addWidget(self.fixture_label)
        self.fixture_table = QTableWidget()
        self.fixture_table.setColumnCount(5)
        self.fixture_table.setHorizontalHeaderLabels(["名称", "制造商", "类型", "功率(W)", "重量(kg)"])
        self.fixture_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.fixture_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.fixture_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.fixture_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.fixture_table.currentCellChanged.connect(self._on_fixture_selected)
        self.fixture_table.doubleClicked.connect(self._edit_fixture)
        list_layout.addWidget(self.fixture_table)
        right_splitter.addWidget(list_panel)

        # 详情面板
        detail_panel = QWidget()
        detail_layout = QVBoxLayout(detail_panel)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.addWidget(QLabel("灯具详情"))

        info_layout = QHBoxLayout()
        self.detail_info = QLabel("选择一个灯具查看详情")
        self.detail_info.setWordWrap(True)
        self.detail_info.setAlignment(Qt.AlignTop)
        info_layout.addWidget(self.detail_info, 1)

        self.mode_combo = QComboBox()
        self.mode_combo.currentIndexChanged.connect(self._on_mode_selected)
        self.mode_label = QLabel("通道模式:")
        info_layout.addWidget(self.mode_label)
        info_layout.addWidget(self.mode_combo)
        detail_layout.addLayout(info_layout)

        # 频道显示
        self.ch_display_label = QLabel("通道分配:")
        detail_layout.addWidget(self.ch_display_label)
        self.channel_bar = ChannelBarWidget()
        self.channel_bar.setMinimumHeight(80)
        detail_layout.addWidget(self.channel_bar)

        # 通道列表
        self.ch_detail_table = QTableWidget()
        self.ch_detail_table.setColumnCount(3)
        self.ch_detail_table.setHorizontalHeaderLabels(["偏移", "通道名称", "颜色"])
        self.ch_detail_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.ch_detail_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.ch_detail_table.setMaximumHeight(200)
        detail_layout.addWidget(self.ch_detail_table)
        right_splitter.addWidget(detail_panel)

        splitter.addWidget(right_splitter)
        splitter.setSizes([200, 800])
        main_layout.addWidget(splitter)

        # 状态栏
        self.status_label = QLabel("就绪 | 内置灯具数量: 0")
        main_layout.addWidget(self.status_label)

        self.set_central_content(main_widget)

    def _populate_tree(self):
        """填充分类树"""
        self.category_tree.clear()
        all_item = QTreeWidgetItem(["全部灯具"])
        all_item.setData(0, Qt.UserRole, "all")
        self.category_tree.addTopLevelItem(all_item)

        for cat in FIXTURE_CATEGORIES:
            cat_item = QTreeWidgetItem([cat["name"]])
            cat_item.setData(0, Qt.UserRole, cat["id"])
            all_item.addChild(cat_item)

        # 制造商子分类
        mfrs = sorted(set(f["manufacturer"] for f in self.all_fixtures))
        mfr_root = QTreeWidgetItem(["按制造商"])
        mfr_root.setData(0, Qt.UserRole, "_mfr_root")
        for m in mfrs:
            mfr_item = QTreeWidgetItem([m])
            mfr_item.setData(0, Qt.UserRole, f"_mfr:{m}")
            mfr_root.addChild(mfr_item)
        self.category_tree.addTopLevelItem(mfr_root)

        all_item.setExpanded(True)
        mfr_root.setExpanded(True)
        self.category_tree.setCurrentItem(all_item)

    def _filter_fixtures(self):
        """根据搜索和分类过滤灯具"""
        search_text = self.search_edit.text().strip().lower()
        current_item = self.category_tree.currentItem()
        cat_id = current_item.data(0, Qt.UserRole) if current_item else "all"

        self.filtered_fixtures = []
        for f in self.all_fixtures:
            # 分类过滤
            if cat_id and cat_id != "all" and cat_id != "_mfr_root":
                if cat_id.startswith("_mfr:"):
                    if f["manufacturer"] != cat_id[5:]:
                        continue
                else:
                    expected_type = CATEGORY_TYPE_MAP.get(cat_id, "")
                    if f["type"] != expected_type:
                        continue
            # 搜索过滤
            if search_text:
                searchable = f"{f['name']} {f['manufacturer']} {f['type']} {f.get('description', '')}".lower()
                if search_text not in searchable:
                    continue
            self.filtered_fixtures.append(f)

        self._update_fixture_table()
        self.status_label.setText(f"显示 {len(self.filtered_fixtures)} / {len(self.all_fixtures)} 个灯具")

    def _update_fixture_table(self):
        """更新灯具列表表格"""
        self.fixture_table.setRowCount(len(self.filtered_fixtures))
        for i, f in enumerate(self.filtered_fixtures):
            self.fixture_table.setItem(i, 0, QTableWidgetItem(f["name"]))
            self.fixture_table.setItem(i, 1, QTableWidgetItem(f["manufacturer"]))
            self.fixture_table.setItem(i, 2, QTableWidgetItem(f["type"]))
            self.fixture_table.setItem(i, 3, QTableWidgetItem(str(f.get("power", ""))))
            self.fixture_table.setItem(i, 4, QTableWidgetItem(str(f.get("weight", ""))))

    def _on_category_changed(self, current, previous):
        self._filter_fixtures()

    def _on_fixture_selected(self, row, col, prev_row, prev_col):
        if 0 <= row < len(self.filtered_fixtures):
            fixture = self.filtered_fixtures[row]
            self._show_fixture_detail(fixture)

    def _show_fixture_detail(self, fixture):
        """显示灯具详情"""
        info = (
            f"<b>{fixture['name']}</b><br>"
            f"制造商: {fixture['manufacturer']}<br>"
            f"类型: {fixture['type']}<br>"
            f"功率: {fixture.get('power', 'N/A')} W<br>"
            f"重量: {fixture.get('weight', 'N/A')} kg<br>"
            f"描述: {fixture.get('description', '无')}"
        )
        self.detail_info.setText(info)

        self.mode_combo.blockSignals(True)
        self.mode_combo.clear()
        for mode in fixture.get("modes", []):
            self.mode_combo.addItem(mode["name"])
        self.mode_combo.blockSignals(False)
        if fixture.get("modes"):
            self._display_mode(fixture["modes"][0])

    def _on_mode_selected(self, idx):
        row = self.fixture_table.currentRow()
        if 0 <= row < len(self.filtered_fixtures):
            fixture = self.filtered_fixtures[row]
            if 0 <= idx < len(fixture.get("modes", [])):
                self._display_mode(fixture["modes"][idx])

    def _display_mode(self, mode):
        """显示通道模式详情"""
        channels = mode.get("channels", [])
        self.channel_bar.set_channels(channels)
        self.ch_detail_table.setRowCount(len(channels))
        for i, ch in enumerate(channels):
            self.ch_detail_table.setItem(i, 0, QTableWidgetItem(str(ch["offset"])))
            self.ch_detail_table.setItem(i, 1, QTableWidgetItem(ch["name"]))
            color = get_channel_color(ch["name"])
            color_item = QTableWidgetItem()
            color_item.setBackground(color)
            color_item.setFlags(Qt.ItemIsEnabled)
            self.ch_detail_table.setItem(i, 2, color_item)

    def _add_fixture(self):
        dialog = FixtureEditDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_fixture_data()
            if data["name"]:
                self.all_fixtures.append(data)
                self._save_user_fixtures()
                self._populate_tree()
                self._filter_fixtures()
                self.logger.info(f"添加灯具: {data['name']}")

    def _edit_fixture(self):
        row = self.fixture_table.currentRow()
        if row < 0 or row >= len(self.filtered_fixtures):
            QMessageBox.information(self, "提示", "请先选择一个灯具")
            return
        fixture = self.filtered_fixtures[row]
        dialog = FixtureEditDialog(fixture, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_fixture_data()
            if data["name"]:
                idx = self.all_fixtures.index(fixture)
                self.all_fixtures[idx] = data
                self._save_user_fixtures()
                self._populate_tree()
                self._filter_fixtures()
                self.logger.info(f"编辑灯具: {data['name']}")

    def _delete_fixture(self):
        row = self.fixture_table.currentRow()
        if row < 0 or row >= len(self.filtered_fixtures):
            QMessageBox.information(self, "提示", "请先选择一个灯具")
            return
        fixture = self.filtered_fixtures[row]
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除灯具 '{fixture['name']}' 吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.all_fixtures.remove(fixture)
            self._save_user_fixtures()
            self._populate_tree()
            self._filter_fixtures()
            self.logger.info(f"删除灯具: {fixture['name']}")

    def _export_json(self):
        """导出当前灯具库到JSON文件"""
        path, _ = QFileDialog.getSaveFileName(
            self, "导出灯具库", "", "JSON文件 (*.json)"
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self.all_fixtures, f, ensure_ascii=False, indent=2)
                self.status_label.setText(f"已导出到: {path}")
                self.logger.info(f"导出灯具库到: {path}")
            except Exception as e:
                QMessageBox.warning(self, "导出失败", str(e))

    def _import_file(self):
        """从JSON文件导入灯具"""
        path, _ = QFileDialog.getOpenFileName(
            self, "导入灯具库", "", "JSON文件 (*.json)"
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    count = 0
                    for fixture in data:
                        if "name" in fixture and "manufacturer" in fixture:
                            self.all_fixtures.append(fixture)
                            count += 1
                    self._save_user_fixtures()
                    self._populate_tree()
                    self._filter_fixtures()
                    self.status_label.setText(f"已导入 {count} 个灯具")
                    self.logger.info(f"导入 {count} 个灯具从: {path}")
                else:
                    QMessageBox.warning(self, "格式错误", "JSON文件格式不正确，应为灯具数组")
            except Exception as e:
                QMessageBox.warning(self, "导入失败", str(e))


def main():
    import sys as _sys
    from PySide6.QtWidgets import QApplication
    app = QApplication(_sys.argv)
    window = FixtureLibrary()
    window.show()
    _sys.exit(app.exec())


if __name__ == "__main__":
    import traceback
    try:

        main()
    except Exception as _e:
        traceback.print_exc()
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            _app = QApplication.instance() or QApplication([])
            QMessageBox.critical(None, "FixtureLibrary - 启动错误",
                f"{type(_e).__name__}: {_e}\n\n请检查日志文件。")
        except Exception:
            pass
