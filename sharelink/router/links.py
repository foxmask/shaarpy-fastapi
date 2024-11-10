# coding: utf-8
"""
2024 - ShareLink - 셰어 링크
"""
from typing import Annotated, Optional

from fastapi import Request, HTTPException, Depends, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from fastapi import APIRouter

from fastapi_csrf_protect import CsrfProtect

from sqlmodel import Session

from sharelink.config import settings, CsrfSettings
from sharelink.dependencies import get_session, markdown
from sharelink.models import LinksForm
from sharelink.models import get_link, get_link_by_url_hashed
from sharelink.models import get_links_private, get_links_public, get_links_daily
from sharelink.models import add_link, update_link


templates = Jinja2Templates(directory="templates")
templates.env.filters["markdown"] = markdown

router = APIRouter()

# A - SECURITY

# A.1 - CSRF


@CsrfProtect.load_config
def get_csrf_config():
    """
    CSRF config
    """
    return CsrfSettings()


@router.get("/newlinks/", response_class=HTMLResponse)
async def create_link_form(request: Request,
                           csrf_protect: CsrfProtect = Depends(),
                           session: Session = Depends(get_session)):
    """
    form to create a link
    """
    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
    form = LinksForm()
    context = {"request": request,
               "csrf_token": csrf_token,
               "settings": settings,
               "form": form,
               "edit_link": False}
    response = templates.TemplateResponse("sharelink/links_form.html", context)
    csrf_protect.set_csrf_cookie(signed_token, response)
    return response


@router.post("/links/", response_class=RedirectResponse, status_code=302)
async def create_link(request: Request,
                      link_form: Annotated[LinksForm, Form()],
                      csrf_protect: CsrfProtect = Depends(),
                      session: Session = Depends(get_session)):
    """
    Form submitted, save the link
    """
    await csrf_protect.validate_csrf(request)
    link = await add_link(session=session, link_form=link_form)
    if link:
        redirect_url = request.url_for('links_detail', url_hashed=link.url_hashed)
    else:
        # @TODO go back to the form and displays validation errors
        redirect_url = request.url_for('newlinks')

    response: RedirectResponse = RedirectResponse(redirect_url, status_code=303)
    csrf_protect.unset_csrf_cookie(response)  # prevent token reuse
    return response


@router.get("/links/{url_hashed}", response_class=HTMLResponse)
async def links_detail(request: Request,
                       url_hashed: str,
                       session: Session = Depends(get_session)):
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


@router.get("/links_edit/{url_hashed}", response_class=HTMLResponse)
async def links_edit(request: Request,
                     url_hashed: str,
                     link_form: Annotated[LinksForm, Form()],
                     csrf_protect: CsrfProtect = Depends(),
                     session: Session = Depends(get_session)):
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
    }

    response = templates.TemplateResponse("sharelink/links_form.html", context)
    csrf_protect.set_csrf_cookie(signed_token, response)
    return response


@router.post("/links_save/{url_hashed}", response_class=RedirectResponse, status_code=302)
async def links_save(request: Request,
                     url_hashed: str,
                     link_form: Annotated[LinksForm, Form()],
                     csrf_protect: CsrfProtect = Depends(),
                     session: Session = Depends(get_session)):
    """
    Form submitted, update Link
    """

    await csrf_protect.validate_csrf(request)

    link = await update_link(url_hashed=url_hashed, link_form=link_form, session=session)

    if link:
        redirect_url = request.url_for('links_detail', url_hashed=link.url_hashed)
    else:
        # @TODO go back to the form and displays validation errors
        redirect_url = request.url_for('links_edit', url_hashed=url_hashed)

    response: RedirectResponse = RedirectResponse(redirect_url, status_code=303)
    csrf_protect.unset_csrf_cookie(response)  # prevent token reuse
    return response


@router.get("/links_delete/{link_id}", response_class=RedirectResponse, status_code=302)
async def links_delete(request: Request,
                       link_id: int,
                       session: Session = Depends(get_session)):
    """
    delete a link by its ID
    """
    link = await get_link(link_id=link_id, session=session)

    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    session.delete(link)
    session.commit()

    redirect_url = request.url_for('home')
    return RedirectResponse(redirect_url, status_code=303)


@router.get("/private", response_class=HTMLResponse)
async def links_private(request: Request,
                        session: Session = Depends(get_session),
                        offset: int = 0,
                        limit: Annotated[int, Query(le=settings.LINKS_PER_PAGE)] = 5
                        ):
    """
    get the private links
    """
    links, ttl = await get_links_private(session=session,
                                         offset=offset,
                                         limit=limit)
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
async def links_public(request: Request,
                       session: Session = Depends(get_session),
                       offset: int = 0,
                       limit: Annotated[int, Query(le=settings.LINKS_PER_PAGE)] = 5,
                       ):
    """
    get the public links
    """
    links, ttl = await get_links_public(session=session,
                                        offset=offset,
                                        limit=limit)

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


@router.get("/daily", response_class=HTMLResponse)
async def daily(request: Request,
                session: Session = Depends(get_session),
                offset: int = 0,
                limit: Annotated[int, Query(le=settings.DAILY_PER_PAGE)] = 5,
                yesterday: Optional[str] = None):
    """
    get the daily links
    """
    daily_links = await get_links_daily(session=session,
                                        offset=offset,
                                        limit=limit,
                                        yesterday=yesterday)

    context = {
        "request": request,
        "links": daily_links['links'],
        "previous_date": daily_links['previous_date'],
        "next_date": daily_links['next_date'],
        "current_date": daily_links['current_date'],
        "settings": settings,
    }

    response = templates.TemplateResponse("sharelink/links_daily.html", context)

    return response
