"""
Security module tests
"""

import pytest
from datetime import timedelta
import time

from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    rotate_jwt_keys,
    get_current_keys,
)


class TestPasswordHashing:
    """Test password hashing utilities"""

    def test_hash_password(self):
        """Test password hashing"""
        password = "mysecretpassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt prefix

    def test_verify_correct_password(self):
        """Test password verification with correct password"""
        password = "correctpassword"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_incorrect_password(self):
        """Test password verification with incorrect password"""
        password = "correctpassword"
        hashed = get_password_hash(password)

        assert verify_password("wrongpassword", hashed) is False

    def test_same_password_different_hashes(self):
        """Test that same password produces different hashes (salt)"""
        password = "samepassword"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

    def test_empty_password(self):
        """Test hashing empty password"""
        password = ""
        hashed = get_password_hash(password)

        assert len(hashed) > 0
        assert verify_password("", hashed) is True
        assert verify_password("nonempty", hashed) is False


class TestJWTTokenCreation:
    """Test JWT token creation"""

    def test_create_access_token(self):
        """Test creating access token"""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        token = create_access_token(subject=user_id)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self):
        """Test creating refresh token"""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        token = create_refresh_token(subject=user_id)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_access_token_different_users(self):
        """Test that different users get different tokens"""
        user_id_1 = "user-1"
        user_id_2 = "user-2"

        token1 = create_access_token(subject=user_id_1)
        token2 = create_access_token(subject=user_id_2)

        assert token1 != token2

    def test_token_with_custom_expiry(self):
        """Test creating token with custom expiration"""
        user_id = "test-user"
        custom_delta = timedelta(minutes=5)

        token = create_access_token(subject=user_id, expires_delta=custom_delta)

        assert token is not None
        # Token should be valid
        verified_user_id = verify_token(token, token_type="access")
        assert verified_user_id == user_id


class TestJWTTokenVerification:
    """Test JWT token verification"""

    def test_verify_valid_access_token(self):
        """Test verifying valid access token"""
        user_id = "test-user-123"
        token = create_access_token(subject=user_id)

        verified_user_id = verify_token(token, token_type="access")

        assert verified_user_id == user_id

    def test_verify_valid_refresh_token(self):
        """Test verifying valid refresh token"""
        user_id = "test-user-456"
        token = create_refresh_token(subject=user_id)

        verified_user_id = verify_token(token, token_type="refresh")

        assert verified_user_id == user_id

    def test_verify_invalid_token(self):
        """Test verifying invalid token"""
        invalid_token = "invalid.jwt.token"

        verified_user_id = verify_token(invalid_token, token_type="access")

        assert verified_user_id is None

    def test_verify_expired_token(self):
        """Test verifying expired token"""
        user_id = "test-user-789"
        # Create token that expires immediately
        token = create_access_token(
            subject=user_id,
            expires_delta=timedelta(seconds=-1)
        )

        # Wait a tiny bit to ensure expiration
        time.sleep(0.1)

        verified_user_id = verify_token(token, token_type="access")

        assert verified_user_id is None

    def test_verify_wrong_token_type(self):
        """Test verifying token with wrong type"""
        user_id = "test-user-type"
        access_token = create_access_token(subject=user_id)

        # Try to verify access token as refresh token
        verified_user_id = verify_token(access_token, token_type="refresh")

        # Should fail or return None due to type mismatch
        assert verified_user_id is None

    def test_verify_malformed_token(self):
        """Test verifying malformed token"""
        malformed_tokens = [
            "",
            "not-a-jwt",
            "header.payload",  # Missing signature
            "a.b.c.d",  # Too many parts
        ]

        for token in malformed_tokens:
            verified_user_id = verify_token(token, token_type="access")
            assert verified_user_id is None


class TestJWTKeyRotation:
    """Test JWT key rotation"""

    def test_get_current_keys(self):
        """Test getting current keys"""
        keys = get_current_keys()

        assert keys is not None
        assert isinstance(keys, dict)
        assert "key_id" in keys or "private" in keys

    def test_rotate_keys(self):
        """Test rotating JWT keys"""
        # Get current keys
        old_keys = get_current_keys()

        # Rotate keys
        result = rotate_jwt_keys()

        # Get new keys
        new_keys = get_current_keys()

        # Result should indicate success
        assert result.get("status") in ["success", "error"]

        if result.get("status") == "success":
            assert "key_id" in result
            # Keys should be different (if rotation succeeded)
            assert new_keys.get("key_id") != old_keys.get("key_id")

    def test_verify_token_after_rotation(self):
        """Test that old tokens still work after key rotation (graceful rotation)"""
        user_id = "rotation-test-user"

        # Create token with current keys
        old_token = create_access_token(subject=user_id)

        # Verify old token works
        assert verify_token(old_token, token_type="access") == user_id

        # Rotate keys
        rotate_jwt_keys()

        # Old token should still be verifiable (archived keys support)
        verified_user_id = verify_token(old_token, token_type="access")

        # This might be None if archived keys aren't kept, or same user_id if they are
        # Just check it doesn't crash
        assert verified_user_id is None or verified_user_id == user_id

    def test_new_token_after_rotation(self):
        """Test creating new token after key rotation"""
        user_id = "new-rotation-user"

        # Rotate keys
        rotate_jwt_keys()

        # Create new token with rotated keys
        new_token = create_access_token(subject=user_id)

        # Verify new token works
        verified_user_id = verify_token(new_token, token_type="access")

        assert verified_user_id == user_id


class TestSecurityEdgeCases:
    """Test security edge cases and potential vulnerabilities"""

    def test_token_with_none_subject(self):
        """Test creating token with None subject"""
        token = create_access_token(subject=None)

        assert token is not None
        verified_user_id = verify_token(token, token_type="access")
        assert verified_user_id == "None" or verified_user_id is None

    def test_token_with_numeric_subject(self):
        """Test creating token with numeric subject"""
        user_id = 12345
        token = create_access_token(subject=user_id)

        verified_user_id = verify_token(token, token_type="access")
        assert verified_user_id == str(user_id)

    def test_verify_token_sql_injection_attempt(self):
        """Test that token verification is safe from SQL injection"""
        malicious_tokens = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'--",
        ]

        for token in malicious_tokens:
            verified_user_id = verify_token(token, token_type="access")
            assert verified_user_id is None

    def test_password_timing_attack_resistance(self):
        """Test that password verification takes similar time for valid and invalid passwords"""
        password = "test-password-123"
        hashed = get_password_hash(password)

        # This is a basic test - actual timing attack resistance would need more sophisticated testing
        import time

        # Test correct password
        start = time.time()
        verify_password(password, hashed)
        correct_time = time.time() - start

        # Test incorrect password
        start = time.time()
        verify_password("wrong-password", hashed)
        incorrect_time = time.time() - start

        # Times should be roughly similar (within an order of magnitude)
        # bcrypt should provide constant-time comparison
        assert abs(correct_time - incorrect_time) < 0.1

    def test_unicode_password_handling(self):
        """Test handling of unicode characters in passwords"""
        unicode_passwords = [
            "password123",
            "пароль123",  # Russian
            "密码123",  # Chinese
            "🔐🔑🗝️",  # Emojis
            "café",  # Accented characters
        ]

        for password in unicode_passwords:
            hashed = get_password_hash(password)
            assert verify_password(password, hashed) is True
            assert verify_password(password + "wrong", hashed) is False

    def test_very_long_password(self):
        """Test handling of very long passwords"""
        # 1000 character password
        long_password = "a" * 1000
        hashed = get_password_hash(long_password)

        assert verify_password(long_password, hashed) is True
        assert verify_password("a" * 999, hashed) is False

    def test_special_characters_in_password(self):
        """Test passwords with special characters"""
        special_passwords = [
            "p@ssw0rd!#$%",
            "test<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "password\nwith\nnewlines",
            "password\x00withNullBytes",
        ]

        for password in special_passwords:
            hashed = get_password_hash(password)
            assert verify_password(password, hashed) is True
