from typing import Annotated, TypedDict

from fastapi import Depends


class Paging(TypedDict):
    page: int
    limit: int


def get_paging_query_params(page: int = 0, limit: int = 0) -> Paging:
    return {"page": page, "limit": limit}


PagingDep = Annotated[Paging, Depends(get_paging_query_params)]
