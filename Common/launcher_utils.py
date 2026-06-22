# -*- coding: utf-8 -*-
""""""
import subprocess
import logging
from pathlib import Path


def run_process(command, cwd=None, logger=None):
    """"""
    try:
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
        if logger:
            logger.debug(": %s", command)
            if result.stdout:
                logger.debug("stdout: %s", result.stdout.strip())
            if result.stderr:
                logger.debug("stderr: %s", result.stderr.strip())
        return result
    except FileNotFoundError as exc:
        if logger:
            logger.error(": %s", command, exc_info=exc)
        raise
    except Exception as exc:
        if logger:
            logger.error(": %s", command, exc_info=exc)
        raise
