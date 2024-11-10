# coding: utf-8
"""
2024 - ShareLink - 셰어 링크
"""
import pypandoc

from sqlmodel import SQLModel, Session, create_engine
from sharelink.config import settings


engine = create_engine(settings.DATABASE_URL)


async def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


async def get_session():
    with Session(engine) as session:
        yield session


# B - TEMPLATE filter

def markdown(text: str):
    """
    convert into Github_Flavor_Markdown
    """
    return pypandoc.convert_text(text, "html", format="gfm")
