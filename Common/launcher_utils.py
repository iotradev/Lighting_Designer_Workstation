# -*- coding: utf-8 -*-

import subprocess


def run_process(command, cwd=None, logger=None):

    try:

        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)

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

    except Exception as exc:

        if logger:

            logger.error(f": {command} - {exc}")

        raise
