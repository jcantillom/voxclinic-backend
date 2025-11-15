from fastapi import Depends
from src.apps.document.services.llm_service import AbstractLLMEngine, GeminiLlmEngine # Usamos GeminiLlmEngine
from src.apps.document.repository import DocumentRepository
from src.apps.document.services.document_services import DocumentService

# Factory/Dependency para el motor LLM
def get_llm_engine() -> AbstractLLMEngine:
    """
    Retorna la implementación real del motor LLM (Gemini).
    """
    # Usamos la implementación REAL de Gemini
    return GeminiLlmEngine()

def get_document_service(
    llm_engine: AbstractLLMEngine = Depends(get_llm_engine)
) -> DocumentService:
    """
    Dependencia que inyecta el repositorio y el motor LLM al DocumentService.
    """
    return DocumentService(DocumentRepository(), llm_engine=llm_engine)