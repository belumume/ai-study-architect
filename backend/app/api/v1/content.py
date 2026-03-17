"""Content management API endpoints"""

import hashlib
import logging
import re
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from sqlalchemy import and_, func, literal
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.core.cache import redis_cache
from app.core.config import settings
from app.core.csrf import require_csrf_token
from app.core.exceptions import (
    ContentAlreadyExistsError,
    ContentNotFoundError,
    FileTooLargeError,
    FileUploadError,
    InvalidFileTypeError,
    ValidationError,
)
from app.core.rate_limiter import limiter
from app.core.utils import utcnow
from app.models.concept import Concept
from app.models.content import Content
from app.models.user import User
from app.models.user_concept_mastery import UserConceptMastery
from app.schemas.content import ContentResponse, ContentUpdate
from app.services import storage as r2
from app.services.content_processor import content_processor
from app.utils.sanitization import sanitize_filename, sanitize_input

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/content", tags=["content"])

VIEW_COUNT_PREFIX = "view_count:"


def _increment_view_count(content_id: uuid.UUID) -> None:
    """Buffer view count increment in Redis. Falls back to no-op if Redis unavailable."""
    try:
        client = redis_cache._get_client()
        key = f"{VIEW_COUNT_PREFIX}{content_id}"
        client.incr(key)
        client.expire(key, 86400)
    except Exception as e:
        logger.debug(f"View count buffer failed for {content_id}: {e}")


def flush_view_counts(db: Session) -> int:
    """Flush buffered view counts from Redis to the database.

    Must be called periodically by an external scheduler (cron, background task).
    Not called automatically — view counts accumulate in Redis until flushed.
    Returns number of content items flushed.
    """
    try:
        client = redis_cache._get_client()
        keys = client.keys(f"{VIEW_COUNT_PREFIX}*")
        if not keys:
            return 0

        flushed = 0
        for key in keys:
            raw = redis_cache.get(key)
            if not raw:
                continue
            count = int(raw)
            if count <= 0:
                continue

            # Extract content_id from key
            content_id_str = (
                key.replace(VIEW_COUNT_PREFIX, "")
                if isinstance(key, str)
                else key.decode().replace(VIEW_COUNT_PREFIX, "")
            )
            try:
                content_id = uuid.UUID(content_id_str)
            except ValueError:
                redis_cache.delete(key)
                continue

            db.query(Content).filter(Content.id == content_id).update(
                {Content.view_count: Content.view_count + count},
                synchronize_session=False,
            )
            flushed += 1

        if flushed:
            db.commit()
            # Delete keys after successful commit. Small race window exists
            # where concurrent INCR between read and delete loses ~1-2 views.
            # Acceptable for analytics counters at current scale.
            for key in keys:
                redis_cache.delete(key)
        return flushed
    except Exception as e:
        logger.warning(f"View count flush failed: {e}")
        db.rollback()
        return 0


# tsquery special characters that must be stripped to prevent injection
_TSQUERY_SPECIAL_RE = re.compile(r"[&|!():*<>'\\]")


def _sanitize_tsquery_word(word: str) -> str:
    """Remove tsquery special characters from a single word."""
    return _TSQUERY_SPECIAL_RE.sub("", word).strip()


def _build_prefix_tsquery(raw_query: str) -> str:
    """Build a to_tsquery expression string with prefix matching.

    - Normalizes non-alphanumeric chars to spaces (so "well-known", "node.js",
      "c/c++" all split into separate words matching tsvector tokenization)
    - Strips tsquery-special characters to prevent syntax injection
    - Single word: ``term:*`` (prefix match)
    - Multi-word: ``word1 & word2 & lastword:*`` (all must match, last gets prefix)

    Returns an empty string if no valid words remain after sanitization.
    """
    # Normalize non-alnum to spaces before splitting — to_tsquery expects
    # tsquery syntax and doesn't tokenize on punctuation, but tsvector does.
    normalized = re.sub(r"[^a-zA-Z0-9\s]", " ", raw_query)
    words = [_sanitize_tsquery_word(w) for w in normalized.split()]
    words = [w for w in words if w]
    if not words:
        return ""
    if len(words) == 1:
        return f"{words[0]}:*"
    return " & ".join(words[:-1]) + f" & {words[-1]}:*"


# File type validation
ALLOWED_MIME_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
    "application/vnd.ms-powerpoint": "ppt",  # Old PowerPoint format
    "text/plain": "txt",
    "text/markdown": "md",
    "image/jpeg": "jpg",
    "image/png": "png",
    "audio/mpeg": "mp3",
    "audio/mp4": "mp4",
    "audio/wav": "wav",
    "video/mp4": "mp4",
}

# Extensions that might be detected as zip but are actually allowed
OFFICE_EXTENSIONS = {".docx", ".pptx", ".xlsx"}


def validate_file(file: UploadFile) -> tuple[str, str]:
    """
    Validate uploaded file with enhanced security checks.
    Returns (mime_type, extension) if valid.
    """
    if not file:
        raise ValidationError("No file provided")

    if not file.filename:
        raise ValidationError("No filename provided")

    # Read entire file content for deep validation
    file_content = file.file.read()
    file.file.seek(0)  # Reset file pointer

    # Check file size
    file_size = len(file_content)
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise FileTooLargeError(max_size=settings.MAX_UPLOAD_SIZE)

    # Get file extension
    file_extension = Path(file.filename).suffix.lower()

    # Perform deep content validation
    from app.utils.file_validation import validate_file_content

    # For Office files, add application/zip to allowed types
    allowed_types = list(ALLOWED_MIME_TYPES.keys())
    if file_extension in OFFICE_EXTENSIONS:
        allowed_types.append("application/zip")

    is_valid, error_msg, validation_info = validate_file_content(
        file_content,
        file.filename,
        allowed_mime_types=allowed_types,
        max_file_size=settings.MAX_UPLOAD_SIZE,
    )

    if not is_valid:
        logger.warning(
            f"File validation failed: {error_msg}, warnings: {validation_info.get('security_warnings', [])}"
        )
        raise ValidationError(f"File validation failed: {error_msg}")

    # Log security warnings if any
    if validation_info.get("security_warnings"):
        logger.warning(
            f"Security warnings for file {file.filename}: {validation_info['security_warnings']}"
        )

    mime_type = validation_info["mime_type"]

    # Handle Office files detected as zip
    if mime_type == "application/zip" and file_extension in OFFICE_EXTENSIONS:
        # Map extension to proper mime type and extension
        if file_extension == ".docx":
            mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            extension = "docx"
        elif file_extension == ".pptx":
            mime_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            extension = "pptx"
        elif file_extension == ".xlsx":
            mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            extension = "xlsx"
    else:
        extension = ALLOWED_MIME_TYPES.get(mime_type)
        if not extension:
            raise ValidationError(f"File type '{mime_type}' not allowed")

    return mime_type, extension


def generate_file_hash(file: UploadFile) -> str:
    """Generate SHA-256 hash of file content for deduplication"""
    sha256_hash = hashlib.sha256()

    # Read file in chunks to handle large files
    for chunk in iter(lambda: file.file.read(4096), b""):
        sha256_hash.update(chunk)

    file.file.seek(0)  # Reset file pointer
    return sha256_hash.hexdigest()


def save_upload_file(
    file_content: bytes, user_id: str, extension: str, mime_type: str
) -> tuple[str, str]:
    """
    Upload file to R2 storage.
    Returns (r2_key, file_id)
    """
    file_id = str(uuid.uuid4())
    r2_key = f"uploads/{user_id}/{file_id}.{extension}"

    try:
        success = r2.upload_file(r2_key, file_content, content_type=mime_type)
        if not success:
            raise FileUploadError(detail="Failed to upload file to storage")
    except FileUploadError:
        raise
    except Exception as e:
        logger.error(f"Failed to upload file to R2: {str(e)}", exc_info=True)
        raise FileUploadError(detail="Failed to save uploaded file") from e

    return r2_key, file_id


@router.post("/upload", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def upload_content(
    request: Request,
    file: UploadFile = File(...),
    title: str | None = Form(None),
    description: str | None = Form(None),
    content_type: str | None = Form(None),
    subject: str | None = Form(None),
    tags: str | None = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload educational content.

    - **file**: The file to upload (PDF, DOCX, PPTX, TXT, MD, images, audio, video)
    - **title**: Title of the content
    - **description**: Optional description
    - **content_type**: Type of content (notes, textbook, video, etc.)
    - **tags**: Comma-separated tags
    """
    try:
        logger.info(f"Upload request from user {current_user.id}: {file.filename}")
        logger.info(f"Form data - title: {title}, content_type: {content_type}, subject: {subject}")

        # Use filename as title if not provided
        if not title:
            title = file.filename

        # Default content_type if not provided
        if not content_type:
            content_type = "document"  # Default to document

        # Read file content once for all operations
        file_content = file.file.read()
        file.file.seek(0)

        # Validate file
        mime_type, extension = validate_file(file)
        logger.info(f"File validated: {mime_type}, extension: {extension}")

        # Generate file hash for deduplication using already-read content
        from app.utils.file_validation import calculate_file_hash

        file_hash = calculate_file_hash(file_content)

        # Check if file already exists for this user
        existing_content = (
            db.query(Content)
            .filter(and_(Content.user_id == current_user.id, Content.file_hash == file_hash))
            .first()
        )

        if existing_content:
            raise ContentAlreadyExistsError()

        # Upload file to R2
        file_path, file_id = save_upload_file(
            file_content, str(current_user.id), extension, mime_type
        )

        # Sanitize inputs
        sanitized_title = sanitize_input(title)
        sanitized_description = sanitize_input(description) if description else None
        sanitized_subject = sanitize_input(subject) if subject else None
        sanitized_filename = sanitize_filename(file.filename)

        # Parse and sanitize tags
        tag_list = []
        if tags:
            tag_list = [sanitize_input(tag.strip()) for tag in tags.split(",") if tag.strip()]

        # File size from in-memory content
        file_size = len(file_content)

        # Create content record
        content = Content(
            id=uuid.uuid4(),
            user_id=current_user.id,
            title=sanitized_title,
            description=sanitized_description,
            content_type=content_type,
            subject=sanitized_subject,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            file_hash=file_hash,
            original_filename=sanitized_filename,
            tags=tag_list,
            processing_status="pending",
            created_at=utcnow(),
            updated_at=utcnow(),
        )

        db.add(content)
        db.commit()
        db.refresh(content)

        logger.info(f"User {current_user.id} uploaded content: {content.id}")

        # Process the file synchronously for reliability
        logger.info(f"=== STARTING CONTENT PROCESSING for {content.id} ===")

        # Send WebSocket update if available
        try:
            import asyncio

            from app.api.v1.websocket import websocket_manager

            asyncio.create_task(
                websocket_manager.send_personal_message(
                    {
                        "type": "processing_status",
                        "content_id": str(content.id),
                        "status": "processing",
                        "message": f"Extracting text from {content.title}...",
                    },
                    str(current_user.id),
                )
            )
        except Exception as e:
            logger.warning(f"Could not send WebSocket update: {e}")

        try:
            logger.info(f"Processing content {content.id}")

            # Extract text from the file (write to temp file for processing)
            import tempfile

            suffix = f".{extension}"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(file_content)
                tmp_path = tmp.name
            try:
                logger.info(f"Processing file via temp: {tmp_path}")
                processing_result = content_processor.process_file(tmp_path, mime_type)
            finally:
                Path(tmp_path).unlink(missing_ok=True)
            logger.info(f"Processing result: success={processing_result['success']}")

            if processing_result["success"]:
                # Update content with full extracted text - no truncation at storage
                content.extracted_text = processing_result["text"]  # Store full text
                content.processing_status = "completed"
                content.content_metadata = processing_result["metadata"]

                # Commit the extracted text immediately
                db.commit()
                logger.info(f"Text extraction saved for {content.id}")

                # Skip AI summary for now - it's causing issues with async in sync context
                # Just add a basic summary based on the extracted text
                if processing_result["text"]:
                    text_preview = processing_result["text"][:500].replace("\n", " ").strip()
                    content.summary = f"Content from {content.title}. Preview: {text_preview}..."

                    # Extract some basic keywords as concepts
                    words = processing_result["text"].lower().split()
                    # Get most common non-trivial words
                    word_freq = {}
                    stop_words = {
                        "the",
                        "a",
                        "an",
                        "and",
                        "or",
                        "but",
                        "in",
                        "on",
                        "at",
                        "to",
                        "for",
                        "of",
                        "with",
                        "by",
                        "from",
                        "as",
                        "is",
                        "was",
                        "are",
                        "were",
                    }
                    for word in words:
                        if len(word) > 4 and word not in stop_words and word.isalpha():
                            word_freq[word] = word_freq.get(word, 0) + 1

                    # Get top 5 most frequent words as key concepts
                    key_concepts = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
                    content.key_concepts = [word for word, _ in key_concepts]

                    db.commit()
                    logger.info(f"Basic summary and keywords added for {content.id}")
            else:
                content.processing_status = "failed"
                content.processing_error = processing_result["metadata"].get(
                    "error", "Unknown error"
                )

            db.commit()
            db.refresh(content)
            logger.info(f"=== CONTENT PROCESSING COMPLETED for {content.id} ===")
            logger.info(f"Final status: {content.processing_status}")
            logger.info(f"Has extracted text: {bool(content.extracted_text)}")
            logger.info(f"Has summary: {bool(content.summary)}")

        except Exception as e:
            logger.error(f"Error processing content {content.id}: {str(e)}", exc_info=True)
            # Don't fail the upload if processing fails
            content.processing_status = "pending"  # Mark as pending instead of failed
            content.processing_error = f"Processing deferred: {str(e)}"
            db.commit()

            # Return success even if processing failed - user can still see the file
            logger.warning(f"Upload succeeded but processing deferred for {content.id}")

        return content

    except (
        ContentAlreadyExistsError,
        InvalidFileTypeError,
        FileTooLargeError,
        FileUploadError,
        ValidationError,
    ):
        raise
    except Exception as e:
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        raise FileUploadError(detail="Failed to upload content") from e


@router.get("/", response_model=list[ContentResponse])
@limiter.limit("30/minute")
def list_content(
    request: Request,
    skip: int = 0,
    limit: int = 20,
    content_type: str | None = None,
    tag: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List user's uploaded content with optional filtering

    Optimized to prevent N+1 queries by using efficient database queries
    with proper indexing and minimal data loading.
    """
    # Use optimized query with proper eager loading
    query = (
        db.query(Content)
        .options(
            # Only load user relationship if needed (currently not in response model)
            # joinedload(Content.user) - commented out as not needed in response
        )
        .filter(Content.user_id == current_user.id)
    )

    # Apply filters
    if content_type:
        query = query.filter(Content.content_type == content_type)

    if tag:
        # Optimized tag filtering using JSON contains operator
        query = query.filter(Content.tags.contains([tag]))

    # Apply ordering and pagination
    # Order by created_at DESC is indexed for performance
    query = query.order_by(Content.created_at.desc())

    # Execute query with pagination
    content_items = query.offset(skip).limit(limit).all()

    logger.info(f"User {current_user.id} listed {len(content_items)} content items")

    return content_items


@router.get("/stats", response_model=dict)
@limiter.limit("20/minute")
def get_content_stats(
    request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Get content statistics for the current user

    Returns summary statistics without loading all content items,
    preventing N+1 queries through aggregate functions.
    """
    # Consolidated: 2 queries instead of 5 using conditional aggregation
    # Query 1: Scalar aggregates (total count, total size, total study time)
    agg_row = (
        db.query(
            func.count(Content.id).label("total_count"),
            func.coalesce(func.sum(Content.file_size), 0).label("total_size"),
            func.coalesce(func.sum(Content.study_time_minutes), 0).label("total_study_time"),
        )
        .filter(Content.user_id == current_user.id)
        .one()
    )
    total_count = agg_row.total_count
    total_size = agg_row.total_size
    total_study_time = agg_row.total_study_time

    # Query 2: Grouped counts for both content_type and processing_status
    # Uses UNION ALL to get both breakdowns in a single round-trip
    type_q = (
        db.query(
            literal("type").label("dimension"),
            Content.content_type.label("key"),
            func.count(Content.id).label("count"),
        )
        .filter(Content.user_id == current_user.id)
        .group_by(Content.content_type)
    )
    status_q = (
        db.query(
            literal("status").label("dimension"),
            Content.processing_status.label("key"),
            func.count(Content.id).label("count"),
        )
        .filter(Content.user_id == current_user.id)
        .group_by(Content.processing_status)
    )
    grouped_rows = type_q.union_all(status_q).all()

    by_type: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for dimension, key, count in grouped_rows:
        if dimension == "type":
            by_type[key] = count
        else:
            by_status[key] = count

    stats = {
        "total_content": total_count,
        "by_type": by_type,
        "by_status": by_status,
        "total_file_size_bytes": total_size,
        "total_study_time_minutes": float(total_study_time),
        "avg_file_size_bytes": total_size // total_count if total_count > 0 else 0,
    }

    logger.info(f"User {current_user.id} requested content stats")
    return stats


@router.get("/search", response_model=list[ContentResponse])
@limiter.limit("20/minute")
def search_content(
    request: Request,
    q: str,  # Search query
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Search user's content by title, description, or extracted text

    Optimized full-text search using database indexes and efficient queries.
    """
    if len(q.strip()) < 2:
        raise ValidationError("Search query must be at least 2 characters")

    # Build prefix-matching tsquery for typeahead behavior.
    # Single word "algo" becomes "algo:*" matching "algorithm", "algorithmic", etc.
    # Multi-word "data struct" becomes "data & struct:*".
    tsquery_expr = _build_prefix_tsquery(q)
    if not tsquery_expr:
        return []

    ts_query = func.to_tsquery("english", tsquery_expr)

    content_items = (
        db.query(Content)
        .filter(
            and_(
                Content.user_id == current_user.id,
                Content.search_vector.op("@@")(ts_query),
            )
        )
        .order_by(
            func.ts_rank(Content.search_vector, ts_query).desc(),
            Content.created_at.desc(),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )

    logger.info(f"User {current_user.id} searched for '{q}' - found {len(content_items)} results")

    return content_items


@router.get("/{content_id}", response_model=ContentResponse)
@limiter.limit("30/minute")
def get_content(
    request: Request,
    content_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get specific content by ID

    Optimized query that only loads the requested content item
    without any unnecessary relationships.
    View count is buffered in Redis and flushed periodically,
    avoiding a DB write on every read.
    """
    content = (
        db.query(Content)
        .filter(and_(Content.id == content_id, Content.user_id == current_user.id))
        .first()
    )

    if not content:
        raise ContentNotFoundError()

    # Buffer view count in Redis (non-blocking, no DB write)
    _increment_view_count(content_id)

    # Update last_accessed_at in a background task so it doesn't block the response
    def _update_last_accessed(cid: uuid.UUID, uid: uuid.UUID) -> None:
        from app.core.database import SessionLocal

        session = SessionLocal()
        try:
            session.query(Content).filter(and_(Content.id == cid, Content.user_id == uid)).update(
                {Content.last_accessed_at: utcnow()},
                synchronize_session=False,
            )
            session.commit()
        except Exception as e:
            logger.warning(f"Failed to update last_accessed_at: {e}")
            session.rollback()
        finally:
            session.close()

    background_tasks.add_task(_update_last_accessed, content_id, current_user.id)

    logger.info(f"User {current_user.id} accessed content {content_id}")
    return content


@router.put("/{content_id}", response_model=ContentResponse)
@limiter.limit("10/minute")
def update_content(
    request: Request,
    content_id: uuid.UUID,
    content_update: ContentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update content metadata

    Optimized to only fetch and update the specific content item
    without loading unnecessary relationships.
    """
    # Use efficient query to find and lock the content for update
    content = (
        db.query(Content)
        .filter(and_(Content.id == content_id, Content.user_id == current_user.id))
        .first()
    )

    if not content:
        raise ContentNotFoundError()

    # Track what fields are being updated for logging
    updated_fields = []

    # Update fields with sanitization
    update_data = content_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:  # Only update non-None values
            if field == "title" and value:
                value = sanitize_input(value)
                updated_fields.append("title")
            elif field == "description" and value:
                value = sanitize_input(value)
                updated_fields.append("description")
            elif field == "tags" and value:
                value = [sanitize_input(tag) for tag in value if tag.strip()]
                updated_fields.append("tags")
            elif field == "content_type":
                updated_fields.append("content_type")
            elif field == "subject":
                value = sanitize_input(value) if value else None
                updated_fields.append("subject")

            setattr(content, field, value)

    # Always update the timestamp
    content.updated_at = utcnow()

    try:
        db.commit()
        db.refresh(content)
        logger.info(f"User {current_user.id} updated content {content_id} fields: {updated_fields}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update content {content_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update content") from e

    return content


@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
def delete_content(
    request: Request,
    content_id: uuid.UUID,
    confirm_delete: bool = False,
    _csrf: None = Depends(require_csrf_token),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete content and associated file.

    If content has extracted concepts, returns 409 with cascade impact
    unless confirm_delete=true is passed as a query parameter.
    """
    # Only select the fields we need for deletion
    content = (
        db.query(Content.id, Content.file_path, Content.title)
        .filter(and_(Content.id == content_id, Content.user_id == current_user.id))
        .first()
    )

    if not content:
        raise ContentNotFoundError()

    # Check cascade impact before deleting
    if not confirm_delete:
        concept_count = (
            db.query(func.count(Concept.id)).filter(Concept.content_id == content_id).scalar()
        )
        if concept_count > 0:
            mastery_count = (
                db.query(func.count(UserConceptMastery.id))
                .join(Concept, Concept.id == UserConceptMastery.concept_id)
                .filter(
                    Concept.content_id == content_id,
                    UserConceptMastery.user_id == current_user.id,
                )
                .scalar()
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": (
                        f"Deleting this content will also delete {concept_count} concepts "
                        f"and {mastery_count} mastery records. "
                        f"Add ?confirm_delete=true to proceed."
                    ),
                    "concepts_count": concept_count,
                    "mastery_records": mastery_count,
                },
            )

    content_title = content.title
    file_path = content.file_path

    # Delete file from R2 first (before database deletion)
    file_deleted = False
    if file_path:
        try:
            file_deleted = r2.delete_file(file_path)
            if file_deleted:
                logger.info(f"Deleted file from R2: {file_path}")
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {str(e)}")

    # Delete database record using efficient delete query
    try:
        deleted_count = (
            db.query(Content)
            .filter(and_(Content.id == content_id, Content.user_id == current_user.id))
            .delete(synchronize_session=False)
        )  # More efficient than loading object

        if deleted_count == 0:
            raise ContentNotFoundError()

        db.commit()

        logger.info(
            f"User {current_user.id} deleted content '{content_title}' "
            f"(ID: {content_id}, file_deleted: {file_deleted})"
        )

    except ContentNotFoundError:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete content {content_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete content") from e

    return None


@router.post("/bulk-delete", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
def bulk_delete_content(
    request: Request,
    content_ids: list[uuid.UUID],
    _csrf: None = Depends(require_csrf_token),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Bulk delete multiple content items

    Highly optimized for deleting multiple items with minimal database queries.
    Returns summary of deletion results.
    """
    if not content_ids:
        raise ValidationError("No content IDs provided")

    if len(content_ids) > 50:  # Reasonable limit
        raise ValidationError("Cannot delete more than 50 items at once")

    # Fetch only necessary fields for deletion in a single query
    content_items = (
        db.query(Content.id, Content.file_path, Content.title)
        .filter(and_(Content.id.in_(content_ids), Content.user_id == current_user.id))
        .all()
    )

    if not content_items:
        raise ContentNotFoundError("No matching content items found")

    # Track results
    results = {
        "requested": len(content_ids),
        "found": len(content_items),
        "files_deleted": 0,
        "files_failed": 0,
        "db_deleted": 0,
    }

    # Delete files from R2 in parallel (boto3 is sync, so use threads)
    file_paths = [c.file_path for c in content_items if c.file_path]

    def _delete_one(path: str) -> bool:
        try:
            return r2.delete_file(path)
        except Exception as e:
            logger.error(f"Failed to delete file {path}: {e}")
            return False

    if file_paths:
        with ThreadPoolExecutor(max_workers=min(len(file_paths), 10)) as executor:
            delete_results = list(executor.map(_delete_one, file_paths))
        results["files_deleted"] = sum(1 for ok in delete_results if ok)
        results["files_failed"] = sum(1 for ok in delete_results if not ok)

    # Bulk delete from database
    try:
        found_ids = [content.id for content in content_items]
        deleted_count = (
            db.query(Content)
            .filter(and_(Content.id.in_(found_ids), Content.user_id == current_user.id))
            .delete(synchronize_session=False)
        )

        db.commit()
        results["db_deleted"] = deleted_count

        logger.info(
            f"User {current_user.id} bulk deleted {deleted_count} content items. "
            f"Files: {results['files_deleted']} deleted, {results['files_failed']} failed"
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to bulk delete content: {e}")
        raise HTTPException(status_code=500, detail="Failed to bulk delete content") from e

    return {
        "message": f"Successfully deleted {results['db_deleted']} content items",
        "details": results,
    }


@router.get("/{content_id}/download")
@limiter.limit("20/minute")
def download_content(
    request: Request,
    content_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Download a content file

    Returns the file for download with appropriate headers.
    """
    # Fetch content and verify ownership
    content = (
        db.query(Content)
        .filter(and_(Content.id == content_id, Content.user_id == current_user.id))
        .first()
    )

    if not content:
        raise ContentNotFoundError()

    if not content.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No file associated with this content"
        )

    # Generate presigned URL for R2 download (offloads bandwidth from container)
    url = r2.generate_presigned_url(content.file_path)
    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found in storage"
        )

    from fastapi.responses import RedirectResponse

    logger.info(f"User {current_user.id} downloading content {content_id}")

    return RedirectResponse(url=url)
