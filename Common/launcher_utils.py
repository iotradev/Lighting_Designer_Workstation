# -*- coding: utf-8 -*-
"""启动工具封装"""
import subprocess
import logging
from pathlib import Path


def run_process(command, cwd=None, logger=None):
    """运行外部命令并捕获输出"""
    try:
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
        if logger:
            logger.debug("命令: %s", command)
            if result.stdout:
                logger.debug("stdout: %s", result.stdout.strip())
            if result.stderr:
                logger.debug("stderr: %s", result.stderr.strip())
        return result
    except FileNotFoundError as exc:
        if logger:
            logger.error("命令不存在: %s", command, exc_info=exc)
        raise
    except Exception as exc:
        if logger:
            logger.error("运行命令失败: %s", command, exc_info=exc)
        raise
