# coding: utf-8
"""
2024 - ShareLink - 셰어 링크
"""

from typing import Annotated

from fastapi import Request, FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from fastapi_csrf_protect.exceptions import CsrfProtectError

from sqlmodel import Session

from sharelink.config import settings
from sharelink.dependencies import get_session, create_db_and_tables, markdown
from sharelink.models import get_links
from sharelink.router import feeds as feeds_router, links as links_router, tags as tags_router

# SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI()  # dependencies=[Depends(SessionDep)])

app.include_router(feeds_router.router)
app.include_router(links_router.router)
app.include_router(tags_router.router)

templates = Jinja2Templates(directory="templates")
templates.env.filters["markdown"] = markdown


# SECURITY

# A.1 CSRF


@app.exception_handler(CsrfProtectError)
def csrf_protect_exception_handler(request: Request,
                                   exc: CsrfProtectError):
    """
    display the CSRF Exception when occurs
    """
    return JSONResponse(status_code=exc.status_code,
                        content={"detail": exc.message})

# A.2 - CORS


origins = [
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# C - THE APP
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
async def on_startup():
    await create_db_and_tables()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request,
               offset: int = 0,
               limit: Annotated[int, Query(le=settings.LINKS_PER_PAGE)] = 5,
               session: Session = Depends(get_session)):
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
