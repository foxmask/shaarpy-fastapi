# coding: utf-8
"""
2024 - ShareLink - Models - 셰어 링크
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl, TypeAdapter, field_validator, model_validator
from sqlmodel import Field, SQLModel
from typing_extensions import Self


class LinksForm(BaseModel):
    """
    check if URL , Title  and Text are empty
    """

    url: str | None = None
    title: str | None = None
    text: str | None = None
    tags: str | None = Field(default=None, index=True)
    private: Optional[bool] = False
    sticky: Optional[bool] = False
    image: str | None = None
    video: str | None = None

    @field_validator("url")
    @classmethod
    def trim_url(cls: Self, v: str) -> str:
        if v:
            # check if it's a valid URL
            ta = TypeAdapter(HttpUrl)
            url = ta.validate_strings(v.strip())
            return str(url)
        return ""

    @field_validator("title")
    @classmethod
    def trim_title(cls: Self, v: str) -> str:
        if v:
            return v.strip()
        return ""

    @field_validator("text")
    @classmethod
    def trim_text(cls: Self, v: str) -> str:
        if v:
            return v.strip()
        return ""

    @model_validator(mode="after")
    def check_form(self: Self) -> Self:
        url = self.url
        title = self.title
        text = self.text
        if url == "" and title == "" and text == "":
            raise ValueError("URL, title or text can not be empty")
        return self


class LinkBase(SQLModel):
    url: str | None = Field(default=None, index=True)
    url_hashed: str | None = None
    title: str | None = None
    text: str | None = None
    tags: str | None = Field(default=None, index=True)
    private: Optional[bool] = False
    sticky: Optional[bool] = False
    image: str | None = None
    video: str | None = None


class Links(LinkBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    date_created: datetime
