# -*- coding: utf-8 -*-
"""
: Info / Warning / Error / Debug 
: (QTextEdit) + (Logs/)
"""
import sys
from datetime import datetime
from pathlib import Path
from enum import IntEnum

from PySide6.QtCore import QObject, Signal, Qt as QtCoreQt
from PySide6.QtWidgets import QTextEdit, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox
from PySide6.QtGui import QTextCharFormat, QColor, QTextCursor, QFont

BASE_DIR = Path(__file__).parent.parent.parent
LOGS_DIR = BASE_DIR / "Logs"

class LogLevel(IntEnum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3

class _LogEmitter(QObject):
    log_message = Signal(str, str, str)  # level_name, timestamp, message

class ToolLogger:
    """

    
    :
        logger = ToolLogger("BPMAnalyzer")
        logger.info("BPM: 120")
        logger.error("")

    """
    _emitter = None

    @classmethod
    def _get_emitter(cls):
        if cls._emitter is None:
            cls._emitter = _LogEmitter()
        return cls._emitter

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
        # 连接信号到GUI更新（跨线程安全）
        self._get_emitter().log_message.connect(self._append_to_widget, QtCoreQt.ConnectionType.QueuedConnection)

    def _write(self, level: LogLevel, msg: str):
        """"""
        if level < self.min_level:
            return
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        level_name = level.name
        line = f"[{ts}] [{level_name}] [{self.tool_name}] {msg}"
        if level >= LogLevel.WARNING:
            print(line, file=sys.stderr)
        else:
            print(line)
        if self.file_logging and self._log_path:
            try:
                with open(self._log_path, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
            except IOError:
                print(f"Failed to write log: {self._log_path}", file=sys.stderr)
        if self.log_widget and isinstance(self.log_widget, QTextEdit):
            self._get_emitter().log_message.emit(level.name, ts, msg)

    def _append_to_widget(self, level_name, ts, msg):
        """"""
        if not self.log_widget:
            return
        fmt = QTextCharFormat()
        color_map = {
            "DEBUG": QColor("#808080"),
            "INFO": QColor("#569cd6"),
            "WARNING": QColor("#e8912d"),
            "ERROR": QColor("#f44747"),
        }
        fmt.setForeground(color_map.get(level_name, QColor("#cccccc")))
        cursor = self.log_widget.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(f"[{ts[-12:]}] {msg}\n", fmt)
        self.log_widget.setTextCursor(cursor)
        self.log_widget.ensureCursorVisible()

    def set_widget(self, widget):
        """"""
        self.log_widget = widget

    def set_level(self, level):
        """"""
        self.min_level = level

    def debug(self, msg):
        self._write(LogLevel.DEBUG, msg)

    def info(self, msg):
        self._write(LogLevel.INFO, msg)

    def warning(self, msg):
        self._write(LogLevel.WARNING, msg)

    def error(self, msg):
        self._write(LogLevel.ERROR, msg)


class LogPanel(QWidget):
    """

    
    :  +  + 

    """
    def __init__(self, tool_name="", parent=None):
        super().__init__(parent)
        self.logger = ToolLogger(tool_name)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        from PySide6.QtWidgets import QLabel
        lbl = QLabel(" ")
        lbl.setStyleSheet("font-weight:bold; color:#e8912d;")
        toolbar.addWidget(lbl)
        self.level_combo = QComboBox()
        self.level_combo.addItems(["", "Info", "Warning", "Error", "Debug"])
        self.level_combo.currentTextChanged.connect(self._on_level_changed)
        toolbar.addWidget(self.level_combo)
        toolbar.addStretch()
        btn_clear = QPushButton("")
        btn_clear.setFixedWidth(60)
        btn_clear.clicked.connect(lambda: self.log_text.clear())
        toolbar.addWidget(btn_clear)
        layout.addLayout(toolbar)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 11))
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
        self.level_combo.setCurrentText("Info")

    def _on_level_changed(self, text):
        """"""
        level_map = {"": LogLevel.DEBUG, "Debug": LogLevel.DEBUG,
                     "Info": LogLevel.INFO, "Warning": LogLevel.WARNING, "Error": LogLevel.ERROR}
        self.logger.set_level(level_map.get(text, LogLevel.DEBUG))

    def get_logger(self):
        return self.logger
