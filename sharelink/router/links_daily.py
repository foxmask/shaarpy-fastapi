# coding: utf-8
"""
2024 - ShareLink - router daily links - 셰어 링크
"""

from datetime import date, datetime, timedelta, timezone
from typing import Annotated, Optional

import pytz
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from sharelink.config import settings
from sharelink.dependencies import filter_datetime, filter_markdown, get_session
from sharelink.models import Links

templates = Jinja2Templates(directory="templates")
templates.env.filters["filter_markdown"] = filter_markdown
templates.env.filters["filter_datetime"] = filter_datetime

router = APIRouter()

# ENDPOINT


@router.get("/daily", response_class=HTMLResponse)
async def daily(
    request: Request,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: Annotated[int, Query(le=settings.DAILY_PER_PAGE)] = 5,
    yesterday: Optional[str] = None,
):
    """
    get the daily links
    """
    # @TODO check the data related to the date
    daily_links = await get_links_daily(
        session=session, offset=offset, limit=limit, yesterday=yesterday
    )

    context = {
        "request": request,
        "links": daily_links["links"],
        "previous_date": daily_links["previous_date"],
        "next_date": daily_links["next_date"],
        "current_date": daily_links["current_date"],
        "settings": settings,
    }

    response = templates.TemplateResponse("sharelink/links_daily.html", context)

    return response


# Function to handle daily links


async def get_links_daily(
    session: Session,
    offset: int = 0,
    limit: Annotated[int, Query(le=10)] = 10,
    yesterday: Optional[str] = None,
) -> dict:
    """
    get the daily links
    look for the date of "yesterday" and "tomorrow"
    then look for the data
    """
    previous_date = next_date = ""
    now = datetime.now(tz=pytz.timezone(settings.SHARELINK_TZ))
    today = date.today()

    if yesterday:
        yesterday = datetime.strptime(yesterday, "%Y-%m-%d").replace(tzinfo=timezone.utc)

        start_of_day = yesterday

    else:
        yesterday = today - timedelta(days=1, seconds=-1)

        start_of_day = datetime(now.year, now.month, now.day)

    end_of_day = start_of_day + timedelta(days=1, seconds=-1)

    # @TODO do not return private links
    statement = (
        select(Links).where(Links.date_created <= yesterday).order_by(Links.date_created.desc())
    )
    previous_date = session.exec(statement).first()

    if previous_date:
        previous_date = previous_date.date_created.date()

    # @TODO do not return private links
    statement = (
        select(Links).where(Links.date_created > end_of_day).order_by(Links.date_created.asc())
    )
    next_date = session.exec(statement).first()

    if next_date:
        next_date = next_date.date_created.date()

    data = session.exec(
        select(Links)
        .where(Links.date_created <= end_of_day)
        .where(Links.date_created >= start_of_day)
        .order_by(Links.date_created.desc())
        .offset(offset)
        .limit(limit)
    )

    context = {
        "previous_date": previous_date,
        "next_date": next_date,
        "current_date": yesterday,
        "links": data,
    }

    return context
