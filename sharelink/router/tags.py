# coding: utf-8
"""
2024 - ShareLink - router tags - 셰어 링크
"""

from typing import Annotated, Tuple

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.engine.result import ScalarResult
from sqlmodel import Sequence, Session, column, func, select

from sharelink.config import settings
from sharelink.dependencies import filter_datetime, filter_markdown, get_session
from sharelink.models import Links

templates = Jinja2Templates(directory="templates")
templates.env.filters["filter_markdown"] = filter_markdown
templates.env.filters["filter_datetime"] = filter_datetime

router = APIRouter()

# ENDPOINTS


@router.get("/tags", response_class=HTMLResponse)
async def tags_list(request: Request, session: Session = Depends(get_session)):
    """
    get the used tags and get the links of each tag
    """

    links = await get_tags(session=session)
    tags = []
    for data in links:
        if data.tags is not None:
            for tag in data.tags.split(","):
                tags.append(tag)
        else:
            tags.append("0Tag")

    tags = sorted(tags)
    tags_dict = {}
    for my_tag in tags:
        tags_dict.update({my_tag: tags.count(my_tag)})

    context = {
        "request": request,
        "links": links,
        "tags": tags_dict,
        "settings": settings,
    }

    response = templates.TemplateResponse("sharelink/links_tags_cloud.html", context)

    return response


@router.get("/links_by_tag/{tag}", response_class=HTMLResponse)
async def links_by_tag(
    request: Request,
    tag: str,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: Annotated[int, Query(le=settings.LINKS_PER_PAGE)] = 5,
):
    """
    get the links of a given tag
    """

    links, ttl = await get_links_by_tag(tag=tag, session=session, offset=offset, limit=limit)
    context = {
        "request": request,
        "links": links,
        "ttl": ttl,
        "offset": offset,
        "limit": limit,
        # link to use when using pagination
        "url": "home",
        "settings": settings,
    }

    response = templates.TemplateResponse("sharelink/links_list.html", context)
    response.headers["X-Total-Count"] = str(ttl)
    response.headers["X-Offset"] = str(offset)
    response.headers["X-Limit"] = str(limit)

    return response


# ALL Functions to handle TAGS


async def get_tags(session: Session) -> Sequence[Links]:
    """
    get the tags of all the links
    """
    return session.exec(select(Links)).all()


async def get_links_by_tag(
    session: Session,
    tag: str,
    offset: int = 0,
    limit: Annotated[int, Query(le=10)] = 10,
) -> Tuple[ScalarResult[Links], int]:
    """
    get the links related to a tag
    """

    tag = None if tag == "0Tag" else tag

    if tag:
        count_query = select(func.count(Links.id)).filter(column("tags").contains(tag))
        count = session.exec(count_query).one()  # Get the count

        links = session.exec(
            select(Links)
            .filter(column("tags").contains(tag))
            .order_by(Links.date_created.desc())
            .offset(offset)
            .limit(limit)
        )
    else:
        count_query = select(func.count(Links.id)).where(Links.tags is None)
        count = session.exec(count_query).one()  # Get the count

        links = session.exec(
            select(Links)
            .where(Links.tags is None)
            .order_by(Links.date_created.desc())
            .offset(offset)
            .limit(limit)
        )

    return links, count
