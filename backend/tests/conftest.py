# -*- coding: utf-8 -*-
"""pytest 公共配置。

每个测试最多 30s；测试集整体不超过 600s（10 分钟）。
测试使用 tempfile.TemporaryDirectory 建立隔离的 SQLite 数据库，
不依赖 Windows 挂载路径上的 listening.db。
"""
import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "slow: 标记为慢速测试（单次 > 10s）"
    )
