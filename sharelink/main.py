# coding: utf-8
"""
2024 - ShareLink - 셰어 링크
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from fastapi_csrf_protect.exceptions import CsrfProtectError

from sharelink.dependencies import create_db_and_tables, markdown
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


# B - THE APP
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
async def on_startup():
    await create_db_and_tables()
