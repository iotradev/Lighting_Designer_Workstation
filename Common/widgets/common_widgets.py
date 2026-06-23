# -*- coding: utf-8 -*-
"""

: LEDDMX
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QSlider, QGridLayout, QGroupBox, QPushButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor, QFont


class LEDMeter(QWidget):
    """LEDVU"""
    def __init__(self, channels=1, parent=None):
        super().__init__(parent)
        self.channels = channels
        self.values = [0.0] * channels  # 0.0 ~ 1.0
        self.setMinimumWidth(30 + channels * 20)

    def set_value(self, channel, value):
        if 0 <= channel < self.channels:
            self.values[channel] = max(0.0, min(1.0, value))
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        w = self.width()
        h = self.height()
        bar_w = max(8, (w - 10) // self.channels - 2)

        for i, val in enumerate(self.values):
            x = 8 + i * (bar_w + 2)
            bar_h = int(val * (h - 10))

            # 
            painter.setPen(QColor("#3f3f46"))
            painter.setBrush(QColor("#252526"))
            painter.drawRect(x, 5, bar_w, h - 10)

            #  (--)
            if val < 0.6:
                color = QColor("#4ec9b0")
            elif val < 0.85:
                color = QColor("#e8912d")
            else:
                color = QColor("#f44747")
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(x, h - 5 - bar_h, bar_w, bar_h)

        painter.end()


class DMXBar(QWidget):
    """DMX (0-255)"""
    value_changed = Signal(int, int)  # channel, value

    def __init__(self, channel=1, value=0, parent=None):
        super().__init__(parent)
        self.channel = channel
        self._value = value
        self.setFixedHeight(28)
        self.setMinimumWidth(200)

    def paintEvent(self, event):
        painter = QPainter(self)
        w = self.width()
        h = self.height()

        # 
        painter.setPen(QColor("#e8912d"))
        painter.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        painter.drawText(2, 0, 30, h, Qt.AlignmentFlag.AlignVCenter, f"{self.channel:03d}")

        # 
        bar_x = 36
        bar_w = w - 80
        painter.setPen(QColor("#3f3f46"))
        painter.setBrush(QColor("#252526"))
        painter.drawRect(bar_x, 6, bar_w, h - 12)

        # 
        fill_w = int(self._value / 255 * bar_w)
        painter.setBrush(QColor("#e8912d"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(bar_x, 6, fill_w, h - 12)

        # 
        painter.setPen(QColor("#cccccc"))
        painter.drawText(w - 40, 0, 38, h,
                        Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                        f"{self._value}")
        painter.end()

    def mousePressEvent(self, event):
        self._update_from_mouse(event.position().x())

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._update_from_mouse(event.position().x())

    def _update_from_mouse(self, x):
        bar_x = 36
        bar_w = max(1, self.width() - 80)
        val = int(max(0, min(255, (x - bar_x) / bar_w * 255)))
        if val != self._value:
            self._value = val
            self.value_changed.emit(self.channel, val)
            self.update()

    def set_value(self, val):
        self._value = max(0, min(255, val))
        self.update()


class ChannelGrid(QWidget):
    """DMX (16/)"""
    channel_changed = Signal(int, int)  # channel, value

    def __init__(self, channels=512, parent=None):
        super().__init__(parent)
        self.channels = channels
        self.values = [0] * channels
        self._init_ui()

    def _init_ui(self):
        layout = QGridLayout(self)
        layout.setSpacing(2)
        cols = 16
        rows = (self.channels + cols - 1) // cols
        for i in range(min(self.channels, 256)):
            row, col = divmod(i, cols)
            btn = QPushButton(f"{i+1}")
            btn.setFixedSize(48, 36)
            btn.setToolTip(f"CH {i+1}: 0")
            btn.setStyleSheet("background-color:#252526; color:#808080; font-size:10px;")
            btn.setProperty("channel", i)
            btn.clicked.connect(lambda checked, ch=i: self._on_click(ch))
            layout.addWidget(btn, row, col)

    def _on_click(self, ch):
        # : 0 -> 128 -> 255 -> 0
        v = self.values[ch]
        if v == 0:
            v = 128
        elif v == 128:
            v = 255
        else:
            v = 0
        self.values[ch] = v
        self.channel_changed.emit(ch + 1, v)
        self._update_cell(ch)

    def _update_cell(self, ch):
        layout = self.layout()
        item = layout.itemAt(ch)
        if item:
            widget = item.widget()
            if widget:
                v = self.values[ch]
                if v == 0:
                    color = "#252526"
                    text_color = "#808080"
                elif v < 128:
                    color = "#3d2800"
                    text_color = "#e8912d"
                else:
                    color = "#e8912d"
                    text_color = "#ffffff"
                widget.setStyleSheet(
                    f"background-color:{color}; color:{text_color}; font-size:10px; font-weight:bold;"
                )
                widget.setToolTip(f"CH {ch+1}: {v}")

    def set_value(self, channel, value):
        if 0 < channel <= self.channels:
            self.values[channel-1] = value
            self._update_cell(channel-1)


class ColorSwatch(QWidget):
    """"""
    clicked = Signal(str)  # hex

    def __init__(self, color="#e8912d", size=40, parent=None):
        super().__init__(parent)
        self.color = color
        self.swatch_size = size
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(self.color))
        painter.setPen(QColor("#3f3f46"))
        painter.drawRoundedRect(1, 1, self.swatch_size-2, self.swatch_size-2, 4, 4)
        painter.end()

    def mousePressEvent(self, event):
        self.clicked.emit(self.color)

    def set_color(self, color):
        self.color = color
        self.update()


class SearchBox(QLineEdit):
    """"""
    def __init__(self, placeholder="...", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setClearButtonEnabled(True)
        self.setObjectName("search_box")


class PropertyPanel(QWidget):
    """"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(4)
        self.layout.addStretch()

    def add_group(self, title, widgets=None):
        """"""
        group = QGroupBox(title)
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(6)
        if widgets:
            for w in widgets:
                group_layout.addWidget(w)
        self.layout.insertWidget(self.layout.count()-1, group)
        return group_layout


class ValueSlider(QWidget):
    """"""
    value_changed = Signal(float)

    def __init__(self, label="", min_val=0, max_val=100, default=50, suffix="", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if label:
            lbl = QLabel(label)
            lbl.setFixedWidth(80)
            layout.addWidget(lbl)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(int(min_val))
        self.slider.setMaximum(int(max_val))
        self.slider.setValue(int(default))
        layout.addWidget(self.slider, 1)

        self.value_label = QLabel(f"{default}{suffix}")
        self.value_label.setFixedWidth(60)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.value_label)

        self.suffix = suffix
        self.slider.valueChanged.connect(self._on_change)

    def _on_change(self, val):
        self.value_label.setText(f"{val}{self.suffix}")
        self.value_changed.emit(float(val))

    def value(self):
        return self.slider.value()

    def set_value(self, val):
        self.slider.setValue(int(val))


class StatusBar(QLabel):
    """"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(28)
        self.set_status("ready")

    def set_status(self, status, text=""):
        colors = {
            "ready": ("#4ec9b0", ""),
            "busy": ("#e8912d", "..."),
            "error": ("#f44747", ""),
            "offline": ("#808080", ""),
            "online": ("#4ec9b0", ""),
        }
        color, default_text = colors.get(status, ("#808080", status))
        display = text or default_text
        self.setText(display)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: #ffffff;
                border-radius: 3px;
                font-weight: bold;
                font-size: 12px;
                padding: 0 12px;
            }}
        """)
