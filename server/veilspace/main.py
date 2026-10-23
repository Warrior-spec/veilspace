from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from veilspace.config import Settings, get_settings
from veilspace.database import initialize_database
from veilspace.auth import AuthLimiter, router as auth_router


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    development = settings.environment == "development"

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        initialize_database(settings.data_dir)
        yield

    app = FastAPI(
        title="VeilSpace API",
        version="0.1.0",
        description="Document workspace foundation. Processing is not enabled yet.",
        docs_url="/docs" if development else None,
        redoc_url=None,
        openapi_url="/openapi.json" if development else None,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.auth_limiter = AuthLimiter()
    app.include_router(auth_router)
    if development:
        app.add_middleware(
            CORSMiddleware,
            allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
            allow_methods=["GET", "POST", "DELETE", "PATCH"],
            allow_headers=["Authorization", "Content-Type"],
        )

    @app.middleware("http")
    async def response_headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        if request.url.path.startswith("/api/auth/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "veilspace", "version": "0.1.0"}

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def home() -> str:
        return (
            '<!doctype html><html lang="en"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>VeilSpace</title><body style="font-family:system-ui;max-width:640px;'
            'margin:15vh auto;padding:24px;background:#f3f7f5;color:#183d35">'
            '<h1>VeilSpace</h1><p>The server is running.</p>'
            '<p>The document workspace is under construction.</p></body></html>'
        )

    return app


app = create_app()
