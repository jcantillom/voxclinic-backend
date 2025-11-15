from fastapi import Depends
from src.apps.document.services.llm_service import AbstractLLMEngine, OllamaLlmEngine
from src.apps.document.repository import DocumentRepository
from src.apps.document.services.document_services import DocumentService

# Factory/Dependency para el motor LLM
def get_llm_engine() -> AbstractLLMEngine:
    """
    Retorna la implementación real del motor LLM (Ollama/Llama 3).
    """
    # Usamos la implementación REAL de Ollama
    return OllamaLlmEngine() # <--- Debe estar así

def get_document_service(
    llm_engine: AbstractLLMEngine = Depends(get_llm_engine)
) -> DocumentService:
    """
    Dependencia que inyecta el repositorio y el motor LLM al DocumentService.
    """
    return DocumentService(DocumentRepository(), llm_engine=llm_engine)