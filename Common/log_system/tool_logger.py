# -*- coding: utf-8 -*-
"""
缁熶竴鏃ュ織绯荤粺
鏀寔: Info / Warning / Error / Debug 鍥涗釜绾у埆
杈撳嚭: 鏃ュ織绐楀彛(QTextEdit) + 鏂囦欢(Logs/)
"""
import os, sys
from datetime import datetime
from pathlib import Path
from enum import IntEnum

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QTextEdit, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox
from PySide6.QtGui import QTextCharFormat, QColor, QTextCursor, QFont

BASE_DIR = Path(__file__).parent.parent.parent
LOGS_DIR = BASE_DIR / "Logs"

class LogLevel(IntEnum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3

class LogSignal(QObject):
    """鏃ュ織淇″彿锛堣法绾跨▼瀹夊叏锛?""
    message = signal = None  # 鍗犱綅锛屽疄闄呯敤 Signal

# 浣跨敤鐙珛鐨勪俊鍙峰璞￠伩鍏嶅厓绫诲啿绐?from PySide6.QtCore import Signal as _Signal

class _LogEmitter(QObject):
    log_message = _Signal(str, str, str)  # level, timestamp, message

class ToolLogger:
    """
    宸ュ叿鏃ュ織鍣?    鐢ㄦ硶:
        logger = ToolLogger("BPMAnalyzer")
        logger.info("BPM妫€娴嬪畬鎴? 120")
        logger.error("鏃犳硶鍔犺浇鏂囦欢")
    """
    _emitter = _LogEmitter()

    def __init__(self, tool_name, log_widget=None, file_logging=True):
        self.tool_name = tool_name
        self.log_widget = log_widget
        self.file_logging = file_logging
        self.min_level = LogLevel.INFO
        self._log_file = None

        if file_logging:
            LOGS_DIR.mkdir(parents=True, exist_ok=True)
            date_str = datetime.now().strftime("%Y%m%d")
            self._log_path = LOGS_DIR / f"{tool_name}_{date_str}.log"

    def _write(self, level: LogLevel, msg: str):
        """鍐欏叆鏃ュ織"""
        if level < self.min_level:
            return
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        level_name = level.name
        line = f"[{ts}] [{level_name}] [{self.tool_name}] {msg}"

        # 杈撳嚭鍒版帶鍒跺彴
        if level >= LogLevel.WARNING:
            print(line, file=sys.stderr)
        else:
            print(line)

        # 杈撳嚭鍒版枃浠?        if self.file_logging and self._log_path:
            try:
                with open(self._log_path, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
            except IOError:
                pass

        # 杈撳嚭鍒版棩蹇楃獥鍙ｆ帶浠?        if self.log_widget and isinstance(self.log_widget, QTextEdit):
            self._append_to_widget(level, ts, msg)

    def _append_to_widget(self, level, ts, msg):
        """杩藉姞鏂囨湰鍒版棩蹇楁帶浠?""
        fmt = QTextCharFormat()
        color_map = {
            LogLevel.DEBUG: QColor("#808080"),
            LogLevel.INFO: QColor("#569cd6"),
            LogLevel.WARNING: QColor("#e8912d"),
            LogLevel.ERROR: QColor("#f44747"),
        }
        fmt.setForeground(color_map.get(level, QColor("#cccccc")))

        cursor = self.log_widget.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(f"[{ts[-12:]}] {msg}\n", fmt)
        self.log_widget.setTextCursor(cursor)
        self.log_widget.ensureCursorVisible()

    def set_widget(self, widget):
        """璁剧疆鏃ュ織杈撳嚭鎺т欢"""
        self.log_widget = widget

    def set_level(self, level):
        """璁剧疆鏈€浣庢棩蹇楃骇鍒?""
        self.min_level = level

    def debug(self, msg):
        self._write(LogLevel.DEBUG, msg)

    def info(self, msg):
        self._write(LogLevel.INFO, msg)

    def warning(self, msg):
        self._write(LogLevel.WARNING, msg)

    def error(self, msg):
        self._write(LogLevel.ERROR, msg)

    def exception(self, msg, exc):
        """记录带堆栈的错误"""
        import traceback
        self._write(LogLevel.ERROR, f"{msg}\n{traceback.format_exc()}")


class LogPanel(QWidget):
    """
    鍙祵鍏ョ殑鏃ュ織闈㈡澘缁勪欢
    鍖呭惈: 鏃ュ織鏂囨湰鍖?+ 绾у埆绛涢€?+ 娓呴櫎鎸夐挳
    """
    def __init__(self, tool_name="", parent=None):
        super().__init__(parent)
        self.logger = ToolLogger(tool_name)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # 宸ュ叿鏍?        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        from PySide6.QtWidgets import QLabel
        lbl = QLabel("馃搵 鏃ュ織")
        lbl.setStyleSheet("font-weight:bold; color:#e8912d;")
        toolbar.addWidget(lbl)

        self.level_combo = QComboBox()
        self.level_combo.addItems(["鍏ㄩ儴", "Info", "Warning", "Error", "Debug"])
        self.level_combo.currentTextChanged.connect(self._on_level_changed)
        toolbar.addWidget(self.level_combo)

        toolbar.addStretch()

        btn_clear = QPushButton("娓呴櫎")
        btn_clear.setFixedWidth(60)
        btn_clear.clicked.connect(lambda: self.log_text.clear())
        toolbar.addWidget(btn_clear)

        layout.addLayout(toolbar)

        # 鏃ュ織鏂囨湰鍖?        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Cascadia Code, Consolas, monospace", 11))
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #cccccc;
                border: 1px solid #3f3f46;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.log_text)

        self.logger.set_widget(self.log_text)

    def _on_level_changed(self, text):
        """鍒囨崲鏃ュ織绾у埆绛涢€?""
        level_map = {"鍏ㄩ儴": LogLevel.DEBUG, "Debug": LogLevel.DEBUG,
                     "Info": LogLevel.INFO, "Warning": LogLevel.WARNING, "Error": LogLevel.ERROR}
        self.logger.set_level(level_map.get(text, LogLevel.DEBUG))

    def get_logger(self):
        return self.logger

