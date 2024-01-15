from pydantic import BaseModel


class OAuthToken(BaseModel):
    id_token: str
