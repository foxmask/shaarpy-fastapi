# coding: utf-8
"""
2024 - ShareLink - dependencies - 셰어 링크
"""

from datetime import date, datetime

import pypandoc
from sqlmodel import Session, SQLModel, create_engine

from sharelink.config import settings

engine = create_engine(settings.DATABASE_URL)


async def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


async def get_session():  # noqa: ANN201
    with Session(engine) as session:
        yield session


# template filters


def filter_markdown(text: str) -> str:
    """
    convert into Github_Flavor_Markdown
    """
    return pypandoc.convert_text(text, "html", format="gfm")


def filter_datetime(date: str, fmt: str = "%Y-%m-%d") -> date:
    """
    return a date from a string, formated as expected
    """
    return datetime.strftime(date, fmt)
