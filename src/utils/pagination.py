from pydantic import BaseModel
from typing import Optional


class PaginationSchema(BaseModel):
    total: int
    previous: Optional[str]
    next: Optional[str]
    result: list


def paginate(result, entity_schema, page: int, page_size: int):
    """
    Paginate a result
    """

    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_result = [entity_schema(**entity.dict()) for entity in result[start_idx:end_idx]]

    return PaginationSchema(
        total=len(result),
        previous=f"/users/?page={page - 1}&page_size={page_size}" if start_idx > 0 else None,
        next=f"/users/?page={page + 1}&page_size={page_size}" if end_idx < len(result) else None,
        result=paginated_result
    )
