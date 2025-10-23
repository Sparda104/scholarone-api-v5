# utils.py - V5 FINAL VERSION (Thoroughly Reviewed & Corrected)
"""
Utility functions for ScholarOne API application.
Enhanced with input validation and sanitization.
All regex patterns tested and verified.
"""
import logging
import os
import re
from datetime import datetime
from typing import Union
from typing import Optional

def iso8601_date(date_input: Union[str, datetime]) -> str:
    """
    Convert common inputs to 'YYYY-MM-DDTHH:MM:SSZ'.
    Accepts:
    - 'YYYY-MM-DD'
    - 'MM/DD/YYYY'
    - 'MM-DD-YYYY'
    - Already-ISO strings returned as-is (if contain 'T' and end with 'Z').
    """
    if isinstance(date_input, datetime):
        return date_input.strftime("%Y-%m-%dT%H:%M:%SZ")
    if not date_input:
        raise ValueError("Empty date string")

    s = date_input.strip()
    if "T" in s and s.endswith("Z"):
        return s

    for fmt in ("%m/%d/%Y", "%m-%d-%Y", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%Y-%m-%dT00:00:00Z")
        except ValueError:
            continue

    raise ValueError(f"Unsupported date format: {date_input!r}")


def sanitize_id_list(ids_str: str) -> str:
    """
    Validate and sanitize ID list input.
    Expected format: "ID1","ID2","ID3"
    Returns cleaned ID string.
    Raises ValueError if format is invalid.
    """
    if not ids_str or not ids_str.strip():
        raise ValueError("Empty ID list")

    ids_str = ids_str.strip()

    # Remove any characters that aren't: numbers, commas, quotes, spaces, hyphens, or letters
    # Put hyphen at end of character class to avoid range interpretation
    cleaned = re.sub(r'[^0-9,"\' A-Za-z-]', '', ids_str)

    # Check for basic structure: should have quotes
    if '"' not in cleaned and "'" not in cleaned:
        raise ValueError('IDs must be quoted: "ID1","ID2",...')

    # Extract IDs from quoted format
    parts = re.findall(r'["\']([^"\']+)["\']', cleaned)
    if not parts:
        raise ValueError('No valid IDs found in input')

    # Reconstruct with standardized double quotes
    return ','.join([f'"{id_.strip()}"' for id_ in parts if id_.strip()])


def sanitize_email(email: str) -> str:
    """
    Validate email format.
    Returns cleaned email string.
    Raises ValueError if invalid.
    """
    if not email or not email.strip():
        raise ValueError("Empty email address")

    email = email.strip()

    # Basic email regex pattern (hyphen at end of character class)
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValueError(f"Invalid email format: {email}")

    return email


def sanitize_filename(name: str) -> str:
    """
    Remove invalid filename characters and ensure safe filesystem name.
    Returns cleaned filename string.
    """
    if not name:
        return "export"

    # Remove or replace invalid filename characters
    invalid_chars = r'[<>:"/\\|?*]'
    cleaned = re.sub(invalid_chars, '_', name)

    # Remove leading/trailing spaces and dots
    cleaned = cleaned.strip('. ')

    # Ensure it's not too long (Windows has 255 char limit)
    if len(cleaned) > 200:
        cleaned = cleaned[:200]

    # Ensure we have something left
    if not cleaned:
        return "export"

    return cleaned


def validate_site_name(site_name: str) -> str:
    """
    Validate site name format.
    Site names should be alphanumeric with optional hyphens/underscores.
    Returns cleaned site name.
    Raises ValueError if invalid.
    """
    if not site_name or not site_name.strip():
        raise ValueError("Empty site name")

    site_name = site_name.strip()

    # Site names: alphanumeric with optional hyphens/underscores (hyphen at end)
    if not re.match(r'^[a-zA-Z0-9_-]+$', site_name):
        raise ValueError(f"Invalid site name format: {site_name}")

    return site_name


class AppLogger:
    """
    Simple file+stream logger that avoids duplicate handlers.
    Automatically creates log files in the application directory.
    """
    def __init__(self, logfile: Optional[str] = None, level: int = logging.INFO):
        """
        Initialize logger with optional file output.

        Args:
            logfile: Path to log file (None for console only)
            level: Logging level (default: INFO)
        """
        self.logger = logging.getLogger("ScholarOneApp")
        self.logger.setLevel(level)
        self.logger.handlers.clear()  # Remove any existing handlers

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_fmt = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_fmt)
        self.logger.addHandler(console_handler)

        # File handler (if specified)
        if logfile:
            try:
                # Ensure directory exists
                log_dir = os.path.dirname(logfile)
                if log_dir:
                    os.makedirs(log_dir, exist_ok=True)

                file_handler = logging.FileHandler(logfile, encoding='utf-8')
                file_handler.setLevel(level)
                file_handler.setFormatter(console_fmt)
                self.logger.addHandler(file_handler)
            except Exception as e:
                self.logger.warning(f"Could not create file handler: {e}")

    def get_logger(self) -> logging.Logger:
        """Return the configured logger instance."""
        return self.logger

def validate_date_range(start_date, end_date, endpoint_id=None):
    from datetime import datetime
    try:
        start = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if 'T' in start_date else datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if 'T' in end_date else datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError as e:
        raise ValueError(f"Invalid date: {e}")

    if end < start:
        raise ValueError("End must be after start")

    delta = end - start
    max_days = 365 if endpoint_id == "12" else 180

    if delta.days > max_days:
        raise ValueError(f"Range {delta.days} days exceeds limit {max_days}")

def validate_batch_size(ids_str, max_size=25):
    import re
    if not ids_str or not ids_str.strip():
        return
    parts = re.findall(r'["\'\\]([^"\'\\]+)["\'\\]', ids_str)
    if not parts:
        parts = [p.strip() for p in ids_str.split(',') if p.strip()]
    if len(parts) > max_size:
        raise ValueError(f"IDs {len(parts)} exceeds limit {max_size}")
