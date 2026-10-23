from fastapi import FastAPI

from veilspace.config import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    development = settings.environment == "development"
    app = FastAPI(
        title="VeilSpace API",
        version="0.1.0",
        description="Document workspace foundation. Processing is not enabled yet.",
        docs_url="/docs" if development else None,
        redoc_url=None,
        openapi_url="/openapi.json" if development else None,
    )

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "veilspace", "version": "0.1.0"}

    return app


app = create_app()
