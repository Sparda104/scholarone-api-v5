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
