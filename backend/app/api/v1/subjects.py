"""
Subject CRUD endpoints
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import get_current_user, get_db
from app.core.rate_limiter import shared_limiter as limiter
from app.models.subject import Subject, SUBJECT_COLORS
from app.models.user import User
from app.schemas.subject import SubjectCreate, SubjectResponse, SubjectUpdate
from app.utils.sanitization import sanitize_input

router = APIRouter(prefix="/subjects")


@router.post("/", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_subject(
    request: Request,
    subject_data: SubjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    subject_count = (
        db.query(Subject)
        .filter(
            Subject.user_id == current_user.id,
            Subject.is_active == True,
        )
        .count()
    )

    if subject_count >= 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum of 50 active subjects allowed",
        )

    if not subject_data.color or subject_data.color == "#D4FF00":
        color_index = subject_count % len(SUBJECT_COLORS)
        subject_data_dict = subject_data.model_dump()
        subject_data_dict["color"] = SUBJECT_COLORS[color_index]
    else:
        subject_data_dict = subject_data.model_dump()

    subject_data_dict["name"] = sanitize_input(subject_data_dict["name"])

    subject = Subject(
        user_id=current_user.id,
        **subject_data_dict,
    )

    try:
        db.add(subject)
        db.commit()
        db.refresh(subject)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Subject '{subject_data.name}' already exists",
        )

    return subject


@router.get("/", response_model=List[SubjectResponse])
@limiter.limit("60/minute")
async def list_subjects(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    include_inactive: bool = False,
):
    query = db.query(Subject).filter(Subject.user_id == current_user.id)
    if not include_inactive:
        query = query.filter(Subject.is_active == True)
    return query.order_by(Subject.created_at.desc()).all()


@router.get("/{subject_id}", response_model=SubjectResponse)
@limiter.limit("60/minute")
async def get_subject(
    request: Request,
    subject_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    subject = (
        db.query(Subject)
        .filter(
            Subject.id == subject_id,
            Subject.user_id == current_user.id,
        )
        .first()
    )
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    return subject


@router.patch("/{subject_id}", response_model=SubjectResponse)
@limiter.limit("30/minute")
async def update_subject(
    request: Request,
    subject_id: str,
    update_data: SubjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    subject = (
        db.query(Subject)
        .filter(
            Subject.id == subject_id,
            Subject.user_id == current_user.id,
        )
        .first()
    )
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")

    update_dict = update_data.model_dump(exclude_unset=True)
    if "name" in update_dict:
        update_dict["name"] = sanitize_input(update_dict["name"])

    for key, value in update_dict.items():
        setattr(subject, key, value)

    try:
        db.commit()
        db.refresh(subject)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Subject '{update_data.name}' already exists",
        )

    return subject


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_subject(
    request: Request,
    subject_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    subject = (
        db.query(Subject)
        .filter(
            Subject.id == subject_id,
            Subject.user_id == current_user.id,
        )
        .first()
    )
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")

    subject.is_active = False
    db.commit()
