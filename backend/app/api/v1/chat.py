"""Chat endpoint for AI tutor interactions"""

import json
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.models.content import Content
from app.core.cache import redis_cache
from app.core.agent_manager import agent_manager
from app.services.claude_service import claude_service
from app.services.openai_fallback import openai_fallback
from app.services.ai_service_manager import ai_service_manager

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatMessage(BaseModel):
    """Single chat message"""
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str
    timestamp: Optional[datetime] = None
    metadata: Optional[dict] = None


class ChatRequest(BaseModel):
    """Chat request with message history"""
    messages: List[ChatMessage]
    content_ids: Optional[List[UUID]] = Field(
        default=None, 
        description="IDs of content to include in context"
    )
    stream: bool = Field(default=True, description="Stream the response")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1, le=4096)


class ChatResponse(BaseModel):
    """Chat response"""
    message: ChatMessage
    session_id: str
    usage: Optional[dict] = None


async def stream_chat_response(
    request: ChatRequest,
    user: User,
    db: Session
):
    """
    Stream chat response from AI tutor using available AI services.
    Yields Server-Sent Events (SSE) format.
    """
    try:
        logger.info(f"=== STREAMING CHAT DEBUG ===")
        logger.info(f"User: {user.username} (ID: {user.id})")
        logger.info(f"Request content_ids: {request.content_ids}")
        logger.info(f"Number of messages: {len(request.messages)}")
        
        # Prepare context with user's content if specified
        context_messages = []
        
        # Add system prompt
        system_prompt = """You are the AI Study Architect - a learning companion that builds cognitive strength, not cognitive debt.

Your core mission: Help students develop deep understanding and intellectual confidence through guided discovery.

FUNDAMENTAL APPROACH:

1. HONOR THE STRUGGLE
   - Confusion is not failure; it's the birthplace of insight
   - When they say "I don't know," respond: "That's a perfect starting point. What part feels unclear?"
   - Celebrate attempts, not just correct answers
   - Say: "You're wrestling with exactly the right questions"

2. BUILD CONFIDENCE, NOT DEPENDENCY
   - After they succeed: "You figured that out yourself - I just asked questions"
   - Point out their growing abilities: "Notice how you just connected those concepts?"
   - Gradually reduce scaffolding as they gain strength
   - Make them aware of their own thinking process

3. SOCRATIC METHOD WITH WARMTH
   Student: "What is recursion?"
   You: "I love that you're tackling recursion! Before we dive in - have you noticed any patterns in your uploaded materials where something refers back to itself? Maybe in the code examples or even in everyday life?"
   
   Student: "I'm completely lost"
   You: "Being lost means you're in new territory - that's where learning happens. Let's start with what feels familiar. What's the last thing that made sense to you?"
   
   Student: "Just tell me the answer!"
   You: "I hear your frustration - it's real and valid. Here's the thing: if I just tell you, it won't stick. But if we work through it together, you'll own this knowledge forever. Can we try one small step?"

4. REFERENCE THEIR ACTUAL MATERIALS
   - "Looking at page 5 of your PDF..."
   - "Your professor's slide about X shows..."
   - "In the example from your textbook..."
   - Connect new questions to their specific content

5. REVEAL THE LEARNING PROCESS
   - "Notice how you just used deductive reasoning?"
   - "You're building a mental model - that's exactly what experts do"
   - "That 'aha' moment you just had? That's your brain forming new connections"
   - Make metacognition visible and celebrated

6. HANDLE MISTAKES WITH GRACE
   - "That's a really logical assumption, and here's why it makes sense..."
   - "You're thinking in the right direction. What if we adjust..."
   - "Many students think that initially. Let's explore why..."
   - Never shame, always reframe as learning opportunity

7. PROGRESSIVE CHALLENGE
   - Start where they are, not where they "should" be
   - Each question slightly harder than the last
   - Say: "You're ready for something more challenging"
   - Celebrate when they surprise themselves

REMEMBER:
- You're building thinkers, not answer-seekers
- Every interaction should leave them stronger
- Confusion is temporary, understanding is permanent
- You're not their crutch, you're their training partner

TONE: Warm teacher who believes in them, not cold information dispenser. Use "we" and "let's" to signal partnership. Be the teacher everyone wishes they had - patient, insightful, genuinely excited about their growth.

NEVER:
- Give direct answers in first response
- Accept "I don't know" without gentle probing
- Let them leave without real understanding
- Make them feel stupid for not knowing
- Rush through confusion to get to answers"""
        
        context_messages.append({
            "role": "system",
            "content": system_prompt
        })
        
        # If content IDs are provided, fetch and include content
        if request.content_ids:
            logger.info(f"Fetching content for IDs: {request.content_ids}")
            contents = db.query(Content).filter(
                Content.id.in_(request.content_ids),
                Content.user_id == user.id
            ).all()
            
            logger.info(f"Found {len(contents)} content items")
            for c in contents:
                logger.info(f"  - {c.title}: status={c.processing_status}, has_text={bool(c.extracted_text)}, text_len={len(c.extracted_text) if c.extracted_text else 0}")
            
            if contents:
                content_context = "The student has uploaded the following materials:\n\n"
                
                for content in contents:
                    content_context += f"- {content.title} ({content.content_type})"
                    if content.description:
                        content_context += f": {content.description}"
                    content_context += "\n"
                    
                    # Include extracted text - increased limit to prevent content loss
                    if content.extracted_text:
                        content_context += f"\nContent from '{content.title}':\n"
                        
                        # Send full content up to 50K chars to prevent dropping slides
                        # Previous 15K limit was causing slides 28-37 to be lost
                        if len(content.extracted_text) <= 50000:
                            content_context += content.extracted_text
                        else:
                            # For very large documents (>50K), use smarter chunking
                            text_len = len(content.extracted_text)
                            chunk_size = 16000  # Larger chunks to preserve more content
                            
                            # Beginning section
                            content_context += content.extracted_text[:chunk_size]
                            content_context += "\n\n[... some content omitted for length ...]\n\n"
                            
                            # End section (important for conclusions/later slides)
                            content_context += content.extracted_text[-chunk_size:]
                            content_context += f"\n\n[Note: Document contains {text_len} characters. Showing first and last {chunk_size} characters.]"
                        
                        content_context += "\n\n"
                    
                    # Include AI summary if available
                    if content.summary:
                        content_context += f"Summary: {content.summary}\n"
                    
                    # Include key concepts if available
                    if content.key_concepts:
                        content_context += f"Key concepts: {', '.join(content.key_concepts)}\n"
                    
                    content_context += "\n"
                
                context_messages.append({
                    "role": "system", 
                    "content": content_context + "\nUse this content to answer the student's questions. Be specific and reference the materials when appropriate."
                })
                
                logger.info(f"Added content context. Total length: {len(content_context)} chars")
                logger.info(f"First 500 chars of context: {content_context[:500]}...")
        
        # Add conversation history
        for msg in request.messages:
            context_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Start streaming response
        session_id = str(uuid4())
        logger.info(f"Starting AI chat session {session_id} for user {user.id}")
        logger.info(f"Total messages being sent to AI service: {len(context_messages)}")
        for i, msg in enumerate(context_messages):
            logger.info(f"  Message {i}: role={msg['role']}, content_length={len(msg['content'])}, preview={msg['content'][:100]}...")
        
        # Yield initial connection event
        yield f"data: {json.dumps({'type': 'connection', 'session_id': session_id})}\n\n"
        
        # Get response from best available AI service
        full_response = ""
        token_count = 0
        
        # Get streaming response from best available service
        service_name, service = await ai_service_manager.get_available_service()
        
        if not service:
            # No services available - likely missing API keys
            logger.error("No AI services available - check API keys configuration")
            error_response = "⚠️ AI services are not configured. Please ensure ANTHROPIC_API_KEY or OPENAI_API_KEY environment variables are set in production."
            for i, char in enumerate(error_response):
                chunk_data = {
                    "type": "content",
                    "content": char,
                    "index": i
                }
                yield f"data: {json.dumps(chunk_data)}\n\n"
            full_response = error_response
        elif request.stream:
            # ALL services now support streaming
            if False:  # Removed Ollama support
                # Legacy code removed
                async with service as svc:
                    response_stream = await svc.chat_completion(
                        messages=context_messages,
                        temperature=request.temperature,
                        max_tokens=request.max_tokens,
                        stream=True
                    )
                
                index = 0
                async for chunk in response_stream:
                    try:
                        # Parse the JSON response from AI service
                        chunk_data = json.loads(chunk)
                        
                        if "response" in chunk_data:
                            content = chunk_data["response"]
                            full_response += content
                            
                            # Send each character as a separate event
                            for char in content:
                                yield f"data: {json.dumps({'type': 'content', 'content': char, 'index': index})}\n\n"
                                index += 1
                                token_count += 1
                        
                        # Check if this is the final chunk
                        if chunk_data.get("done", False):
                            # Extract context for future conversations
                            if "context" in chunk_data:
                                # Store context in cache for conversation continuity
                                context_key = f"chat:context:{user.id}"
                                redis_cache.set(context_key, chunk_data["context"], 3600)
                            
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse AI service chunk: {chunk}")
                        continue
            else:
                # Claude and OpenAI also support streaming now!
                response_stream = await service.chat_completion(
                    messages=context_messages,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    stream=True
                )
                
                index = 0
                async for chunk in response_stream:
                    try:
                        # Parse the JSON response (same format for all services now)
                        chunk_data = json.loads(chunk)
                        
                        if "response" in chunk_data:
                            content = chunk_data["response"]
                            full_response += content
                            
                            # Send each character as a separate event
                            for char in content:
                                yield f"data: {json.dumps({'type': 'content', 'content': char, 'index': index})}\n\n"
                                index += 1
                                token_count += 1
                        
                        # Check if this is the final chunk
                        if chunk_data.get("done", False):
                            break
                            
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse {service_name} chunk: {chunk}")
                        continue
        else:
            # Non-streaming mode - get complete response and send it all at once
            response_data = await ai_service_manager.chat_completion(
                messages=context_messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=False
            )
            
            if "error" in response_data:
                logger.error(f"AI service error: {response_data.get('error')}")
                full_response = response_data.get("response", "Failed to get AI response. Please check API keys configuration.")
                # If the response is about missing API keys, make it clearer
                if "API key" in str(response_data.get("error", "")):
                    full_response = "⚠️ AI service API keys are not configured. Please set ANTHROPIC_API_KEY or OPENAI_API_KEY in the production environment."
            else:
                full_response = response_data.get("response", "")
                # Check for empty response
                if not full_response:
                    logger.warning("AI service returned empty response")
                    full_response = "⚠️ The AI service returned an empty response. This usually means the API keys are not properly configured."
            
            # Send the COMPLETE response in one chunk (no fake streaming!)
            chunk_data = {
                "type": "content",
                "content": full_response,
                "index": 0
            }
            yield f"data: {json.dumps(chunk_data)}\n\n"
            token_count = len(full_response.split())
        
        # Yield completion event
        complete_data = {
            "type": "complete",
            "message": {
                "role": "assistant",
                "content": full_response,
                "timestamp": datetime.utcnow().isoformat()
            },
            "usage": {
                "prompt_tokens": sum(len(m.content.split()) for m in request.messages),
                "completion_tokens": len(full_response.split()),
                "total_tokens": sum(len(m.content.split()) for m in request.messages) + len(full_response.split())
            }
        }
        yield f"data: {json.dumps(complete_data)}\n\n"
        
        # Cache the conversation
        cache_key = f"chat:session:{session_id}"
        conversation = {
            "user_id": str(user.id),
            "messages": [m.model_dump() for m in request.messages] + [complete_data["message"]],
            "created_at": datetime.utcnow().isoformat()
        }
        redis_cache.set(cache_key, conversation, 3600)  # 1 hour cache
        
        logger.info(f"Completed AI chat session {session_id}")
        
    except Exception as e:
        logger.error(f"Error in chat stream: {str(e)}", exc_info=True)
        error_data = {
            "type": "error",
            "error": "An error occurred while processing your request"
        }
        yield f"data: {json.dumps(error_data)}\n\n"


@router.post("/", response_model=ChatResponse)
async def create_chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a chat interaction with the AI tutor.
    
    Supports both streaming and non-streaming responses.
    For streaming, returns Server-Sent Events (SSE).
    
    Requires authentication via JWT token in Authorization header.
    """
    # Log authentication success
    logger.info(f"Chat request from authenticated user: {current_user.username} (ID: {current_user.id})")
    
    if request.stream:
        return StreamingResponse(
            stream_chat_response(request, current_user, db),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
    else:
        # Non-streaming response
        session_id = str(uuid4())
        
        # Prepare messages for AI service
        context_messages = [{
            "role": "system",
            "content": """You are the AI Study Architect - a learning companion that builds cognitive strength, not cognitive debt.

Your core mission: Help students develop deep understanding and intellectual confidence through guided discovery.

FUNDAMENTAL APPROACH:

1. HONOR THE STRUGGLE
   - Confusion is not failure; it's the birthplace of insight
   - When they say "I don't know," respond: "That's a perfect starting point. What part feels unclear?"
   - Celebrate attempts, not just correct answers
   - Say: "You're wrestling with exactly the right questions"

2. BUILD CONFIDENCE, NOT DEPENDENCY
   - After they succeed: "You figured that out yourself - I just asked questions"
   - Point out their growing abilities: "Notice how you just connected those concepts?"
   - Gradually reduce scaffolding as they gain strength
   - Make them aware of their own thinking process

3. SOCRATIC METHOD WITH WARMTH
   Student: "What is recursion?"
   You: "I love that you're tackling recursion! Before we dive in - have you noticed any patterns in your uploaded materials where something refers back to itself? Maybe in the code examples or even in everyday life?"
   
   Student: "I'm completely lost"
   You: "Being lost means you're in new territory - that's where learning happens. Let's start with what feels familiar. What's the last thing that made sense to you?"
   
   Student: "Just tell me the answer!"
   You: "I hear your frustration - it's real and valid. Here's the thing: if I just tell you, it won't stick. But if we work through it together, you'll own this knowledge forever. Can we try one small step?"

4. REFERENCE THEIR ACTUAL MATERIALS
   - "Looking at page 5 of your PDF..."
   - "Your professor's slide about X shows..."
   - "In the example from your textbook..."
   - Connect new questions to their specific content

5. REVEAL THE LEARNING PROCESS
   - "Notice how you just used deductive reasoning?"
   - "You're building a mental model - that's exactly what experts do"
   - "That 'aha' moment you just had? That's your brain forming new connections"
   - Make metacognition visible and celebrated

6. HANDLE MISTAKES WITH GRACE
   - "That's a really logical assumption, and here's why it makes sense..."
   - "You're thinking in the right direction. What if we adjust..."
   - "Many students think that initially. Let's explore why..."
   - Never shame, always reframe as learning opportunity

7. PROGRESSIVE CHALLENGE
   - Start where they are, not where they "should" be
   - Each question slightly harder than the last
   - Say: "You're ready for something more challenging"
   - Celebrate when they surprise themselves

REMEMBER:
- You're building thinkers, not answer-seekers
- Every interaction should leave them stronger
- Confusion is temporary, understanding is permanent
- You're not their crutch, you're their training partner

TONE: Warm teacher who believes in them, not cold information dispenser. Use "we" and "let's" to signal partnership. Be the teacher everyone wishes they had - patient, insightful, genuinely excited about their growth.

NEVER:
- Give direct answers in first response
- Accept "I don't know" without gentle probing
- Let them leave without real understanding
- Make them feel stupid for not knowing
- Rush through confusion to get to answers"""
        }]
        
        # If content IDs are provided, fetch and include content
        if request.content_ids:
            logger.info(f"Chat request includes content_ids: {request.content_ids}")
            contents = db.query(Content).filter(
                Content.id.in_(request.content_ids),
                Content.user_id == current_user.id
            ).all()
            
            logger.info(f"Found {len(contents)} content items for user {current_user.id}")
            
            if contents:
                content_context = "The student has uploaded the following materials:\n\n"
                
                for content in contents:
                    content_context += f"- {content.title} ({content.content_type})"
                    if content.description:
                        content_context += f": {content.description}"
                    content_context += "\n"
                    
                    # Include extracted text - increased limit to prevent content loss
                    if content.extracted_text:
                        content_context += f"\nContent from '{content.title}':\n"
                        
                        # Send full content up to 50K chars to prevent dropping slides
                        # Previous 15K limit was causing slides 28-37 to be lost
                        if len(content.extracted_text) <= 50000:
                            content_context += content.extracted_text
                        else:
                            # For very large documents (>50K), use smarter chunking
                            text_len = len(content.extracted_text)
                            chunk_size = 16000  # Larger chunks to preserve more content
                            
                            # Beginning section
                            content_context += content.extracted_text[:chunk_size]
                            content_context += "\n\n[... some content omitted for length ...]\n\n"
                            
                            # End section (important for conclusions/later slides)
                            content_context += content.extracted_text[-chunk_size:]
                            content_context += f"\n\n[Note: Document contains {text_len} characters. Showing first and last {chunk_size} characters.]"
                        
                        content_context += "\n\n"
                    
                    # Include AI summary if available
                    if content.summary:
                        content_context += f"Summary: {content.summary}\n"
                    
                    # Include key concepts if available
                    if content.key_concepts:
                        content_context += f"Key concepts: {', '.join(content.key_concepts)}\n"
                    
                    content_context += "\n"
                
                context_messages.append({
                    "role": "system", 
                    "content": content_context + "\nUse this content to answer the student's questions. Be specific and reference the materials when appropriate."
                })
                logger.info(f"Added content context to messages. Total context length: {len(content_context)} chars")
        
        # Add user messages
        for msg in request.messages:
            context_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Get response from best available AI service
        logger.info(f"Sending {len(context_messages)} messages to AI service")
        for i, msg in enumerate(context_messages):
            logger.debug(f"Message {i}: role={msg['role']}, content_length={len(msg['content'])}")
        
        # Use AI service manager to get response from best available service
        response_data = await ai_service_manager.chat_completion(
            messages=context_messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=False
        )
        
        if "error" in response_data:
            response_text = response_data.get("response", "Failed to get AI response")
            logger.error(f"AI service error: {response_data.get('error')}")
        else:
            response_text = response_data.get("response", "I couldn't generate a response.")
        
        message = ChatMessage(
            role="assistant",
            content=response_text,
            timestamp=datetime.utcnow()
        )
        
        # Cache the conversation
        cache_key = f"chat:session:{session_id}"
        conversation = {
            "user_id": str(current_user.id),
            "messages": [m.model_dump() for m in request.messages] + [message.model_dump()],
            "created_at": datetime.utcnow().isoformat()
        }
        redis_cache.set(cache_key, conversation, 3600)  # 1 hour cache
        
        return ChatResponse(
            message=message,
            session_id=session_id,
            usage={
                "prompt_tokens": sum(len(m.content.split()) for m in request.messages),
                "completion_tokens": len(response_text.split()),
                "total_tokens": sum(len(m.content.split()) for m in request.messages) + len(response_text.split())
            }
        )


@router.get("/history")
async def get_chat_history(
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user's chat history.
    
    TODO: Implement persistent chat history storage in database.
    For now, returns empty list.
    """
    return {
        "history": [],
        "total": 0
    }


@router.get("/session/{session_id}")
async def get_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific chat session by ID.
    """
    # Try to get from cache
    cache_key = f"chat:session:{session_id}"
    session_data = redis_cache.get(cache_key)
    
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Verify user owns this session
    if session_data.get("user_id") != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return session_data


class QARequest(BaseModel):
    """Q&A request about specific content"""
    question: str = Field(..., min_length=1, max_length=1000)
    content_ids: List[UUID] = Field(..., min_items=1, max_items=10)
    include_summary: bool = Field(default=True, description="Include content summaries in context")
    include_full_text: bool = Field(default=False, description="Include full extracted text")
    max_context_chars: int = Field(default=3000, ge=500, le=10000)


class QAResponse(BaseModel):
    """Q&A response"""
    answer: str
    confidence: float = Field(ge=0.0, le=1.0)
    referenced_content: List[Dict[str, Any]]
    suggestions: Optional[List[str]] = None


@router.post("/qa", response_model=QAResponse)
async def answer_content_question(
    request: QARequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Answer questions about specific uploaded content.
    
    This endpoint provides Q&A functionality for uploaded materials,
    allowing students to ask questions about their study content.
    """
    # Fetch the requested content
    contents = db.query(Content).filter(
        Content.id.in_(request.content_ids),
        Content.user_id == current_user.id,
        Content.processing_status == "completed"  # Only use processed content
    ).all()
    
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No processed content found with the provided IDs"
        )
    
    # Build context from content
    context_parts = []
    referenced_content = []
    total_chars = 0
    
    for content in contents:
        # Track referenced content
        ref_info = {
            "id": str(content.id),
            "title": content.title,
            "type": content.content_type
        }
        
        # Add summary if requested and available
        if request.include_summary and content.summary:
            context_parts.append(f"Summary of '{content.title}': {content.summary}")
            total_chars += len(content.summary)
        
        # Add extracted text
        if content.extracted_text:
            available_chars = request.max_context_chars - total_chars
            if available_chars > 500:  # Minimum useful context
                if request.include_full_text:
                    text_to_add = content.extracted_text[:available_chars]
                else:
                    # Use first portion of text
                    text_to_add = content.extracted_text[:min(10000, available_chars)]
                
                context_parts.append(f"\nContent from '{content.title}':\n{text_to_add}")
                total_chars += len(text_to_add)
                ref_info["chars_used"] = len(text_to_add)
        
        # Add key concepts
        if content.key_concepts:
            ref_info["key_concepts"] = content.key_concepts
        
        referenced_content.append(ref_info)
    
    # Prepare messages for Ollama
    messages = [
        {
            "role": "system",
            "content": """You are an AI tutor helping a student understand their study materials. 
Answer their questions based on the provided content. Be specific, accurate, and helpful.
If the content doesn't contain enough information to fully answer the question, 
acknowledge this and provide what information you can."""
        },
        {
            "role": "system",
            "content": "Study materials context:\n\n" + "\n\n".join(context_parts)
        },
        {
            "role": "user",
            "content": request.question
        }
    ]
    
    # Get answer from best available AI service
    response = await ai_service_manager.chat_completion(
        messages=messages,
        temperature=0.3,  # Lower temperature for more factual answers
        stream=False
    )
    
    if "error" in response:
        # Try to provide a helpful error message
        error_detail = response.get("error", "Unknown error")
        if "not configured" in error_detail.lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service is not properly configured. Please contact support."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate answer: {error_detail}"
            )
    
    answer = response.get("response", "I couldn't generate an answer.")
    
    # Calculate confidence based on content coverage
    confidence = min(0.95, len(contents) * 0.3 + (total_chars / request.max_context_chars) * 0.4)
    
    # Generate follow-up suggestions
    suggestions = [
        "Can you explain this concept in simpler terms?",
        "Can you provide an example?",
        "How does this relate to other topics in the material?"
    ]
    
    return QAResponse(
        answer=answer,
        confidence=confidence,
        referenced_content=referenced_content,
        suggestions=suggestions
    )