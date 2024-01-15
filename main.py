import asyncio
import json
import os
import threading
import traceback
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated

import httpx
from bson import ObjectId
from fastapi import FastAPI, Request, HTTPException, Header
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse

from database import MongoDB
from doc_gpt.json_gpt import run_query_prompt
from models.auth import OAuthToken
from models.query import QueryResponse, Query

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


async def task_done_callback(object_id: str, result: str) -> None:
    print("INSIDE task_done_callback " * 10)
    print(result, type(result), dir(result))
    print("INITIATING Task done callback")
    print(DB)
    db = MongoDB()
    document_to_update = await db.find(
        "queries",
        {"id": object_id},
        find_one=True
    )
    print("Document to update: ", document_to_update)
    document_to_update = await document_to_update
    print("Document to update: ", document_to_update)
    if not document_to_update:
        document_to_update = QueryResponse(**{"id": object_id}).dict()
    document_to_update = {
        **document_to_update,
        "response": result,
    }
    print("Updated document to update:", document_to_update)
    updated_db = await db.update(
        "queries",
        {"id": object_id},
        data=document_to_update,
    )
    print("Updated DB:", await updated_db)


@app.post("/", response_model=Query)
@limiter.limit("20/day")
async def root(request: Request, query: Query, token: Annotated[str | None, Header()]):

    async def task_worker():
        print("Starting task worker")
        print("&" * 100)
        print(query, query.prompt)

        # async def debug():
        #     return "debug"

        task = asyncio.ensure_future(run_query_prompt(query.prompt))
        # task = asyncio.ensure_future(debug())
        for f in asyncio.as_completed([task]):
            result_task = await f
            await task_done_callback(query.id, result_task)

    th = threading.Thread(
        target=lambda: asyncio.run(task_worker()),
        daemon=True
    )
    th.start()
    threads.add(th)
    try:
        await DB.create_collection("queries")
        document = await DB.insert_document("queries", **query.dict())
        print(document)
        print(document.inserted_id)
        print(query.id, query.dict())

        result_document = await DB.find(
            "queries",
            {"id": document.inserted_id},
            find_one=True
        )
        result = await result_document

        return {
            **query.dict(),
            "id": document.inserted_id,
            "result": result.get("response", query.dict()["response"]) if result else query.dict()["response"]
        }
    except Exception as exc:
        print(traceback.format_exc())
        raise HTTPException(400, str(exc))


@app.get("/tasks/{query_id}", response_model=QueryResponse)
async def get_task_by_id(request: Request, query_id: str, token: Annotated[str | None, Header()]):
    document = await DB.find(
        "queries",
        {"_id": ObjectId(query_id)},
        find_one=True
    )
    result = await document
    print(result)
    if result:
        try:
            return QueryResponse(**{"response": result["response"], "id": result["_id"]}).dict()
        except HTTPException as http_exc:
            raise http_exc
    raise HTTPException(
        404,
        QueryResponse(**{"error": f"task with id {query_id} not found", "id": str(query_id)}).dict()
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
