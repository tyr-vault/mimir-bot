from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

TransactionType = Literal["expense", "income"]
DraftKind = Literal["transaction", "category"]
DraftStatus = Literal["pending", "confirmed", "rejected"]


class Category(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    user_id: str = Field(alias="userId")
    name: str
    created_at: datetime | str = Field(alias="createdAt")
    updated_at: datetime | str = Field(alias="updatedAt")


class Transaction(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    user_id: str = Field(alias="userId")
    category_id: str = Field(alias="categoryId")
    category_name: str | None = Field(default=None, alias="categoryName")
    type: TransactionType
    amount: Decimal
    date: str
    note: str | None = None
    created_at: datetime | str = Field(alias="createdAt")
    updated_at: datetime | str = Field(alias="updatedAt")

    @field_validator("amount", mode="before")
    @classmethod
    def coerce_amount(cls, value: Any) -> Decimal:
        return Decimal(str(value))


class PeriodSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_: str | None = Field(default=None, alias="from")
    to: str | None = None
    type: TransactionType | None = None
    total_income: Decimal = Field(alias="totalIncome")
    total_expense: Decimal = Field(alias="totalExpense")
    net: Decimal
    count: int

    @field_validator("total_income", "total_expense", "net", mode="before")
    @classmethod
    def coerce_money(cls, value: Any) -> Decimal:
        return Decimal(str(value))


class TransactionDraftPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    category_id: str | None = Field(default=None, alias="categoryId")
    category_name: str | None = Field(default=None, alias="categoryName")
    type: TransactionType
    amount: Annotated[Decimal, Field(gt=0)]
    date: str
    note: str | None = None

    def to_api_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": self.type,
            "amount": float(self.amount.quantize(Decimal("0.01"))),
            "date": self.date,
            "note": self.note,
        }
        if self.category_id:
            payload["categoryId"] = self.category_id
        if self.category_name:
            payload["categoryName"] = self.category_name
        return payload


class CategoryDraftPayload(BaseModel):
    name: str


class CreateDraftBody(BaseModel):
    kind: DraftKind
    payload: TransactionDraftPayload | CategoryDraftPayload
    source: str = "bot"

    def to_api_dict(self) -> dict[str, Any]:
        if isinstance(self.payload, TransactionDraftPayload):
            payload = self.payload.to_api_dict()
        else:
            payload = {"name": self.payload.name}
        return {"kind": self.kind, "payload": payload, "source": self.source}


class Draft(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    user_id: str = Field(alias="userId")
    kind: DraftKind
    status: DraftStatus
    payload: dict[str, Any]
    source: str
    confirmed_at: datetime | str | None = Field(default=None, alias="confirmedAt")
    rejected_at: datetime | str | None = Field(default=None, alias="rejectedAt")
    created_at: datetime | str = Field(alias="createdAt")
    updated_at: datetime | str = Field(alias="updatedAt")


class LoginResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    token: str
    user: dict[str, Any]
