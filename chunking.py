"""
chunking.py - Auto-Chunking Module for V5.1
============================================

Handles automatic date range chunking when API returns S1-705 "too many results" error.

Standing Order #11: Zero-config user experience
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Callable

logger = logging.getLogger(__name__)


def _split_date_range(start_date: datetime, end_date: datetime) -> Tuple[Tuple[datetime, datetime], Tuple[datetime, datetime]]:
    """
    Split a date range into two equal halves.

    Args:
        start_date: Range start
        end_date: Range end

    Returns:
        Two tuples: (first_half_start, first_half_end), (second_half_start, second_half_end)

    Example:
        >>> start = datetime(2025, 1, 1)
        >>> end = datetime(2025, 12, 31)
        >>> first, second = _split_date_range(start, end)
        >>> # first: (2025-01-01, 2025-07-01), second: (2025-07-02, 2025-12-31)
    """
    total_days = (end_date - start_date).days
    mid_days = total_days // 2

    mid_date = start_date + timedelta(days=mid_days)

    # First half: start to midpoint (inclusive)
    first_half = (start_date, mid_date)

    # Second half: midpoint+1 to end
    second_half = (mid_date + timedelta(days=1), end_date)

    return first_half, second_half


def _is_too_many_results_error(error_response: Dict) -> bool:
    """
    Detect S1-705 "Too many results" error.

    Args:
        error_response: API error response dict

    Returns:
        True if this is a "too many results" error (S1-705)

    Example:
        >>> error = {
        ...     'Response': {
        ...         'errorDetails': {
        ...             'moreInfo': {
        ...                 'errors': {
        ...                     'errorCode': 705,
        ...                     'errorMessage': 'Too many results'
        ...                 }
        ...             }
        ...         }
        ...     }
        ... }
        >>> _is_too_many_results_error(error)
        True
    """
    try:
        if isinstance(error_response, dict):
            # Check for S1-705 error code
            error_details = error_response.get('Response', {}).get('errorDetails', {})
            more_info = error_details.get('moreInfo', {})
            errors = more_info.get('errors', {})
            error_code = errors.get('errorCode')
            error_msg = errors.get('errorMessage', '').lower()

            # S1-705 or "too many results" message
            if error_code == 705 or 'too many results' in error_msg:
                return True
    except Exception as e:
        logger.debug(f"Error checking for S1-705: {e}")

    return False


def fetch_with_auto_chunking(
    api_caller: Callable,
    site_name: str,
    start_date: datetime,
    end_date: datetime,
    max_depth: int = 10,
    current_depth: int = 0,
    progress_callback: Optional[Callable] = None
) -> List[Dict]:
    """
    Fetch data with automatic date range chunking if "too many results" error.

    This is a recursive function that:
    1. Tries to fetch data for given date range
    2. If S1-705 error, splits range in half and retries both halves
    3. Merges results from all successful chunks
    4. Handles edge cases (single day ranges, max recursion)

    Args:
        api_caller: Function that makes API call (site, start, end) -> (success, data_or_error)
        site_name: Site to query
        start_date: Range start
        end_date: Range end
        max_depth: Maximum recursion depth (safety limit)
        current_depth: Current recursion level
        progress_callback: Optional callback for progress updates

    Returns:
        List of records (merged from all chunks)

    Example:
        >>> def my_api_caller(site, start, end):
        ...     # Make API call
        ...     return (success, records_or_error)
        >>> 
        >>> records = fetch_with_auto_chunking(
        ...     my_api_caller, 
        ...     'ijoc', 
        ...     datetime(2025, 1, 1), 
        ...     datetime(2025, 12, 31)
        ... )
    """
    # Safety: Check recursion depth
    if current_depth >= max_depth:
        logger.error(f"Max chunking depth ({max_depth}) reached for {site_name}. Date range may be too large.")
        return []

    # Calculate range info for logging
    days = (end_date - start_date).days + 1
    date_str = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} ({days} days)"

    indent = "  " * current_depth
    logger.info(f"{indent}[Chunk] Trying {site_name}: {date_str}")

    # Call progress callback if provided
    if progress_callback:
        progress_callback(f"Chunking {site_name}: {date_str}")

    # Try to fetch data for this date range
    try:
        success, result = api_caller(site_name, start_date, end_date)

        if success:
            # Success! Return the records
            record_count = len(result) if isinstance(result, list) else 0
            logger.info(f"{indent}[Chunk] ✓ Success: {record_count} records")
            return result if isinstance(result, list) else []

        # Check if this is a "too many results" error
        if _is_too_many_results_error(result):
            # S1-705 detected - need to chunk
            logger.info(f"{indent}[Chunk] S1-705 detected - splitting range...")

            # Edge case: Can't split single-day range
            if days <= 1:
                logger.warning(f"{indent}[Chunk] Can't split single-day range. Skipping {site_name}.")
                return []

            # Split the date range
            first_half, second_half = _split_date_range(start_date, end_date)

            # Recursively fetch both halves
            logger.info(f"{indent}[Chunk] Splitting into 2 chunks...")
            first_results = fetch_with_auto_chunking(
                api_caller, site_name, first_half[0], first_half[1],
                max_depth, current_depth + 1, progress_callback
            )
            second_results = fetch_with_auto_chunking(
                api_caller, site_name, second_half[0], second_half[1],
                max_depth, current_depth + 1, progress_callback
            )

            # Merge results
            merged = first_results + second_results
            logger.info(f"{indent}[Chunk] Merged: {len(merged)} total records")
            return merged

        else:
            # Different error (not S1-705) - don't chunk, just fail
            logger.error(f"{indent}[Chunk] Non-705 error - not chunking")
            return []

    except Exception as e:
        logger.error(f"{indent}[Chunk] Exception: {e}")
        return []


def load_chunking_config(config: Dict) -> Dict:
    """
    Load auto-chunking configuration from config dict.

    Args:
        config: Configuration dictionary

    Returns:
        Dict with chunking configuration

    Default values:
        {
            'enabled': True,
            'max_depth': 10,
            'min_chunk_days': 1,
            'show_progress': True
        }
    """
    defaults = {
        'enabled': True,
        'max_depth': 10,
        'min_chunk_days': 1,
        'show_progress': True
    }

    if 'api' in config and 'auto_chunking' in config['api']:
        return {**defaults, **config['api']['auto_chunking']}

    return defaults


# Module version
__version__ = '5.1.0'
__author__ = 'Chris Asher'
__description__ = 'Auto-chunking for ScholarOne API S1-705 errors'
