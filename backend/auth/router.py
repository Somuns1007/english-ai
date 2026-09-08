"""Cookie-only auth endpoints with an explicit same-origin mutation guard."""
import os

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from . import service
from .models import User


def protect_request(request: Request, response: Response):
    response.headers["Cache-Control"] = "no-store"
    if request.method != "GET":
        # A custom header forces cross-origin browser requests through CORS preflight.
        if request.headers.get("X-Auth-Request") != "1":
            raise HTTPException(403, "无效的认证请求")
        origin = request.headers.get("origin")
        allowed = {str(request.base_url).rstrip("/")}
        allowed.update(item.strip().rstrip("/") for item in os.getenv(
            "AUTH_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if item.strip())
        if origin and origin not in allowed:
            raise HTTPException(403, "不允许的请求来源")


router = APIRouter(prefix="/api/auth", tags=["auth"], dependencies=[Depends(protect_request)])


class Credentials(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=72)


def cookie_options():
    return dict(httponly=True, secure=os.getenv("AUTH_COOKIE_SECURE", "true").lower() != "false",
                samesite="lax", path="/")


@router.post("/register", response_model=User, status_code=201)
def register(data: Credentials):
    return service.register(data.email, data.password)


@router.post("/login", response_model=User)
def login(data: Credentials, response: Response):
    user, token = service.login(data.email, data.password)
    response.set_cookie("token", token, max_age=service.TOKEN_SECONDS, **cookie_options())
    return user


@router.post("/logout", status_code=204)
def logout(response: Response):
    response.delete_cookie("token", **cookie_options())


@router.get("/me", response_model=User)
def me(request: Request):
    return service.get_user_by_token(request.cookies.get("token"))
