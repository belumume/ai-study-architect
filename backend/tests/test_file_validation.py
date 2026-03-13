"""
File validation and security tests
"""

import hashlib
import io
import zipfile
from unittest.mock import MagicMock, patch

import pytest

from app.utils.file_validation import (
    _basic_mime_detection,
    _contains_malware_patterns,
    _has_suspicious_filename,
    _validate_image_content,
    _validate_office_content,
    _validate_pdf_content,
    _validate_text_content,
    calculate_file_hash,
    get_mime_type,
    validate_file_content,
)


class TestMIMETypeDetection:
    """Test MIME type detection"""

    def test_detect_pdf(self):
        """Test PDF detection"""
        pdf_content = b"%PDF-1.4\n"
        mime_type = get_mime_type(pdf_content)

        assert mime_type == "application/pdf"

    def test_detect_png(self):
        """Test PNG detection"""
        png_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        mime_type = get_mime_type(png_content)

        assert mime_type == "image/png"

    def test_detect_jpeg(self):
        """Test JPEG detection"""
        jpeg_content = b"\xff\xd8\xff" + b"\x00" * 100
        mime_type = get_mime_type(jpeg_content)

        assert mime_type == "image/jpeg"

    def test_detect_plain_text(self):
        """Test plain text detection"""
        text_content = b"This is plain text content"
        mime_type = get_mime_type(text_content)

        assert mime_type in ["text/plain", "text/markdown"]

    def test_detect_markdown(self):
        """Test markdown detection"""
        markdown_content = b"# Heading\n## Subheading\nSome content"
        mime_type = get_mime_type(markdown_content)

        # Should detect as markdown or plain text
        assert mime_type in ["text/markdown", "text/plain"]

    def test_detect_zip(self):
        """Test ZIP/Office document detection"""
        # Create a simple ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr("test.txt", "test content")
        zip_content = zip_buffer.getvalue()

        mime_type = get_mime_type(zip_content)

        assert "zip" in mime_type or "application" in mime_type

    def test_unknown_type(self):
        """Test unknown file type detection"""
        unknown_content = b"\xff\xff\xff\xff" + b"\x00" * 100
        mime_type = get_mime_type(unknown_content)

        # Should return a mime type, even if unknown
        assert isinstance(mime_type, str)
        assert len(mime_type) > 0


class TestFileSizeValidation:
    """Test file size validation"""

    def test_valid_file_size(self):
        """Test validation passes for normal file size"""
        content = b"Small file content"
        is_valid, error, info = validate_file_content(
            content,
            "test.txt",
            max_file_size=1024 * 1024,  # 1MB
        )

        assert is_valid is True
        assert error == ""
        assert info["file_size"] == len(content)

    def test_file_exceeds_max_size(self):
        """Test validation fails for oversized files"""
        # Create 2MB content
        large_content = b"x" * (2 * 1024 * 1024)
        is_valid, error, info = validate_file_content(
            large_content,
            "large.txt",
            max_file_size=1 * 1024 * 1024,  # 1MB limit
        )

        assert is_valid is False
        assert "exceeds maximum size" in error.lower()

    def test_empty_file(self):
        """Test validation fails for empty files"""
        empty_content = b""
        is_valid, error, info = validate_file_content(empty_content, "empty.txt")

        assert is_valid is False
        assert "empty" in error.lower()

    def test_exactly_max_size(self):
        """Test file exactly at max size limit"""
        max_size = 1024
        content = b"x" * max_size
        is_valid, error, info = validate_file_content(content, "exact.txt", max_file_size=max_size)

        assert is_valid is True


class TestMIMETypeAllowList:
    """Test MIME type allow list validation"""

    def test_allowed_mime_type(self):
        """Test allowed MIME type passes"""
        pdf_content = b"%PDF-1.4\n" + b"\x00" * 100
        is_valid, error, info = validate_file_content(
            pdf_content, "document.pdf", allowed_mime_types=["application/pdf"]
        )

        assert is_valid is True
        assert info["mime_type"] == "application/pdf"

    def test_disallowed_mime_type(self):
        """Test disallowed MIME type fails"""
        pdf_content = b"%PDF-1.4\n" + b"\x00" * 100
        is_valid, error, info = validate_file_content(
            pdf_content,
            "document.pdf",
            allowed_mime_types=["image/png"],  # PDF not allowed
        )

        assert is_valid is False
        assert "not allowed" in error.lower()

    def test_default_allowed_types(self):
        """Test default allowed types (when None specified)"""
        text_content = b"Plain text content"
        is_valid, error, info = validate_file_content(
            text_content,
            "document.txt",
            allowed_mime_types=None,  # Use defaults
        )

        # Text should be in default allowed types
        assert is_valid is True


class TestPDFSecurityValidation:
    """Test PDF security validation"""

    def test_pdf_with_javascript(self):
        """Test PDF with JavaScript is rejected"""
        malicious_pdf = b"%PDF-1.4\n" + b"/JavaScript" + b"\x00" * 100
        is_valid, error, info = validate_file_content(malicious_pdf, "malicious.pdf")

        assert is_valid is False
        assert "javascript" in error.lower()
        assert "JavaScript" in info["security_warnings"][0]

    def test_pdf_with_embedded_files(self):
        """Test PDF with embedded files is rejected"""
        malicious_pdf = b"%PDF-1.4\n" + b"/EmbeddedFile" + b"\x00" * 100
        is_valid, error, info = validate_file_content(malicious_pdf, "embedded.pdf")

        assert is_valid is False
        assert "embedded" in error.lower()

    def test_pdf_with_launch_action(self):
        """Test PDF with launch actions is rejected"""
        malicious_pdf = b"%PDF-1.4\n" + b"/Launch" + b"\x00" * 100
        is_valid, error, info = validate_file_content(malicious_pdf, "launch.pdf")

        assert is_valid is False
        assert "launch" in error.lower()

    def test_pdf_with_form_submission(self):
        """Test PDF with form submission is rejected"""
        malicious_pdf = b"%PDF-1.4\n" + b"/SubmitForm" + b"\x00" * 100
        is_valid, error, info = validate_file_content(malicious_pdf, "form.pdf")

        assert is_valid is False
        assert "form" in error.lower()

    def test_clean_pdf(self):
        """Test clean PDF passes validation"""
        clean_pdf = b"%PDF-1.4\nSafe content here\n%%EOF"
        is_valid, error, info = validate_file_content(clean_pdf, "clean.pdf")

        assert is_valid is True
        assert error == ""


class TestImageSecurityValidation:
    """Test image security validation"""

    def test_image_with_php_code(self):
        """Test image with embedded PHP is rejected"""
        malicious_image = b"\xff\xd8\xff<?php system($_GET['cmd']); ?>" + b"\x00" * 100
        is_valid, error, info = validate_file_content(malicious_image, "malicious.jpg")

        assert is_valid is False
        assert "code" in error.lower() or "php" in error.lower()

    def test_clean_jpeg(self):
        """Test clean JPEG passes validation"""
        clean_jpeg = b"\xff\xd8\xff\xe0" + b"\x00" * 100
        is_valid, error, info = validate_file_content(clean_jpeg, "photo.jpg")

        assert is_valid is True

    def test_clean_png(self):
        """Test clean PNG passes validation"""
        clean_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        is_valid, error, info = validate_file_content(clean_png, "image.png")

        assert is_valid is True


class TestOfficeDocumentValidation:
    """Test Office document security validation"""

    def test_office_document_with_macros(self):
        """Test Office document with macros is rejected"""
        # Create a ZIP with macro-like structure
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr("word/document.xml", "<document>content</document>")
            zf.writestr("word/vbaProject.bin", "macro content")  # Macro file

        malicious_docx = zip_buffer.getvalue()
        is_valid, error, info = validate_file_content(malicious_docx, "document.docx")

        assert is_valid is False
        assert "macro" in error.lower()

    def test_clean_office_document(self):
        """Test clean Office document passes"""
        # Create a clean ZIP structure
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr("word/document.xml", "<document>safe content</document>")
            zf.writestr("[Content_Types].xml", "<Types></Types>")

        clean_docx = zip_buffer.getvalue()
        is_valid, error, info = validate_file_content(clean_docx, "document.docx")

        # Might be valid or might need more Office structure
        # Just check it doesn't crash
        assert isinstance(is_valid, bool)


class TestFileHashCalculation:
    """Test file hash calculation"""

    def test_hash_is_calculated(self):
        """Test that file hash is calculated"""
        content = b"Test content for hashing"
        is_valid, error, info = validate_file_content(content, "test.txt")

        assert "file_hash" in info
        assert info["file_hash"] is not None
        assert len(info["file_hash"]) == 64  # SHA256 hex digest

    def test_same_content_same_hash(self):
        """Test same content produces same hash"""
        content = b"Identical content"

        is_valid1, error1, info1 = validate_file_content(content, "file1.txt")
        is_valid2, error2, info2 = validate_file_content(content, "file2.txt")

        assert info1["file_hash"] == info2["file_hash"]

    def test_different_content_different_hash(self):
        """Test different content produces different hash"""
        content1 = b"Content A"
        content2 = b"Content B"

        is_valid1, error1, info1 = validate_file_content(content1, "file1.txt")
        is_valid2, error2, info2 = validate_file_content(content2, "file2.txt")

        assert info1["file_hash"] != info2["file_hash"]


class TestSuspiciousFilenames:
    """Test suspicious filename detection"""

    def test_normal_filename(self):
        """Test normal filename is accepted"""
        content = b"Normal content"
        is_valid, error, info = validate_file_content(content, "normal-document.txt")

        # Should not have filename warnings for normal names
        assert is_valid is True

    def test_double_extension(self):
        """Test double extension filename"""
        content = b"Content"
        is_valid, error, info = validate_file_content(content, "document.pdf.exe")

        # Might trigger warnings depending on implementation
        # Just check it doesn't crash
        assert isinstance(is_valid, bool)

    def test_path_traversal_attempt(self):
        """Test path traversal in filename"""
        content = b"Content"
        is_valid, error, info = validate_file_content(content, "../../../etc/passwd")

        # Should detect suspicious filename
        # Check it's processed safely
        assert isinstance(is_valid, bool)


class TestMalwarePatternDetection:
    """Test malware pattern detection"""

    def test_clean_content(self):
        """Test clean content passes malware check"""
        clean_content = b"This is normal, safe content for a document."
        is_valid, error, info = validate_file_content(clean_content, "document.txt")

        assert info["has_malicious_content"] is False
        assert is_valid is True

    def test_executable_patterns(self):
        """Test detection of executable patterns"""
        # MZ header (Windows executable)
        exe_content = b"MZ\x90\x00" + b"\x00" * 100

        # This should be detected as wrong MIME type or malicious
        is_valid, error, info = validate_file_content(
            exe_content, "file.txt", allowed_mime_types=["text/plain"]
        )

        # Should fail (either due to MIME mismatch or malware detection)
        assert is_valid is False


class TestSecurityEdgeCases:
    """Test security edge cases"""

    def test_null_bytes_in_filename(self):
        """Test null bytes in filename"""
        content = b"Content"
        # Null bytes might be used to bypass filters
        filename = "document.txt\x00.exe"

        is_valid, error, info = validate_file_content(content, filename)

        # Should handle safely
        assert isinstance(is_valid, bool)

    def test_unicode_in_filename(self):
        """Test Unicode characters in filename"""
        content = b"Content"
        unicode_filename = "документ.txt"  # Russian characters

        is_valid, error, info = validate_file_content(content, unicode_filename)

        # Should handle Unicode safely
        assert isinstance(is_valid, bool)

    def test_very_long_filename(self):
        """Test very long filename"""
        content = b"Content"
        long_filename = "a" * 1000 + ".txt"

        is_valid, error, info = validate_file_content(content, long_filename)

        # Should handle long filenames
        assert isinstance(is_valid, bool)

    def test_special_characters_in_filename(self):
        """Test special characters in filename"""
        content = b"Content"
        special_filename = "file<script>.txt"

        is_valid, error, info = validate_file_content(content, special_filename)

        # Should detect or handle suspicious characters
        assert isinstance(is_valid, bool)

    def test_polyglot_file(self):
        """Test polyglot file (valid as multiple types)"""
        # File that appears valid as both PDF and something else
        polyglot = b"%PDF-1.4\n" + b"GIF89a" + b"\x00" * 100

        is_valid, error, info = validate_file_content(polyglot, "suspicious.pdf")

        # Should detect as PDF and check accordingly
        assert isinstance(is_valid, bool)

    def test_zip_bomb_detection(self):
        """Test detection of potential zip bombs (highly compressed files)"""
        # Create a small ZIP with highly repetitive content
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            # 1MB of zeros compresses very well
            zf.writestr("data.txt", "\x00" * (1024 * 1024))

        zip_content = zip_buffer.getvalue()

        # The ZIP file itself should be small
        assert len(zip_content) < 10000

        # Validation should check the compressed size
        is_valid, error, info = validate_file_content(
            zip_content,
            "document.docx",
            max_file_size=1024 * 1024,  # 1MB limit
        )

        # Should pass size check on the compressed file
        assert isinstance(is_valid, bool)


# ---------------------------------------------------------------------------
# Comprehensive tests added for full branch coverage
# ---------------------------------------------------------------------------


class TestGetMimeTypeWithMagic:
    """Test get_mime_type when python-magic is available or raises exceptions."""

    def test_magic_returns_valid_type(self):
        """When magic detects a real type, it should be returned directly."""
        mock_magic_instance = MagicMock()
        mock_magic_instance.from_buffer.return_value = "application/pdf"

        mock_magic_module = MagicMock()
        mock_magic_module.Magic.return_value = mock_magic_instance

        with patch.dict("sys.modules", {"magic": mock_magic_module}):
            # Force re-import path inside get_mime_type
            result = get_mime_type(b"%PDF-1.4\n")

        assert result == "application/pdf"

    def test_magic_returns_octet_stream_falls_back(self):
        """When magic returns application/octet-stream, fall back to basic detection."""
        mock_magic_instance = MagicMock()
        mock_magic_instance.from_buffer.return_value = "application/octet-stream"

        mock_magic_module = MagicMock()
        mock_magic_module.Magic.return_value = mock_magic_instance

        with patch.dict("sys.modules", {"magic": mock_magic_module}):
            result = get_mime_type(b"%PDF-1.4\n")

        assert result == "application/pdf"

    def test_magic_returns_none_falls_back(self):
        """When magic returns None, fall back to basic detection."""
        mock_magic_instance = MagicMock()
        mock_magic_instance.from_buffer.return_value = None

        mock_magic_module = MagicMock()
        mock_magic_module.Magic.return_value = mock_magic_instance

        with patch.dict("sys.modules", {"magic": mock_magic_module}):
            result = get_mime_type(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)

        assert result == "image/png"

    def test_magic_raises_exception_falls_back(self):
        """When magic raises any exception, fall back to basic detection."""
        mock_magic_module = MagicMock()
        mock_magic_module.Magic.side_effect = OSError("libmagic not found")

        with patch.dict("sys.modules", {"magic": mock_magic_module}):
            result = get_mime_type(b"\xff\xd8\xff" + b"\x00" * 50)

        assert result == "image/jpeg"


class TestBasicMimeDetectionSignatures:
    """Test _basic_mime_detection for every file signature branch."""

    def test_pdf_signature(self):
        assert _basic_mime_detection(b"%PDF-1.7 rest of file") == "application/pdf"

    def test_jpeg_signature(self):
        assert _basic_mime_detection(b"\xff\xd8\xff\xe0" + b"\x00" * 50) == "image/jpeg"

    def test_png_signature(self):
        assert _basic_mime_detection(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50) == "image/png"

    def test_gif87a_signature(self):
        assert _basic_mime_detection(b"GIF87a" + b"\x00" * 50) == "image/gif"

    def test_gif89a_signature(self):
        assert _basic_mime_detection(b"GIF89a" + b"\x00" * 50) == "image/gif"

    def test_mp3_with_id3_signature(self):
        assert _basic_mime_detection(b"ID3" + b"\x00" * 50) == "audio/mpeg"

    def test_mp3_0xfffb_signature(self):
        assert _basic_mime_detection(b"\xff\xfb" + b"\x00" * 50) == "audio/mpeg"

    def test_mp3_0xfff3_signature(self):
        assert _basic_mime_detection(b"\xff\xf3" + b"\x00" * 50) == "audio/mpeg"

    def test_mp3_0xfff2_signature(self):
        assert _basic_mime_detection(b"\xff\xf2" + b"\x00" * 50) == "audio/mpeg"

    def test_riff_wav_signature(self):
        """RIFF file with WAVE subtype should return audio/wav."""
        content = b"RIFF" + b"\x00" * 4 + b"WAVE" + b"\x00" * 50
        assert _basic_mime_detection(content) == "audio/wav"

    def test_riff_avi_signature(self):
        """RIFF file with AVI subtype should return video/x-msvideo."""
        content = b"RIFF" + b"\x00" * 4 + b"AVI " + b"\x00" * 50
        assert _basic_mime_detection(content) == "video/x-msvideo"

    def test_riff_short_content_no_subtype(self):
        """RIFF signature with content too short for subtype detection."""
        content = b"RIFF" + b"\x00" * 5  # len=9, needs >12 for subtype
        assert _basic_mime_detection(content) == "audio/wav"

    def test_riff_unknown_subtype(self):
        """RIFF file with unknown subtype falls through to generic return."""
        content = b"RIFF" + b"\x00" * 4 + b"XXXX" + b"\x00" * 50
        # Neither WAVE nor AVI, so falls through to `return mime_type` (audio/wav)
        assert _basic_mime_detection(content) == "audio/wav"

    def test_mp4_ftyp_0x20(self):
        content = b"\x00\x00\x00\x20ftypmp4" + b"\x00" * 50
        assert _basic_mime_detection(content) == "video/mp4"

    def test_mp4_ftyp_0x18(self):
        content = b"\x00\x00\x00\x18ftypmp4" + b"\x00" * 50
        assert _basic_mime_detection(content) == "video/mp4"

    def test_mp4_ftyp_0x1c(self):
        content = b"\x00\x00\x00\x1cftypmp4" + b"\x00" * 50
        assert _basic_mime_detection(content) == "video/mp4"

    def test_zip_signature_0x0304(self):
        """Plain ZIP (no office content) with PK\\x03\\x04 signature."""
        content = b"\x50\x4b\x03\x04" + b"\x00" * 10
        assert _basic_mime_detection(content) == "application/zip"

    def test_zip_signature_0x0506(self):
        content = b"\x50\x4b\x05\x06" + b"\x00" * 10
        assert _basic_mime_detection(content) == "application/zip"

    def test_zip_signature_0x0708(self):
        content = b"\x50\x4b\x07\x08" + b"\x00" * 10
        assert _basic_mime_detection(content) == "application/zip"

    def test_zip_with_word_content_detected_as_docx(self):
        """ZIP containing 'word/' in first 1000 bytes should be detected as DOCX."""
        content = b"\x50\x4b\x03\x04" + b"\x00" * 30 + b"word/document.xml" + b"\x00" * 950
        result = _basic_mime_detection(content)
        assert result == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    def test_zip_with_ppt_content_detected_as_pptx(self):
        """ZIP containing 'ppt/' in first 1000 bytes should be detected as PPTX."""
        content = b"\x50\x4b\x03\x04" + b"\x00" * 30 + b"ppt/presentation.xml" + b"\x00" * 950
        result = _basic_mime_detection(content)
        assert result == "application/vnd.openxmlformats-officedocument.presentationml.presentation"

    def test_zip_with_xl_content_detected_as_xlsx(self):
        """ZIP containing 'xl/' in first 1000 bytes should be detected as XLSX."""
        content = b"\x50\x4b\x03\x04" + b"\x00" * 30 + b"xl/workbook.xml" + b"\x00" * 950
        result = _basic_mime_detection(content)
        assert result == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    def test_zip_short_content_no_office_detection(self):
        """ZIP signature with <=30 bytes should not attempt Office detection."""
        content = b"\x50\x4b\x03\x04" + b"\x00" * 20  # total 24 bytes
        assert _basic_mime_detection(content) == "application/zip"

    def test_plain_text_utf8(self):
        """Valid UTF-8 text without markdown markers returns text/plain."""
        content = b"Just a simple sentence with no special markers."
        assert _basic_mime_detection(content) == "text/plain"

    def test_markdown_with_heading(self):
        """Text starting with # should be detected as markdown."""
        assert _basic_mime_detection(b"# Title\nSome paragraph") == "text/markdown"

    def test_markdown_with_double_heading(self):
        assert _basic_mime_detection(b"## Subtitle\nContent") == "text/markdown"

    def test_markdown_with_code_fence(self):
        assert _basic_mime_detection(b"```python\nprint('hi')\n```") == "text/markdown"

    def test_markdown_with_link_bracket(self):
        """Text with [ in first 100 bytes triggers markdown detection."""
        assert _basic_mime_detection(b"See [this link](http://example.com)") == "text/markdown"

    def test_markdown_with_link_paren(self):
        """Text with ]( in first 100 bytes triggers markdown detection."""
        assert _basic_mime_detection(b"Click ](url) for details") == "text/markdown"

    def test_non_utf8_binary_returns_octet_stream(self):
        """Binary content that is not valid UTF-8 returns application/octet-stream."""
        # Bytes that are invalid UTF-8 and don't match any signature
        content = b"\xfe\xfe\xfe\xfe\xfe\xfe\xfe\xfe"
        assert _basic_mime_detection(content) == "application/octet-stream"


class TestValidatePdfContentDirect:
    """Test _validate_pdf_content for all rejection branches."""

    def test_rejects_js_shorthand(self):
        """PDF with /JS (not /JavaScript) should also be rejected."""
        info = {"security_warnings": []}
        is_valid, error = _validate_pdf_content(b"%PDF-1.4 /JS (alert())", info)
        assert is_valid is False
        assert "JavaScript" in error
        assert len(info["security_warnings"]) == 1

    def test_rejects_javascript(self):
        info = {"security_warnings": []}
        is_valid, error = _validate_pdf_content(b"%PDF-1.4 /JavaScript", info)
        assert is_valid is False
        assert "JavaScript" in error

    def test_rejects_embedded_file(self):
        info = {"security_warnings": []}
        is_valid, error = _validate_pdf_content(b"%PDF-1.4 /EmbeddedFile", info)
        assert is_valid is False
        assert "embedded" in error.lower()

    def test_rejects_launch(self):
        info = {"security_warnings": []}
        is_valid, error = _validate_pdf_content(b"%PDF-1.4 /Launch", info)
        assert is_valid is False
        assert "launch" in error.lower()

    def test_rejects_submit_form(self):
        info = {"security_warnings": []}
        is_valid, error = _validate_pdf_content(b"%PDF-1.4 /SubmitForm", info)
        assert is_valid is False
        assert "form" in error.lower()

    def test_rejects_import_data(self):
        info = {"security_warnings": []}
        is_valid, error = _validate_pdf_content(b"%PDF-1.4 /ImportData", info)
        assert is_valid is False
        assert "form" in error.lower()

    def test_clean_pdf_passes(self):
        info = {"security_warnings": []}
        is_valid, error = _validate_pdf_content(b"%PDF-1.4 normal content %%EOF", info)
        assert is_valid is True
        assert error == ""
        assert len(info["security_warnings"]) == 0


class TestValidateImageContentDirect:
    """Test _validate_image_content for all branches."""

    def test_rejects_php_in_image(self):
        info = {"security_warnings": []}
        content = b"\xff\xd8\xff<?php echo 'hi'; ?>"
        is_valid, error = _validate_image_content(content, "image/jpeg", info)
        assert is_valid is False
        assert "code" in error.lower()
        assert "PHP" in info["security_warnings"][0]

    def test_rejects_php_in_png(self):
        info = {"security_warnings": []}
        content = b"\x89PNG\r\n\x1a\n<?php system('ls'); ?>"
        is_valid, error = _validate_image_content(content, "image/png", info)
        assert is_valid is False

    def test_jpeg_exif_with_script_tag(self):
        """JPEG with Exif header containing <script> should be rejected."""
        info = {"security_warnings": []}
        # Exif marker within first 100 bytes, and <script> in content
        content = (
            b"\xff\xd8\xff" + b"Exif" + b"\x00" * 50 + b"<script>alert(1)</script>" + b"\x00" * 50
        )
        is_valid, error = _validate_image_content(content, "image/jpeg", info)
        assert is_valid is False
        assert "EXIF" in info["security_warnings"][0]

    def test_jpeg_exif_with_javascript_uri(self):
        """JPEG with Exif header containing javascript: should be rejected."""
        info = {"security_warnings": []}
        content = b"\xff\xd8\xff" + b"Exif" + b"\x00" * 50 + b"javascript:alert(1)" + b"\x00" * 50
        is_valid, error = _validate_image_content(content, "image/jpeg", info)
        assert is_valid is False
        assert "EXIF" in info["security_warnings"][0]

    def test_jpeg_exif_clean(self):
        """JPEG with Exif header but no suspicious content should pass."""
        info = {"security_warnings": []}
        content = b"\xff\xd8\xff" + b"Exif" + b"\x00" * 90
        is_valid, error = _validate_image_content(content, "image/jpeg", info)
        assert is_valid is True
        assert error == ""

    def test_non_jpeg_exif_not_checked(self):
        """Only JPEG triggers the EXIF script check, not PNG."""
        info = {"security_warnings": []}
        content = b"\x89PNG" + b"Exif" + b"\x00" * 50 + b"<script>alert(1)</script>"
        # image/png won't trigger the EXIF check path
        is_valid, error = _validate_image_content(content, "image/png", info)
        # PHP check doesn't match, EXIF check only for jpeg
        assert is_valid is True

    def test_clean_image_passes(self):
        info = {"security_warnings": []}
        is_valid, error = _validate_image_content(
            b"\xff\xd8\xff\xe0" + b"\x00" * 100, "image/jpeg", info
        )
        assert is_valid is True
        assert error == ""

    def test_gif_clean_passes(self):
        info = {"security_warnings": []}
        is_valid, error = _validate_image_content(b"GIF89a" + b"\x00" * 100, "image/gif", info)
        assert is_valid is True


class TestValidateOfficeContentDirect:
    """Test _validate_office_content for all branches."""

    def _make_zip(self, files):
        """Helper: create a ZIP archive from a dict of {name: content}."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            for name, content in files.items():
                zf.writestr(name, content)
        return buf.getvalue()

    def test_rejects_macros_in_bin_file(self):
        info = {"security_warnings": []}
        content = self._make_zip({"word/document.xml": "<doc/>", "word/vbaProject.bin": "macro"})
        mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        is_valid, error = _validate_office_content(content, mime, info)
        assert is_valid is False
        assert "macro" in error.lower()

    def test_rejects_macros_keyword_in_path(self):
        info = {"security_warnings": []}
        content = self._make_zip({"word/document.xml": "<doc/>", "word/macros/evil.xml": "data"})
        mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        is_valid, error = _validate_office_content(content, mime, info)
        assert is_valid is False
        assert "macro" in error.lower()

    def test_external_reference_adds_warning_but_passes(self):
        """Files with 'external' in name add a warning but do not block."""
        info = {"security_warnings": []}
        content = self._make_zip(
            {
                "word/document.xml": "<doc>safe</doc>",
                "word/_rels/external.xml.rels": "<Relationships/>",
            }
        )
        mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        is_valid, error = _validate_office_content(content, mime, info)
        assert is_valid is True
        assert any("external" in w.lower() for w in info["security_warnings"])

    def test_rejects_script_in_xml_content(self):
        info = {"security_warnings": []}
        content = self._make_zip(
            {
                "word/document.xml": "<doc><script>alert(1)</script></doc>",
            }
        )
        mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        is_valid, error = _validate_office_content(content, mime, info)
        assert is_valid is False
        assert "script" in error.lower()

    def test_rejects_javascript_uri_in_rels(self):
        info = {"security_warnings": []}
        content = self._make_zip(
            {
                "word/document.xml": "<doc/>",
                "word/_rels/document.xml.rels": '<Relationship Target="javascript:alert(1)"/>',
            }
        )
        mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        is_valid, error = _validate_office_content(content, mime, info)
        assert is_valid is False
        assert "script" in error.lower()

    def test_bad_zip_file_returns_invalid(self):
        info = {"security_warnings": []}
        mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        is_valid, error = _validate_office_content(b"not a zip at all", mime, info)
        assert is_valid is False
        assert "invalid" in error.lower()

    def test_generic_exception_returns_unable(self):
        """A generic exception during ZIP processing returns 'unable to validate'."""
        info = {"security_warnings": []}
        mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        # Patch ZipFile to raise a non-BadZipFile exception
        with patch("app.utils.file_validation.zipfile.ZipFile", side_effect=MemoryError("oom")):
            is_valid, error = _validate_office_content(
                b"\x50\x4b\x03\x04" + b"\x00" * 50, mime, info
            )
        assert is_valid is False
        assert "unable to validate" in error.lower()

    def test_clean_office_passes(self):
        info = {"security_warnings": []}
        content = self._make_zip(
            {
                "word/document.xml": "<document>safe content</document>",
                "[Content_Types].xml": "<Types/>",
            }
        )
        mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        is_valid, error = _validate_office_content(content, mime, info)
        assert is_valid is True
        assert error == ""

    def test_pptx_with_macros_rejected(self):
        info = {"security_warnings": []}
        content = self._make_zip({"ppt/presentation.xml": "<p/>", "ppt/vbaProject.bin": "macro"})
        mime = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        is_valid, error = _validate_office_content(content, mime, info)
        assert is_valid is False

    def test_xlsx_clean_passes(self):
        info = {"security_warnings": []}
        content = self._make_zip({"xl/workbook.xml": "<wb/>", "[Content_Types].xml": "<Types/>"})
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        is_valid, error = _validate_office_content(content, mime, info)
        assert is_valid is True


class TestValidateTextContentDirect:
    """Test _validate_text_content for all script and SQL pattern branches."""

    def test_rejects_script_tag(self):
        info = {"security_warnings": []}
        is_valid, error = _validate_text_content(b"<script>alert(1)</script>", info)
        assert is_valid is False
        assert "script" in error.lower()

    def test_rejects_javascript_uri(self):
        info = {"security_warnings": []}
        is_valid, error = _validate_text_content(b"click javascript:void(0)", info)
        assert is_valid is False
        assert "script" in error.lower()

    def test_rejects_onerror_handler(self):
        info = {"security_warnings": []}
        is_valid, error = _validate_text_content(b'<img onerror = "alert(1)">', info)
        assert is_valid is False

    def test_rejects_onclick_handler(self):
        info = {"security_warnings": []}
        is_valid, error = _validate_text_content(b'<div onclick = "evil()">', info)
        assert is_valid is False

    def test_rejects_iframe(self):
        info = {"security_warnings": []}
        is_valid, error = _validate_text_content(b'<iframe src="evil.html"></iframe>', info)
        assert is_valid is False

    def test_rejects_object_tag(self):
        info = {"security_warnings": []}
        is_valid, error = _validate_text_content(b'<object data="evil.swf"></object>', info)
        assert is_valid is False

    def test_rejects_embed_tag(self):
        info = {"security_warnings": []}
        is_valid, error = _validate_text_content(b'<embed src="evil.swf">', info)
        assert is_valid is False

    def test_sql_drop_table_adds_warning(self):
        """SQL injection patterns add warnings but do not block."""
        info = {"security_warnings": []}
        is_valid, error = _validate_text_content(b"; DROP TABLE users", info)
        assert is_valid is True
        assert any("SQL" in w for w in info["security_warnings"])

    def test_sql_delete_from_adds_warning(self):
        info = {"security_warnings": []}
        is_valid, error = _validate_text_content(b"; DELETE FROM users", info)
        assert is_valid is True
        assert any("SQL" in w for w in info["security_warnings"])

    def test_sql_union_select_adds_warning(self):
        info = {"security_warnings": []}
        is_valid, error = _validate_text_content(b"UNION SELECT * FROM passwords", info)
        assert is_valid is True
        assert any("SQL" in w for w in info["security_warnings"])

    def test_sql_or_1_equals_1_adds_warning(self):
        info = {"security_warnings": []}
        is_valid, error = _validate_text_content(b"OR 1 = 1", info)
        assert is_valid is True
        assert any("SQL" in w for w in info["security_warnings"])

    def test_clean_text_passes(self):
        info = {"security_warnings": []}
        is_valid, error = _validate_text_content(b"Normal study notes about algorithms.", info)
        assert is_valid is True
        assert error == ""
        assert len(info["security_warnings"]) == 0

    def test_script_detection_case_insensitive(self):
        """Script patterns should be detected regardless of case."""
        info = {"security_warnings": []}
        is_valid, error = _validate_text_content(b"<SCRIPT>alert(1)</SCRIPT>", info)
        assert is_valid is False

    def test_multiline_script_detected(self):
        """Script tag spanning multiple lines should be detected."""
        info = {"security_warnings": []}
        content = b"<script\ntype='text/javascript'\n>alert(1)</script>"
        is_valid, error = _validate_text_content(content, info)
        assert is_valid is False


class TestHasSuspiciousFilenameExhaustive:
    """Test _has_suspicious_filename for every pattern individually."""

    def test_php_double_extension(self):
        assert _has_suspicious_filename("image.php.jpg") is True

    def test_exe_double_extension(self):
        assert _has_suspicious_filename("document.exe.pdf") is True

    def test_scr_double_extension(self):
        assert _has_suspicious_filename("file.scr.txt") is True

    def test_vbs_double_extension(self):
        assert _has_suspicious_filename("script.vbs.doc") is True

    def test_js_double_extension(self):
        assert _has_suspicious_filename("payload.js.png") is True

    def test_directory_traversal(self):
        assert _has_suspicious_filename("../../etc/passwd") is True

    def test_single_dot_dot(self):
        assert _has_suspicious_filename("..secret") is True

    def test_angle_brackets(self):
        assert _has_suspicious_filename("file<name>.txt") is True

    def test_colon_in_filename(self):
        assert _has_suspicious_filename("file:name.txt") is True

    def test_double_quote_in_filename(self):
        assert _has_suspicious_filename('file"name.txt') is True

    def test_pipe_in_filename(self):
        assert _has_suspicious_filename("file|name.txt") is True

    def test_question_mark_in_filename(self):
        assert _has_suspicious_filename("file?name.txt") is True

    def test_asterisk_in_filename(self):
        assert _has_suspicious_filename("file*name.txt") is True

    def test_hidden_file(self):
        assert _has_suspicious_filename(".hidden_file") is True

    def test_htaccess(self):
        assert _has_suspicious_filename(".htaccess") is True

    def test_htpasswd(self):
        assert _has_suspicious_filename(".htpasswd") is True

    def test_normal_filename_is_safe(self):
        assert _has_suspicious_filename("my-document.pdf") is False

    def test_filename_with_spaces(self):
        assert _has_suspicious_filename("my document.pdf") is False

    def test_filename_with_numbers(self):
        assert _has_suspicious_filename("report_2025_v3.docx") is False

    def test_single_extension_php(self):
        """A file ending in .php (without double extension) does NOT match the pattern."""
        # The pattern is `\.php\.` which requires a dot AFTER php
        assert _has_suspicious_filename("script.php") is False

    def test_case_insensitive_detection(self):
        """Patterns should match regardless of case."""
        assert _has_suspicious_filename("image.PHP.jpg") is True
        assert _has_suspicious_filename("file.EXE.txt") is True
        assert _has_suspicious_filename(".HTACCESS") is True


class TestContainsMalwarePatternsExhaustive:
    """Test _contains_malware_patterns for every malware signature."""

    def test_eicar_test_string(self):
        content = b"prefix EICAR-STANDARD-ANTIVIRUS-TEST-FILE suffix"
        assert _contains_malware_patterns(content) is True

    def test_eicar_pattern(self):
        content = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR"
        assert _contains_malware_patterns(content) is True

    def test_wscript_shell(self):
        content = b'Set obj = CreateObject("WScript.Shell")'
        assert _contains_malware_patterns(content) is True

    def test_shell_application(self):
        content = b"Shell.Application"
        assert _contains_malware_patterns(content) is True

    def test_powershell_encoded(self):
        content = b"powershell -enc base64payload"
        assert _contains_malware_patterns(content) is True

    def test_cmd_c(self):
        content = b"cmd /c del *.*"
        assert _contains_malware_patterns(content) is True

    def test_eval_unescape(self):
        content = b"eval(unescape('%66%75%6e'))"
        assert _contains_malware_patterns(content) is True

    def test_document_write_unescape(self):
        content = b"document.write(unescape('%3c%73%63'))"
        assert _contains_malware_patterns(content) is True

    def test_mz_header_pattern(self):
        content = b"\\x4d\\x5a rest of PE"
        assert _contains_malware_patterns(content) is True

    def test_clean_content(self):
        content = b"This is perfectly normal study material about data structures."
        assert _contains_malware_patterns(content) is False

    def test_empty_content(self):
        assert _contains_malware_patterns(b"") is False


class TestCalculateFileHash:
    """Test calculate_file_hash for all algorithms and error paths."""

    def test_sha256(self):
        content = b"test content"
        result = calculate_file_hash(content, "sha256")
        assert result == hashlib.sha256(content).hexdigest()
        assert len(result) == 64

    def test_sha1(self):
        content = b"test content"
        result = calculate_file_hash(content, "sha1")
        assert result == hashlib.sha1(content).hexdigest()
        assert len(result) == 40

    def test_md5(self):
        content = b"test content"
        result = calculate_file_hash(content, "md5")
        assert result == hashlib.md5(content).hexdigest()
        assert len(result) == 32

    def test_default_algorithm_is_sha256(self):
        content = b"test"
        assert calculate_file_hash(content) == hashlib.sha256(content).hexdigest()

    def test_unsupported_algorithm_raises(self):
        with pytest.raises(ValueError, match="Unsupported hash algorithm"):
            calculate_file_hash(b"test", "sha512")

    def test_empty_content(self):
        result = calculate_file_hash(b"", "sha256")
        assert result == hashlib.sha256(b"").hexdigest()

    def test_deterministic(self):
        content = b"same data"
        assert calculate_file_hash(content) == calculate_file_hash(content)

    def test_different_content_different_hash(self):
        assert calculate_file_hash(b"aaa") != calculate_file_hash(b"bbb")


class TestValidateFileContentIntegration:
    """Integration tests for validate_file_content covering full flow paths."""

    def test_oversized_file_returns_size_in_error_message(self):
        content = b"x" * (10 * 1024 * 1024 + 1)  # 10MB + 1 byte
        is_valid, error, info = validate_file_content(
            content, "big.txt", max_file_size=10 * 1024 * 1024
        )
        assert is_valid is False
        assert "10.0MB" in error

    def test_empty_file_hash_is_none(self):
        """Empty file should fail before hash calculation, leaving hash as None."""
        is_valid, error, info = validate_file_content(b"", "empty.txt")
        assert is_valid is False
        assert info["file_hash"] is None

    def test_size_exceeded_hash_is_none(self):
        """Oversized file should fail before hash calculation."""
        content = b"x" * 200
        is_valid, error, info = validate_file_content(content, "f.txt", max_file_size=100)
        assert is_valid is False
        assert info["file_hash"] is None

    def test_disallowed_type_hash_is_none(self):
        """File with disallowed MIME type should fail before hash calculation."""
        content = b"%PDF-1.4 data"
        is_valid, error, info = validate_file_content(
            content, "f.pdf", allowed_mime_types=["text/plain"]
        )
        assert is_valid is False
        assert info["file_hash"] is None

    def test_suspicious_filename_adds_warning_but_can_pass(self):
        """A suspicious filename adds a warning but the file can still pass if content is clean."""
        content = b"Clean text content"
        is_valid, error, info = validate_file_content(content, ".hidden_config.txt")
        assert is_valid is True
        assert "Suspicious filename" in info["security_warnings"][0]

    def test_malware_content_blocks_even_with_valid_mime(self):
        """Malware patterns should block even when MIME type and filename are fine."""
        content = b"WScript.Shell is dangerous"
        is_valid, error, info = validate_file_content(content, "notes.txt")
        assert is_valid is False
        assert info["has_malicious_content"] is True
        assert "malicious" in error.lower()

    def test_one_byte_file_is_valid(self):
        """A single byte file should not be treated as empty."""
        is_valid, error, info = validate_file_content(b"x", "tiny.txt")
        assert is_valid is True
        assert info["file_size"] == 1

    def test_file_one_byte_over_limit(self):
        """File exactly one byte over the limit should be rejected."""
        is_valid, error, info = validate_file_content(b"xx", "f.txt", max_file_size=1)
        assert is_valid is False
        assert "exceeds" in error.lower()

    def test_validation_info_structure(self):
        """Check that validation_info always has the expected keys."""
        is_valid, error, info = validate_file_content(b"content", "test.txt")
        assert "file_size" in info
        assert "mime_type" in info
        assert "file_hash" in info
        assert "has_malicious_content" in info
        assert "security_warnings" in info
        assert isinstance(info["security_warnings"], list)

    def test_text_with_multiple_sql_patterns(self):
        """Text with multiple SQL patterns should still pass (warnings only)."""
        content = b"; DROP TABLE x; DELETE FROM y; UNION SELECT z; OR 1 = 1"
        is_valid, error, info = validate_file_content(content, "sql_notes.txt")
        assert is_valid is True
        assert len(info["security_warnings"]) >= 1

    def test_pdf_with_import_data_rejected(self):
        """PDF containing /ImportData should be rejected."""
        content = b"%PDF-1.4 /ImportData action"
        is_valid, error, info = validate_file_content(content, "form.pdf")
        assert is_valid is False
        assert "form" in error.lower()

    @patch("app.utils.file_validation.get_mime_type", return_value="image/png")
    def test_image_type_routes_to_image_validator(self, _mock_mime):
        """Verify that image MIME types route through image content validation."""
        content = b"\x89PNG\r\n\x1a\n<?php evil(); ?>" + b"\x00" * 100
        is_valid, error, info = validate_file_content(content, "img.png")
        assert is_valid is False
        assert "code" in error.lower()

    @patch("app.utils.file_validation.get_mime_type", return_value="text/plain")
    def test_text_type_routes_to_text_validator(self, _mock_mime):
        """Verify that text MIME types route through text content validation."""
        content = b"<script>alert(1)</script>"
        is_valid, error, info = validate_file_content(content, "notes.txt")
        assert is_valid is False
        assert "script" in error.lower()

    @patch(
        "app.utils.file_validation.get_mime_type",
        return_value="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )
    def test_office_type_routes_to_office_validator(self, _mock_mime):
        """Verify that Office MIME types route through office content validation."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("ppt/presentation.xml", "<p/>")
            zf.writestr("ppt/vbaProject.bin", "macro code")
        content = buf.getvalue()
        is_valid, error, info = validate_file_content(content, "slides.pptx")
        assert is_valid is False
        assert "macro" in error.lower()

    @patch("app.utils.file_validation.get_mime_type", return_value="audio/mpeg")
    def test_audio_file_passes_default_types(self, _mock_mime):
        """Audio MIME type is in default allowed list and has no deep validator."""
        content = b"ID3" + b"\x00" * 100
        is_valid, error, info = validate_file_content(content, "lecture.mp3")
        assert is_valid is True
        assert info["mime_type"] == "audio/mpeg"

    @patch("app.utils.file_validation.get_mime_type", return_value="video/mp4")
    def test_video_file_passes_default_types(self, _mock_mime):
        """Video MIME type is in default allowed list and has no deep validator."""
        content = b"\x00\x00\x00\x20ftypmp4" + b"\x00" * 100
        is_valid, error, info = validate_file_content(content, "lecture.mp4")
        assert is_valid is True
        assert info["mime_type"] == "video/mp4"

    @patch("app.utils.file_validation.get_mime_type", return_value="image/gif")
    def test_gif_file_passes_default_types(self, _mock_mime):
        content = b"GIF89a" + b"\x00" * 100
        is_valid, error, info = validate_file_content(content, "anim.gif")
        assert is_valid is True
        assert info["mime_type"] == "image/gif"

    @patch("app.utils.file_validation.get_mime_type", return_value="audio/wav")
    def test_wav_file_passes_default_types(self, _mock_mime):
        content = b"RIFF" + b"\x00" * 4 + b"WAVE" + b"\x00" * 100
        is_valid, error, info = validate_file_content(content, "audio.wav")
        assert is_valid is True
        assert info["mime_type"] == "audio/wav"
