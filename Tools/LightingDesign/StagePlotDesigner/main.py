# -*- coding: utf-8 -*-
"""
舞台平面图设计器 - StagePlotDesigner
基于 QGraphicsScene/QGraphicsView 的舞台灯光布局设计工具
"""
import sys
import json
from pathlib import Path

# 设置导入路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'Common'))

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QLabel, QSpinBox, QDoubleSpinBox, QLineEdit,
    QGroupBox, QFormLayout, QFileDialog, QMessageBox, QColorDialog,
    QToolBar, QSizePolicy, QCheckBox, QScrollArea, QFrame,
    QGraphicsScene, QGraphicsView, QGraphicsItem
)
from PySide6.QtCore import Qt, QPointF, QRectF, QSize
from PySide6.QtGui import (
    QPen, QBrush, QColor, QFont, QPainter, QTransform,
    QKeySequence, QAction, QPageSize, QPageLayout
)

from ui.base_window import BaseToolWindow

from stage_elements import (
    StageElement, AudienceElement, WingElement, TrussElement,
    FixtureElement, TextElement, LineElement, BaseStageElement,
    create_element, serialize_scene, deserialize_scene
)


# ────────────────────────────────────────────
#  自定义 QGraphicsView：支持网格、缩放、平移
# ────────────────────────────────────────────
class StageCanvas(QGraphicsView):
    """舞台画布视图"""

    GRID_SIZE = 50
    ZOOM_FACTOR = 1.15

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHints(QPainter.RenderHint.Antialiasing |
                            QPainter.RenderHint.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self._show_grid = True
        self._snap_enabled = True
        self._pan_active = False
        self._pan_start = QPointF()
        self._zoom_level = 0

    # ── 网格绘制 ──
    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        if not self._show_grid:
            return

        grid = self.GRID_SIZE
        left = int(rect.left()) - (int(rect.left()) % grid)
        top = int(rect.top()) - (int(rect.top()) % grid)

        pen_light = QPen(QColor("#2A2A2A"), 0.5)
        pen_heavy = QPen(QColor("#333333"), 1.0)

        x = left
        while x < rect.right():
            pen = pen_heavy if x % (grid * 4) == 0 else pen_light
            painter.setPen(pen)
            painter.drawLine(int(x), int(rect.top()), int(x), int(rect.bottom()))
            x += grid

        y = top
        while y < rect.bottom():
            pen = pen_heavy if y % (grid * 4) == 0 else pen_light
            painter.setPen(pen)
            painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))
            y += grid

    # ── 网格吸附 ──
    def snap_to_grid(self, pos):
        if not self._snap_enabled:
            return pos
        g = self.GRID_SIZE
        return QPointF(
            round(pos.x() / g) * g,
            round(pos.y() / g) * g
        )

    # ── 缩放 ──
    def zoom_in(self):
        self.scale(self.ZOOM_FACTOR, self.ZOOM_FACTOR)
        self._zoom_level += 1

    def zoom_out(self):
        self.scale(1 / self.ZOOM_FACTOR, 1 / self.ZOOM_FACTOR)
        self._zoom_level -= 1

    def fit_scene(self):
        self.fitInView(self.sceneRect().adjusted(-50, -50, 50, 50),
                       Qt.AspectRatioMode.KeepAspectRatio)
        self._zoom_level = 0

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    # ── 中键平移 ──
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._pan_active = True
            self._pan_start = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._pan_active:
            delta = event.position() - self._pan_start
            self._pan_start = event.position()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - int(delta.x()))
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - int(delta.y()))
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._pan_active = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)


# ────────────────────────────────────────────
#  属性编辑面板
# ────────────────────────────────────────────
class PropertiesPanel(QWidget):
    """右侧属性编辑面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_item = None
        self._updating = False
        self._setup_ui()
        self._set_enabled(False)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        title = QLabel("属性编辑器")
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: #E0E0E0;")
        layout.addWidget(title)

        # 类型标签
        self.type_label = QLabel("类型: -")
        self.type_label.setStyleSheet("color: #AAAAAA;")
        layout.addWidget(self.type_label)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.x_spin = QDoubleSpinBox()
        self.x_spin.setRange(-99999, 99999)
        self.x_spin.setDecimals(1)
        form.addRow("X:", self.x_spin)

        self.y_spin = QDoubleSpinBox()
        self.y_spin.setRange(-99999, 99999)
        self.y_spin.setDecimals(1)
        form.addRow("Y:", self.y_spin)

        self.w_spin = QDoubleSpinBox()
        self.w_spin.setRange(1, 99999)
        self.w_spin.setDecimals(1)
        form.addRow("宽度:", self.w_spin)

        self.h_spin = QDoubleSpinBox()
        self.h_spin.setRange(1, 99999)
        self.h_spin.setDecimals(1)
        form.addRow("高度:", self.h_spin)

        self.rot_spin = QDoubleSpinBox()
        self.rot_spin.setRange(-360, 360)
        self.rot_spin.setDecimals(1)
        self.rot_spin.setSuffix("°")
        form.addRow("旋转:", self.rot_spin)

        self.label_edit = QLineEdit()
        form.addRow("标签:", self.label_edit)

        self.color_btn = QPushButton("选择颜色")
        self.color_btn.clicked.connect(self._pick_color)
        form.addRow("颜色:", self.color_btn)

        layout.addLayout(form)

        layout.addStretch()

        self._widgets = [self.x_spin, self.y_spin, self.w_spin, self.h_spin,
                         self.rot_spin, self.label_edit, self.color_btn]

        # 连接信号
        self.x_spin.editingFinished.connect(self._apply_properties)
        self.y_spin.editingFinished.connect(self._apply_properties)
        self.w_spin.editingFinished.connect(self._apply_properties)
        self.h_spin.editingFinished.connect(self._apply_properties)
        self.rot_spin.editingFinished.connect(self._apply_properties)
        self.label_edit.editingFinished.connect(self._apply_properties)

    def _set_enabled(self, enabled):
        for w in self._widgets:
            w.setEnabled(enabled)

    def set_item(self, item):
        """选中元素时加载属性"""
        self._current_item = item
        if item is None:
            self._set_enabled(False)
            self.type_label.setText("类型: -")
            for w in [self.x_spin, self.y_spin, self.w_spin, self.h_spin,
                      self.rot_spin]:
                w.setValue(0)
            self.label_edit.clear()
            return

        self._set_enabled(True)
        self._updating = True

        etype = getattr(item, 'ELEMENT_TYPE', '?')
        type_names = {
            "stage": "舞台", "audience": "观众区", "wing": "侧幕",
            "truss": "桁架", "fixture": "灯具", "text": "文本", "line": "线条"
        }
        self.type_label.setText(f"类型: {type_names.get(etype, etype)}")

        pos = item.pos()
        self.x_spin.setValue(pos.x())
        self.y_spin.setValue(pos.y())

        # 获取尺寸
        if hasattr(item, 'rect'):
            r = item.rect()
            self.w_spin.setValue(r.width())
            self.h_spin.setValue(r.height())
        elif hasattr(item, 'boundingRect'):
            r = item.boundingRect()
            self.w_spin.setValue(r.width())
            self.h_spin.setValue(r.height())

        self.rot_spin.setValue(item.rotation())

        label = getattr(item, 'label', '')
        self.label_edit.setText(label)

        self._updating = False

    def _apply_properties(self):
        if self._updating or self._current_item is None:
            return
        item = self._current_item

        item.setPos(self.x_spin.value(), self.y_spin.value())
        item.setRotation(self.rot_spin.value())

        # 尺寸
        if isinstance(item, (StageElement, AudienceElement, WingElement)):
            item.setRect(0, 0, self.w_spin.value(), self.h_spin.value())
        elif isinstance(item, FixtureElement):
            r = min(self.w_spin.value(), self.h_spin.value()) / 2
            item.radius = max(r, 5)

        # 标签
        if isinstance(item, TextElement):
            item.text_content = self.label_edit.text()
        elif hasattr(item, '_label'):
            item._label = self.label_edit.text()

    def _pick_color(self):
        if self._current_item is None:
            return
        color = QColorDialog.getColor(
            self._current_item.element_color, self, "选择颜色")
        if color.isValid():
            self._current_item.element_color = color


# ────────────────────────────────────────────
#  元素面板（左侧）
# ────────────────────────────────────────────
class ElementPalette(QWidget):
    """左侧元素面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._main = parent  # StagePlotDesigner 引用
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        title = QLabel("元素面板")
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: #E0E0E0;")
        layout.addWidget(title)

        elements = [
            ("⬛ 添加舞台", "stage"),
            ("🟦 添加桁架", "truss"),
            ("🔴 添加灯具", "fixture"),
            ("📝 文本标签", "text"),
            ("➖ 添加线条", "line"),
            ("🟩 观众区域", "audience"),
            ("🟨 侧幕区域", "wing"),
        ]

        for label, etype in elements:
            btn = QPushButton(label)
            btn.setMinimumHeight(36)
            btn.setStyleSheet(
                "QPushButton { text-align: left; padding-left: 10px; font-size: 13px; }"
            )
            btn.clicked.connect(lambda checked, t=etype: self._add_element(t))
            layout.addWidget(btn)

        layout.addStretch()

    def _add_element(self, etype):
        if self._main:
            self._main.add_element_to_scene(etype)


# ────────────────────────────────────────────
#  主窗口
# ────────────────────────────────────────────
class StagePlotDesigner(BaseToolWindow):
    """舞台平面图设计器主窗口"""

    VERSION = "1.0.0"

    def __init__(self):
        super().__init__(
            tool_name="StagePlotDesigner",
            tool_title="舞台平面图设计器",
            version=self.VERSION,
            width=1600,
            height=950
        )

        self._current_file = None
        self._setup_ui()
        self._setup_toolbar()
        self.logger.info("舞台平面图设计器初始化完成")

    # ── 中心 UI ──
    def _setup_ui(self):
        # 场景与视图
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(-2000, -2000, 4000, 4000)
        self.scene.selectionChanged.connect(self._on_selection_changed)

        self.view = StageCanvas(self.scene, self)

        # 左侧面板
        self.palette = ElementPalette(self)
        palette_scroll = QScrollArea()
        palette_scroll.setWidget(self.palette)
        palette_scroll.setWidgetResizable(True)
        palette_scroll.setMaximumWidth(180)
        palette_scroll.setMinimumWidth(140)

        # 右侧面板
        self.props_panel = PropertiesPanel()
        props_scroll = QScrollArea()
        props_scroll.setWidget(self.props_panel)
        props_scroll.setWidgetResizable(True)
        props_scroll.setMaximumWidth(220)
        props_scroll.setMinimumWidth(180)

        # 布局
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(palette_scroll)
        splitter.addWidget(self.view)
        splitter.addWidget(props_scroll)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)

        self.set_central_content(splitter)

    # ── 工具栏 ──
    def _setup_toolbar(self):
        tb = self.toolbar
        tb.addSeparator()

        self._add_tb("🔍+ 放大", self.view.zoom_in)
        self._add_tb("🔍- 缩小", self.view.zoom_out)
        self._add_tb("⬜ 适应视图", self.view.fit_scene)

        tb.addSeparator()

        # 网格开关
        self.grid_action = self._add_tb("▦ 网格", self._toggle_grid, checkable=True)
        self.grid_action.setChecked(True)

        # 吸附开关
        self.snap_action = self._add_tb("🧲 吸附", self._toggle_snap, checkable=True)
        self.snap_action.setChecked(True)

        tb.addSeparator()

        self._add_tb("📷 导出PNG", self._export_png)
        self._add_tb("📄 导出SVG", self._export_svg)

        tb.addSeparator()

        self._add_tb("📂 打开布局", self._load_json)
        self._add_tb("💾 保存布局", self._save_json)

        tb.addSeparator()

        self._add_tb("🗑 删除选中", self._delete_selected)

    def _add_tb(self, text, slot, checkable=False):
        action = QAction(text, self)
        action.setCheckable(checkable)
        action.triggered.connect(slot)
        self.toolbar.addAction(action)
        return action

    # ── 元素管理 ──
    def add_element_to_scene(self, etype):
        """从面板添加元素到场景中心"""
        center = self.view.mapToScene(self.view.viewport().rect().center())
        kwargs = {"x": center.x(), "y": center.y()}

        if etype == "stage":
            kwargs["width"] = 800
            kwargs["height"] = 400
            kwargs["x"] = center.x() - 400
            kwargs["y"] = center.y() - 200
        elif etype == "truss":
            kwargs = {
                "x1": center.x() - 300,
                "y1": center.y(),
                "x2": center.x() + 300,
                "y2": center.y(),
            }
        elif etype == "audience":
            kwargs["width"] = 800
            kwargs["height"] = 200
            kwargs["x"] = center.x() - 400
            kwargs["y"] = center.y() + 100
        elif etype == "wing":
            kwargs["width"] = 100
            kwargs["height"] = 400
            kwargs["x"] = center.x() - 450
            kwargs["y"] = center.y() - 200
        elif etype == "line":
            kwargs = {
                "x1": 0,
                "y1": 0,
                "x2": 200,
                "y2": 0,
            }

        elem = create_element(etype, **kwargs)

        # 吸附到网格
        if self.view._snap_enabled:
            pos = self.view.snap_to_grid(elem.pos())
            elem.setPos(pos)

        self.scene.addItem(elem)
        self.scene.clearSelection()
        elem.setSelected(True)
        self.logger.info(f"已添加元素: {etype}")

    # ── 选择变化 → 更新属性面板 ──
    def _on_selection_changed(self):
        items = self.scene.selectedItems()
        if items:
            self.props_panel.set_item(items[0])
        else:
            self.props_panel.set_item(None)

    # ── 删除选中 ──
    def _delete_selected(self):
        for item in self.scene.selectedItems():
            self.scene.removeItem(item)
        self.logger.info("已删除选中元素")

    # ── 键盘快捷键 ──
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            self._delete_selected()
        elif event.key() == Qt.Key.Key_Plus or event.key() == Qt.Key.Key_Equal:
            self.view.zoom_in()
        elif event.key() == Qt.Key.Key_Minus:
            self.view.zoom_out()
        else:
            super().keyPressEvent(event)

    # ── 网格/吸附切换 ──
    def _toggle_grid(self):
        self.view._show_grid = not self.view._show_grid
        self.view.viewport().update()

    def _toggle_snap(self):
        self.view._snap_enabled = not self.view._snap_enabled

    # ── 导出 PNG ──
    def _export_png(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "导出PNG图片", "stage_plot.png",
            "PNG图片 (*.png)")
        if not path:
            return
        from PySide6.QtGui import QImage
        rect = self.scene.itemsBoundingRect().adjusted(-40, -40, 40, 40)
        w = max(int(rect.width()), 100)
        h = max(int(rect.height()), 100)
        image = QImage(w * 2, h * 2, QImage.Format.Format_ARGB32)
        image.fill(QColor("#1E1E1E"))
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.scene.render(painter, QRectF(0, 0, w * 2, h * 2), rect)
        painter.end()
        image.save(path)
        self.logger.info(f"已导出PNG: {path}")

    # ── 导出 SVG ──
    def _export_svg(self):
        try:
            from PySide6.QtSvg import QSvgGenerator
        except ImportError:
            QMessageBox.warning(self, "警告",
                                "需要安装 PySide6-Addons 才能导出SVG")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "导出SVG文件", "stage_plot.svg",
            "SVG文件 (*.svg)")
        if not path:
            return
        rect = self.scene.itemsBoundingRect().adjusted(-40, -40, 40, 40)
        svg_gen = QSvgGenerator()
        svg_gen.setFileName(path)
        svg_gen.setSize(QSize(int(rect.width()), int(rect.height())))
        svg_gen.setViewBox(QRectF(0, 0, rect.width(), rect.height()))
        painter = QPainter(svg_gen)
        self.scene.render(painter, QRectF(0, 0, rect.width(), rect.height()), rect)
        painter.end()
        self.logger.info(f"已导出SVG: {path}")

    # ── 保存/加载 JSON ──
    def _save_json(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "保存布局", "stage_plot.json",
            "JSON文件 (*.json)")
        if not path:
            return
        data = {
            "version": self.VERSION,
            "scene_rect": {
                "x": self.scene.sceneRect().x(),
                "y": self.scene.sceneRect().y(),
                "w": self.scene.sceneRect().width(),
                "h": self.scene.sceneRect().height()
            },
            "elements": serialize_scene(self.scene)
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self._current_file = path
        self.logger.info(f"已保存布局: {path}")

    def _load_json(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "打开布局", "",
            "JSON文件 (*.json)")
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.scene.clear()
            deserialize_scene(self.scene, data.get("elements", []))
            self._current_file = path
            self.view.fit_scene()
            self.logger.info(f"已加载布局: {path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载失败:\n{e}")

    # ── 项目文件处理（拖放） ──
    def _handle_dropped_file(self, path):
        if path.endswith('.json'):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.scene.clear()
                deserialize_scene(self.scene, data.get("elements", []))
                self._current_file = path
                self.view.fit_scene()
                self.logger.info(f"已加载拖入布局: {path}")
            except Exception as e:
                self.logger.error(f"无法加载文件: {e}")
        else:
            self.logger.info(f"不支持的文件类型: {path}")


# ────────────────────────────────────────────
#  启动入口
# ────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("舞台平面图设计器")
    window = StagePlotDesigner()
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
            QMessageBox.critical(None, "StagePlotDesigner - 启动错误",
                f"{type(_e).__name__}: {_e}\n\n请检查日志文件。")
        except Exception:
            pass
