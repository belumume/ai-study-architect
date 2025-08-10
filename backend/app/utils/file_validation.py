"""Enhanced file validation utilities with deep content validation and security checks"""
import sys
import logging
import hashlib
import zipfile
import io
from typing import Tuple, Dict, Optional, List
import re

logger = logging.getLogger(__name__)

# Import magic with fallback for different installations
try:
    import magic
    
    def get_mime_type(file_content: bytes) -> str:
        """Get MIME type from file content"""
        try:
            mime = magic.Magic(mime=True)
            return mime.from_buffer(file_content)
        except Exception as e:
            logger.error(f"Error detecting MIME type: {e}")
            # Fallback to basic detection
            return _basic_mime_detection(file_content)
            
except ImportError:
    logger.warning("python-magic not available, using basic MIME detection")
    
    def get_mime_type(file_content: bytes) -> str:
        """Fallback MIME type detection without python-magic"""
        return _basic_mime_detection(file_content)


def _basic_mime_detection(content: bytes) -> str:
    """
    Basic MIME type detection based on file signatures.
    
    Args:
        content: The first few bytes of file content
        
    Returns:
        str: The detected MIME type or 'application/octet-stream' if unknown
    """
    # Common file signatures
    signatures = {
        b'%PDF': 'application/pdf',
        b'\x50\x4B\x03\x04': 'application/zip',  # Also covers docx, pptx
        b'\x50\x4B\x05\x06': 'application/zip',
        b'\x50\x4B\x07\x08': 'application/zip',
        b'\xFF\xD8\xFF': 'image/jpeg',
        b'\x89PNG\r\n\x1a\n': 'image/png',
        b'GIF87a': 'image/gif',
        b'GIF89a': 'image/gif',
        b'ID3': 'audio/mpeg',  # MP3 with ID3
        b'\xFF\xFB': 'audio/mpeg',  # MP3
        b'\xFF\xF3': 'audio/mpeg',  # MP3
        b'\xFF\xF2': 'audio/mpeg',  # MP3
        b'RIFF': 'audio/wav',  # Also could be AVI
        b'\x00\x00\x00\x20ftypmp4': 'video/mp4',
        b'\x00\x00\x00\x18ftypmp4': 'video/mp4',
        b'\x00\x00\x00\x1Cftypmp4': 'video/mp4',
    }
    
    # Check signatures
    for sig, mime_type in signatures.items():
        if content.startswith(sig):
            # Special handling for Office files
            if mime_type == 'application/zip' and len(content) > 30:
                # Check for Office Open XML signatures
                if b'word/' in content[:1000]:
                    return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                elif b'ppt/' in content[:1000]:
                    return 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
                elif b'xl/' in content[:1000]:
                    return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            
            # Special handling for RIFF files
            if sig == b'RIFF' and len(content) > 12:
                if content[8:12] == b'WAVE':
                    return 'audio/wav'
                elif content[8:12] == b'AVI ':
                    return 'video/x-msvideo'
            
            return mime_type
    
    # Check if it's plain text
    try:
        content[:1000].decode('utf-8')
        # Check for markdown
        if any(marker in content[:100] for marker in [b'#', b'##', b'```', b'[', b'](']):
            return 'text/markdown'
        return 'text/plain'
    except:
        pass
    
    # Default
    return 'application/octet-stream'


def validate_file_content(
    file_content: bytes,
    file_name: str,
    allowed_mime_types: Optional[List[str]] = None,
    max_file_size: int = 50 * 1024 * 1024  # 50MB default
) -> Tuple[bool, str, Dict[str, any]]:
    """
    Perform deep file content validation with security checks.
    
    Args:
        file_content: The file content as bytes
        file_name: The original filename
        allowed_mime_types: List of allowed MIME types (None allows all safe types)
        max_file_size: Maximum allowed file size in bytes
        
    Returns:
        Tuple of (is_valid, error_message, validation_info)
    """
    validation_info = {
        "file_size": len(file_content),
        "mime_type": None,
        "file_hash": None,
        "has_malicious_content": False,
        "security_warnings": []
    }
    
    # Check file size
    if len(file_content) > max_file_size:
        return False, f"File exceeds maximum size of {max_file_size/1024/1024:.1f}MB", validation_info
    
    if len(file_content) == 0:
        return False, "Empty file", validation_info
    
    # Get MIME type
    mime_type = get_mime_type(file_content)
    validation_info["mime_type"] = mime_type
    
    # Default allowed types if not specified
    if allowed_mime_types is None:
        allowed_mime_types = [
            'application/pdf',
            'text/plain',
            'text/markdown',
            'image/jpeg',
            'image/png',
            'image/gif',
            'audio/mpeg',
            'audio/wav',
            'video/mp4',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ]
    
    # Check if MIME type is allowed
    if mime_type not in allowed_mime_types:
        return False, f"File type '{mime_type}' not allowed", validation_info
    
    # Calculate file hash
    validation_info["file_hash"] = hashlib.sha256(file_content).hexdigest()
    
    # Perform deep content validation based on file type
    if mime_type == 'application/pdf':
        is_valid, error = _validate_pdf_content(file_content, validation_info)
        if not is_valid:
            return False, error, validation_info
            
    elif mime_type.startswith('image/'):
        is_valid, error = _validate_image_content(file_content, mime_type, validation_info)
        if not is_valid:
            return False, error, validation_info
            
    elif mime_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                       'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                       'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
        is_valid, error = _validate_office_content(file_content, mime_type, validation_info)
        if not is_valid:
            return False, error, validation_info
            
    elif mime_type.startswith('text/'):
        is_valid, error = _validate_text_content(file_content, validation_info)
        if not is_valid:
            return False, error, validation_info
    
    # Check filename for suspicious patterns
    if _has_suspicious_filename(file_name):
        validation_info["security_warnings"].append("Suspicious filename pattern detected")
    
    # Final malware pattern check
    if _contains_malware_patterns(file_content):
        validation_info["has_malicious_content"] = True
        return False, "File contains potentially malicious patterns", validation_info
    
    return True, "", validation_info


def _validate_pdf_content(content: bytes, validation_info: Dict) -> Tuple[bool, str]:
    """Validate PDF file content for security issues."""
    # Check for embedded JavaScript
    if b'/JavaScript' in content or b'/JS' in content:
        validation_info["security_warnings"].append("PDF contains JavaScript")
        return False, "PDF files with embedded JavaScript are not allowed"
    
    # Check for embedded files
    if b'/EmbeddedFile' in content:
        validation_info["security_warnings"].append("PDF contains embedded files")
        return False, "PDF files with embedded files are not allowed"
    
    # Check for launch actions
    if b'/Launch' in content:
        validation_info["security_warnings"].append("PDF contains launch actions")
        return False, "PDF files with launch actions are not allowed"
    
    # Check for suspicious form actions
    if b'/SubmitForm' in content or b'/ImportData' in content:
        validation_info["security_warnings"].append("PDF contains form actions")
        return False, "PDF files with form submission actions are not allowed"
    
    return True, ""


def _validate_image_content(content: bytes, mime_type: str, validation_info: Dict) -> Tuple[bool, str]:
    """Validate image file content for security issues."""
    # Check for embedded PHP in images
    if b'<?php' in content:
        validation_info["security_warnings"].append("Image contains PHP code")
        return False, "Image files with embedded code are not allowed"
    
    # Check for EXIF data that might contain malicious payloads
    if mime_type == 'image/jpeg' and b'Exif' in content[:100]:
        # Look for suspicious EXIF patterns
        if b'<script' in content or b'javascript:' in content:
            validation_info["security_warnings"].append("Image EXIF contains suspicious data")
            return False, "Image files with suspicious EXIF data are not allowed"
    
    return True, ""


def _validate_office_content(content: bytes, mime_type: str, validation_info: Dict) -> Tuple[bool, str]:
    """Validate Office document content for security issues."""
    try:
        # Office files are ZIP archives
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            # Check for macros
            for name in zf.namelist():
                if 'macros' in name.lower() or name.endswith('.bin'):
                    validation_info["security_warnings"].append("Document contains macros")
                    return False, "Office documents with macros are not allowed"
                
                # Check for external relationships
                if 'external' in name.lower():
                    validation_info["security_warnings"].append("Document contains external references")
                    # This is a warning, not a block
            
            # Check file contents for suspicious patterns
            for name in zf.namelist():
                if name.endswith('.xml') or name.endswith('.rels'):
                    try:
                        file_content = zf.read(name)
                        if b'<script' in file_content or b'javascript:' in file_content:
                            validation_info["security_warnings"].append("Document contains script references")
                            return False, "Office documents with embedded scripts are not allowed"
                    except:
                        pass
                        
    except zipfile.BadZipFile:
        return False, "Invalid Office document format"
    except Exception as e:
        logger.error(f"Error validating Office document: {e}")
        return False, "Unable to validate Office document"
    
    return True, ""


def _validate_text_content(content: bytes, validation_info: Dict) -> Tuple[bool, str]:
    """Validate text file content for security issues."""
    try:
        # Try to decode as text
        text = content.decode('utf-8', errors='ignore')
        
        # Check for script injections
        script_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'onerror\s*=',
            r'onclick\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>'
        ]
        
        for pattern in script_patterns:
            if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
                validation_info["security_warnings"].append(f"Text contains suspicious pattern: {pattern}")
                return False, "Text files with embedded scripts are not allowed"
        
        # Check for SQL injection patterns
        sql_patterns = [
            r';\s*DROP\s+TABLE',
            r';\s*DELETE\s+FROM',
            r'UNION\s+SELECT',
            r'OR\s+1\s*=\s*1'
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                validation_info["security_warnings"].append("Text contains SQL injection patterns")
                # This is a warning, not necessarily a block
                
    except UnicodeDecodeError:
        return False, "Invalid text encoding"
    
    return True, ""


def _has_suspicious_filename(filename: str) -> bool:
    """Check if filename has suspicious patterns."""
    suspicious_patterns = [
        r'\.php\.',  # Double extension with PHP
        r'\.exe\.',  # Double extension with EXE
        r'\.scr\.',  # Screensaver files
        r'\.vbs\.',  # VBScript files
        r'\.js\.',   # JavaScript files with double extension
        r'\.\.',     # Directory traversal
        r'[<>:"|?*]',  # Invalid filename characters
        r'^\.',      # Hidden files
        r'\.ht',     # .htaccess or .htpasswd
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, filename, re.IGNORECASE):
            return True
            
    return False


def _contains_malware_patterns(content: bytes) -> bool:
    """Check for common malware patterns in file content."""
    # Common malware signatures (simplified)
    malware_patterns = [
        b'EICAR-STANDARD-ANTIVIRUS-TEST-FILE',  # EICAR test string
        b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR',  # EICAR pattern
        b'WScript.Shell',  # Windows Script Host
        b'Shell.Application',  # Shell execution
        b'powershell -enc',  # Encoded PowerShell
        b'cmd /c',  # Command execution
        b'eval(unescape',  # JavaScript eval
        b'document.write(unescape',  # JavaScript injection
        b'\\x4d\\x5a',  # MZ header (PE executable)
    ]
    
    for pattern in malware_patterns:
        if pattern in content:
            return True
            
    return False


def calculate_file_hash(content: bytes, algorithm: str = 'sha256') -> str:
    """
    Calculate hash of file content.
    
    Args:
        content: File content as bytes
        algorithm: Hash algorithm to use ('sha256', 'sha1', 'md5')
        
    Returns:
        Hex string of the hash
    """
    if algorithm == 'sha256':
        return hashlib.sha256(content).hexdigest()
    elif algorithm == 'sha1':
        return hashlib.sha1(content).hexdigest()
    elif algorithm == 'md5':
        return hashlib.md5(content).hexdigest()
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")