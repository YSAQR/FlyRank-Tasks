"""
Pydantic data models for validated book records.

A ``Book`` instance represents a fully validated, clean book record
ready for export.  Validation rules are enforced by Pydantic field
validators so that invalid records are rejected with clear error
messages.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class Book(BaseModel):
    """A validated book record.

    Validation rules
    ----------------
    - ``title``: non-empty string.
    - ``price``: non-negative float (monetary value).
    - ``rating``: integer in [1, 5].
    - ``availability``: one of ``'in stock'`` or ``'out of stock'``.
    - ``product_url``: non-empty absolute URL starting with ``http``.
    """

    title: str = Field(..., min_length=1,
                       description="Full book title")
    price: float = Field(..., ge=0.0,
                         description="Price as a non-negative number")
    rating: int = Field(..., ge=1, le=5,
                        description="Star rating from 1 to 5")
    availability: str = Field(...,
                              description="'in stock' or 'out of stock'")
    product_url: str = Field(..., min_length=1,
                             description="Absolute URL to the product page")

    @field_validator("availability")
    @classmethod
    def availability_must_be_known(cls, v: str) -> str:
        allowed = {"in stock", "out of stock"}
        if v not in allowed:
            raise ValueError(
                f"availability must be one of {allowed!r}, got {v!r}"
            )
        return v

    @field_validator("product_url")
    @classmethod
    def url_must_be_absolute(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError(
                f"product_url must be an absolute URL, got {v!r}"
            )
        return v
