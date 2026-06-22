# -*- coding: utf-8 -*-
"""
舞台元素类 - StagePlotDesigner
定义舞台平面图中使用的所有图形元素
"""
import json
import uuid
from PySide6.QtWidgets import (
    QGraphicsRectItem, QGraphicsLineItem, QGraphicsEllipseItem,
    QGraphicsTextItem, QGraphicsItem, QGraphicsPathItem
)
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPen, QBrush, QColor, QFont, QPainterPath


class BaseStageElement:
    """所有舞台元素的混入基类，提供通用属性支持"""

    ELEMENT_TYPE = "base"

    def __init__(self):
        self._element_id = str(uuid.uuid4())[:8]
        self._label = ""
        self._element_color = QColor("#FFFFFF")
        self._locked = False

    @property
    def element_id(self):
        return self._element_id

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, value):
        self._label = value

    @property
    def element_color(self):
        return self._element_color

    @element_color.setter
    def element_color(self, color):
        if isinstance(color, str):
            self._element_color = QColor(color)
        else:
            self._element_color = color
        self._apply_color()

    def _apply_color(self):
        """子类实现：应用颜色到图形"""
        pass

    def to_dict(self):
        """序列化为字典"""
        rect = self.sceneBoundingRect() if hasattr(self, 'sceneBoundingRect') else QRectF()
        pos = self.pos() if hasattr(self, 'pos') else QPointF()
        return {
            "type": self.ELEMENT_TYPE,
            "id": self._element_id,
            "x": pos.x(),
            "y": pos.y(),
            "width": rect.width(),
            "height": rect.height(),
            "rotation": self.rotation() if hasattr(self, 'rotation') else 0,
            "label": self._label,
            "color": self._element_color.name(),
            "locked": self._locked,
        }

    def from_dict(self, data):
        """从字典恢复"""
        self._element_id = data.get("id", self._element_id)
        self._label = data.get("label", "")
        self._locked = data.get("locked", False)
        color = data.get("color", "#FFFFFF")
        self.element_color = QColor(color)
        if hasattr(self, 'setPos'):
            self.setPos(data.get("x", 0), data.get("y", 0))
        if hasattr(self, 'setRotation'):
            self.setRotation(data.get("rotation", 0))


class StageElement(BaseStageElement, QGraphicsRectItem):
    """舞台矩形元素 - 用于舞台轮廓"""
    ELEMENT_TYPE = "stage"

    def __init__(self, x=0, y=0, width=800, height=400):
        QGraphicsRectItem.__init__(self, 0, 0, width, height)
        BaseStageElement.__init__(self)
        self.setPos(x, y)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self._label = "舞台"
        self._element_color = QColor("#4A90D9")
        self._apply_color()

    def _apply_color(self):
        pen = QPen(self._element_color, 2.5, Qt.PenStyle.SolidLine)
        self.setPen(pen)
        fill = QColor(self._element_color)
        fill.setAlpha(40)
        self.setBrush(QBrush(fill))

    def to_dict(self):
        d = BaseStageElement.to_dict(self)
        r = self.rect()
        d["width"] = r.width()
        d["height"] = r.height()
        return d

    def from_dict(self, data):
        BaseStageElement.from_dict(self, data)
        w = data.get("width", 800)
        h = data.get("height", 400)
        self.setRect(0, 0, w, h)


class AudienceElement(BaseStageElement, QGraphicsRectItem):
    """观众区域元素"""
    ELEMENT_TYPE = "audience"

    def __init__(self, x=0, y=500, width=800, height=200):
        QGraphicsRectItem.__init__(self, 0, 0, width, height)
        BaseStageElement.__init__(self)
        self.setPos(x, y)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self._label = "观众区域"
        self._element_color = QColor("#666666")
        self._apply_color()

    def _apply_color(self):
        pen = QPen(self._element_color, 1.5, Qt.PenStyle.DashLine)
        self.setPen(pen)
        fill = QColor(self._element_color)
        fill.setAlpha(30)
        self.setBrush(QBrush(fill))

    def to_dict(self):
        d = BaseStageElement.to_dict(self)
        r = self.rect()
        d["width"] = r.width()
        d["height"] = r.height()
        return d

    def from_dict(self, data):
        BaseStageElement.from_dict(self, data)
        w = data.get("width", 800)
        h = data.get("height", 200)
        self.setRect(0, 0, w, h)


class WingElement(BaseStageElement, QGraphicsRectItem):
    """侧幕/翼幕区域元素"""
    ELEMENT_TYPE = "wing"

    def __init__(self, x=0, y=0, width=100, height=400):
        QGraphicsRectItem.__init__(self, 0, 0, width, height)
        BaseStageElement.__init__(self)
        self.setPos(x, y)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self._label = "侧幕"
        self._element_color = QColor("#8B6914")
        self._apply_color()

    def _apply_color(self):
        pen = QPen(self._element_color, 1.5, Qt.PenStyle.DotLine)
        self.setPen(pen)
        fill = QColor(self._element_color)
        fill.setAlpha(35)
        self.setBrush(QBrush(fill))

    def to_dict(self):
        d = BaseStageElement.to_dict(self)
        r = self.rect()
        d["width"] = r.width()
        d["height"] = r.height()
        return d

    def from_dict(self, data):
        BaseStageElement.from_dict(self, data)
        w = data.get("width", 100)
        h = data.get("height", 400)
        self.setRect(0, 0, w, h)


class TrussElement(BaseStageElement, QGraphicsLineItem):
    """桁架线元素"""
    ELEMENT_TYPE = "truss"

    def __init__(self, x1=0, y1=0, x2=800, y2=0):
        QGraphicsLineItem.__init__(self, x1, y1, x2, y2)
        BaseStageElement.__init__(self)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self._label = "桁架"
        self._element_color = QColor("#E8A020")
        self._apply_color()

    def _apply_color(self):
        pen = QPen(self._element_color, 4, Qt.PenStyle.SolidLine)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.setPen(pen)

    def to_dict(self):
        d = BaseStageElement.to_dict(self)
        line = self.line()
        d["x1"] = line.x1()
        d["y1"] = line.y1()
        d["x2"] = line.x2()
        d["y2"] = line.y2()
        pos = self.pos()
        d["x"] = pos.x()
        d["y"] = pos.y()
        return d

    def from_dict(self, data):
        BaseStageElement.from_dict(self, data)
        x1 = data.get("x1", 0)
        y1 = data.get("y1", 0)
        x2 = data.get("x2", 800)
        y2 = data.get("y2", 0)
        self.setLine(x1, y1, x2, y2)


class FixtureElement(BaseStageElement, QGraphicsEllipseItem):
    """灯具位置元素"""
    ELEMENT_TYPE = "fixture"

    def __init__(self, x=0, y=0, radius=20):
        QGraphicsEllipseItem.__init__(self, -radius, -radius, radius * 2, radius * 2)
        BaseStageElement.__init__(self)
        self.setPos(x, y)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self._label = "灯具"
        self._radius = radius
        self._element_color = QColor("#FF6B35")
        self._apply_color()

    def _apply_color(self):
        pen = QPen(self._element_color, 2, Qt.PenStyle.SolidLine)
        self.setPen(pen)
        fill = QColor(self._element_color)
        fill.setAlpha(80)
        self.setBrush(QBrush(fill))

    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, r):
        self._radius = r
        self.setEllipse(-r, -r, r * 2, r * 2)

    def to_dict(self):
        d = BaseStageElement.to_dict(self)
        d["radius"] = self._radius
        rect = self.rect()
        d["width"] = rect.width()
        d["height"] = rect.height()
        pos = self.pos()
        d["x"] = pos.x()
        d["y"] = pos.y()
        return d

    def from_dict(self, data):
        BaseStageElement.from_dict(self, data)
        r = data.get("radius", 20)
        self._radius = r
        self.setEllipse(-r, -r, r * 2, r * 2)


class TextElement(BaseStageElement, QGraphicsTextItem):
    """文本标签元素"""
    ELEMENT_TYPE = "text"

    def __init__(self, text="标签", x=0, y=0):
        QGraphicsTextItem.__init__(self, text)
        BaseStageElement.__init__(self)
        self.setPos(x, y)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self._label = text
        self._element_color = QColor("#FFFFFF")
        font = QFont("Microsoft YaHei", 12)
        self.setFont(font)
        self._apply_color()

    def _apply_color(self):
        self.setDefaultTextColor(self._element_color)

    @property
    def text_content(self):
        return self.toPlainText()

    @text_content.setter
    def text_content(self, value):
        self.setPlainText(value)
        self._label = value

    def to_dict(self):
        d = BaseStageElement.to_dict(self)
        d["text"] = self.toPlainText()
        pos = self.pos()
        d["x"] = pos.x()
        d["y"] = pos.y()
        r = self.boundingRect()
        d["width"] = r.width()
        d["height"] = r.height()
        return d

    def from_dict(self, data):
        BaseStageElement.from_dict(self, data)
        text = data.get("text", data.get("label", "标签"))
        self.setPlainText(text)
        self._label = text


class LineElement(BaseStageElement, QGraphicsLineItem):
    """自由线条元素"""
    ELEMENT_TYPE = "line"

    def __init__(self, x1=0, y1=0, x2=200, y2=0):
        QGraphicsLineItem.__init__(self, x1, y1, x2, y2)
        BaseStageElement.__init__(self)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self._label = "线条"
        self._element_color = QColor("#AAAAAA")
        self._apply_color()

    def _apply_color(self):
        pen = QPen(self._element_color, 1.5, Qt.PenStyle.SolidLine)
        self.setPen(pen)

    def to_dict(self):
        d = BaseStageElement.to_dict(self)
        line = self.line()
        d["x1"] = line.x1()
        d["y1"] = line.y1()
        d["x2"] = line.x2()
        d["y2"] = line.y2()
        pos = self.pos()
        d["x"] = pos.x()
        d["y"] = pos.y()
        return d

    def from_dict(self, data):
        BaseStageElement.from_dict(self, data)
        x1 = data.get("x1", 0)
        y1 = data.get("y1", 0)
        x2 = data.get("x2", 200)
        y2 = data.get("y2", 0)
        self.setLine(x1, y1, x2, y2)


# 元素工厂
ELEMENT_CLASSES = {
    "stage": StageElement,
    "audience": AudienceElement,
    "wing": WingElement,
    "truss": TrussElement,
    "fixture": FixtureElement,
    "text": TextElement,
    "line": LineElement,
}


def create_element(element_type, **kwargs):
    """工厂函数：根据类型创建元素"""
    cls = ELEMENT_CLASSES.get(element_type)
    if cls is None:
        raise ValueError(f"未知元素类型: {element_type}")
    return cls(**kwargs)


def serialize_scene(scene):
    """将场景中所有元素序列化为JSON兼容的列表"""
    items = []
    for item in scene.items():
        if isinstance(item, BaseStageElement):
            items.append(item.to_dict())
    return items


def deserialize_scene(scene, data_list):
    """从数据列表恢复场景元素"""
    for d in data_list:
        etype = d.get("type")
        elem = create_element(etype)
        elem.from_dict(d)
        scene.addItem(elem)
