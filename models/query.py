import secrets
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, Field

from models.validators.query import PyObjectId


class QueryResponse(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=lambda: secrets.token_hex(12), alias="_id")
    # id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    response: str | None = Field(default="Response not processed yet. Come back later.")
    error: str | None = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "id": "<mongo id>",
                "response": "<query response>",
                "error": "<error response>",
            }
        }


class Query(QueryResponse):
    prompt: str

    class Config(QueryResponse.Config):
        schema_extra = {
            "example": {
                "id": "<mongo id>",
                "prompt": "<query prompt>",
                "response": "<query response>",
                "error": "<error response>",
            }
        }
