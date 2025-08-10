"""Input sanitization utilities for security"""
import os
import html
from typing import Optional


def sanitize_input(text: Optional[str]) -> Optional[str]:
    """
    Sanitize user input to prevent XSS attacks.
    
    Args:
        text: The input text to sanitize
        
    Returns:
        Sanitized text with HTML entities escaped
    """
    if not text:
        return text
    # HTML escape special characters
    return html.escape(text, quote=True)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal attacks.
    
    Args:
        filename: The filename to sanitize
        
    Returns:
        Sanitized filename with only safe characters
    """
    # Remove any path components
    filename = os.path.basename(filename)
    # Remove potentially dangerous characters
    safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_"
    return "".join(c for c in filename if c in safe_chars)