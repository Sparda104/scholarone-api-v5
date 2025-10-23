# endpoints.py - V4 API Compliant Version
"""
ScholarOne API Endpoints Definitions - API Compliant Edition
Enhanced with comprehensive API compliance, rate limiting, and error handling
"""

from __future__ import annotations

import requests
from requests.auth import HTTPDigestAuth
import time
import json
from typing import Any, Dict, List, Optional, Iterable
from utils import iso8601_date, AppLogger

BASE_URL = "https://mc-api.manuscriptcentral.com"

# API COMPLIANCE CONFIGURATION
API_LIMITS = {
    "max_batch_size": 25,  # API-enforced maximum for most endpoints
    "rate_limit_delay": 1.5,  # Minimum seconds between requests
    "request_timeout_base": 60,  # Base timeout in seconds
    "request_timeout_extended": 120,  # Extended timeout for complex endpoints
    "max_retries": 3,
    "retry_delay_base": 2.0,  # Base retry delay
    "maintenance_delay": 30.0,  # Delay for maintenance mode
}

# COMPLETE ENDPOINT CATALOGUE - API COMPLIANT
ENDPOINTS: Dict[str, Dict[str, Any]] = {
    # ---- Submissions / IDs & Metadata ----
    "1": {
        "name": "Get Submission Info Basic",
        "path": "/api/s1m/v3/submissions/basic/metadata/submissionids",
        "req": ["ids"],
        "opt": ["id_type"],
        "param_types": {"ids": "ids"},
        "max_ids_per_call": 25,
        "timeout": "base",
        "complexity": "low",
    },

    "2": {
        "name": "Get Submission Info Full", 
        "path": "/api/s1m/v9/submissions/full/metadata/submissionids",
        "req": ["ids"],
        "opt": ["id_type"],
        "param_types": {"ids": "ids"},
        "max_ids_per_call": 25,
        "timeout": "extended",
        "complexity": "high",
    },

    "3": {
        "name": "Get Submission Versions",
        "path": "/api/s1m/v2/submissions/full/revisions/submissionids",
        "req": ["ids"],
        "opt": ["id_type"],
        "param_types": {"ids": "ids"},
        "max_ids_per_call": 25,
        "timeout": "base",
        "complexity": "medium",
    },

    "4": {
        "name": "Get IDs By Date", 
        "path": "/api/s1m/v4/submissions/full/idsByDate",
        "req": ["from_time", "to_time"],
        "opt": ["document_status", "criteria"],
        "param_types": {"from_time": "date", "to_time": "date"},
        "timeout": "extended",
        "complexity": "high",
        "rate_sensitive": True,  # Can return large datasets
    },

    "5": {
        "name": "Get Person Info Full (by personIds)",
        "path": "/api/s1m/v7/person/full/personids/search",
        "req": ["ids"],
        "opt": ["is_deleted"],
        "param_types": {"ids": "ids"},
        "max_ids_per_call": 25,  # Higher limit for person endpoints
        "timeout": "extended",
        "complexity": "high",
    },

    "7": {
        "name": "Get Author Info Full",
        "path": "/api/s1m/v3/submissions/full/contributors/authors/submissionids",
        "req": ["ids"],
        "opt": ["id_type"],
        "param_types": {"ids": "ids"},
        "max_ids_per_call": 25,
        "timeout": "extended",
        "complexity": "high",
    },

    "8": {
        "name": "Get Reviewer Info Full",
        "path": "/api/s1m/v2/submissions/full/reviewer/submissionids",
        "req": ["ids"],
        "opt": ["id_type"],
        "param_types": {"ids": "ids"},
        "max_ids_per_call": 25,
        "timeout": "extended",
        "complexity": "high",
    },

    "9": {
        "name": "Get Review Files Full (by submissionIds)",
        "path": "/api/s1m/v3/submissions/full/review_files/submissionids",
        "req": ["ids"],
        "opt": ["id_type"],
        "param_types": {"ids": "ids"},
        "max_ids_per_call": 25,
        "timeout": "extended",
        "complexity": "high",
    },

    "10": {
        "name": "Get Review Files Full (by documentIds)",
        "path": "/api/s1m/v3/submissions/full/review_files/documentids",
        "req": ["ids"],
        "param_types": {"ids": "ids"},
        "max_ids_per_call": 25,
        "timeout": "extended",
        "complexity": "high",
    },

    "11": {
        "name": "Get Decision Correspondence",
        "path": "/api/s1m/v4/submissions/full/decisioncorrespondence/submissionids",
        "req": ["ids"],
        "opt": ["id_type"],
        "param_types": {"ids": "ids"},
        "max_ids_per_call": 25,
        "timeout": "extended",
        "complexity": "medium",
    },

    "12": {
        "name": "Get Editor Assignments By Date",
        "path": "/api/s1m/v1/submissions/full/editorAssignmentsByDate",
        "req": ["from_time", "to_time"],
        "opt": ["role_type", "custom_question"],
        "param_types": {"from_time": "date", "to_time": "date"},
        "timeout": "extended",
        "complexity": "high",
        "rate_sensitive": True,
    },

    "13": {
        "name": "Get Metadata Info (by documentIds)",
        "path": "/api/s1m/v3/submissions/full/metadatainfo/documentids",
        "req": ["ids"],
        "opt": ["id_type"],
        "param_types": {"ids": "ids"},
        "max_ids_per_call": 25,
        "timeout": "extended",
        "complexity": "high",
    },

    "14": {
        "name": "Get Metadata Info (by submissionIds)",
        "path": "/api/s1m/v3/submissions/full/metadatainfo/submissionids",
        "req": ["ids"],
        "opt": ["id_type"],
        "param_types": {"ids": "ids"},
        "max_ids_per_call": 25,
        "timeout": "extended",
        "complexity": "high",
    },

    # ---- Checklists ----
    "15": {
        "name": "Get Checklist By ID",
        "path": "/api/s1m/v2/submissions/full/checklistsbyid/submissionids",
        "req": ["ids"],
        "opt": ["task_id", "detail_id", "question_id", "id_type"],
        "param_types": {"ids": "ids"},
        "max_ids_per_call": 25,
        "timeout": "base",
        "complexity": "medium",
    },

    "16": {
        "name": "Get Checklist By Name",
        "path": "/api/s1m/v2/submissions/full/checklistsbyname/submissionids",
        "req": ["ids"],
        "opt": ["task_name", "detail_name", "question_name", "id_type"],
        "param_types": {"ids": "ids"},
        "max_ids_per_call": 25,
        "timeout": "base",
        "complexity": "medium",
    },

    # ---- Staff & Stub ----
    "17": {
        "name": "Get Staff Users Full (by submissionIds)",
        "path": "/api/s1m/v3/submissions/full/staff_users/submissionids",
        "req": ["ids"],
        "opt": ["id_type"],
        "param_types": {"ids": "ids"},
        "max_ids_per_call": 25,
        "timeout": "base",
        "complexity": "low",
    },

    "18": {
        "name": "Get Staff Users Full (by documentIds)",
        "path": "/api/s1m/v3/submissions/full/staff_users/documentids",
        "req": ["ids"],
        "param_types": {"ids": "ids"},
        "max_ids_per_call": 25,
        "timeout": "base",
        "complexity": "low",
    },

    "19": {
        "name": "Get Stub Info Full (Invited Manuscripts)",
        "path": "/api/s1m/v4/submissions/full/stub/documentids",
        "req": ["ids"],
        "param_types": {"ids": "ids"},
        "max_ids_per_call": 25,
        "timeout": "extended",
        "complexity": "high",
    },

    # ---- Configuration ----
    "20": {
        "name": "Get Attribute List Configuration",
        "path": "/api/s1m/v3/configuration/full/attributeList",
        "req": [],
        "timeout": "base",
        "complexity": "low",
    },

    "21": {
        "name": "Get Custom Question List Configuration",
        "path": "/api/s1m/v2/configuration/full/customQuestionList",
        "req": [],
        "timeout": "base",
        "complexity": "medium",
    },

    "22": {
        "name": "Get Editor List Configuration",
        "path": "/api/s1m/v2/configuration/full/editorList",
        "req": [],
        "opt": ["role_type", "role_name"],
        "timeout": "base",
        "complexity": "low",
    },

    # ---- Person (Basic) ----
    "23": {
        "name": "Get Person Info Basic (by personIds)",
        "path": "/api/s1m/v3/person/basic/personids/search",
        "req": ["ids"],
        "opt": ["is_deleted"],
        "param_types": {"ids": "ids"},
        "max_ids_per_call": 25,
        "timeout": "base",
        "complexity": "low",
    },

    "24": {
        "name": "Get Person Info Basic (by email)",
        "path": "/api/s1m/v3/person/basic/email/search",
        "req": ["primary_email"],
        "opt": ["is_deleted"],
        "timeout": "base",
        "complexity": "low",
    },

    # ---- Person (Full) ----
    "25": {
        "name": "Get Person Info Full (by email)",
        "path": "/api/s1m/v7/person/full/email/search",
        "req": ["primary_email"],
        "opt": ["is_deleted"],
        "timeout": "extended",
        "complexity": "high",
    },

    # ---- Integration ----
    "26": {
        "name": "Get External Document IDs (Full)",
        "path": "/api/s1m/v2/submissions/full/externaldocids",
        "req": ["integration_key", "from_time", "to_time"],
        "param_types": {"from_time": "date", "to_time": "date"},
        "timeout": "extended",
        "complexity": "medium",
        "date_range_limit": "1_week",  # API enforced limit
    },

    "27": {
        "name": "Add External ID (POST)",
        "path": "/api/s1m/v2/integration/full/addExternalId",
        "req": ["clientKey", "documentId", "externalId"],
        "method": "POST",
        "timeout": "base",
        "complexity": "low",
    },

    "28": {
        "name": "Relay API: Add JSON Data (POST)",
        "path": "/api/s1m/v2/system/addJSONData",
        "req": ["data"],
        "method": "POST",
        "timeout": "extended",
        "complexity": "high",
    },

    "29": {
        "name": "Set External Revision Flag (POST)",
        "path": "/api/s1m/v2/integration/full/externalRevision",
        "req": ["documentId", "externalId", "lockRevisionFl"],
        "method": "POST",
        "timeout": "base",
        "complexity": "low",
    },
}

# Enhanced field name mapping for better Excel column headers
FIELD_NAME_MAPPINGS = {
    "submissionId": "Submission ID",
    "documentId": "Document ID", 
    "authorFullName": "Author Name",
    "authorFirstName": "Author First Name",
    "authorLastName": "Author Last Name",
    "authorEmailAddress": "Author Email",
    "submissionTitle": "Manuscript Title",
    "submissionDate": "Submission Date",
    "submissionStatus": "Submission Status",
    "documentStatusName": "Document Status",
    "decisionName": "Editorial Decision",
    "reviewerRecommendation": "Reviewer Recommendation",
    "reviewerFullName": "Reviewer Name",
    "editorFullName": "Editor Name",
    "institutionName": "Institution",
    "departmentName": "Department",
    "countryName": "Country",
    "primaryEmailAddress": "Email Address",
    "personId": "Person ID",
    "firstName": "First Name",
    "lastName": "Last Name",
    "fullName": "Full Name",
    "datetimeCreated": "Creation Date",
    "submittingAuthorId": "Submitting Author ID",
}


class APIComplianceError(Exception):
    """Custom exception for API compliance violations."""
    pass

class RateLimitError(APIComplianceError):
    """Rate limiting error."""
    pass

class BatchSizeError(APIComplianceError):
    """Batch size limit exceeded."""
    pass



def _safe_log_params(params):
    safe = params.copy() if isinstance(params, dict) else params
    if isinstance(safe, dict):
        for field in ['username', 'api_key', 'password']:
            if field in safe:
                safe[field] = '***REDACTED***'
    return safe

def classify_error(response):
    """
    Classify API error and determine retry strategy.
    Returns: (should_retry, error_type, wait_time, callback_time)
    """
    status_code = response.status_code

    try:
        response_data = response.json()
        error_details = response_data.get('Response', {}).get('errorDetails', {})
        s1_code = error_details.get('errorCode', '')
        callback_time = error_details.get('callBackTime')
    except:
        s1_code = ''
        callback_time = None

    # Throttle: S1 code 500 with HTTP 400
    if status_code == 400 and s1_code == '500':
        return (True, 'throttle', 0, callback_time)

    # Maintenance: S1 codes 600/601/602 with HTTP 500
    if status_code == 500 and s1_code in ('600', '601', '602'):
        maint_type = {'600': 'platform', '601': 'stack', '602': 'site'}.get(s1_code, 'unknown')
        return (True, f'maintenance_{maint_type}', 0, callback_time)

    # Auth: HTTP 401
    if status_code == 401:
        return (False, 'auth', 0, None)

    # Server errors: HTTP 500/502/504 (non-maintenance)
    if status_code in (500, 502, 504) and s1_code not in ('600', '601', '602'):
        return (True, 'server_error', 5.0, None)

    # Bad request: HTTP 400 (non-throttle)
    if status_code == 400 and s1_code != '500':
        return (False, 'bad_request', 0, None)

    return (False, 'unknown', 0, None)

def parse_callback_time(callback_time_str):
    """Parse callBackTime from API and return wait seconds."""
    if not callback_time_str:
        return 0.0

    try:
        from datetime import datetime
        callback_dt = datetime.fromisoformat(callback_time_str.replace('Z', '+00:00'))
        now_dt = datetime.now(callback_dt.tzinfo)
        wait_seconds = (callback_dt - now_dt).total_seconds()
        return max(0.0, wait_seconds)
    except:
        return 30.0

def detect_s1_705_error(response_data):
    """
    Detect S1-705 "Too many results" error in API response.

    Args:
        response_data: API response dictionary

    Returns:
        bool: True if S1-705 error detected
    """
    try:
        if isinstance(response_data, dict):
            error_details = response_data.get('Response', {}).get('errorDetails', {})
            more_info = error_details.get('moreInfo', {})
            errors = more_info.get('errors', {})
            error_code = errors.get('errorCode')
            error_msg = errors.get('errorMessage', '').lower()

            if error_code == 705 or 'too many results' in error_msg:
                return True
    except Exception:
        pass

    return False


class EndpointExecutor:
    """
    Enhanced API executor with comprehensive compliance and error handling.
    """
    
    def __init__(self, eid: str, params: Dict[str, Any],
                 logger: Optional[AppLogger] = None, checkpointer=None):
        if eid not in ENDPOINTS:
            raise ValueError(f"Unknown endpoint id: {eid}")
        
        self.eid = eid
        self.config = ENDPOINTS[eid]
        self.params = dict(params or {})
        self.logger = logger or AppLogger()
        self.checkpointer = checkpointer
        self._results: List[Dict[str, Any]] = []
        self._last_raw: Optional[Dict[str, Any]] = None
        self._cancel = False
        
        # API compliance tracking
        self._api_stats = {
            "calls_made": 0,
            "retries": 0,
            "rate_limited": 0,
            "maintenance_delays": 0,
        }

    def _validate_batch_size(self, ids_param: str) -> None:
        """Validate that batch size doesn't exceed API limits."""
        if "ids" in self.config.get("param_types", {}):
            # Count comma-separated quoted IDs
            id_count = len([id_.strip("'\"") for id_ in ids_param.split(",") if id_.strip("'\"',")])
            max_allowed = self.config.get("max_ids_per_call", API_LIMITS["max_batch_size"])
            
            if id_count > max_allowed:
                raise BatchSizeError(
                    f"Batch size {id_count} exceeds API limit of {max_allowed} for endpoint {self.eid}"
                )

    def _get_timeout_for_endpoint(self) -> int:
        """Get appropriate timeout based on endpoint complexity."""
        timeout_type = self.config.get("timeout", "base")
        complexity = self.config.get("complexity", "medium")
        
        if timeout_type == "extended" or complexity == "high":
            return API_LIMITS["request_timeout_extended"]
        else:
            return API_LIMITS["request_timeout_base"]

    def _apply_rate_limiting(self) -> None:
        """Apply rate limiting based on endpoint sensitivity."""
        delay = API_LIMITS["rate_limit_delay"]
        
        # Extra delay for rate-sensitive endpoints
        if self.config.get("rate_sensitive", False):
            delay *= 1.5
        
        # Extra delay for high complexity endpoints
        if self.config.get("complexity") == "high":
            delay *= 1.2
        
        self.logger.debug(f"Applying rate limit delay: {delay:.2f}s")
        time.sleep(delay)

    def _handle_api_error(self, response: requests.Response, attempt: int) -> bool:
        """
        Handle specific API errors with appropriate retry logic.
        Returns True if request should be retried, False otherwise.
        """
        status_code = response.status_code
        
        try:
            error_content = response.json() if response.content else {}
        except:
            error_content = {"raw": response.text}
        
        # Rate limiting (429)
        if status_code == 429:
            self._api_stats["rate_limited"] += 1
            if attempt < API_LIMITS["max_retries"]:
                retry_delay = API_LIMITS["retry_delay_base"] * (2 ** attempt)  # Exponential backoff
                self.logger.warning(f"Rate limited (429), retrying in {retry_delay:.1f}s")
                time.sleep(retry_delay)
                return True
        
        # Maintenance mode (503)
        elif status_code == 503:
            self._api_stats["maintenance_delays"] += 1
            if attempt < API_LIMITS["max_retries"]:
                self.logger.warning(f"Maintenance mode (503), retrying in {API_LIMITS['maintenance_delay']}s")
                time.sleep(API_LIMITS["maintenance_delay"])
                return True
        
        # Temporary server errors (500, 502, 504)
        elif status_code in (500, 502, 504):
            if attempt < API_LIMITS["max_retries"]:
                retry_delay = API_LIMITS["retry_delay_base"] * attempt
                self.logger.warning(f"Server error ({status_code}), retrying in {retry_delay:.1f}s")
                time.sleep(retry_delay)
                return True
        
        # Authentication issues (401, 403) - don't retry
        elif status_code in (401, 403):
            self.logger.error(f"Authentication error ({status_code}): Check credentials and IP registration")
        
        # Client errors (400, 404) - don't retry
        elif status_code in (400, 404):
            self.logger.error(f"Client error ({status_code}): {error_content}")
        
        return False

    def _call_api(self, path: str, call_params: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced API call with comprehensive compliance and error handling."""
        username = self.params.get("username") or call_params.get("username")
        api_key = self.params.get("api_key") or call_params.get("api_key")
        site = self.params.get("site_name") or call_params.get("site_name")
        
        if not (username and api_key and site):
            raise ValueError("username, api_key and site_name are required")

        # Validate batch sizes if applicable
        if "ids" in call_params:
            self._validate_batch_size(str(call_params["ids"]))

        # Normalize date params
        for k, t in (self.config.get("param_types") or {}).items():
            if t == "date" and k in call_params and call_params[k]:
                try:
                    call_params[k] = iso8601_date(call_params[k])
                except Exception as e:
                    self.logger.warning(f"Date normalization failed for {k}: {e}")

        # Apply rate limiting before request
        self._apply_rate_limiting()

        url = f"{BASE_URL}{path}"
        timeout = self._get_timeout_for_endpoint()
        
        # Remove credentials from query parameters (CRITICAL FIX)
        q = dict(call_params)
        q.pop("username", None)
        q.pop("api_key", None)
        q["_type"] = "json"

        # Retry loop with enhanced error handling
        for attempt in range(API_LIMITS["max_retries"] + 1):
            try:
                if self.config.get("method") == "POST":
                    self.logger.info(f"API POST {path} (attempt {attempt + 1}/{API_LIMITS['max_retries'] + 1})")
                    q_params = {k: q.pop(k) for k in list(q.keys()) 
                               if k in ("site_name", "_type")}
                    
                    response = requests.post(
                        url, params=q_params, json=q,
                        auth=HTTPDigestAuth(username, api_key), 
                        timeout=timeout
                    )
                else:
                    self.logger.info(f"API GET {path} (attempt {attempt + 1}/{API_LIMITS['max_retries'] + 1})")
                    response = requests.get(
                        url, params=q, 
                        auth=HTTPDigestAuth(username, api_key), 
                        timeout=timeout
                    )

                self._api_stats["calls_made"] += 1
                
                # Check for HTTP errors
                if not response.ok:
                    should_retry = self._handle_api_error(response, attempt)
                    if should_retry:
                        self._api_stats["retries"] += 1
                        continue
                    else:
                        response.raise_for_status()

                # Parse response
                try:
                    data = response.json()
                except Exception as e:
                    self.logger.warning(f"JSON parsing failed, using raw text: {e}")
                    data = {"raw": response.text}

                # Check API-level status
                if isinstance(data, dict):
                    api_response = data.get("Response", {})
                    if isinstance(api_response, dict):
                        status = api_response.get("Status")
                        if status == "MAINTENANCE":
                            if attempt < API_LIMITS["max_retries"]:
                                self.logger.warning("API in maintenance mode, retrying...")
                                self._api_stats["maintenance_delays"] += 1
                                time.sleep(API_LIMITS["maintenance_delay"])
                                continue
                            else:
                                raise APIComplianceError("API is in maintenance mode")
                        elif status and status != "SUCCESS":
                            raise APIComplianceError(f"API returned status: {status}")

                self.logger.info(f"API call successful: {response.status_code} ({len(str(data))} chars)")
                return data

            except requests.exceptions.Timeout:
                if attempt < API_LIMITS["max_retries"]:
                    retry_delay = API_LIMITS["retry_delay_base"] * (attempt + 1)
                    self.logger.warning(f"Request timeout, retrying in {retry_delay:.1f}s")
                    time.sleep(retry_delay)
                    self._api_stats["retries"] += 1
                    continue
                else:
                    raise APIComplianceError(f"Request timeout after {API_LIMITS['max_retries']} retries")
            
            except requests.exceptions.RequestException as e:
                if attempt < API_LIMITS["max_retries"] and "connection" in str(e).lower():
                    retry_delay = API_LIMITS["retry_delay_base"] * (attempt + 1)
                    self.logger.warning(f"Connection error, retrying in {retry_delay:.1f}s: {e}")
                    time.sleep(retry_delay)
                    self._api_stats["retries"] += 1
                    continue
                else:
                    raise APIComplianceError(f"Request failed: {e}")

        # Should not reach here, but safety fallback
        raise APIComplianceError("Maximum retries exceeded")

    def extract_rows(self, payload: Any) -> List[Dict[str, Any]]:
        """
        UNIVERSAL JSON response parser with comprehensive nested structure handling.
        Automatically detects and extracts arrays from common ScholarOne response patterns.

        Handles:
        - Direct arrays: Response.result.submission[]
        - Configuration endpoints: Response.result.editorList.editor[]
        - Nested submissions: Response.result.submission[].files[]
        - Any similar nested patterns
        """
        if not isinstance(payload, dict):
            self.logger.warning("Non-dict response received")
            return []

        self.last_raw = payload

        resp = payload.get("Response") or payload.get("response")
        if isinstance(resp, dict):
            # Check status
            status = resp.get("Status") or resp.get("status")
            if status and status != "SUCCESS":
                self.logger.warning(f"API returned status: {status}")
                error_msg = resp.get("ErrorMessage") or resp.get("errorMessage")
                if error_msg:
                    self.logger.error(f"API Error: {error_msg}")
                return []

            result = resp.get("result") or resp.get("Result")

            # Case A: Direct list of records
            if isinstance(result, list):
                self.logger.debug(f"Found direct list with {len(result)} records")
                return result

            # Case B: Nested structure - UNIVERSAL HANDLER
            if isinstance(result, dict):
                return self._extract_nested_arrays(result)

        self.logger.warning("No extractable data found in response")
        return []

    def _extract_nested_arrays(self, data: Dict[str, Any], depth: int = 0, max_depth: int = 3) -> List[Dict[str, Any]]:
        """
        UNIVERSAL nested array extractor.
        Recursively searches for arrays of dict objects within nested structures.

        Prioritizes:
        1. Known configuration patterns (editorList.editor, attributeList.attribute, etc.)
        2. Direct arrays of dicts
        3. Largest nested array found

        Args:
            data: Dictionary to search
            depth: Current recursion depth
            max_depth: Maximum depth to search

        Returns:
            List of dict objects, or [data] if no arrays found
        """
        if depth > max_depth:
            return [data]

        # === PATTERN 1: Configuration Endpoints ===
        # Known patterns: editorList.editor[], attributeList.attribute[], etc.
        CONFIG_PATTERNS = {
            'editorList': ['editor', 'editors'],
            'attributeList': ['attribute', 'attributes'],
            'customQuestionList': ['customQuestion', 'customQuestions'],
            'checklistList': ['checklist', 'checklists'],
            'roleList': ['role', 'roles']
        }

        for config_key, possible_array_keys in CONFIG_PATTERNS.items():
            if config_key in data:
                config_data = data[config_key]
                if isinstance(config_data, dict):
                    # Look for nested array with expected key
                    for array_key in possible_array_keys:
                        if array_key in config_data:
                            array_data = config_data[array_key]
                            if isinstance(array_data, list) and array_data:
                                if all(isinstance(item, dict) for item in array_data):
                                    self.logger.debug(
                                        f"Found config pattern: {config_key}.{array_key} "
                                        f"with {len(array_data)} records"
                                    )
                                    return array_data
                elif isinstance(config_data, list):
                    # Direct array
                    if all(isinstance(item, dict) for item in config_data):
                        self.logger.debug(
                            f"Found direct config array: {config_key} "
                            f"with {len(config_data)} records"
                        )
                        return config_data

        # === PATTERN 2: Submission/Document wrappers ===
        # Check for submission[], document[], person[] arrays
        for wrapper_key in ['submission', 'submissions', 'document', 'documents', 
                            'person', 'persons', 'reviewer', 'reviewers']:
            if wrapper_key in data:
                wrapper_data = data[wrapper_key]
                if isinstance(wrapper_data, list) and wrapper_data:
                    if all(isinstance(item, dict) for item in wrapper_data):
                        self.logger.debug(
                            f"Found wrapper array: {wrapper_key} "
                            f"with {len(wrapper_data)} records"
                        )
                        return wrapper_data

        # === PATTERN 3: Generic nested array search ===
        # Find ALL arrays of dicts in the structure
        found_arrays = []

        for key, value in data.items():
            if isinstance(value, list) and value:
                # Check if it's an array of dicts
                if all(isinstance(item, dict) for item in value):
                    found_arrays.append((key, value, len(value)))
                    self.logger.debug(f"Found array '{key}' with {len(value)} records")

            elif isinstance(value, dict):
                # Recurse into nested dicts
                nested_result = self._extract_nested_arrays(value, depth + 1, max_depth)
                if len(nested_result) > 1 or (len(nested_result) == 1 and nested_result[0] != value):
                    # Found a valid array in nested structure
                    self.logger.debug(
                        f"Found nested array in '{key}' with {len(nested_result)} records"
                    )
                    return nested_result

        # === PATTERN 4: Return the largest array found ===
        if found_arrays:
            # Sort by array length (descending) and return largest
            found_arrays.sort(key=lambda x: x[2], reverse=True)
            largest_key, largest_array, largest_len = found_arrays[0]
            self.logger.debug(
                f"Using largest array '{largest_key}' with {largest_len} records"
            )
            return largest_array

        # === FALLBACK: Single record ===
        # No arrays found - treat entire dict as single record
        self.logger.debug("No arrays found, treating as single record")
        return [data]
    def run(self, site_name: str, progress_callback=None) -> Iterable[List[Dict[str, Any]]]:
        """
        Execute API call with comprehensive compliance and monitoring.
        """
        if self._cancel:
            self.logger.info("Execution cancelled")
            return

        # Merge site_name into parameters
        call_params = dict(self.params)
        call_params["site_name"] = site_name

        try:
            # Log execution start with compliance info
            max_batch = self.config.get("max_ids_per_call", "unlimited")
            complexity = self.config.get("complexity", "medium")
            self.logger.info(f"Starting {self.config['name']} for site {site_name}")
            self.logger.debug(f"Max batch: {max_batch}, Complexity: {complexity}")

            # Execute API call
            data = self._call_api(self.config["path"], call_params)
            rows = self.extract_rows(data)

            # Add Journal (site_name) as first field in each row
            for row in rows:
                if isinstance(row, dict):
                    row['Journal'] = site_name

            self._results = rows

            # Log results and compliance stats
            stats_msg = f"Retrieved {len(rows)} records"
            if self._api_stats["retries"] > 0:
                stats_msg += f", {self._api_stats['retries']} retries"
            if self._api_stats["rate_limited"] > 0:
                stats_msg += f", {self._api_stats['rate_limited']} rate limits"
            
            self.logger.info(stats_msg)

            # Progress callback
            if progress_callback and callable(progress_callback):
                progress_info = {
                    "progress": 1.0, 
                    "records": len(rows),
                    "api_calls": self._api_stats["calls_made"],
                    "retries": self._api_stats["retries"],
                    "rate_limited": self._api_stats["rate_limited"],
                }
                progress_callback(progress_info)

            yield rows
            
        except Exception as e:
            self.logger.error(f"Execution failed: {e}")
            # Include compliance stats in error
            if self._api_stats["rate_limited"] > 0:
                self.logger.error(f"Rate limited {self._api_stats['rate_limited']} times during execution")
            raise

    def get_compliance_stats(self) -> Dict[str, Any]:
        """Get API compliance statistics for this executor."""
        return dict(self._api_stats)

    def cancel(self):
        """Cancel execution."""
        self._cancel = True
        self.logger.info("Execution cancelled by user")