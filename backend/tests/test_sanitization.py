"""Tests for input sanitization utilities."""

import pytest
from app.utils.sanitization import sanitize_input, sanitize_filename


class TestSanitizeInput:
    def test_none_returns_none(self):
        assert sanitize_input(None) is None

    def test_empty_string_returns_empty(self):
        assert sanitize_input("") == ""

    def test_plain_text_unchanged(self):
        assert sanitize_input("Hello world") == "Hello world"

    def test_html_tags_escaped(self):
        assert (
            sanitize_input("<script>alert('xss')</script>")
            == "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"
        )

    def test_ampersand_escaped(self):
        assert sanitize_input("A & B") == "A &amp; B"

    def test_quotes_escaped(self):
        result = sanitize_input('He said "hello"')
        assert "&quot;" in result

    def test_single_quotes_escaped(self):
        result = sanitize_input("It's a test")
        assert "&#x27;" in result

    def test_angle_brackets_escaped(self):
        assert "&lt;" in sanitize_input("<div>")
        assert "&gt;" in sanitize_input("</div>")


class TestSanitizeFilename:
    def test_simple_filename(self):
        assert sanitize_filename("document.pdf") == "document.pdf"

    def test_removes_path_traversal(self):
        assert sanitize_filename("../../etc/passwd") == "passwd"

    def test_removes_absolute_path(self):
        assert sanitize_filename("/etc/passwd") == "passwd"

    def test_removes_windows_path(self):
        import sys

        result = sanitize_filename("C:\\Users\\test\\file.txt")
        if sys.platform == "win32":
            assert result == "file.txt"
        else:
            # On Linux, os.path.basename doesn't split on backslash
            # The backslashes get stripped by the safe_chars filter
            assert "file.txt" in result

    def test_removes_special_characters(self):
        result = sanitize_filename("file name (1).pdf")
        assert " " not in result
        assert "(" not in result
        assert ")" not in result

    def test_preserves_safe_characters(self):
        assert sanitize_filename("my-file_v2.txt") == "my-file_v2.txt"

    def test_preserves_dots_dashes_underscores(self):
        assert sanitize_filename("a.b-c_d") == "a.b-c_d"

    def test_empty_after_sanitization(self):
        assert sanitize_filename("!!!") == "unnamed_file"

    def test_traversal_after_sanitization(self):
        assert sanitize_filename("..") == "unnamed_file"
        assert sanitize_filename("...") == "unnamed_file"
        assert sanitize_filename(".") == "unnamed_file"

    def test_extension_preserved_with_leading_dots(self):
        assert sanitize_filename("....pdf") == ".pdf"
        assert sanitize_filename(".hidden.txt") == ".hidden.txt"

    def test_unicode_stripped(self):
        result = sanitize_filename("resume\u0301.pdf")
        assert "\u0301" not in result
