# -*- coding: utf-8 -*-

import sys
import subprocess
import traceback


def run_process(command, cwd=None, logger=None, timeout=30):

    try:

        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout)

        if logger:

            logger.debug(f": {command}")

            if result.stdout:

                logger.debug(f"stdout: {result.stdout.strip()}")

            if result.stderr:

                logger.debug(f"stderr: {result.stderr.strip()}")

        return result

    except FileNotFoundError as exc:

        if logger:

            logger.error(f": {command} - {exc}")

        raise

    except subprocess.TimeoutExpired as exc:

        if logger:

            logger.error(f": {command} - : {timeout}s")

        raise

    except Exception as exc:

        if logger:

            logger.error(f": {command} - {exc}")

        raise


def run_tool(tool_class, tool_name):
    """工具启动模板，替代各工具重复的 __main__ 代码"""
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication(sys.argv)
        window = tool_class()
        window.show()
        sys.exit(app.exec())
    except Exception as _e:
        traceback.print_exc()
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            _app = QApplication.instance() or QApplication([])
            QMessageBox.critical(None, f"{tool_name} - 启动错误",
                f"{type(_e).__name__}: {_e}\n\n请检查日志文件。")
        except Exception:
            pass
