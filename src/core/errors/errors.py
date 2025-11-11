from typing import Any
from fastapi import HTTPException, status


class EntityNotFoundError(HTTPException):
    """
    Error para entidad no encontrada.
    Ejemplo: raise EntityNotFoundError("Tenant", "code", "clinica-medellin")
    """

    def __init__(self, entity: str, attribute: str, value: Any):
        detail = f"{entity} with {attribute} '{value}' not found."
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class EntityAlreadyExistsError(HTTPException):
    """
    Error para entidad duplicada.
    Ejemplo: raise EntityAlreadyExistsError("Tenant", "code", "clinica-medellin")
    """

    def __init__(self, entity: str, attribute: str, value: Any):
        detail = f"{entity} with {attribute} '{value}' already exists."
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class InvalidQueryParamsError(HTTPException):
    """
    Error cuando faltan parámetros obligatorios.
    Ejemplo: raise InvalidQueryParamsError(["page", "page_size"])
    """

    def __init__(self, params: list[str]):
        params_str = ", ".join(params)
        detail = f"Query parameters required: {params_str}."
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class ConflictError(HTTPException):
    """
    Error cuando ocurre un conflicto lógico.
    Ejemplo: actualizar un registro inactivo, intentar realizar operación inválida.
    """

    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class BadRequestError(HTTPException):
    """
    Error genérico para request mal formada.
    """

    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
