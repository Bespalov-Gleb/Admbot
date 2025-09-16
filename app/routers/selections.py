from fastapi import APIRouter, Response
from pydantic import BaseModel
from typing import List, Literal


router = APIRouter()


class SelectionItem(BaseModel):
    title: str
    image: str
    restaurant_id: int | None = None
    dish_id: int | None = None


class Selection(BaseModel):
    id: int
    title: str
    kind: Literal["dishes", "restaurants"]
    items: List[SelectionItem]


_SELECTIONS: List[Selection] = []


@router.get("/selections")
async def list_selections(response: Response) -> List[Selection]:
    # Добавляем заголовки для предотвращения кэширования
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return _SELECTIONS

