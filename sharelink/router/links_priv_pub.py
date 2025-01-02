# coding: utf-8
"""
2024 - ShareLink - router private & public links - 셰어 링크
"""

from typing import Annotated, Tuple

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.engine.result import ScalarResult
from sqlmodel import Session, func, select

from sharelink.config import settings
from sharelink.dependencies import filter_datetime, filter_markdown, get_session
from sharelink.models import Links

templates = Jinja2Templates(directory="templates")
templates.env.filters["filter_markdown"] = filter_markdown
templates.env.filters["filter_datetime"] = filter_datetime

router = APIRouter()


@router.get("/private", response_class=HTMLResponse)
async def links_private(
    request: Request,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: Annotated[int, Query(le=settings.LINKS_PER_PAGE)] = 5,
) -> HTMLResponse:
    """
    get the private links
    """
    links, ttl = await get_links_private(session=session, offset=offset, limit=limit)
    context = {
        "request": request,
        "links": links,
        "ttl": ttl,
        "offset": offset,
        "limit": limit,
        # link to use when using pagination
        "url": "links_private",
        "settings": settings,
    }

    response = templates.TemplateResponse("sharelink/links_list.html", context)
    response.headers["X-Total-Count"] = str(ttl)
    response.headers["X-Offset"] = str(offset)
    response.headers["X-Limit"] = str(limit)

    return response


@router.get("/public", response_class=HTMLResponse)
async def links_public(
    request: Request,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: Annotated[int, Query(le=settings.LINKS_PER_PAGE)] = 5,
) -> HTMLResponse:
    """
    get the public links
    """
    links, ttl = await get_links_public(session=session, offset=offset, limit=limit)

    context = {
        "request": request,
        "links": links,
        "ttl": ttl,
        "offset": offset,
        "limit": limit,
        # link to use when using pagination
        "url": "links_public",
        "settings": settings,
    }

    response = templates.TemplateResponse("sharelink/links_list.html", context)
    response.headers["X-Total-Count"] = str(ttl)
    response.headers["X-Offset"] = str(offset)
    response.headers["X-Limit"] = str(limit)

    return response


# ALL Functions to handle Private/Public Links


async def get_links_private(
    session: Session,
    offset: int = 0,
    limit: Annotated[int, Query(le=10)] = 10,
) -> Tuple[ScalarResult[Links], int | None]:
    """
    only get the private link created for ourselves
    """
    # count_query = select(func.count(Links.id)).where(Links.private == 1)
    # count = session.exec(count_query).one()  # Get the count

    count = session.exec(select(func.count()).select_from(Links).where(Links.private == 1)).first()

    links = session.exec(
        select(Links)
        .where(Links.private == 1)
        .order_by(Links.date_created.desc())  # type: ignore
        .offset(offset)
        .limit(limit)
    )
    return links, count


async def get_links_public(
    session: Session,
    offset: int = 0,
    limit: Annotated[int, Query(le=10)] = 10,
) -> Tuple[ScalarResult[Links], int | None]:
    """
    only get the link created for everyone
    """
    # count_query = select(func.count(Links.id)).where(Links.private == 0)
    # count = session.exec(count_query).one()  # Get the count
    count = session.exec(select(func.count()).select_from(Links).where(Links.private == 0)).first()

    links = session.exec(
        select(Links)
        .where(Links.private == 0)
        .order_by(Links.date_created.desc())  # type: ignore
        .offset(offset)
        .limit(limit)
    )
    return links, count
