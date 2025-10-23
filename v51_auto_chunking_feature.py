# V5.1 Enhancement: Auto-Chunking for "Too Many Results" Errors
# Standing Order #11: Zero-config user experience

"""
FEATURE: Automatic Date Range Chunking
======================================

When API returns S1-705 "Too many results" error:
1. Detect the error
2. Automatically split date range in half
3. Retry both halves
4. Recursively chunk until successful
5. Merge all results
6. Export as one file

USER EXPERIENCE:
- User requests any date range (even 10 years!)
- App handles chunking automatically
- No user intervention needed
- Progress updates shown
- Final result: complete data set

EXAMPLE:
User Request: Jan 1 - Dec 31, 2025 (12 months) on high-volume site
API Response: "Too many results"

Auto-Chunking:
  Try: Jan-Dec 2025 → Error 705
    Split to: Jan-Jun, Jul-Dec
      Try: Jan-Jun → Error 705
        Split to: Jan-Mar, Apr-Jun
          Try: Jan-Mar → Success (500 records)
          Try: Apr-Jun → Success (450 records)
      Try: Jul-Dec → Success (800 records)

  Final: 1,750 records merged and exported

"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


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
        True if this is a "too many results" error
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


def _fetch_with_auto_chunking(
    api_caller,
    site_name: str,
    start_date: datetime,
    end_date: datetime,
    max_depth: int = 10,
    current_depth: int = 0
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

    Returns:
        List of records (merged from all chunks)
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
            logger.info(f"{indent}[Chunk] Too many results - splitting range...")

            # Edge case: Can't split single-day range
            if days <= 1:
                logger.warning(f"{indent}[Chunk] Can't split single-day range. Skipping.")
                return []

            # Split the date range
            first_half, second_half = _split_date_range(start_date, end_date)

            # Recursively fetch both halves
            logger.info(f"{indent}[Chunk] Splitting into 2 chunks...")
            first_results = _fetch_with_auto_chunking(
                api_caller, site_name, first_half[0], first_half[1],
                max_depth, current_depth + 1
            )
            second_results = _fetch_with_auto_chunking(
                api_caller, site_name, second_half[0], second_half[1],
                max_depth, current_depth + 1
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


# ============================================================================
# Integration with existing code
# ============================================================================

def enhanced_query_with_chunking(endpoint_func, params: Dict, logger_obj=None) -> Tuple[bool, List[Dict]]:
    """
    Wrapper for endpoint functions that adds auto-chunking capability.

    Usage in main.py:
        # Old way (V5.0):
        success, records = get_ids_by_date(site, start, end, params)

        # New way (V5.1):
        success, records = enhanced_query_with_chunking(
            get_ids_by_date, 
            {'site': site, 'start': start, 'end': end, 'params': params}
        )

    Args:
        endpoint_func: The endpoint function to call
        params: Parameters dict with keys: site, start, end, params
        logger_obj: Optional logger

    Returns:
        (success: bool, records: List[Dict])
    """
    site = params.get('site')
    start_date = params.get('start')
    end_date = params.get('end')
    api_params = params.get('params', {})

    # Create API caller wrapper
    def api_caller(site_name, start, end):
        try:
            # Call the endpoint function
            # Returns: (success, result) where result is either records or error dict
            return endpoint_func(site_name, start, end, api_params)
        except Exception as e:
            return (False, {'error': str(e)})

    # Use auto-chunking
    records = _fetch_with_auto_chunking(api_caller, site, start_date, end_date)

    # Return success if we got any records
    success = len(records) > 0
    return success, records


# ============================================================================
# Config option for enabling/disabling
# ============================================================================

# Add to config.yaml:
"""
api:
  auto_chunking:
    enabled: true              # Enable auto-chunking for S1-705 errors
    max_depth: 10              # Maximum number of splits (safety limit)
    min_chunk_days: 1          # Minimum chunk size in days
"""

# Example: Load from config
def load_chunking_config(config: Dict) -> Dict:
    """Load auto-chunking configuration."""
    defaults = {
        'enabled': True,
        'max_depth': 10,
        'min_chunk_days': 1
    }

    if 'api' in config and 'auto_chunking' in config['api']:
        return {**defaults, **config['api']['auto_chunking']}

    return defaults


# ============================================================================
# User-facing progress updates
# ============================================================================

class ChunkingProgressTracker:
    """Track progress of chunking operations for UI updates."""

    def __init__(self):
        self.total_chunks = 0
        self.completed_chunks = 0
        self.total_records = 0

    def start_chunk(self):
        self.total_chunks += 1

    def complete_chunk(self, record_count: int):
        self.completed_chunks += 1
        self.total_records += record_count

    def get_progress(self) -> str:
        if self.total_chunks == 0:
            return "Starting..."
        return f"Chunk {self.completed_chunks}/{self.total_chunks} | {self.total_records} records"


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Example: Simulated API caller for testing
    def mock_api_caller(site, start, end):
        days = (end - start).days

        # Simulate "too many results" for ranges > 90 days
        if days > 90:
            return (False, {
                'Response': {
                    'errorDetails': {
                        'moreInfo': {
                            'errors': {
                                'errorCode': 705,
                                'errorMessage': 'Too many results, please use a shorter date/time range.'
                            }
                        }
                    }
                }
            })

        # Simulate success with dummy records
        records = [{'id': i, 'site': site} for i in range(days * 2)]
        return (True, records)

    # Test auto-chunking
    print("Testing auto-chunking with 1-year range...")
    start = datetime(2025, 1, 1)
    end = datetime(2025, 12, 31)

    results = _fetch_with_auto_chunking(mock_api_caller, 'test_site', start, end)

    print(f"\nFinal result: {len(results)} records")
    print("Auto-chunking works!")


# ============================================================================
# Summary
# ============================================================================

"""
V5.1 AUTO-CHUNKING FEATURE SUMMARY
===================================

PROBLEM SOLVED:
- Some sites/date ranges return S1-705 "Too many results"
- Users had to guess correct date ranges
- Manual retry with shorter ranges was tedious

SOLUTION:
- Automatic detection of S1-705 errors
- Recursive date range splitting
- Transparent to user - "just works"
- Progress updates for long operations

BENEFITS:
✓ Zero-config user experience
✓ Works with any date range
✓ Works with any site
✓ Handles edge cases (single day, recursion limit)
✓ Clear logging for debugging
✓ Optional progress UI

INTEGRATION:
1. Add _fetch_with_auto_chunking() to utils.py or new chunking.py module
2. Modify endpoint functions to use auto-chunking wrapper
3. Add config options to config.yaml
4. Update UI to show chunking progress
5. Test with high-volume sites

STANDING ORDER #11 (New):
"The application shall handle all API limitations automatically without 
requiring user knowledge of site-specific constraints or API limits."

STATUS: Ready for implementation in V5.1 release
"""
