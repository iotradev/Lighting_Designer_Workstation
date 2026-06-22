# -*- coding: utf-8 -*-
import pytest
from Common.launcher_utils import run_process


def test_run_process_success():
    result = run_process(["python", "-c", "print('ok')"])
    assert result.returncode == 0
    assert "ok" in result.stdout


def test_run_process_failure():
    with pytest.raises(FileNotFoundError):
        run_process(["nonexistent_command"])