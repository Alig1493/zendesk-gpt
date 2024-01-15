from bson import ObjectId
from bson.errors import InvalidId


class PyObjectId(str):
    """Creating a ObjectId class for pydantic models."""

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

    @classmethod
    def validate(cls, value):
        """Validate given str value to check if good for being ObjectId."""
        try:
            return ObjectId(value)
        except InvalidId as e:
            raise ValueError("Not a valid ObjectId") from e

    @classmethod
    def __get_validators__(cls):
        yield cls.validate
