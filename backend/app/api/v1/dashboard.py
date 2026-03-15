"""
Dashboard summary endpoint — aggregated study data
Uses focused queries (not single monolithic query) per performance P0.
"""

import logging
import uuid
import zoneinfo
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Date, and_, case, cast, distinct, func
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.core.rate_limiter import limiter
from app.models.concept import Concept
from app.models.content import Content
from app.models.study_session import SessionStatus, StudySession
from app.models.subject import Subject
from app.models.user import User
from app.models.user_concept_mastery import UserConceptMastery

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard")


class SubjectWithProgress(BaseModel):
    id: uuid.UUID
    name: str
    color: str
    weekly_goal_minutes: int
    week_minutes: int
    today_minutes: int
    concept_count: int = 0
    mastery_percentage: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class HeatmapDay(BaseModel):
    date: str
    minutes: int


class DashboardSummary(BaseModel):
    today_minutes: int
    week_minutes: int
    current_streak: int
    active_session_id: uuid.UUID | None = None
    subjects: list[SubjectWithProgress]
    heatmap: list[HeatmapDay]
    mastery_index: float | None = None
    total_concepts: int = 0
    mastered_concepts: int = 0


@router.get("/", response_model=DashboardSummary)
@limiter.limit("60/minute")
async def get_dashboard(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_tz = zoneinfo.ZoneInfo(current_user.timezone or "UTC")
    now_local = datetime.now(user_tz)
    today_start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start_local = today_start_local - timedelta(days=today_start_local.weekday())
    heatmap_start_local = today_start_local - timedelta(days=27)

    # Convert to UTC for WHERE clauses (preserves index usage per P1)
    utc = zoneinfo.ZoneInfo("UTC")
    today_start_utc = today_start_local.astimezone(utc)
    week_start_utc = week_start_local.astimezone(utc)
    heatmap_start_utc = heatmap_start_local.astimezone(utc)

    # Query 1: 28-day aggregation grouped by date + subject
    # Covers today, week, heatmap, and subject breakdown in one scan
    try:
        raw_data = (
            db.query(
                cast(StudySession.actual_start, Date).label("study_date"),
                StudySession.subject_id,
                func.sum(StudySession.duration_minutes).label("minutes"),
            )
            .filter(
                StudySession.user_id == current_user.id,
                StudySession.status == SessionStatus.COMPLETED,
                StudySession.actual_start.isnot(None),
                StudySession.actual_start >= heatmap_start_utc,
            )
            .group_by("study_date", StudySession.subject_id)
            .all()
        )
    except Exception:
        logger.warning("Dashboard 28-day aggregation query failed", exc_info=True)
        raw_data = []

    # Process raw data into dashboard components
    today_date = today_start_local.date()
    week_start_date = week_start_local.date()

    today_minutes = 0
    week_minutes = 0
    subject_week: dict[uuid.UUID | None, int] = {}
    subject_today: dict[uuid.UUID | None, int] = {}
    daily_totals: dict[str, int] = {}

    for row in raw_data:
        study_date = row.study_date
        mins = row.minutes or 0
        sid = row.subject_id

        # Heatmap
        date_str = str(study_date)
        daily_totals[date_str] = daily_totals.get(date_str, 0) + mins

        # Today
        if study_date == today_date:
            today_minutes += mins
            subject_today[sid] = subject_today.get(sid, 0) + mins

        # This week
        if study_date >= week_start_date:
            week_minutes += mins
            subject_week[sid] = subject_week.get(sid, 0) + mins

    # Build heatmap (28 days, fill gaps with 0)
    heatmap = []
    for i in range(28):
        d = heatmap_start_local.date() + timedelta(days=i)
        heatmap.append(
            HeatmapDay(
                date=str(d),
                minutes=daily_totals.get(str(d), 0),
            )
        )

    # Query 2: Active session check (partial index, instant)
    active_session = (
        db.query(StudySession.id)
        .filter(
            StudySession.user_id == current_user.id,
            StudySession.status.in_([SessionStatus.IN_PROGRESS, SessionStatus.PAUSED]),
        )
        .first()
    )

    # Query 3: Streak — distinct study dates descending
    try:
        study_dates = (
            db.query(distinct(cast(StudySession.actual_start, Date)))
            .filter(
                StudySession.user_id == current_user.id,
                StudySession.status == SessionStatus.COMPLETED,
                StudySession.duration_minutes >= 1,
                StudySession.actual_start.isnot(None),
            )
            .order_by(cast(StudySession.actual_start, Date).desc())
            .limit(365)
            .all()
        )
    except Exception:
        logger.warning("Dashboard streak query failed", exc_info=True)
        study_dates = []

    # Calculate streak: count consecutive days backwards from today
    streak = 0
    check_date = today_date
    study_date_set = {row[0] for row in study_dates}
    while check_date in study_date_set:
        streak += 1
        check_date -= timedelta(days=1)

    # Build subject progress
    subjects_db = (
        db.query(Subject)
        .filter(Subject.user_id == current_user.id, Subject.is_active == True)
        .all()
    )

    # Query per-subject concept/mastery counts
    mastery_by_subject: dict[uuid.UUID, tuple[int, int]] = {}
    try:
        subject_mastery_rows = (
            db.query(
                Concept.subject_id,
                func.count(Concept.id).label("concept_count"),
                func.sum(
                    case(
                        (UserConceptMastery.status == "mastered", 1),
                        else_=0,
                    )
                ).label("mastered_count"),
            )
            .join(Content, Content.id == Concept.content_id)
            .outerjoin(
                UserConceptMastery,
                and_(
                    UserConceptMastery.concept_id == Concept.id,
                    UserConceptMastery.user_id == current_user.id,
                ),
            )
            .filter(
                Concept.subject_id.isnot(None),
                Content.user_id == current_user.id,
            )
            .group_by(Concept.subject_id)
            .all()
        )
        for row in subject_mastery_rows:
            mastery_by_subject[row.subject_id] = (
                row.concept_count or 0,
                row.mastered_count or 0,
            )
    except Exception:
        logger.warning("Per-subject mastery query failed", exc_info=True)

    subjects = []
    for s in subjects_db:
        concept_count, mastered_count = mastery_by_subject.get(s.id, (0, 0))
        mastery_pct = (mastered_count / concept_count * 100) if concept_count > 0 else 0.0
        subjects.append(
            SubjectWithProgress(
                id=s.id,
                name=s.name,
                color=s.color,
                weekly_goal_minutes=s.weekly_goal_minutes,
                week_minutes=subject_week.get(s.id, 0),
                today_minutes=subject_today.get(s.id, 0),
                concept_count=concept_count,
                mastery_percentage=round(mastery_pct, 1),
            )
        )

    # Query 4: Concept mastery summary
    try:
        mastery_stats = (
            db.query(
                func.count(UserConceptMastery.id).label("total"),
                func.sum(
                    case(
                        (UserConceptMastery.status == "mastered", 1),
                        else_=0,
                    )
                ).label("mastered"),
            )
            .filter(UserConceptMastery.user_id == current_user.id)
            .first()
        )
        total_concepts = (mastery_stats.total or 0) if mastery_stats else 0
        mastered_concepts = (mastery_stats.mastered or 0) if mastery_stats else 0
    except Exception:
        logger.warning("Global mastery count query failed", exc_info=True)
        total_concepts = 0
        mastered_concepts = 0

    mastery_index = (mastered_concepts / total_concepts * 100) if total_concepts > 0 else None

    return DashboardSummary(
        today_minutes=today_minutes,
        week_minutes=week_minutes,
        current_streak=streak,
        active_session_id=active_session[0] if active_session else None,
        subjects=subjects,
        heatmap=heatmap,
        mastery_index=mastery_index,
        total_concepts=total_concepts,
        mastered_concepts=mastered_concepts,
    )
