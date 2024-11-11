# coding: utf-8
"""
2024 - ShareLink - 셰어 링크
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from fastapi_csrf_protect.exceptions import CsrfProtectError

from sharelink.config import settings
from sharelink.dependencies import create_db_and_tables, filter_markdown, filter_datetime
from sharelink.router import feeds as feeds_router, links as links_router, tags as tags_router

# SessionDep = Annotated[Session, Depends(get_session)]

# APP

app = FastAPI()  # dependencies=[Depends(SessionDep)])

# A.1 ROUTER for each part of the APP

app.include_router(feeds_router.router)
app.include_router(links_router.router)
app.include_router(tags_router.router)

templates = Jinja2Templates(directory="templates")

# SECURITY

# B.1 CSRF


@app.exception_handler(CsrfProtectError)
def csrf_protect_exception_handler(request: Request,
                                   exc: CsrfProtectError):
    """
    display the CSRF Exception when occurs
    """
    return JSONResponse(status_code=exc.status_code,
                        content={"detail": exc.message})

# B.2 - CORS + TrustesHost


app.add_middleware(
    TrustedHostMiddleware, allowed_hosts=settings.CSRF_TRUSTED_ORIGINS,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CSRF_TRUSTED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
async def on_startup():
    """
    Let's create the table and database if needed then instantiate connection
    """
    await create_db_and_tables()
