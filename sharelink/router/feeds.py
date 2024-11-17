# coding: utf-8
"""
2024 - ShareLink - router feeds - 셰어 링크
"""

import datetime

import pypandoc
import pytz
from fastapi import APIRouter, Depends
from fastapi.templating import Jinja2Templates
from fastapi_rss import Item, RSSFeed, RSSResponse
from sqlmodel import Session

from sharelink.config import settings
from sharelink.dependencies import get_session
from sharelink.router.links import get_links

templates = Jinja2Templates(directory="templates")

router = APIRouter()


@router.get("/feeds")
async def feeds(session: Session = Depends(get_session)) -> RSSResponse:
    """
    flow to generate a feeds
    """
    links, ttl = await get_links(session=session)
    right_now = datetime.datetime.now(tz=pytz.timezone(settings.SHARELINK_TZ))
    feed_data = {
        "title": settings.SHARELINK_NAME,
        "link": settings.SHARELINK_URL,
        "description": settings.SHARELINK_DESCRIPTION,
        "language": settings.LANGUAGE_CODE,
        "last_build_date": datetime.datetime(
            right_now.year,
            right_now.month,
            right_now.day,
            right_now.hour,
            right_now.minute,
            right_now.second,
        ),
        "generator": "ShareLink",
        "ttl": 30,
        "item": [
            Item(
                title=link.title,
                link=link.url,
                description=pypandoc.convert_text(link.text, "html", format="md"),
                author=settings.SHARELINK_AUTHOR,
                pub_date=link.date_created,
            )
            for link in links
        ],
    }
    feed = RSSFeed(**feed_data)
    return RSSResponse(feed)
