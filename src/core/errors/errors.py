from typing import Any

from fastapi import HTTPException, status


class UsersNotFoundError(HTTPException):
    def __init__(self, attribute: Any, value: Any = None):
        detail = f" There are no users related to the {attribute} {value}"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class UserNotFoundError(HTTPException):
    def __init__(self, attribute: Any, value: Any = None):
        detail = f"User with  {attribute} {value} not found"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class UserAlreadyExistsError(HTTPException):
    def __init__(self, attribute: Any):
        detail = f"User with email {attribute} already exists"
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class QueryParamsRequiredError(HTTPException):
    def __init__(self, attribute: Any):
        detail = f"Query parameters are required: {attribute}"
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
