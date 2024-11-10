# coding: utf-8
"""
2024 - ShareLink - 셰어 링크
"""
from fastapi import APIRouter

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from sharelink.config import settings

templates = Jinja2Templates(directory="templates")

router = APIRouter()


@router.get("/feed", response_class=HTMLResponse)
async def feed(request: Request):

    links = {}

    #   @TODO get the links and produce a feed

    context = {
        "request": request,
        "links": links,
        "settings": settings,
    }

    response = templates.TemplateResponse("sharelink/feeds.html", context)

    return response
