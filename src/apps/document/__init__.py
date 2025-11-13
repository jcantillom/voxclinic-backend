# src/apps/document/__init__.py
from .controllers import router as document_router
from .services import DocumentService

__all__ = ["document_router", "DocumentService"]
