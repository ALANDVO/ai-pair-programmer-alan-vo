"""Main FastAPI application entrypoint and app factory."""
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
from app.core.config import settings
from app.cli import run_cli

def create_app() -> FastAPI:
    """Create and configure FastAPI application instance."""
    application = FastAPI(
        title="AI Pair Programmer",
        description="Codebase-aware AI pair programming terminal and API by Alan Vo",
        version=settings.app_version,
    )

    # CORS Middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount API routes
    application.include_router(api_router, prefix="/api")

    @application.get("/")
    def root():
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "author": f"{settings.author_name} <{settings.author_email}>",
            "docs": "/docs",
            "health": "/api/health"
        }

    return application

app = create_app()

def cli_main():
    """CLI entrypoint for console scripts."""
    run_cli(sys.argv[1:])

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("suggest", "session", "explain", "refactor"):
        cli_main()
    else:
        import uvicorn
        uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
