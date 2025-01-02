# coding: utf-8
"""
2024 - ShareLink - dependencies - 셰어 링크
"""

from datetime import datetime

import markdown

# template filters


def filter_markdown(text: str) -> str:
    """
    convert Markdown
    """
    return markdown.markdown(text, extensions=["fenced_code", "codehilite", "footnotes", "tables"])


def filter_datetime(my_date: str, fmt: str = "%Y-%m-%d") -> str:
    """
    return a date from a string, formated as expected
    """
    return datetime.strftime(my_date, fmt)  # type: ignore
