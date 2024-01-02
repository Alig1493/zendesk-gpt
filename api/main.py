import json
import uuid

from fastapi import FastAPI, Request, HTTPException
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=uuid.uuid4(), max_age=None)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/login", response_class=RedirectResponse, status_code=302)
async def login(request: Request):
    # Create the OAuth flow object
    flow = InstalledAppFlow.from_client_secrets_file(
        "credentials-google.json",
        scopes=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile"
        ],
        redirect_uri="https://b2c7-99-238-98-26.ngrok-free.app/callback/"
    )
    auth_url, state = flow.authorization_url()
    request.session["state"] = state
    print(auth_url, type(auth_url))
    return auth_url


@app.get("/callback")
async def callback(request: Request):
    flow = InstalledAppFlow.from_client_secrets_file(
        "credentials-google.json",
        scopes=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile"
        ],
        redirect_uri="https://b2c7-99-238-98-26.ngrok-free.app/callback/",
        state=request.session.get("state")
    )
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    print(request.query_params, type(request.query_params))
    print(code)
    print(state)
    try:
        flow.fetch_token(code=code)
        credentials = json.loads(flow.credentials.to_json())
        user_info_service = build("oauth2", "v2", credentials=flow.credentials)
        user_info = user_info_service.userinfo().get().execute()
        print(user_info)
        return user_info
    except Exception as flow_exception:
        raise HTTPException(status_code=400, detail=str(flow_exception))
