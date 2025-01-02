# coding: utf-8
"""
2024 - ShareLink - router links - 셰어 링크
"""

from datetime import datetime
from typing import Annotated, Tuple

import pytz
from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi_csrf_protect import CsrfProtect
from pydantic import ValidationError
from sqlalchemy.engine.result import ScalarResult
from sqlmodel import Session, func, select

from sharelink.config import CsrfSettings, settings
from sharelink.core.hashed_urls import small_hash
from sharelink.dependencies import filter_datetime, filter_markdown
from sharelink.dependencies_sqlalchemy import get_session
from sharelink.forms import LinksForm
from sharelink.models import Links

templates = Jinja2Templates(directory="templates")
templates.env.filters["filter_markdown"] = filter_markdown
templates.env.filters["filter_datetime"] = filter_datetime

router = APIRouter()

# A - SECURITY

# A.1 - CSRF


@CsrfProtect.load_config
def get_csrf_config():  # type: ignore
    """
    CSRF config
    """
    return CsrfSettings()


# ENDPOINTS


@router.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    offset: int = 0,
    limit: Annotated[int, Query(le=settings.LINKS_PER_PAGE)] = 5,
    session: Session = Depends(get_session),
) -> HTMLResponse:
    """
    get the links on the home page
    """

    links, ttl = await get_links(session, offset=offset, limit=limit)

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


@router.get("/newlinks/", response_class=HTMLResponse)
async def create_link_form(
    request: Request,
    csrf_protect: CsrfProtect = Depends(),
    session: Session = Depends(get_session),
) -> HTMLResponse:
    """
    form to create a link
    """
    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()

    context = {
        "request": request,
        "csrf_token": csrf_token,
        "settings": settings,
        "form_data": {},
        "errors": {},
        "edit_link": False,
    }

    response = templates.TemplateResponse("sharelink/links_form.html", context)
    csrf_protect.set_csrf_cookie(signed_token, response)
    return response


# @router.post("/newlinks/", response_class=HTMLResponse)
@router.post("/newlinks/", response_class=HTMLResponse, status_code=302)
async def create_link(
    request: Request,
    csrf_protect: CsrfProtect = Depends(),
    session: Session = Depends(get_session),
) -> HTMLResponse:
    """
    Form submitted, save the link
    """
    form = await request.form()

    await csrf_protect.validate_csrf(request)

    try:
        # form validated
        linkForm = LinksForm(**form)

        if linkForm.url:
            existing_link = await get_link_by_url(url=str(linkForm.url), session=session)
            if existing_link:
                context = {
                    "request": request,
                    "data": existing_link,
                    "settings": settings,
                }
                response = templates.TemplateResponse("sharelink/links_detail.html", context)
                csrf_protect.unset_csrf_cookie(response)  # prevent token reuse
                return response

        # add link if it does not already exist
        new_link = await add_link(session=session, link_form=linkForm)
        context = {
            "request": request,
            "data": new_link,
            "settings": settings,
        }

        response = templates.TemplateResponse("sharelink/links_detail.html", context)
        csrf_protect.unset_csrf_cookie(response)  # prevent token reuse

    except ValidationError as e:
        # form not validated - return to the current form with errors
        csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
        for err in e.errors():
            if type(err.get("input")) is str:
                errors = {err["loc"][0]: err["msg"]}
            # "input" become a dict when we check several input in a raw
            # so I tweaked the behavior in the html to display the error
            # on top of the form
            elif type(err.get("input")) is dict:
                errors = {"all": err["msg"]}
        context = {
            "request": request,
            "csrf_token": csrf_token,
            "settings": settings,
            "form": form,
            "edit_link": False,
            "errors": errors,
        }
        response = templates.TemplateResponse("sharelink/links_form.html", context)
        csrf_protect.set_csrf_cookie(signed_token, response)

    return response


@router.get("/links/{url_hashed}", response_class=HTMLResponse)
async def links_detail(
    request: Request, url_hashed: str, session: Session = Depends(get_session)
) -> HTMLResponse:
    """
    view the link by its hashed URL
    """
    link = await get_link_by_url_hashed(url_hashed=url_hashed, session=session)
    context = {
        "request": request,
        "data": link,
        "settings": settings,
    }

    response = templates.TemplateResponse("sharelink/links_detail.html", context)

    return response


@router.get("/edit/{url_hashed}", response_class=HTMLResponse)
async def links_edit(
    request: Request,
    url_hashed: str,
    csrf_protect: CsrfProtect = Depends(),
    session: Session = Depends(get_session),
) -> HTMLResponse:
    """
    edit the link by its hashed URL
    """

    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
    link = await get_link_by_url_hashed(url_hashed=url_hashed, session=session)
    link_form = link

    context = {
        "request": request,
        "csrf_token": csrf_token,
        "form": link_form,
        "url_hashed": url_hashed,
        "edit_link": True,
        "settings": settings,
        "errors": {},
    }

    response = templates.TemplateResponse("sharelink/links_form.html", context)
    csrf_protect.set_csrf_cookie(signed_token, response)
    return response


@router.post("/save/{url_hashed}", response_class=HTMLResponse)
async def links_save(
    request: Request,
    url_hashed: str,
    csrf_protect: CsrfProtect = Depends(),
    session: Session = Depends(get_session),
) -> HTMLResponse:
    """
    Form submitted, update Link
    """
    form = await request.form()

    await csrf_protect.validate_csrf(request)

    try:
        # form validated
        linkForm = LinksForm(**form)
        # update link if it already exists
        link = await update_link(url_hashed=url_hashed, link_form=linkForm, session=session)

        context = {
            "request": request,
            "data": link,
            "settings": settings,
        }

        response = templates.TemplateResponse("sharelink/links_detail.html", context)
        csrf_protect.unset_csrf_cookie(response)  # prevent token reuse

    except ValidationError as e:
        # form not validated - return to the current form with errors
        csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
        for err in e.errors():
            if type(err.get("input")) is str:
                errors = {err["loc"][0]: err["msg"]}
            # "input" become a dict when we check several input in a raw
            # so I tweaked the behavior in the html to display the error
            # on top of the form
            elif type(err.get("input")) is dict:
                errors = {"all": err["msg"]}
        context = {
            "request": request,
            "csrf_token": csrf_token,
            "settings": settings,
            "form": form,
            "edit_link": False,
            "errors": errors,
        }
        response = templates.TemplateResponse("sharelink/links_form.html", context)
        csrf_protect.set_csrf_cookie(signed_token, response)

    return response


@router.get("/delete/{link_id}", response_class=RedirectResponse, status_code=302)
async def links_delete(
    request: Request, link_id: int, session: Session = Depends(get_session)
) -> RedirectResponse:
    """
    delete a link by its ID
    """
    link = await get_link(link_id=link_id, session=session)

    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    session.delete(link)
    session.commit()

    redirect_url = request.url_for("home")
    return RedirectResponse(redirect_url, status_code=303)


# ALL functions to handle links


async def get_links(
    session: Session,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> Tuple[ScalarResult[Links], int | None]:
    """
    get all the links
    """
    count = session.exec(select(func.count()).select_from(Links)).first()
    query = select(Links).order_by(Links.date_created.desc()).offset(offset).limit(limit)  # type: ignore
    links = session.exec(query)
    return links, count


async def get_link(link_id: int, session: Session) -> Links | None:
    """
    get data of the link
    """
    statement = select(Links).where(Links.id == link_id)
    link = session.exec(statement).first()

    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    return link


async def get_link_by_url_hashed(url_hashed: str, session: Session) -> Links | None:
    """
    get the link related to the url_hashed
    """
    statement = select(Links).where(Links.url_hashed == url_hashed)
    link = session.exec(statement).first()

    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    return link


async def get_link_by_url(url: str, session: Session) -> Links | None:
    """
    get the link related to the url
    """
    statement = select(Links).where(Links.url == url)
    link = session.exec(statement).first()
    return link


async def add_link(link_form: Annotated[LinksForm, Form()], session: Session) -> Links:
    """
    let's create a link,
    two path :
    1 - grab the content of an URL from the form and fill title and text from that URL
    2 - fill title text url from the form
    """
    # let's calculate the hashed url of the created Link (not for the URL)
    date_created = datetime.now(tz=pytz.timezone(settings.SHARELINK_TZ))
    url_hashed = await small_hash(date_created.strftime("%Y%m%d_%H%M%S"))

    # let's get the content of the URL only if JUST the URL field has been filled
    # otherwise we'll use URL + title or/and text
    link = Links(
        url=str(link_form.url),
        url_hashed=url_hashed,
        title=link_form.title.strip(),
        text=link_form.text.strip(),
        sticky=link_form.sticky,
        private=link_form.private,
        image=link_form.image,
        video=link_form.video,
        tags=link_form.tags.strip() if link_form.tags else "",
        date_created=datetime.now(tz=pytz.timezone(settings.SHARELINK_TZ)),
    )

    db_link = Links.model_validate(link)

    session.add(db_link)
    session.commit()
    session.refresh(db_link)

    return db_link


async def update_link(
    url_hashed: str, link_form: Annotated[LinksForm, Form()], session: Session
) -> Links:
    """
    save the content of an existing link
    """
    link = await get_link_by_url_hashed(url_hashed=url_hashed, session=session)

    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    link.url = str(link_form.url)
    link.title = link_form.title.strip() if link_form.title else ""
    link.text = link_form.text.strip() if link_form.text else ""
    link.sticky = link_form.sticky
    link.private = link_form.private
    link.image = link_form.image
    link.video = link_form.video
    link.tags = link_form.tags.strip() if link_form.tags else ""

    session.add(link)
    session.commit()
    session.refresh(link)

    return link
