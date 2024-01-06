import asyncio
import json
import os
import threading
import traceback
import uuid
from asyncio import Future
from contextlib import asynccontextmanager
from datetime import datetime
from functools import partial
from typing import Annotated

import httpx
from fastapi import FastAPI, Request, HTTPException, Header
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse

from database import MongoDB
from doc_gpt.json_gpt import run_query_prompt
threads = set()


@asynccontextmanager
async def thread_cleanup(app: FastAPI):
    yield
    for thread in threads:
        print(thread.name)
        thread.join(10)


limiter = Limiter(key_func=get_remote_address)
app = FastAPI(lifespan=thread_cleanup)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SessionMiddleware, secret_key=uuid.uuid4(), max_age=None)
DB = MongoDB()


class OAuthToken(BaseModel):
    id_token: str


class QueryResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    response: str | None = None
    error: str | None = None


class Query(QueryResponse):
    prompt: str


def task_done_callback(request: Request, task: Future) -> None:
    print("INSIDE task_done_callback " * 10)
    print(request, task)
    try:
        request.session[task.get_name()] = task.result()
    except Exception:
        request.session[task.get_name()] = HTTPException(400, task.result())


@app.post("/", response_model=Query)
@limiter.limit("20/day")
async def root(request: Request, query: Query, token: Annotated[str | None, Header()]):
    async def task_worker(request: Request):
        task = asyncio.create_task(run_query_prompt(query.prompt), name=str(query.id))
        task.add_done_callback(partial(task_done_callback, request))
        await task

    th = threading.Thread(target=lambda request: asyncio.run(task_worker(request)), args=(request,), daemon=True)
    th.start()
    threads.add(th)
    print(query.id)
    result = request.session.get("query_response", "Come back in a few mins to get the results")
    return {
        **query.dict(),
        "response": result,
    }


@app.get("/tasks/{task_name}", response_model=QueryResponse)
async def get_task_by_id(request: Request, task_name: str, token: Annotated[str | None, Header()]):
    print(request.session.get(task_name))
    if task_name in request.session:
        try:
            return QueryResponse(**{"response": request.session[task_name], "id": task_name}).dict()
        except HTTPException as http_exc:
            raise http_exc
    raise HTTPException(
        404,
        QueryResponse(**{"error": f"task with id {task_name} not found", "id": task_name}).dict()
    )


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
        redirect_uri=f"{os.getenv('HOST_URL')}/callback/",
    )
    auth_url, state = flow.authorization_url()
    request.session["state"] = state
    print(auth_url, type(auth_url))
    return auth_url


@app.post("/validate")
async def validate(oauth_token: OAuthToken):
    try:
        response_dict = id_token.verify_oauth2_token(oauth_token.id_token, requests.Request())
        token_expired_datetime = datetime.fromtimestamp(response_dict.get("exp"))
        if token_expired_datetime < datetime.now():
            raise HTTPException(401, "Token has expired. Please login again.")
        return response_dict
    except GoogleAuthError as google_auth_error:
        raise HTTPException(401, str(google_auth_error))


@app.get("/callback")
async def callback(request: Request):
    flow = InstalledAppFlow.from_client_secrets_file(
        "credentials-google.json",
        scopes=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile"
        ],
        redirect_uri=f"{os.getenv('HOST_URL')}/callback/",
        state=request.session.get("state")
    )
    code = request.query_params.get("code")
    request.session.clear()
    try:
        flow.fetch_token(code=code)
        user_info_service = build("oauth2", "v2", credentials=flow.credentials)
        user_info = user_info_service.userinfo().get().execute()
        print(user_info, dir(user_info))
        print(flow.credentials.to_json())
        await DB.create_collection("users")
        await DB.create_indexes("users", ["email"])
        await DB.update(
            collection_name="users",
            query={"email": user_info.get("email")},
            data=user_info,
            upsert=True
        )
        await DB.create_collection("credentials")
        await DB.create_indexes("credentials", ["email"])
        await DB.update(
            collection_name="credentials",
            query={"email": user_info.get("email")},
            data=json.loads(flow.credentials.to_json()),
            upsert=True
        )
        return {
            "token": flow.credentials.token,
            "id_token": flow.credentials.id_token
        }
    except Exception as flow_exception:
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(flow_exception))


@app.get("/logout")
async def revoke(
    token: Annotated[str | None, Header()]
):
    async with httpx.AsyncClient() as client:
        try:
            revoke = await asyncio.wait_for(
                client.post(
                  "https://oauth2.googleapis.com/revoke",
                  params={"token": token},
                  headers={"content-type": "application/x-www-form-urlencoded"}
                ),
                timeout=10
            )
        except TimeoutError as asyncio_timeout_error:
            raise HTTPException(400, "Unable to revoke token, details: " + str(asyncio_timeout_error))
    if not revoke.status_code == 200:
        raise HTTPException(revoke.status_code, f"Exception raised with details: {str(revoke.content)}")
    return {
        "status_code": revoke.status_code
    }
