# coding: utf-8
"""
2024 - ShareLink - dependencies - 셰어 링크
"""
import datetime
import pypandoc

from sqlmodel import SQLModel, Session, create_engine
from sharelink.config import settings


engine = create_engine(settings.DATABASE_URL)


async def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


async def get_session():
    with Session(engine) as session:
        yield session


# template filters


def filter_markdown(text: str):
    """
    convert into Github_Flavor_Markdown
    """
    return pypandoc.convert_text(text, "html", format="gfm")


def filter_datetime(date, fmt="%Y-%m-%d"):
    """
    return a date from a string, formated as expected
    """
    return datetime.datetime.strftime(date, fmt)
