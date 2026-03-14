"""
Study session lifecycle endpoints (start/pause/resume/stop)
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.core.rate_limiter import limiter
from app.models.study_session import StudySession, SessionStatus, StudyMode
from app.models.subject import Subject
from app.models.user import User
from app.schemas.study_session import (
    SessionStateResponse,
    StartSessionRequest,
)

router = APIRouter(prefix="/sessions")


@router.post("/start", response_model=SessionStateResponse)
@limiter.limit("5/minute")
async def start_session(
    request: Request,
    session_data: StartSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Check for existing active session (partial unique index also enforces this)
    active = (
        db.query(StudySession)
        .filter(
            StudySession.user_id == current_user.id,
            StudySession.status.in_([SessionStatus.IN_PROGRESS, SessionStatus.PAUSED]),
        )
        .first()
    )
    if active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "Active session exists", "active_session_id": str(active.id)},
        )

    # Verify subject belongs to user (if provided)
    if session_data.subject_id:
        subject = (
            db.query(Subject)
            .filter(
                Subject.id == session_data.subject_id,
                Subject.user_id == current_user.id,
            )
            .first()
        )
        if not subject:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
        title = (
            session_data.title or f"{subject.name} - {datetime.utcnow().strftime('%b %d %H:%M')}"
        )
    else:
        title = session_data.title or f"General Study - {datetime.utcnow().strftime('%b %d %H:%M')}"

    session = StudySession(
        user_id=current_user.id,
        subject_id=session_data.subject_id,
        title=title,
        study_mode=StudyMode(session_data.study_mode),
        status=SessionStatus.IN_PROGRESS,
        actual_start=datetime.utcnow(),
        last_resumed_at=datetime.utcnow(),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.patch("/{session_id}/pause", response_model=SessionStateResponse)
@limiter.limit("30/minute")
async def pause_session(
    request: Request,
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    now = datetime.utcnow()

    session = (
        db.query(StudySession)
        .filter(
            StudySession.id == session_id,
            StudySession.user_id == current_user.id,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.status != SessionStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "Invalid transition", "current_status": session.status.value},
        )

    # Accumulate time from current segment
    if session.last_resumed_at:
        segment = (now - session.last_resumed_at).total_seconds()
        session.accumulated_seconds += int(segment)
    session.status = SessionStatus.PAUSED
    session.last_resumed_at = None
    session.updated_at = now
    db.commit()
    db.refresh(session)
    return session


@router.patch("/{session_id}/resume", response_model=SessionStateResponse)
@limiter.limit("30/minute")
async def resume_session(
    request: Request,
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(StudySession)
        .filter(
            StudySession.id == session_id,
            StudySession.user_id == current_user.id,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.status != SessionStatus.PAUSED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "Invalid transition", "current_status": session.status.value},
        )

    session.status = SessionStatus.IN_PROGRESS
    session.last_resumed_at = datetime.utcnow()
    session.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(session)
    return session


@router.patch("/{session_id}/stop", response_model=SessionStateResponse)
@limiter.limit("10/minute")
async def stop_session(
    request: Request,
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(StudySession)
        .filter(
            StudySession.id == session_id,
            StudySession.user_id == current_user.id,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.status not in (SessionStatus.IN_PROGRESS, SessionStatus.PAUSED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "Invalid transition", "current_status": session.status.value},
        )

    now = datetime.utcnow()

    # Accumulate remaining time if still in progress
    if session.status == SessionStatus.IN_PROGRESS and session.last_resumed_at:
        segment = (now - session.last_resumed_at).total_seconds()
        session.accumulated_seconds += int(segment)

    session.actual_end = now
    session.duration_minutes = session.accumulated_seconds // 60
    session.last_resumed_at = None
    session.updated_at = now

    # Less than 1 minute = cancelled (doesn't count for metrics)
    if session.duration_minutes < 1:
        session.status = SessionStatus.CANCELLED
    else:
        session.status = SessionStatus.COMPLETED

    db.commit()
    db.refresh(session)
    return session


@router.get("/active", response_model=Optional[SessionStateResponse])
@limiter.limit("60/minute")
async def get_active_session(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(StudySession)
        .filter(
            StudySession.user_id == current_user.id,
            StudySession.status.in_([SessionStatus.IN_PROGRESS, SessionStatus.PAUSED]),
        )
        .first()
    )
    return session


@router.get("/history", response_model=List[SessionStateResponse])
@limiter.limit("60/minute")
async def get_session_history(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 20,
    offset: int = 0,
):
    return (
        db.query(StudySession)
        .filter(
            StudySession.user_id == current_user.id,
            StudySession.status.in_([SessionStatus.COMPLETED, SessionStatus.CANCELLED]),
        )
        .order_by(StudySession.actual_end.desc())
        .offset(offset)
        .limit(min(limit, 100))
        .all()
    )
