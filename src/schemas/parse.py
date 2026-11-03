from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

TransactionType = Literal["expense", "income"]


class ParsedTransaction(BaseModel):
    amount: Decimal = Field(gt=0)
    description: str
    type: TransactionType
    category_hint: str
    note: str | None = None
