# coding: utf-8
"""
2024 - ShareLink - Models - 셰어 링크
"""

from datetime import date, datetime, timedelta, timezone

from typing import Annotated, Optional, Tuple

import pytz
from fastapi import HTTPException, Query, Form
from pydantic import BaseModel
from sqlmodel import Session, SQLModel, select, Field, func, column

from sharelink.config import settings
from sharelink.core.hashed_urls import small_hash
from sharelink.core.articles import get_article


class LinksForm(BaseModel):
    url: str | None = None
    title: str | None = None
    text: str | None = None
    tags: str | None = Field(default=None, index=True)
    private: Optional[bool] = False
    sticky: Optional[bool] = False
    image: str | None = None
    video: str | None = None


class LinkBase(SQLModel):
    url: str | None = None
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


# ALL functions to handle links

async def get_links(session: Session,
                    offset: int = 0,
                    limit: Annotated[int, Query(le=100)] = 100,) -> Tuple[int, int]:
    """
    get all the links
    """
    count_query = select(func.count(Links.id))
    count = session.exec(count_query).one()  # Get the count

    query = select(Links).order_by(Links.date_created.desc()).offset(offset).limit(limit)
    links = session.exec(query)
    return links, count


async def get_link(link_id: int, session: Session) -> Links:
    """
    get data of the link
    """
    statement = select(Links).where(Links.id == link_id)
    link = session.exec(statement).first()

    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    return link


async def get_link_by_url_hashed(url_hashed: str, session: Session) -> Links:
    """
    get the link related to the url_hashed
    """
    statement = select(Links).where(Links.url_hashed == url_hashed)
    link = session.exec(statement).first()

    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    return link


async def get_link_by_url(url: str, session: Session) -> Links:
    """
    get the link related to the url
    """
    statement = select(Links).where(Links.url == url)
    link = session.exec(statement).first()

    return link


async def add_link(link_form: Annotated[LinksForm, Form()],
                   session: Session) -> Links:
    """
    let's create a link,
    two path :
    1 - grab the content of an URL from the form and fill title and text from that URL
    2 - fill title text url from the form
    """
    title = text = image = video = ''

    if link_form.url:

        link_exists = await get_link_by_url(url=link_form.url.strip(), session=session)
        if link_exists:
            return link_exists

    # let's calculate the hashed url of the created Link (not for the URL)
    date_created = datetime.now(tz=pytz.timezone(settings.SHARELINK_TZ))
    url_hashed = await small_hash(date_created.strftime("%Y%m%d_%H%M%S"))

    # let's get the content of the URL only if JUST the URL field has been filled
    # otherwise we'll use URL + title or/and text
    if len(link_form.url.strip()) > 0 and (len(link_form.title.strip()) == 0 and len(link_form.text.strip()) == 0):
        title, text, image, video = await get_article(link_form.url.strip())

    link = Links(url=link_form.url.strip(),
                 url_hashed=url_hashed,
                 # check if title is filled from a form or a link
                 title=link_form.title if len(link_form.title.strip()) > 0 else title,
                 # check if text is filled from a form or a link
                 text=link_form.text if len(link_form.text.strip()) > 0 else text,
                 sticky=link_form.sticky,
                 private=link_form.private,
                 image=image,
                 video=video,
                 tags=link_form.tags.strip(),
                 date_created=datetime.now(tz=pytz.timezone(settings.SHARELINK_TZ)))

    db_link = Links.model_validate(link)

    session.add(db_link)
    session.commit()
    session.refresh(db_link)

    return db_link


async def update_link(url_hashed: str,
                      link_form: Annotated[LinksForm, Form()],
                      session: Session) -> Links:
    """
    save the content of an existing link
    """
    link = await get_link_by_url_hashed(url_hashed=url_hashed, session=session)

    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    link.url = link_form.url.strip()
    link.title = link_form.title.strip()
    link.text = link_form.text.strip()
    link.sticky = link_form.sticky
    link.private = link_form.private
    link.image = link_form.image
    link.video = link_form.video
    link.tags = link_form.tags.strip()

    session.add(link)
    session.commit()
    session.refresh(link)

    return link


async def get_tags(session: Session) -> Links:
    """
    get the tags of all the links
    """
    return session.exec(select(Links)).all()


async def get_links_by_tag(session: Session,
                           tag: str,
                           offset: int = 0,
                           limit: Annotated[int, Query(le=10)] = 10) -> Tuple[int, int]:
    """
    get the links related to a tag
    """

    tag = None if tag == '0Tag' else tag

    if tag:
        count_query = select(func.count(Links.id)).filter(column("tags").contains(tag))
        count = session.exec(count_query).one()  # Get the count

        links = session.exec(
            select(Links).filter(column("tags").contains(tag)).order_by(
                Links.date_created.desc()).offset(offset).limit(limit)
        )
    else:
        count_query = select(func.count(Links.id)).where(Links.tags is None)
        count = session.exec(count_query).one()  # Get the count

        links = session.exec(
            select(Links).where(Links.tags is None).order_by(
                Links.date_created.desc()).offset(offset).limit(limit)
        )

    return links, count


async def get_links_daily(session: Session,
                          offset: int = 0,
                          limit: Annotated[int, Query(le=10)] = 10,
                          yesterday: Optional[str] = None,) -> dict:
    """
    get the daily links
    look for the date of "yesterday" and "tomorrow"
    then look for the data
    """
    previous_date = next_date = ''
    now = datetime.now(tz=pytz.timezone(settings.SHARELINK_TZ))
    today = date.today()

    if yesterday:
        yesterday = datetime.strptime(yesterday, '%Y-%m-%d').replace(
            tzinfo=timezone.utc)

        start_of_day = yesterday

    else:
        yesterday = today - timedelta(days=1, seconds=-1)

        start_of_day = datetime(now.year, now.month, now.day)

    end_of_day = start_of_day + timedelta(days=1, seconds=-1)

    # @TODO do not return private links
    statement = select(Links).where(Links.date_created <= yesterday).order_by(
        Links.date_created.desc())
    previous_date = session.exec(statement).first()

    if previous_date:
        previous_date = previous_date.date_created.date()

    # @TODO do not return private links
    statement = select(Links).where(Links.date_created > end_of_day).order_by(
        Links.date_created.asc())
    next_date = session.exec(statement).first()

    if next_date:
        next_date = next_date.date_created.date()

    data = session.exec(select(Links).where(
        Links.date_created <= end_of_day).where(
            Links.date_created >= start_of_day).order_by(
                Links.date_created.desc()).offset(offset).limit(limit))

    context = {
        'previous_date': previous_date,
        'next_date': next_date,
        'current_date': yesterday,
        'links': data
    }

    return context


async def get_links_private(session: Session,
                            offset: int = 0,
                            limit: Annotated[int, Query(le=10)] = 10,) -> Tuple[int, int]:
    """
    only get the private link created for ourselves
    """
    count_query = select(func.count(Links.id)).where(Links.private == 1)
    count = session.exec(count_query).one()  # Get the count

    links = session.exec(
        select(Links).where(Links.private == 1).order_by(
            Links.date_created.desc()).offset(offset).limit(limit))
    return links, count


async def get_links_public(session: Session,
                           offset: int = 0,
                           limit: Annotated[int, Query(le=10)] = 10,) -> Tuple[int, int]:
    """
    only get the link created for everyone
    """
    count_query = select(func.count(Links.id)).where(Links.private == 0)
    count = session.exec(count_query).one()  # Get the count

    links = session.exec(
        select(Links).where(Links.private == 0).order_by(
            Links.date_created.desc()).offset(offset).limit(limit))
    return links, count
