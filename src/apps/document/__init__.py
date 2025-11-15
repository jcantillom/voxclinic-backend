# src/apps/document/__init__.py
from .controllers import router as document_router
from .services.document_services import DocumentService

__all__ = ["document_router", "DocumentService"]
