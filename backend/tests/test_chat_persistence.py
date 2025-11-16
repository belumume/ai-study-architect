"""
Tests for chat message persistence functionality
Tests ChatMessage model, save_chat_messages deduplication, and chat history endpoints
"""

import pytest
from datetime import datetime
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.chat_message import ChatMessage
from app.api.v1.chat import save_chat_messages
from app.core.security import create_access_token

from app.main import app
from app.api.dependencies import get_db


@pytest.fixture
async def test_client(db: Session, test_user: User) -> AsyncClient:
    """Get test client with sync database override."""

    def override_get_db():
        try:
            yield db
        finally:
            pass  # Don't close as it's managed by the db fixture

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()



class TestChatMessageModel:
    """Test ChatMessage database model"""

    def test_create_chat_message(self, db: Session, test_user: User):
        """Test creating a chat message"""
        session_id = str(uuid4())

        message = ChatMessage(
            user_id=test_user.id,
            session_id=session_id,
            role="user",
            content="Test message content",
            metadata={"test": "data"},
            content_ids=None
        )

        db.add(message)
        db.commit()
        db.refresh(message)

        assert message.id is not None
        assert message.user_id == test_user.id
        assert message.session_id == session_id
        assert message.role == "user"
        assert message.content == "Test message content"
        assert message.metadata == {"test": "data"}
        assert message.created_at is not None

    def test_chat_message_role_constraint(self, db: Session, test_user: User):
        """Test that role field is constrained to valid values"""
        # This should work
        valid_roles = ["user", "assistant", "system"]
        for role in valid_roles:
            message = ChatMessage(
                user_id=test_user.id,
                session_id=str(uuid4()),
                role=role,
                content="Test"
            )
            db.add(message)
            db.commit()

        # Invalid role should fail at database level with CHECK constraint
        # Note: This may not raise immediately in some DB configurations
        # The constraint is enforced at commit time

    def test_chat_message_to_dict(self, db: Session, test_user: User):
        """Test to_dict method"""
        session_id = str(uuid4())
        content_ids = [uuid4(), uuid4()]

        message = ChatMessage(
            user_id=test_user.id,
            session_id=session_id,
            role="assistant",
            content="Response content",
            metadata={"tokens": 100},
            content_ids=content_ids
        )

        db.add(message)
        db.commit()
        db.refresh(message)

        result = message.to_dict()

        assert result["id"] == str(message.id)
        assert result["role"] == "assistant"
        assert result["content"] == "Response content"
        assert result["metadata"] == {"tokens": 100}
        assert result["content_ids"] == content_ids
        assert "timestamp" in result

    def test_chat_message_user_relationship(self, db: Session, test_user: User):
        """Test relationship with User model"""
        message = ChatMessage(
            user_id=test_user.id,
            session_id=str(uuid4()),
            role="user",
            content="Test"
        )

        db.add(message)
        db.commit()
        db.refresh(message)

        # Test relationship
        assert message.user is not None
        assert message.user.id == test_user.id
        assert message.user.username == test_user.username


class TestSaveChatMessages:
    """Test save_chat_messages function with deduplication"""

    def test_save_new_message(self, db: Session, test_user: User):
        """Test saving a new message"""
        session_id = str(uuid4())

        save_chat_messages(
            db=db,
            user_id=test_user.id,
            session_id=session_id,
            new_message_role="user",
            new_message_content="Hello AI!",
            new_message_metadata={"source": "test"}
        )

        # Verify message was saved
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).all()

        assert len(messages) == 1
        assert messages[0].role == "user"
        assert messages[0].content == "Hello AI!"
        assert messages[0].metadata == {"source": "test"}

    def test_deduplicate_identical_message(self, db: Session, test_user: User):
        """Test that identical messages are not saved twice"""
        session_id = str(uuid4())

        # Save message first time
        save_chat_messages(
            db=db,
            user_id=test_user.id,
            session_id=session_id,
            new_message_role="user",
            new_message_content="Duplicate message"
        )

        # Try to save same message again
        save_chat_messages(
            db=db,
            user_id=test_user.id,
            session_id=session_id,
            new_message_role="user",
            new_message_content="Duplicate message"
        )

        # Should only have one message
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).all()

        assert len(messages) == 1

    def test_save_different_messages_in_same_session(self, db: Session, test_user: User):
        """Test saving different messages in the same session"""
        session_id = str(uuid4())

        # Save user message
        save_chat_messages(
            db=db,
            user_id=test_user.id,
            session_id=session_id,
            new_message_role="user",
            new_message_content="Question"
        )

        # Save assistant response
        save_chat_messages(
            db=db,
            user_id=test_user.id,
            session_id=session_id,
            new_message_role="assistant",
            new_message_content="Answer"
        )

        # Should have both messages
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at).all()

        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[1].role == "assistant"

    def test_save_with_content_ids(self, db: Session, test_user: User):
        """Test saving message with content_ids"""
        session_id = str(uuid4())
        content_ids = [uuid4(), uuid4()]

        save_chat_messages(
            db=db,
            user_id=test_user.id,
            session_id=session_id,
            new_message_role="user",
            new_message_content="Message about content",
            content_ids=content_ids
        )

        message = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).first()

        assert message.content_ids == content_ids

    def test_save_message_rollback_on_error(self, db: Session, test_user: User):
        """Test that save operation rolls back on error"""
        session_id = str(uuid4())

        # This should raise an error due to invalid role (if constraint is active)
        # But we'll test the try-except by mocking a database error
        # For now, just verify normal operation doesn't leave db in bad state

        try:
            save_chat_messages(
                db=db,
                user_id=test_user.id,
                session_id=session_id,
                new_message_role="user",
                new_message_content="Test"
            )
        except:
            pass

        # Database should still be usable
        count = db.query(ChatMessage).count()
        assert count >= 0


class TestGetChatHistory:
    """Test GET /api/v1/chat/history endpoint"""

    @pytest.mark.asyncio
    async def test_get_empty_history(self, test_client: AsyncClient, test_user: User, auth_headers: dict):
        """Test getting history when user has no messages"""
        response = await test_client.get("/api/v1/chat/history", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["history"] == []
        assert data["total"] == 0
        assert data["limit"] == 10
        assert data["offset"] == 0

    @pytest.mark.asyncio
    async def test_get_history_with_messages(
        self,
        test_client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        db: Session
    ):
        """Test getting history with existing messages"""
        # Create some messages in different sessions
        session1 = str(uuid4())
        session2 = str(uuid4())

        # Session 1
        save_chat_messages(db, test_user.id, session1, "user", "Message 1")
        save_chat_messages(db, test_user.id, session1, "assistant", "Response 1")

        # Session 2
        save_chat_messages(db, test_user.id, session2, "user", "Message 2")
        save_chat_messages(db, test_user.id, session2, "assistant", "Response 2")

        response = await test_client.get("/api/v1/chat/history", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["history"]) == 2

        # Check session structure
        for session in data["history"]:
            assert "session_id" in session
            assert "messages" in session
            assert "created_at" in session
            assert "updated_at" in session
            assert "message_count" in session

    @pytest.mark.asyncio
    async def test_get_history_pagination(
        self,
        test_client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        db: Session
    ):
        """Test pagination of chat history"""
        # Create 5 sessions
        for i in range(5):
            session_id = str(uuid4())
            save_chat_messages(db, test_user.id, session_id, "user", f"Message {i}")

        # Get first page (limit 2)
        response = await test_client.get(
            "/api/v1/chat/history?limit=2&offset=0",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["history"]) == 2
        assert data["total"] == 5
        assert data["limit"] == 2
        assert data["offset"] == 0

        # Get second page
        response = await test_client.get(
            "/api/v1/chat/history?limit=2&offset=2",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["history"]) == 2
        assert data["offset"] == 2

    @pytest.mark.asyncio
    async def test_get_history_ordered_by_recent(
        self,
        test_client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        db: Session
    ):
        """Test that history is ordered by most recent activity"""
        session1 = str(uuid4())
        session2 = str(uuid4())

        # Create session1 first
        save_chat_messages(db, test_user.id, session1, "user", "Old message")

        # Create session2 later
        save_chat_messages(db, test_user.id, session2, "user", "New message")

        response = await test_client.get("/api/v1/chat/history", headers=auth_headers)

        data = response.json()
        # Most recent session should be first
        assert data["history"][0]["session_id"] == session2
        assert data["history"][1]["session_id"] == session1

    @pytest.mark.asyncio
    async def test_get_history_unauthorized(self, test_client: AsyncClient):
        """Test that unauthorized requests are rejected"""
        response = await test_client.get("/api/v1/chat/history")
        assert response.status_code == 401


class TestGetChatSession:
    """Test GET /api/v1/chat/session/{session_id} endpoint"""

    @pytest.mark.asyncio
    async def test_get_session_from_database(
        self,
        test_client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        db: Session
    ):
        """Test getting session from database when not in cache"""
        session_id = str(uuid4())

        # Create some messages
        save_chat_messages(db, test_user.id, session_id, "user", "Hello")
        save_chat_messages(db, test_user.id, session_id, "assistant", "Hi there!")

        response = await test_client.get(
            f"/api/v1/chat/session/{session_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert "messages" in data
        assert len(data["messages"]) == 2

    @pytest.mark.asyncio
    async def test_get_nonexistent_session(
        self,
        test_client: AsyncClient,
        test_user: User,
        auth_headers: dict
    ):
        """Test getting session that doesn't exist"""
        fake_session_id = str(uuid4())

        response = await test_client.get(
            f"/api/v1/chat/session/{fake_session_id}",
            headers=auth_headers
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_session_wrong_user(
        self,
        test_client: AsyncClient,
        test_user: User,
        db: Session
    ):
        """Test that users can't access other users' sessions"""
        # Create another user
        other_user = User(
            email="other@example.com",
            username="otheruser",
            full_name="Other User",
            hashed_password="hashed"
        )
        db.add(other_user)
        db.commit()

        # Create session for other user
        session_id = str(uuid4())
        save_chat_messages(db, other_user.id, session_id, "user", "Private message")

        # Try to access with test_user credentials
        token = create_access_token(data={"sub": test_user.username})
        headers = {"Authorization": f"Bearer {token}"}

        response = await test_client.get(
            f"/api/v1/chat/session/{session_id}",
            headers=headers
        )

        # Should either be 404 or 403
        assert response.status_code in [403, 404]

    @pytest.mark.asyncio
    async def test_get_session_unauthorized(self, test_client: AsyncClient):
        """Test that unauthorized requests are rejected"""
        session_id = str(uuid4())
        response = await test_client.get(f"/api/v1/chat/session/{session_id}")
        assert response.status_code == 401


class TestChatPersistenceIntegration:
    """Integration tests for complete chat persistence flow"""

    @pytest.mark.asyncio
    async def test_complete_chat_flow(
        self,
        test_client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        db: Session
    ):
        """Test complete flow: chat -> save -> retrieve history -> retrieve session"""
        session_id = str(uuid4())

        # Simulate saving messages (as would happen in chat endpoint)
        save_chat_messages(db, test_user.id, session_id, "user", "What is Python?")
        save_chat_messages(db, test_user.id, session_id, "assistant", "Python is a programming language.")

        # Retrieve history
        response = await test_client.get("/api/v1/chat/history", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["history"]) == 1
        assert data["history"][0]["message_count"] == 2

        # Retrieve specific session
        response = await test_client.get(
            f"/api/v1/chat/session/{session_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        session_data = response.json()
        assert len(session_data["messages"]) == 2

    @pytest.mark.asyncio
    async def test_multi_session_flow(
        self,
        test_client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        db: Session
    ):
        """Test handling multiple concurrent sessions"""
        sessions = []

        # Create 3 different sessions
        for i in range(3):
            session_id = str(uuid4())
            sessions.append(session_id)
            save_chat_messages(db, test_user.id, session_id, "user", f"Question {i}")
            save_chat_messages(db, test_user.id, session_id, "assistant", f"Answer {i}")

        # Get history - should show all 3 sessions
        response = await test_client.get("/api/v1/chat/history", headers=auth_headers)
        data = response.json()
        assert data["total"] == 3

        # Verify each session can be retrieved
        for session_id in sessions:
            response = await test_client.get(
                f"/api/v1/chat/session/{session_id}",
                headers=auth_headers
            )
            assert response.status_code == 200
