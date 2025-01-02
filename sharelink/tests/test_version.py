# coding: utf-8
"""
2024 - ShareLink - 셰어 링크
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

import sharelink

app = FastAPI()

client = TestClient(app)


def test_version() -> None:
    assert isinstance(sharelink.__version__, str)
