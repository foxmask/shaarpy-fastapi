# coding: utf-8
"""
2024 - ShareLink - 셰어 링크
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_csrf_protect.exceptions import CsrfProtectError
from starlette.middleware.sessions import SessionMiddleware

from sharelink.config import settings
from sharelink.dependencies import create_db_and_tables
from sharelink.router import (
    feeds as feeds_router,
    links as links_router,
    links_daily,
    links_priv_pub,
    tags as tags_router,
)

# APP

app = FastAPI()

# A.1 ROUTER for each part of the APP

app.include_router(feeds_router.router)
app.include_router(links_router.router)
app.include_router(links_daily.router)
app.include_router(links_priv_pub.router)
app.include_router(tags_router.router)


templates = Jinja2Templates(directory="templates")

# SECURITY

# B.1 CSRF


@app.exception_handler(CsrfProtectError)
def csrf_protect_exception_handler(request: Request, exc: CsrfProtectError):  # noqa: ANN201
    """
    display the CSRF Exception when occurs
    """
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


# B.2 - CORS + TrustedHost


app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOST.split(","))

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CSRF_TRUSTED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# B.3 Session middleware

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
async def on_startup() -> None:
    """
    Let's create the table and database if needed then instantiate connection
    """
    await create_db_and_tables()


"""
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request,
                                       exc: RequestValidationError):  # noqa: ANN201
    errors = []
    for error in exc.errors():
        message = f"{error['loc'][-1]}: {error['msg']}"
        errors.append(message)
    return JSONResponse(status_code=422, content={"errors": errors})
"""


@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc: HTTPException):  # noqa: ANN201
    return templates.TemplateResponse(
        "404.html", {"request": request, "settings": settings}, status_code=404
    )


@app.exception_handler(500)
async def internal_error_exception_handler(request: Request, exc: HTTPException):  # noqa: ANN201
    return templates.TemplateResponse(
        "500.html", {"request": request, "settings": settings}, status_code=500
    )
