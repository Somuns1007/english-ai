"""Authenticated post-listening APIs; all mutations require the existing CSRF guard."""
from typing import Literal

from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field

from auth.router import protect_request
from auth.service import get_user_by_token
from . import learning_service as svc, repository


def owner(request: Request):
    return get_user_by_token(request.cookies.get("token")).id


router = APIRouter(prefix="/api/listening/learning", tags=["listening-learning"],
                   dependencies=[Depends(protect_request)])
Gate = Literal["exam_attempt", "cp_session"]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Start(Input):
    gate_type: Gate
    gate_id: str = Field(min_length=1, max_length=100)
    material_id: str = Field(min_length=1, max_length=100)


class Action(Input):
    request_id: str = Field(min_length=8, max_length=100)


class Reveal(Action):
    segment_id: str = Field(min_length=1, max_length=100)


class Attempt(Reveal):
    text: str = Field(default="", max_length=4000)
    difficulty: Literal["unsure", "meaning", "sound", "relation", "spelling", "skip"] = "unsure"


class SaveCard(Input):
    segment_id: str = Field(min_length=1, max_length=100)
    vocabulary_id: str = Field(min_length=1, max_length=100)


class Grade(Action):
    review_id: str = Field(min_length=8, max_length=100)
    grade: Literal[1, 3, 5]


@router.get("/materials")
def materials(gate_type: Gate, gate_id: str, user: str = Depends(owner)):
    return {"data": svc.list_materials(repository.student_repo, user, gate_type, gate_id)}


@router.get("/sessions")
def recent(user: str = Depends(owner)):
    return {"data": svc.recent(repository.student_repo, user)}


@router.post("/sessions")
def start(body: Start, user: str = Depends(owner)):
    return {"data": svc.create(repository.student_repo, user, body.gate_type, body.gate_id, body.material_id)}


@router.get("/sessions/{session_id}")
def state(session_id: str, user: str = Depends(owner)):
    return {"data": svc.state(repository.student_repo, user, session_id)}


@router.post("/sessions/{session_id}/attempts")
def attempt(session_id: str, body: Attempt, user: str = Depends(owner)):
    return {"data": svc.attempt(repository.student_repo, user, session_id, body.segment_id,
                                body.text, body.difficulty, body.request_id)}


@router.post("/sessions/{session_id}/reveal")
def reveal(session_id: str, body: Reveal, user: str = Depends(owner)):
    return {"data": svc.reveal(repository.student_repo, user, session_id, body.segment_id, body.request_id)}


@router.get("/sessions/{session_id}/compare")
def compare(session_id: str, segment_id: str, user: str = Depends(owner)):
    return {"data": svc.compare(repository.student_repo, user, session_id, segment_id)}


@router.post("/sessions/{session_id}/finish")
def finish(session_id: str, body: Action, user: str = Depends(owner)):
    return {"data": svc.finish(repository.student_repo, user, session_id, body.request_id)}


@router.get("/sessions/{session_id}/audio")
def audio(session_id: str, user: str = Depends(owner)):
    path = svc.audio(repository.student_repo, user, session_id)
    return FileResponse(path, media_type="audio/mp4", headers={"Cache-Control": "private, no-store"})


@router.post("/sessions/{session_id}/cards")
def save_card(session_id: str, body: SaveCard, user: str = Depends(owner)):
    return {"data": svc.save_card(repository.student_repo, user, session_id, body.segment_id, body.vocabulary_id)}


@router.get("/cards")
def due(user: str = Depends(owner)):
    return {"data": svc.due_cards(repository.student_repo, user)}


@router.post("/cards/{card_id}/reveal")
def card_reveal(card_id: str, body: Action, user: str = Depends(owner)):
    return {"data": svc.reveal_card(repository.student_repo, user, card_id, body.request_id)}


@router.post("/cards/{card_id}/grade")
def grade(card_id: str, body: Grade, user: str = Depends(owner)):
    return {"data": svc.grade_card(repository.student_repo, user, card_id, body.review_id, body.grade, body.request_id)}
