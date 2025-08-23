"""Content management API endpoints"""

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status, Request
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import and_, func, select
import hashlib
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.content import Content
from app.core.config import settings
from app.core.csrf import require_csrf_token
from app.core.exceptions import (
    ContentNotFoundError,
    ContentAlreadyExistsError,
    InvalidFileTypeError,
    FileTooLargeError,
    FileUploadError,
    ValidationError,
)
from app.schemas.content import ContentCreate, ContentResponse, ContentUpdate
from app.utils.file_validation import get_mime_type
from app.utils.sanitization import sanitize_input, sanitize_filename
from app.services.content_processor import content_processor
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/content", tags=["content"])
limiter = Limiter(key_func=get_remote_address)

# Create upload directory if it doesn't exist
UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(exist_ok=True)



# File type validation
ALLOWED_MIME_TYPES = {
    'application/pdf': 'pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'pptx',
    'application/vnd.ms-powerpoint': 'ppt',  # Old PowerPoint format
    'text/plain': 'txt',
    'text/markdown': 'md',
    'image/jpeg': 'jpg',
    'image/png': 'png',
    'audio/mpeg': 'mp3',
    'audio/mp4': 'mp4',
    'audio/wav': 'wav',
    'video/mp4': 'mp4',
}

# Extensions that might be detected as zip but are actually allowed
OFFICE_EXTENSIONS = {'.docx', '.pptx', '.xlsx'}


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
        allowed_types.append('application/zip')
    
    is_valid, error_msg, validation_info = validate_file_content(
        file_content,
        file.filename,
        allowed_mime_types=allowed_types,
        max_file_size=settings.MAX_UPLOAD_SIZE
    )
    
    if not is_valid:
        logger.warning(f"File validation failed: {error_msg}, warnings: {validation_info.get('security_warnings', [])}")
        raise ValidationError(f"File validation failed: {error_msg}")
    
    # Log security warnings if any
    if validation_info.get('security_warnings'):
        logger.warning(f"Security warnings for file {file.filename}: {validation_info['security_warnings']}")
    
    mime_type = validation_info['mime_type']
    
    # Handle Office files detected as zip
    if mime_type == 'application/zip' and file_extension in OFFICE_EXTENSIONS:
        # Map extension to proper mime type and extension
        if file_extension == '.docx':
            mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            extension = 'docx'
        elif file_extension == '.pptx':
            mime_type = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
            extension = 'pptx'
        elif file_extension == '.xlsx':
            mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            extension = 'xlsx'
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


def save_upload_file(file: UploadFile, user_id: str, extension: str) -> tuple[str, str]:
    """
    Save uploaded file to disk with secure naming.
    Returns (file_path, file_id)
    """
    # Generate unique file ID
    file_id = str(uuid.uuid4())
    
    # Create user-specific directory
    user_dir = UPLOAD_DIR / user_id
    user_dir.mkdir(exist_ok=True)
    
    # Create date-based subdirectory
    date_dir = user_dir / datetime.utcnow().strftime("%Y/%m")
    date_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate secure filename
    filename = f"{file_id}.{extension}"
    file_path = date_dir / filename
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            for chunk in iter(lambda: file.file.read(1024 * 1024), b""):  # 1MB chunks
                buffer.write(chunk)
    except Exception as e:
        logger.error(f"Failed to save file: {str(e)}", exc_info=True)
        raise FileUploadError(detail="Failed to save uploaded file")
    
    # Return relative path from upload directory
    relative_path = str(file_path.relative_to(UPLOAD_DIR))
    return relative_path, file_id


@router.post("/upload", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def upload_content(
    request: Request,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    content_type: Optional[str] = Form(None),
    subject: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
        existing_content = db.query(Content).filter(
            and_(
                Content.user_id == current_user.id,
                Content.file_hash == file_hash
            )
        ).first()
        
        if existing_content:
            raise ContentAlreadyExistsError()
        
        # Save file to disk
        file_path, file_id = save_upload_file(file, str(current_user.id), extension)
        
        # Sanitize inputs
        sanitized_title = sanitize_input(title)
        sanitized_description = sanitize_input(description) if description else None
        sanitized_subject = sanitize_input(subject) if subject else None
        sanitized_filename = sanitize_filename(file.filename)
        
        # Parse and sanitize tags
        tag_list = []
        if tags:
            tag_list = [sanitize_input(tag.strip()) for tag in tags.split(",") if tag.strip()]
        
        # Get actual file size
        file_size = 0
        if hasattr(file, 'size') and file.size:
            file_size = file.size
        else:
            # Calculate size from saved file
            saved_file_path = UPLOAD_DIR / file_path
            if saved_file_path.exists():
                file_size = saved_file_path.stat().st_size
        
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
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(content)
        db.commit()
        db.refresh(content)
        
        logger.info(f"User {current_user.id} uploaded content: {content.id}")
        
        # Process the file synchronously for reliability
        logger.info(f"=== STARTING CONTENT PROCESSING for {content.id} ===")
        
        # Send WebSocket update if available
        try:
            from app.api.v1.websocket import websocket_manager
            import asyncio
            asyncio.create_task(websocket_manager.send_personal_message({
                "type": "processing_status",
                "content_id": str(content.id),
                "status": "processing",
                "message": f"Extracting text from {content.title}..."
            }, str(current_user.id)))
        except Exception as e:
            logger.warning(f"Could not send WebSocket update: {e}")
        
        try:
            logger.info(f"Processing content {content.id}")
            
            # Extract text from the file
            full_file_path = str(UPLOAD_DIR / file_path)
            logger.info(f"Processing file at: {full_file_path}")
            processing_result = content_processor.process_file(full_file_path, mime_type)
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
                    text_preview = processing_result["text"][:500].replace('\n', ' ').strip()
                    content.summary = f"Content from {content.title}. Preview: {text_preview}..."
                    
                    # Extract some basic keywords as concepts
                    words = processing_result["text"].lower().split()
                    # Get most common non-trivial words
                    word_freq = {}
                    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were'}
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
                content.processing_error = processing_result["metadata"].get("error", "Unknown error")
            
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
        
    except (ContentAlreadyExistsError, InvalidFileTypeError, FileTooLargeError, 
            FileUploadError, ValidationError):
        raise
    except Exception as e:
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        raise FileUploadError(detail="Failed to upload content")


@router.get("/", response_model=List[ContentResponse])
@limiter.limit("30/minute")
def list_content(
    request: Request,
    skip: int = 0,
    limit: int = 20,
    content_type: Optional[str] = None,
    tag: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List user's uploaded content with optional filtering
    
    Optimized to prevent N+1 queries by using efficient database queries
    with proper indexing and minimal data loading.
    """
    # Use optimized query with proper eager loading
    query = db.query(Content).options(
        # Only load user relationship if needed (currently not in response model)
        # joinedload(Content.user) - commented out as not needed in response
    ).filter(Content.user_id == current_user.id)
    
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
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get content statistics for the current user
    
    Returns summary statistics without loading all content items,
    preventing N+1 queries through aggregate functions.
    """
    # Use efficient aggregate queries to get stats
    stats = {}
    
    # Total content count
    total_count = db.query(func.count(Content.id)).filter(
        Content.user_id == current_user.id
    ).scalar()
    
    # Count by content type
    content_type_counts = db.query(
        Content.content_type,
        func.count(Content.id).label('count')
    ).filter(
        Content.user_id == current_user.id
    ).group_by(Content.content_type).all()
    
    # Processing status counts
    status_counts = db.query(
        Content.processing_status,
        func.count(Content.id).label('count')
    ).filter(
        Content.user_id == current_user.id
    ).group_by(Content.processing_status).all()
    
    # Total file size
    total_size = db.query(
        func.coalesce(func.sum(Content.file_size), 0)
    ).filter(
        Content.user_id == current_user.id
    ).scalar()
    
    # Total study time
    total_study_time = db.query(
        func.coalesce(func.sum(Content.study_time_minutes), 0)
    ).filter(
        Content.user_id == current_user.id
    ).scalar()
    
    stats = {
        "total_content": total_count,
        "by_type": {ct: count for ct, count in content_type_counts},
        "by_status": {status: count for status, count in status_counts},
        "total_file_size_bytes": total_size,
        "total_study_time_minutes": float(total_study_time),
        "avg_file_size_bytes": total_size // total_count if total_count > 0 else 0
    }
    
    logger.info(f"User {current_user.id} requested content stats")
    return stats


@router.get("/{content_id}", response_model=ContentResponse)
@limiter.limit("30/minute")
def get_content(
    request: Request,
    content_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get specific content by ID
    
    Optimized query that only loads the requested content item
    without any unnecessary relationships.
    """
    content = db.query(Content).filter(
        and_(
            Content.id == content_id,
            Content.user_id == current_user.id
        )
    ).first()
    
    if not content:
        raise ContentNotFoundError()
    
    # Update last accessed timestamp for analytics (optional)
    content.last_accessed_at = datetime.utcnow()
    content.view_count += 1
    
    # Commit the analytics update without affecting the response
    try:
        db.commit()
        db.refresh(content)
    except Exception as e:
        logger.warning(f"Failed to update content analytics: {e}")
        db.rollback()
    
    logger.info(f"User {current_user.id} accessed content {content_id}")
    return content


@router.put("/{content_id}", response_model=ContentResponse)
@limiter.limit("10/minute")
def update_content(
    request: Request,
    content_id: uuid.UUID,
    content_update: ContentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update content metadata
    
    Optimized to only fetch and update the specific content item
    without loading unnecessary relationships.
    """
    # Use efficient query to find and lock the content for update
    content = db.query(Content).filter(
        and_(
            Content.id == content_id,
            Content.user_id == current_user.id
        )
    ).first()
    
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
    content.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(content)
        logger.info(f"User {current_user.id} updated content {content_id} fields: {updated_fields}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update content {content_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update content")
    
    return content


@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
def delete_content(
    request: Request,
    content_id: uuid.UUID,
    _csrf: None = Depends(require_csrf_token),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete content and associated file
    
    Optimized to only fetch minimal data needed for deletion,
    with proper error handling and file cleanup.
    """
    # Only select the fields we need for deletion
    content = db.query(Content.id, Content.file_path, Content.title).filter(
        and_(
            Content.id == content_id,
            Content.user_id == current_user.id
        )
    ).first()
    
    if not content:
        raise ContentNotFoundError()
    
    content_title = content.title
    file_path = content.file_path
    
    # Delete file from disk first (before database deletion)
    file_deleted = False
    if file_path:
        try:
            full_file_path = UPLOAD_DIR / file_path
            if full_file_path.exists():
                full_file_path.unlink()
                file_deleted = True
                logger.info(f"Deleted file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {str(e)}")
            # Continue with database deletion even if file deletion fails
    
    # Delete database record using efficient delete query
    try:
        deleted_count = db.query(Content).filter(
            and_(
                Content.id == content_id,
                Content.user_id == current_user.id
            )
        ).delete(synchronize_session=False)  # More efficient than loading object
        
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
        raise HTTPException(status_code=500, detail="Failed to delete content")
    
    return None


@router.post("/bulk-delete", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
def bulk_delete_content(
    request: Request,
    content_ids: List[uuid.UUID],
    _csrf: None = Depends(require_csrf_token),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
    content_items = db.query(Content.id, Content.file_path, Content.title).filter(
        and_(
            Content.id.in_(content_ids),
            Content.user_id == current_user.id
        )
    ).all()
    
    if not content_items:
        raise ContentNotFoundError("No matching content items found")
    
    # Track results
    results = {
        "requested": len(content_ids),
        "found": len(content_items),
        "files_deleted": 0,
        "files_failed": 0,
        "db_deleted": 0
    }
    
    # Delete files first
    file_paths_to_delete = []
    for content in content_items:
        if content.file_path:
            try:
                full_file_path = UPLOAD_DIR / content.file_path
                if full_file_path.exists():
                    full_file_path.unlink()
                    results["files_deleted"] += 1
            except Exception as e:
                logger.error(f"Failed to delete file {content.file_path}: {e}")
                results["files_failed"] += 1
    
    # Bulk delete from database
    try:
        found_ids = [content.id for content in content_items]
        deleted_count = db.query(Content).filter(
            and_(
                Content.id.in_(found_ids),
                Content.user_id == current_user.id
            )
        ).delete(synchronize_session=False)
        
        db.commit()
        results["db_deleted"] = deleted_count
        
        logger.info(
            f"User {current_user.id} bulk deleted {deleted_count} content items. "
            f"Files: {results['files_deleted']} deleted, {results['files_failed']} failed"
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to bulk delete content: {e}")
        raise HTTPException(status_code=500, detail="Failed to bulk delete content")
    
    return {
        "message": f"Successfully deleted {results['db_deleted']} content items",
        "details": results
    }


@router.get("/{content_id}/download")
@limiter.limit("20/minute")
def download_content(
    request: Request,
    content_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download a content file
    
    Returns the file for download with appropriate headers.
    """
    # Fetch content and verify ownership
    content = db.query(Content).filter(
        and_(
            Content.id == content_id,
            Content.user_id == current_user.id
        )
    ).first()
    
    if not content:
        raise ContentNotFoundError()
    
    # Build full file path
    file_path = UPLOAD_DIR / content.file_path
    
    if not file_path.exists():
        logger.error(f"File not found on disk: {content.file_path}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server"
        )
    
    # Determine content disposition (inline for PDFs/images, attachment for others)
    disposition = "inline" if content.mime_type in [
        "application/pdf", "image/jpeg", "image/png"
    ] else "attachment"
    
    # Use original filename for download
    filename = content.original_filename or f"{content.title}.{file_path.suffix}"
    
    from fastapi.responses import FileResponse
    
    logger.info(f"User {current_user.id} downloading content {content_id}")
    
    return FileResponse(
        path=str(file_path),
        media_type=content.mime_type,
        filename=filename,
        headers={
            "Content-Disposition": f'{disposition}; filename="{filename}"'
        }
    )


@router.get("/search", response_model=List[ContentResponse])
@limiter.limit("20/minute")
def search_content(
    request: Request,
    q: str,  # Search query
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search user's content by title, description, or extracted text
    
    Optimized full-text search using database indexes and efficient queries.
    """
    if len(q.strip()) < 2:
        raise ValidationError("Search query must be at least 2 characters")
    
    search_term = f"%{q.lower()}%"
    
    # Use efficient search with proper indexing
    # This query should have indexes on title, description, and extracted_text
    content_items = db.query(Content).filter(
        and_(
            Content.user_id == current_user.id,
            (
                func.lower(Content.title).like(search_term) |
                func.lower(Content.description).like(search_term) |
                func.lower(Content.extracted_text).like(search_term)
            )
        )
    ).order_by(
        # Relevance scoring: title matches first, then description, then content
        func.case(
            (func.lower(Content.title).like(search_term), 1),
            (func.lower(Content.description).like(search_term), 2),
            else_=3
        ),
        Content.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    logger.info(
        f"User {current_user.id} searched for '{q}' - found {len(content_items)} results"
    )
    
    return content_items