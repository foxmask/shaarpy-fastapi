# coding: utf-8
"""
2024 - ShareLink - router tags - 셰어 링크
"""
from typing import Annotated

from fastapi import Request, Depends, Query, APIRouter
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from sqlmodel import Session

from sharelink.config import settings
from sharelink.dependencies import get_session, markdown
from sharelink.models import get_tags, get_links_by_tag

templates = Jinja2Templates(directory="templates")
templates.env.filters["markdown"] = markdown

router = APIRouter()


@router.get("/tags", response_class=HTMLResponse)
async def tags_list(request: Request,
                    session: Session = Depends(get_session)):
    """
    get the used tags and get the links of each tag
    """

    links = await get_tags(session=session)
    tags = []
    for data in links:
        if data.tags is not None:
            for tag in data.tags.split(','):
                tags.append(tag)
        else:
            tags.append('0Tag')

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
async def links_by_tag(request: Request,
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
