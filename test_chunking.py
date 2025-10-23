"""
test_chunking.py - Unit Tests for V5.1 Auto-Chunking
======================================================

Tests the auto-chunking functionality for S1-705 "too many results" errors.
"""

import unittest
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chunking import (
    _split_date_range,
    _is_too_many_results_error,
    fetch_with_auto_chunking,
    load_chunking_config
)


class TestDateRangeSplitting(unittest.TestCase):
    """Test date range splitting logic."""

    def test_split_one_year_range(self):
        """Test splitting a 1-year date range."""
        start = datetime(2025, 1, 1)
        end = datetime(2025, 12, 31)

        first, second = _split_date_range(start, end)

        # First half should start at Jan 1
        self.assertEqual(first[0], start)

        # Second half should end at Dec 31
        self.assertEqual(second[1], end)

        # No overlap: first half end < second half start
        self.assertLess(first[1], second[0])

        # Should be roughly equal sizes
        first_days = (first[1] - first[0]).days
        second_days = (second[1] - second[0]).days
        self.assertAlmostEqual(first_days, second_days, delta=2)

        print(f"  ✓ 1-year range split correctly")
        print(f"    First: {first[0].date()} to {first[1].date()} ({first_days} days)")
        print(f"    Second: {second[0].date()} to {second[1].date()} ({second_days} days)")

    def test_split_one_month_range(self):
        """Test splitting a 1-month date range."""
        start = datetime(2025, 1, 1)
        end = datetime(2025, 1, 31)

        first, second = _split_date_range(start, end)

        # Verify no overlap
        self.assertLess(first[1], second[0])

        # Verify coverage
        self.assertEqual(first[0], start)
        self.assertEqual(second[1], end)

        print(f"  ✓ 1-month range split correctly")

    def test_split_two_day_range(self):
        """Test splitting a 2-day date range."""
        start = datetime(2025, 1, 1)
        end = datetime(2025, 1, 2)

        first, second = _split_date_range(start, end)

        # Should split into 1 day each
        first_days = (first[1] - first[0]).days
        second_days = (second[1] - second[0]).days

        self.assertEqual(first_days + second_days, 1)  # Total 2 days, split gives 1

        print(f"  ✓ 2-day range split correctly")


class TestErrorDetection(unittest.TestCase):
    """Test S1-705 error detection."""

    def test_detect_s1_705_by_code(self):
        """Test detection of S1-705 by error code."""
        error_response = {
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
        }

        result = _is_too_many_results_error(error_response)
        self.assertTrue(result)
        print(f"  ✓ S1-705 detected by error code")

    def test_detect_s1_705_by_message(self):
        """Test detection by error message text."""
        error_response = {
            'Response': {
                'errorDetails': {
                    'moreInfo': {
                        'errors': {
                            'errorCode': 800,
                            'errorMessage': 'Too many results returned'
                        }
                    }
                }
            }
        }

        result = _is_too_many_results_error(error_response)
        self.assertTrue(result)
        print(f"  ✓ S1-705 detected by message text")

    def test_dont_detect_other_errors(self):
        """Test that other errors are not detected as S1-705."""
        error_response = {
            'Response': {
                'errorDetails': {
                    'errorCode': 601,
                    'errorMessage': 'API is temporarily unavailable'
                }
            }
        }

        result = _is_too_many_results_error(error_response)
        self.assertFalse(result)
        print(f"  ✓ Other errors not confused with S1-705")

    def test_handle_malformed_error(self):
        """Test handling of malformed error responses."""
        malformed = {'random': 'data'}

        result = _is_too_many_results_error(malformed)
        self.assertFalse(result)
        print(f"  ✓ Malformed errors handled gracefully")


class TestAutoChunkingLogic(unittest.TestCase):
    """Test auto-chunking with mock API."""

    def test_successful_single_request(self):
        """Test when first request succeeds (no chunking needed)."""
        def mock_api(site, start, end):
            # Always succeed
            days = (end - start).days
            records = [{'id': i, 'date': start + timedelta(days=i)} for i in range(days)]
            return (True, records)

        start = datetime(2025, 1, 1)
        end = datetime(2025, 1, 31)

        records = fetch_with_auto_chunking(mock_api, 'test_site', start, end)

        self.assertGreater(len(records), 0)
        self.assertEqual(len(records), 30)  # 30 days
        print(f"  ✓ Single successful request: {len(records)} records")

    def test_chunking_on_large_range(self):
        """Test chunking when range is too large."""
        def mock_api(site, start, end):
            days = (end - start).days

            # Fail if > 90 days (simulate S1-705)
            if days > 90:
                return (False, {
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
                })

            # Success for <= 90 days
            records = [{'id': i} for i in range(days)]
            return (True, records)

        # Try 1-year range (should chunk automatically)
        start = datetime(2025, 1, 1)
        end = datetime(2025, 12, 31)

        records = fetch_with_auto_chunking(mock_api, 'high_volume_site', start, end)

        self.assertGreater(len(records), 0)
        print(f"  ✓ Auto-chunked 1-year range: {len(records)} records")
        print(f"    (Would have failed without chunking)")

    def test_max_depth_protection(self):
        """Test that max depth prevents infinite recursion."""
        def always_fail_api(site, start, end):
            # Always return S1-705
            return (False, {
                'Response': {
                    'errorDetails': {
                        'moreInfo': {
                            'errors': {'errorCode': 705}
                        }
                    }
                }
            })

        start = datetime(2025, 1, 1)
        end = datetime(2025, 12, 31)

        # Should stop at max_depth=3 and return empty
        records = fetch_with_auto_chunking(
            always_fail_api, 
            'impossible_site', 
            start, 
            end,
            max_depth=3
        )

        self.assertEqual(len(records), 0)
        print(f"  ✓ Max depth protection prevents infinite recursion")

    def test_single_day_range_edge_case(self):
        """Test that single-day ranges that fail can't chunk further."""
        def fail_always(site, start, end):
            return (False, {
                'Response': {
                    'errorDetails': {
                        'moreInfo': {
                            'errors': {'errorCode': 705}
                        }
                    }
                }
            })

        start = datetime(2025, 1, 1)
        end = datetime(2025, 1, 1)  # Same day

        records = fetch_with_auto_chunking(fail_always, 'test', start, end)

        self.assertEqual(len(records), 0)
        print(f"  ✓ Single-day range edge case handled")


class TestConfigLoading(unittest.TestCase):
    """Test configuration loading."""

    def test_default_config(self):
        """Test default configuration values."""
        config = load_chunking_config({})

        self.assertTrue(config['enabled'])
        self.assertEqual(config['max_depth'], 10)
        self.assertEqual(config['min_chunk_days'], 1)
        print(f"  ✓ Default config loaded correctly")

    def test_custom_config(self):
        """Test loading custom configuration."""
        custom = {
            'api': {
                'auto_chunking': {
                    'enabled': False,
                    'max_depth': 5
                }
            }
        }

        config = load_chunking_config(custom)

        self.assertFalse(config['enabled'])
        self.assertEqual(config['max_depth'], 5)
        print(f"  ✓ Custom config loaded correctly")


class TestRealWorldScenarios(unittest.TestCase):
    """Test realistic scenarios."""

    def test_mixed_success_failure(self):
        """Test scenario where some chunks succeed, others need more splitting."""
        def variable_api(site, start, end):
            days = (end - start).days

            # First half of year fails, second half succeeds
            if start.month <= 6 and days > 90:
                return (False, {
                    'Response': {
                        'errorDetails': {
                            'moreInfo': {
                                'errors': {'errorCode': 705}
                            }
                        }
                    }
                })

            # Success
            records = [{'id': i, 'month': start.month} for i in range(min(days, 100))]
            return (True, records)

        start = datetime(2025, 1, 1)
        end = datetime(2025, 12, 31)

        records = fetch_with_auto_chunking(variable_api, 'mixed_site', start, end)

        self.assertGreater(len(records), 0)
        print(f"  ✓ Mixed success/failure scenario: {len(records)} records")


def run_tests():
    """Run all tests with detailed output."""
    print("=" * 70)
    print("V5.1 AUTO-CHUNKING TEST SUITE")
    print("=" * 70)
    print()

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDateRangeSplitting))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestAutoChunkingLogic))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigLoading))
    suite.addTests(loader.loadTestsFromTestCase(TestRealWorldScenarios))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print()

    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED!")
        print()
        print("V5.1 auto-chunking is ready for production! 🚀")
    else:
        print("❌ SOME TESTS FAILED")
        print()
        print("Review failures above before deploying.")

    print("=" * 70)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
