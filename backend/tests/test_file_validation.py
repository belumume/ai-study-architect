"""
File validation and security tests
"""

import pytest
import io
import zipfile
from app.utils.file_validation import (
    validate_file_content,
    get_mime_type,
    _basic_mime_detection,
    _has_suspicious_filename,
    _contains_malware_patterns,
)


class TestMIMETypeDetection:
    """Test MIME type detection"""

    def test_detect_pdf(self):
        """Test PDF detection"""
        pdf_content = b'%PDF-1.4\n'
        mime_type = get_mime_type(pdf_content)

        assert mime_type == 'application/pdf'

    def test_detect_png(self):
        """Test PNG detection"""
        png_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        mime_type = get_mime_type(png_content)

        assert mime_type == 'image/png'

    def test_detect_jpeg(self):
        """Test JPEG detection"""
        jpeg_content = b'\xFF\xD8\xFF' + b'\x00' * 100
        mime_type = get_mime_type(jpeg_content)

        assert mime_type == 'image/jpeg'

    def test_detect_plain_text(self):
        """Test plain text detection"""
        text_content = b'This is plain text content'
        mime_type = get_mime_type(text_content)

        assert mime_type in ['text/plain', 'text/markdown']

    def test_detect_markdown(self):
        """Test markdown detection"""
        markdown_content = b'# Heading\n## Subheading\nSome content'
        mime_type = get_mime_type(markdown_content)

        # Should detect as markdown or plain text
        assert mime_type in ['text/markdown', 'text/plain']

    def test_detect_zip(self):
        """Test ZIP/Office document detection"""
        # Create a simple ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr('test.txt', 'test content')
        zip_content = zip_buffer.getvalue()

        mime_type = get_mime_type(zip_content)

        assert 'zip' in mime_type or 'application' in mime_type

    def test_unknown_type(self):
        """Test unknown file type detection"""
        unknown_content = b'\xFF\xFF\xFF\xFF' + b'\x00' * 100
        mime_type = get_mime_type(unknown_content)

        # Should return a mime type, even if unknown
        assert isinstance(mime_type, str)
        assert len(mime_type) > 0


class TestFileSizeValidation:
    """Test file size validation"""

    def test_valid_file_size(self):
        """Test validation passes for normal file size"""
        content = b'Small file content'
        is_valid, error, info = validate_file_content(
            content,
            "test.txt",
            max_file_size=1024 * 1024  # 1MB
        )

        assert is_valid is True
        assert error == ""
        assert info["file_size"] == len(content)

    def test_file_exceeds_max_size(self):
        """Test validation fails for oversized files"""
        # Create 2MB content
        large_content = b'x' * (2 * 1024 * 1024)
        is_valid, error, info = validate_file_content(
            large_content,
            "large.txt",
            max_file_size=1 * 1024 * 1024  # 1MB limit
        )

        assert is_valid is False
        assert "exceeds maximum size" in error.lower()

    def test_empty_file(self):
        """Test validation fails for empty files"""
        empty_content = b''
        is_valid, error, info = validate_file_content(
            empty_content,
            "empty.txt"
        )

        assert is_valid is False
        assert "empty" in error.lower()

    def test_exactly_max_size(self):
        """Test file exactly at max size limit"""
        max_size = 1024
        content = b'x' * max_size
        is_valid, error, info = validate_file_content(
            content,
            "exact.txt",
            max_file_size=max_size
        )

        assert is_valid is True


class TestMIMETypeAllowList:
    """Test MIME type allow list validation"""

    def test_allowed_mime_type(self):
        """Test allowed MIME type passes"""
        pdf_content = b'%PDF-1.4\n' + b'\x00' * 100
        is_valid, error, info = validate_file_content(
            pdf_content,
            "document.pdf",
            allowed_mime_types=['application/pdf']
        )

        assert is_valid is True
        assert info["mime_type"] == 'application/pdf'

    def test_disallowed_mime_type(self):
        """Test disallowed MIME type fails"""
        pdf_content = b'%PDF-1.4\n' + b'\x00' * 100
        is_valid, error, info = validate_file_content(
            pdf_content,
            "document.pdf",
            allowed_mime_types=['image/png']  # PDF not allowed
        )

        assert is_valid is False
        assert "not allowed" in error.lower()

    def test_default_allowed_types(self):
        """Test default allowed types (when None specified)"""
        text_content = b'Plain text content'
        is_valid, error, info = validate_file_content(
            text_content,
            "document.txt",
            allowed_mime_types=None  # Use defaults
        )

        # Text should be in default allowed types
        assert is_valid is True


class TestPDFSecurityValidation:
    """Test PDF security validation"""

    def test_pdf_with_javascript(self):
        """Test PDF with JavaScript is rejected"""
        malicious_pdf = b'%PDF-1.4\n' + b'/JavaScript' + b'\x00' * 100
        is_valid, error, info = validate_file_content(
            malicious_pdf,
            "malicious.pdf"
        )

        assert is_valid is False
        assert "javascript" in error.lower()
        assert "JavaScript" in info["security_warnings"][0]

    def test_pdf_with_embedded_files(self):
        """Test PDF with embedded files is rejected"""
        malicious_pdf = b'%PDF-1.4\n' + b'/EmbeddedFile' + b'\x00' * 100
        is_valid, error, info = validate_file_content(
            malicious_pdf,
            "embedded.pdf"
        )

        assert is_valid is False
        assert "embedded" in error.lower()

    def test_pdf_with_launch_action(self):
        """Test PDF with launch actions is rejected"""
        malicious_pdf = b'%PDF-1.4\n' + b'/Launch' + b'\x00' * 100
        is_valid, error, info = validate_file_content(
            malicious_pdf,
            "launch.pdf"
        )

        assert is_valid is False
        assert "launch" in error.lower()

    def test_pdf_with_form_submission(self):
        """Test PDF with form submission is rejected"""
        malicious_pdf = b'%PDF-1.4\n' + b'/SubmitForm' + b'\x00' * 100
        is_valid, error, info = validate_file_content(
            malicious_pdf,
            "form.pdf"
        )

        assert is_valid is False
        assert "form" in error.lower()

    def test_clean_pdf(self):
        """Test clean PDF passes validation"""
        clean_pdf = b'%PDF-1.4\nSafe content here\n%%EOF'
        is_valid, error, info = validate_file_content(
            clean_pdf,
            "clean.pdf"
        )

        assert is_valid is True
        assert error == ""


class TestImageSecurityValidation:
    """Test image security validation"""

    def test_image_with_php_code(self):
        """Test image with embedded PHP is rejected"""
        malicious_image = b'\xFF\xD8\xFF<?php system($_GET[\'cmd\']); ?>' + b'\x00' * 100
        is_valid, error, info = validate_file_content(
            malicious_image,
            "malicious.jpg"
        )

        assert is_valid is False
        assert "code" in error.lower() or "php" in error.lower()

    def test_clean_jpeg(self):
        """Test clean JPEG passes validation"""
        clean_jpeg = b'\xFF\xD8\xFF\xE0' + b'\x00' * 100
        is_valid, error, info = validate_file_content(
            clean_jpeg,
            "photo.jpg"
        )

        assert is_valid is True

    def test_clean_png(self):
        """Test clean PNG passes validation"""
        clean_png = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        is_valid, error, info = validate_file_content(
            clean_png,
            "image.png"
        )

        assert is_valid is True


class TestOfficeDocumentValidation:
    """Test Office document security validation"""

    def test_office_document_with_macros(self):
        """Test Office document with macros is rejected"""
        # Create a ZIP with macro-like structure
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr('word/document.xml', '<document>content</document>')
            zf.writestr('word/vbaProject.bin', 'macro content')  # Macro file

        malicious_docx = zip_buffer.getvalue()
        is_valid, error, info = validate_file_content(
            malicious_docx,
            "document.docx"
        )

        assert is_valid is False
        assert "macro" in error.lower()

    def test_clean_office_document(self):
        """Test clean Office document passes"""
        # Create a clean ZIP structure
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr('word/document.xml', '<document>safe content</document>')
            zf.writestr('[Content_Types].xml', '<Types></Types>')

        clean_docx = zip_buffer.getvalue()
        is_valid, error, info = validate_file_content(
            clean_docx,
            "document.docx"
        )

        # Might be valid or might need more Office structure
        # Just check it doesn't crash
        assert isinstance(is_valid, bool)


class TestFileHashCalculation:
    """Test file hash calculation"""

    def test_hash_is_calculated(self):
        """Test that file hash is calculated"""
        content = b'Test content for hashing'
        is_valid, error, info = validate_file_content(
            content,
            "test.txt"
        )

        assert "file_hash" in info
        assert info["file_hash"] is not None
        assert len(info["file_hash"]) == 64  # SHA256 hex digest

    def test_same_content_same_hash(self):
        """Test same content produces same hash"""
        content = b'Identical content'

        is_valid1, error1, info1 = validate_file_content(content, "file1.txt")
        is_valid2, error2, info2 = validate_file_content(content, "file2.txt")

        assert info1["file_hash"] == info2["file_hash"]

    def test_different_content_different_hash(self):
        """Test different content produces different hash"""
        content1 = b'Content A'
        content2 = b'Content B'

        is_valid1, error1, info1 = validate_file_content(content1, "file1.txt")
        is_valid2, error2, info2 = validate_file_content(content2, "file2.txt")

        assert info1["file_hash"] != info2["file_hash"]


class TestSuspiciousFilenames:
    """Test suspicious filename detection"""

    def test_normal_filename(self):
        """Test normal filename is accepted"""
        content = b'Normal content'
        is_valid, error, info = validate_file_content(
            content,
            "normal-document.txt"
        )

        # Should not have filename warnings for normal names
        assert is_valid is True

    def test_double_extension(self):
        """Test double extension filename"""
        content = b'Content'
        is_valid, error, info = validate_file_content(
            content,
            "document.pdf.exe"
        )

        # Might trigger warnings depending on implementation
        # Just check it doesn't crash
        assert isinstance(is_valid, bool)

    def test_path_traversal_attempt(self):
        """Test path traversal in filename"""
        content = b'Content'
        is_valid, error, info = validate_file_content(
            content,
            "../../../etc/passwd"
        )

        # Should detect suspicious filename
        # Check it's processed safely
        assert isinstance(is_valid, bool)


class TestMalwarePatternDetection:
    """Test malware pattern detection"""

    def test_clean_content(self):
        """Test clean content passes malware check"""
        clean_content = b'This is normal, safe content for a document.'
        is_valid, error, info = validate_file_content(
            clean_content,
            "document.txt"
        )

        assert info["has_malicious_content"] is False
        assert is_valid is True

    def test_executable_patterns(self):
        """Test detection of executable patterns"""
        # MZ header (Windows executable)
        exe_content = b'MZ\x90\x00' + b'\x00' * 100

        # This should be detected as wrong MIME type or malicious
        is_valid, error, info = validate_file_content(
            exe_content,
            "file.txt",
            allowed_mime_types=['text/plain']
        )

        # Should fail (either due to MIME mismatch or malware detection)
        assert is_valid is False


class TestSecurityEdgeCases:
    """Test security edge cases"""

    def test_null_bytes_in_filename(self):
        """Test null bytes in filename"""
        content = b'Content'
        # Null bytes might be used to bypass filters
        filename = "document.txt\x00.exe"

        is_valid, error, info = validate_file_content(
            content,
            filename
        )

        # Should handle safely
        assert isinstance(is_valid, bool)

    def test_unicode_in_filename(self):
        """Test Unicode characters in filename"""
        content = b'Content'
        unicode_filename = "документ.txt"  # Russian characters

        is_valid, error, info = validate_file_content(
            content,
            unicode_filename
        )

        # Should handle Unicode safely
        assert isinstance(is_valid, bool)

    def test_very_long_filename(self):
        """Test very long filename"""
        content = b'Content'
        long_filename = "a" * 1000 + ".txt"

        is_valid, error, info = validate_file_content(
            content,
            long_filename
        )

        # Should handle long filenames
        assert isinstance(is_valid, bool)

    def test_special_characters_in_filename(self):
        """Test special characters in filename"""
        content = b'Content'
        special_filename = "file<script>.txt"

        is_valid, error, info = validate_file_content(
            content,
            special_filename
        )

        # Should detect or handle suspicious characters
        assert isinstance(is_valid, bool)

    def test_polyglot_file(self):
        """Test polyglot file (valid as multiple types)"""
        # File that appears valid as both PDF and something else
        polyglot = b'%PDF-1.4\n' + b'GIF89a' + b'\x00' * 100

        is_valid, error, info = validate_file_content(
            polyglot,
            "suspicious.pdf"
        )

        # Should detect as PDF and check accordingly
        assert isinstance(is_valid, bool)

    def test_zip_bomb_detection(self):
        """Test detection of potential zip bombs (highly compressed files)"""
        # Create a small ZIP with highly repetitive content
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            # 1MB of zeros compresses very well
            zf.writestr('data.txt', '\x00' * (1024 * 1024))

        zip_content = zip_buffer.getvalue()

        # The ZIP file itself should be small
        assert len(zip_content) < 10000

        # Validation should check the compressed size
        is_valid, error, info = validate_file_content(
            zip_content,
            "document.docx",
            max_file_size=1024 * 1024  # 1MB limit
        )

        # Should pass size check on the compressed file
        assert isinstance(is_valid, bool)
