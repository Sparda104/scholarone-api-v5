"""
chunking_v51.py - Auto-Chunking Module for V5.1 (CORRECTED)
============================================================

Handles automatic date range chunking when API returns S1-705 "too many results" error.

CRITICAL FIXES APPLIED:
- Rate limiting: time.sleep(1.5) between recursive calls
- Shared logger: accepts logger parameter
- Cancellation: supports cancel_flag
- Progress: supports progress_callback

Standing Order #11: Zero-config user experience
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Callable
from threading import Event

# Default logger
_default_logger = logging.getLogger(__name__)


def _split_date_range(start_date: datetime, end_date: datetime) -> Tuple[Tuple[datetime, datetime], Tuple[datetime, datetime]]:
    """
    Split a date range into two equal halves.

    Args:
        start_date: Range start
        end_date: Range end

    Returns:
        Two tuples: (first_half_start, first_half_end), (second_half_start, second_half_end)
    """
    total_days = (end_date - start_date).days
    mid_days = total_days // 2
    mid_date = start_date + timedelta(days=mid_days)

    first_half = (start_date, mid_date)
    second_half = (mid_date + timedelta(days=1), end_date)

    return first_half, second_half


def _is_too_many_results_error(error_response: Dict) -> bool:
    """
    Detect S1-705 "Too many results" error.

    Args:
        error_response: API error response dict

    Returns:
        True if this is a "too many results" error (S1-705)
    """
    try:
        if isinstance(error_response, dict):
            error_details = error_response.get('Response', {}).get('errorDetails', {})
            more_info = error_details.get('moreInfo', {})
            errors = more_info.get('errors', {})
            error_code = errors.get('errorCode')
            error_msg = errors.get('errorMessage', '').lower()

            if error_code == 705 or 'too many results' in error_msg:
                return True
    except Exception:
        pass

    return False


def fetch_with_auto_chunking(
    api_caller: Callable,
    site_name: str,
    start_date: datetime,
    end_date: datetime,
    max_depth: int = 10,
    current_depth: int = 0,
    progress_callback: Optional[Callable] = None,
    logger = None,
    cancel_flag: Optional[Event] = None,
    rate_limit_delay: float = 1.5
) -> List[Dict]:
    """
    Fetch data with automatic date range chunking if "too many results" error.

    CRITICAL FIXES APPLIED:
    - Rate limiting: time.sleep() between recursive calls
    - Logger: shared logger support
    - Cancellation: check cancel_flag
    - Progress: callback for UI updates

    Args:
        api_caller: Function that makes API call (site, start, end) -> (success, data_or_error)
        site_name: Site to query
        start_date: Range start
        end_date: Range end
        max_depth: Maximum recursion depth (safety limit)
        current_depth: Current recursion level
        progress_callback: Optional callback for progress updates
        logger: Optional logger (uses default if None)
        cancel_flag: Optional threading.Event for cancellation
        rate_limit_delay: Seconds to wait between chunks (default 1.5)

    Returns:
        List of records (merged from all chunks)
    """
    # Use provided logger or default
    log = logger if logger else _default_logger

    # CRITICAL FIX #1: Check cancellation
    if cancel_flag and cancel_flag.is_set():
        log.info("[Chunk] Cancelled by user")
        return []

    # Safety: Check recursion depth
    if current_depth >= max_depth:
        log.error(f"[Chunk] Max depth ({max_depth}) reached for {site_name}")
        return []

    # Calculate range info for logging
    days = (end_date - start_date).days + 1
    date_str = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} ({days} days)"

    indent = "  " * current_depth
    log.info(f"{indent}[Chunk] Trying {site_name}: {date_str}")

    # Call progress callback if provided
    if progress_callback:
        progress_callback(f"Chunking {site_name}: {date_str}")

    # Try to fetch data for this date range
    try:
        success, result = api_caller(site_name, start_date, end_date)

        if success:
            # Success! Return the records
            record_count = len(result) if isinstance(result, list) else 0
            log.info(f"{indent}[Chunk] ✓ Success: {record_count} records")
            return result if isinstance(result, list) else []

        # Check if this is a "too many results" error
        if _is_too_many_results_error(result):
            # S1-705 detected - need to chunk
            log.info(f"{indent}[Chunk] S1-705 detected - splitting range...")

            # Edge case: Can't split single-day range
            if days <= 1:
                log.warning(f"{indent}[Chunk] Can't split single-day range")
                return []

            # Split the date range
            first_half, second_half = _split_date_range(start_date, end_date)

            log.info(f"{indent}[Chunk] Splitting into 2 chunks...")

            # Recursively fetch first half
            first_results = fetch_with_auto_chunking(
                api_caller, site_name, first_half[0], first_half[1],
                max_depth, current_depth + 1, progress_callback,
                logger, cancel_flag, rate_limit_delay
            )

            # CRITICAL FIX #2: Rate limiting between chunks!
            if first_results:  # Only wait if we got results
                time.sleep(rate_limit_delay)
                log.debug(f"{indent}[Chunk] Rate limit delay: {rate_limit_delay}s")

            # Check cancellation before second half
            if cancel_flag and cancel_flag.is_set():
                log.info(f"{indent}[Chunk] Cancelled before second chunk")
                return first_results

            # Recursively fetch second half AFTER delay
            second_results = fetch_with_auto_chunking(
                api_caller, site_name, second_half[0], second_half[1],
                max_depth, current_depth + 1, progress_callback,
                logger, cancel_flag, rate_limit_delay
            )

            # Merge results
            merged = first_results + second_results
            log.info(f"{indent}[Chunk] Merged: {len(merged)} total records")
            return merged

        else:
            # Different error (not S1-705) - don't chunk
            log.error(f"{indent}[Chunk] Non-705 error - not chunking")
            return []

    except Exception as e:
        log.error(f"{indent}[Chunk] Exception: {e}")
        return []


def load_chunking_config(config: Dict) -> Dict:
    """
    Load auto-chunking configuration from config dict.

    Args:
        config: Configuration dictionary

    Returns:
        Dict with chunking configuration
    """
    defaults = {
        'enabled': True,
        'max_depth': 10,
        'min_chunk_days': 1,
        'show_progress': True,
        'rate_limit_delay': 1.5  # CRITICAL for API compliance
    }

    if 'api' in config and 'auto_chunking' in config['api']:
        return {**defaults, **config['api']['auto_chunking']}

    return defaults


# Module metadata
__version__ = '5.1.0'
__author__ = 'Chris Asher'
__description__ = 'Auto-chunking for ScholarOne API S1-705 errors (CORRECTED)'
