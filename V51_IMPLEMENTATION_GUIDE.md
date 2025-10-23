# V5.1 Implementation Guide: Auto-Chunking Feature

**Feature:** Automatic Date Range Chunking for S1-705 Errors  
**Status:** Ready for Implementation  
**Complexity:** Medium  
**Time Estimate:** 2-3 hours  
**Standing Order:** #11 (Zero-config user experience)

---

## Overview

This feature eliminates the "too many results" error by automatically detecting S1-705 responses and splitting date ranges into smaller chunks until successful.

**User Experience:**
- User requests **any** date range (1 month, 1 year, 5 years, doesn't matter)
- App handles everything automatically
- User sees progress updates
- Final result: complete dataset in one Excel file

---

## Implementation Steps

### Step 1: Create chunking.py Module (New File)

Create `chunking.py` in your project directory with the auto-chunking functions.

**File:** `chunking.py`

```python
# Copy the code from v51_auto_chunking_feature.py
# Core functions needed:
#   - _split_date_range()
#   - _is_too_many_results_error()
#   - _fetch_with_auto_chunking()
```

**Test it:**
```cmd
python -c "import chunking; print('Chunking module OK')"
```

---

### Step 2: Modify utils.py

Add helper function to utils.py:

```python
# Add to utils.py

def detect_s1_705_error(response_data):
    """
    Check if response contains S1-705 'too many results' error.

    Args:
        response_data: API response dict

    Returns:
        bool: True if S1-705 error detected
    """
    try:
        if isinstance(response_data, dict):
            error_details = response_data.get('Response', {}).get('errorDetails', {})
            more_info = error_details.get('moreInfo', {})
            errors = more_info.get('errors', {})

            # Check for error code 705
            if errors.get('errorCode') == 705:
                return True

            # Check for "too many results" in message
            error_msg = errors.get('errorMessage', '').lower()
            if 'too many results' in error_msg:
                return True
    except:
        pass

    return False
```

---

### Step 3: Modify endpoints.py

Wrap endpoint functions with auto-chunking capability.

**Option A: Modify existing get_ids_by_date() function**

```python
# In endpoints.py

from chunking import _fetch_with_auto_chunking

def get_ids_by_date_with_chunking(site_name, start_date, end_date, params, config):
    """
    Get IDs by date with automatic chunking for S1-705 errors.

    This wraps the original get_ids_by_date with auto-chunking.
    """
    # Create API caller wrapper
    def api_caller(site, start, end):
        try:
            # Call original endpoint function
            url = f"https://mc-api.manuscriptcentral.com/api/s1m/v4/submissions/full/idsByDate"

            params_with_dates = {
                **params,
                'from_time': start.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'to_time': end.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'site_name': site,
                '_type': 'json'
            }

            # Make API call
            response = make_api_request('GET', url, params=params_with_dates)

            # Check response
            if response.status_code == 200:
                data = response.json()
                records = data.get('Response', {}).get('submissions', [])
                return (True, records)
            else:
                # Parse error
                error_data = response.json()
                return (False, error_data)

        except Exception as e:
            return (False, {'error': str(e)})

    # Use auto-chunking
    auto_chunk_enabled = config.get('api', {}).get('auto_chunking', {}).get('enabled', True)

    if auto_chunk_enabled:
        records = _fetch_with_auto_chunking(api_caller, site_name, start_date, end_date)
        return records
    else:
        # Fallback to single request (old behavior)
        success, result = api_caller(site_name, start_date, end_date)
        return result if success else []
```

**Option B: Add as new function (safer for initial testing)**

```python
# In endpoints.py

def get_ids_by_date_v51(site_name, start_date, end_date, params, config):
    """V5.1: With auto-chunking support."""
    # Same implementation as Option A
    pass

# Keep original get_ids_by_date() unchanged for now
```

---

### Step 4: Modify main.py

Update the main processing loop to use chunking.

**Find this section in main.py:**

```python
# Old V5.0 code:
success, records = get_ids_by_date(site, start_date, end_date, params)
```

**Replace with:**

```python
# New V5.1 code:
from chunking import _fetch_with_auto_chunking

def site_api_caller(site_name, start, end):
    """Wrapper for API calls with chunking support."""
    try:
        # Call endpoint function
        records = get_ids_by_date(site_name, start, end, params)
        return (True, records)
    except Exception as e:
        logger.error(f"API call failed: {e}")
        return (False, {'error': str(e)})

# Use auto-chunking
records = _fetch_with_auto_chunking(site_api_caller, site, start_date, end_date)
success = len(records) > 0
```

---

### Step 5: Update config.yaml.template

Add auto-chunking configuration:

```yaml
# config.yaml.template

api:
  rate_limit_delay: 1.5
  max_retries: 3

  # V5.1: Auto-chunking for "too many results" errors
  auto_chunking:
    enabled: true              # Automatically split date ranges on S1-705 errors
    max_depth: 10              # Maximum number of recursive splits (safety limit)
    min_chunk_days: 1          # Minimum chunk size in days
    show_progress: true        # Show chunking progress in console
```

---

### Step 6: Update GUI for Progress

Optional but recommended: Show chunking progress to user.

**In gui_widgets.py or main.py:**

```python
# Add progress callback to _fetch_with_auto_chunking()

def _fetch_with_auto_chunking_with_progress(
    api_caller,
    site_name,
    start_date,
    end_date,
    progress_callback=None
):
    # ... existing code ...

    # Before each chunk
    if progress_callback:
        progress_callback(f"Chunking {site_name}: {date_str}")

    # ... rest of code ...
```

**In main.py:**

```python
# Update progress label during chunking
def update_progress(message):
    print(f"[Chunking] {message}")
    # Or update GUI label if using tkinter

records = _fetch_with_auto_chunking_with_progress(
    site_api_caller, 
    site, 
    start_date, 
    end_date,
    progress_callback=update_progress
)
```

---

### Step 7: Testing

**Test Plan:**

```python
# test_chunking.py

import unittest
from datetime import datetime
from chunking import _split_date_range, _is_too_many_results_error

class TestAutoChunking(unittest.TestCase):

    def test_split_date_range(self):
        """Test date range splitting."""
        start = datetime(2025, 1, 1)
        end = datetime(2025, 12, 31)

        first, second = _split_date_range(start, end)

        # First half should be Jan 1 to ~Jun 30
        self.assertEqual(first[0], start)

        # Second half should be ~Jul 1 to Dec 31
        self.assertEqual(second[1], end)

        # No overlap
        self.assertLess(first[1], second[0])

    def test_detect_s1_705(self):
        """Test S1-705 error detection."""
        error_response = {
            'Response': {
                'errorDetails': {
                    'moreInfo': {
                        'errors': {
                            'errorCode': 705,
                            'errorMessage': 'Too many results'
                        }
                    }
                }
            }
        }

        self.assertTrue(_is_too_many_results_error(error_response))

    def test_auto_chunking_mock(self):
        """Test auto-chunking with mock API."""
        # Mock API that fails on >90 days
        def mock_api(site, start, end):
            days = (end - start).days
            if days > 90:
                return (False, {'Response': {'errorDetails': {'moreInfo': {'errors': {'errorCode': 705}}}}})
            return (True, [{'id': i} for i in range(days)])

        # Test with 1-year range
        start = datetime(2025, 1, 1)
        end = datetime(2025, 12, 31)

        from chunking import _fetch_with_auto_chunking
        records = _fetch_with_auto_chunking(mock_api, 'test', start, end)

        # Should get records (365 days worth)
        self.assertGreater(len(records), 0)
        print(f"Fetched {len(records)} records via auto-chunking")

if __name__ == '__main__':
    unittest.main()
```

**Run tests:**

```cmd
python test_chunking.py
```

---

### Step 8: Real-World Testing

**Test with actual high-volume sites:**

```python
# test_real_chunking.py

from datetime import datetime
from chunking import _fetch_with_auto_chunking
from endpoints import get_ids_by_date

# Test sites known to have S1-705 issues
test_sites = ['ijoc', 'ms', 'msom', 'opre', 'isr']

for site in test_sites:
    print(f"\nTesting auto-chunking on {site}...")

    # Try 1-year range (known to fail without chunking)
    start = datetime(2025, 1, 1)
    end = datetime(2025, 12, 31)

    # This should automatically chunk and succeed
    records = _fetch_with_auto_chunking(
        lambda s, st, en: get_ids_by_date(s, st, en, {}),
        site,
        start,
        end
    )

    print(f"  Result: {len(records)} records")
    print(f"  Status: {'✓ SUCCESS' if len(records) > 0 else '✗ FAILED'}")
```

---

## Rollout Plan

### Phase 1: Development (1-2 hours)
1. Create chunking.py
2. Add helper to utils.py
3. Modify endpoints.py (Option B - new function)
4. Update config.yaml.template

### Phase 2: Testing (30 minutes)
1. Run unit tests (test_chunking.py)
2. Test with mock API
3. Test with 1-2 real high-volume sites

### Phase 3: Integration (30 minutes)
1. Modify main.py to use chunking
2. Add progress updates to GUI
3. Test full workflow

### Phase 4: Production (15 minutes)
1. Update USER_GUIDE.md
2. Update RELEASE_NOTES.md (V5.1)
3. Commit and tag v5.1.0

---

## Config Options Explained

```yaml
auto_chunking:
  enabled: true              # Master switch (can disable if issues)
  max_depth: 10              # Prevents infinite recursion (10 splits = 1024 chunks max)
  min_chunk_days: 1          # Won't split below 1 day (prevents single-hour chunks)
  show_progress: true        # Display chunking status to user
```

**Max Depth Calculation:**
- Depth 0: 1 chunk (full range)
- Depth 1: 2 chunks (split in half)
- Depth 2: 4 chunks (split each half)
- Depth 3: 8 chunks
- Depth 10: 1024 chunks maximum

**Example:** 10-year range (3,650 days)
- If each chunk must be ≤30 days: ~122 chunks needed
- Depth needed: log2(122) ≈ 7 levels
- Well within max_depth of 10 ✓

---

## Edge Cases Handled

1. **Single-day range that still fails**
   - Can't split further
   - Log warning and skip
   - User sees: "Site X: Unable to retrieve (data volume too high even for 1 day)"

2. **Max recursion depth reached**
   - Stop chunking
   - Return partial results
   - Log error with suggestion to contact support

3. **Non-705 errors during chunking**
   - Don't split (error isn't "too many results")
   - Fail gracefully
   - Log actual error message

4. **Network interruption during chunking**
   - Each chunk is independent
   - Already-fetched chunks are preserved
   - Retry logic still applies per chunk

---

## User-Facing Changes

### Before V5.1:
```
User Query: Jan 1 - Dec 31, 2025 on IJOC
Result: Error - "Too many results, use shorter date range"
User Action: Manually try Jan-Mar, Apr-Jun, etc.
```

### After V5.1:
```
User Query: Jan 1 - Dec 31, 2025 on IJOC
App: [Automatically chunks into manageable sizes]
Result: Complete dataset with 1,200 records exported
User Action: None! Just open Excel file
```

---

## Success Criteria

- [ ] Unit tests pass (test_chunking.py)
- [ ] Real-world test succeeds on 1+ high-volume site
- [ ] No regression on existing functionality
- [ ] Config option allows disabling if needed
- [ ] User guide updated with "any date range" capability
- [ ] Logging shows chunking progress clearly

---

## Rollback Plan

If issues arise:

1. **Quick disable:** Set `auto_chunking.enabled: false` in config.yaml
2. **Code rollback:** `git checkout v5.0.0`
3. **Partial rollback:** Keep chunking.py but don't call it (fallback to old behavior)

---

## Documentation Updates

### USER_GUIDE.md:

Add section:

```markdown
## Date Range Selection

V5.1 supports **any date range** without restrictions!

- Query 1 month, 1 year, or even 10 years
- App automatically handles "too many results" errors
- No need to know which sites have high volume
- Progress updates shown during long queries
- Final result: complete dataset in one file

**Example:**
Even if you query Management Science for an entire year, the app will 
automatically split the request into smaller chunks, fetch all data, 
and merge it into one Excel file.
```

### RELEASE_NOTES.md:

```markdown
## V5.1.0 - October 2025

### New Features

**Auto-Chunking for Large Date Ranges**
- Automatically handles "too many results" (S1-705) errors
- Recursive date range splitting until successful
- Works with any date range on any site
- Zero configuration required
- Progress updates during chunking
- Standing Order #11: Zero-config user experience

### Benefits
- Users can request any date range without errors
- No need to know site-specific limitations
- No manual retries with shorter ranges
- Complete datasets in single export
```

---

## Standing Order #11

**New Standing Order:**

> **SO #11: Zero-Config User Experience**
> 
> The application shall handle all API limitations automatically without 
> requiring user knowledge of site-specific constraints, error codes, or 
> API behavioral details. The user experience should be: "select what you 
> want, get complete results."

V5.1 auto-chunking is the first implementation of SO #11!

---

## Summary

**Estimated Implementation Time:** 2-3 hours

**Complexity:** Medium (recursive function, API integration)

**Risk:** Low (can be disabled, doesn't break existing functionality)

**User Impact:** HIGH (eliminates major pain point)

**Recommendation:** Implement in V5.1 release

---

**Ready to implement? Follow the steps above and V5.1 will be complete!**
