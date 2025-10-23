
╔════════════════════════════════════════════════════════════════════════╗
║              V5.1 DEVELOPMENT - MASTER EXECUTION PLAN                  ║
║                    Safe, Automated, Tested                             ║
╚════════════════════════════════════════════════════════════════════════╝

PROJECT: ScholarOne API V5.1 Auto-Chunking with Critical Fixes
VERSION: 5.1.0
APPROACH: Automated scripts + Git checkpointing
DURATION: ~3 hours execution time (8 phases)
SAFETY: Each phase backed up, tagged, and tested

═══════════════════════════════════════════════════════════════════════════
CRITICAL FIXES ADDRESSED:
═══════════════════════════════════════════════════════════════════════════

✓ FIX #1: Rate limiting between chunks (time.sleep added)
✓ FIX #2: API caller adapter (V5.0 ↔ V5.1 bridge)
✓ FIX #3: DateTime/string conversion (proper handling)
✓ FIX #4: S1-705 error detection in endpoints.py
✓ FIX #5: Progress tracking for chunking operations
✓ FIX #6: Logger integration (shared logging)
✓ FIX #7: Cancellation support (user can stop)
✓ FIX #8: Memory optimization (optional generator mode)

═══════════════════════════════════════════════════════════════════════════
8-PHASE DEVELOPMENT PLAN:
═══════════════════════════════════════════════════════════════════════════

PHASE 1: Pre-Integration Safety (v5.1-phase1)
─────────────────────────────────────────────────────────────────────────
Duration: 15 minutes
Purpose: Backup V5.0, create V5.1 branch, verify baseline

Tasks:
  1. Git commit all V5.0 changes
  2. Tag as v5.0.0-final-stable
  3. Create v5.1-development branch
  4. Run V5.0 tests to establish baseline
  5. Document current state

Script: v51_phase1_safety.py
Output: Backup complete, baseline verified

─────────────────────────────────────────────────────────────────────────

PHASE 2: Fix endpoints.py - S1-705 Detection (v5.1-phase2)
─────────────────────────────────────────────────────────────────────────
Duration: 20 minutes
Purpose: Add S1-705 "too many results" error detection

Changes to endpoints.py:
  1. Add detect_s1_705_error() function
  2. Modify _handle_api_error() to detect S1-705
  3. Return error details instead of raising exception on S1-705
  4. Update EndpointExecutor.run() to handle S1-705 specially
  5. Add S1-705 to error statistics tracking

Script: v51_phase2_s1_705_detection.py
Output: endpoints.py enhanced with S1-705 handling
Commit: "Fix: Add S1-705 too many results detection"
Tag: v5.1-phase2

─────────────────────────────────────────────────────────────────────────

PHASE 3: Create chunking_v51.py (CORRECTED) (v5.1-phase3)
─────────────────────────────────────────────────────────────────────────
Duration: 30 minutes
Purpose: Create corrected chunking module with ALL fixes

New file: chunking_v51.py

Fixes applied:
  ✓ Rate limiting: time.sleep(1.5) between recursive calls
  ✓ Logger parameter: accepts shared logger
  ✓ Cancellation: _cancel flag support
  ✓ Progress callback: reports chunking status
  ✓ Type safety: datetime handling explicit
  ✓ Memory optimization: optional generator mode

Key functions:
  - fetch_with_auto_chunking(): Main recursive chunker
  - _split_date_range(): Date splitter
  - _is_too_many_results_error(): S1-705 detector
  - ChunkingStats: Statistics tracker

Script: v51_phase3_corrected_chunking.py
Output: chunking_v51.py created
Commit: "Feature: Corrected chunking module with rate limiting"
Tag: v5.1-phase3

─────────────────────────────────────────────────────────────────────────

PHASE 4: Create Adapter Layer (v5.1-phase4)
─────────────────────────────────────────────────────────────────────────
Duration: 30 minutes
Purpose: Bridge V5.0 endpoints ↔ V5.1 chunking

New file: chunking_adapter.py

Components:
  1. ChunkingAPIAdapter class
     - Wraps EndpointExecutor
     - Converts datetime ↔ string
     - Returns (success, result) tuple
     - Applies rate limiting
     - Handles cancellation

  2. create_chunking_adapter() factory
     - Creates adapter for specific endpoint
     - Configures parameters
     - Injects logger

  3. Integration helpers
     - endpoint_supports_chunking()
     - extract_date_range()
     - format_chunk_progress()

Script: v51_phase4_adapter.py
Output: chunking_adapter.py created
Commit: "Feature: Adapter layer for V5.0/V5.1 integration"
Tag: v5.1-phase4

─────────────────────────────────────────────────────────────────────────

PHASE 5: Integrate into main.py (v5.1-phase5)
─────────────────────────────────────────────────────────────────────────
Duration: 45 minutes
Purpose: Integrate chunking into main application

Changes to main.py:
  1. Import chunking modules
  2. Add _should_use_chunking() method
  3. Modify run_job() to detect date-based endpoints
  4. Add _process_site_with_chunking() method
  5. Update progress tracking for chunking
  6. Add chunking statistics to summary
  7. Pass cancellation flag to chunking

Integration logic:
  if endpoint_uses_dates and chunking_enabled:
      use chunking (new path)
  else:
      use existing V5.0 logic (proven path)

Script: v51_phase5_main_integration.py
Output: main.py enhanced with chunking
Commit: "Feature: Integrate auto-chunking into main workflow"
Tag: v5.1-phase5

─────────────────────────────────────────────────────────────────────────

PHASE 6: Configuration and UI Updates (v5.1-phase6)
─────────────────────────────────────────────────────────────────────────
Duration: 20 minutes
Purpose: Add configuration options and UI indicators

Changes:
  1. config.yaml.template - Add auto_chunking section
  2. config_loader.py - Parse chunking config
  3. gui_widgets.py - Add "Chunking:" status label
  4. version.py - Update to 5.1.0

Configuration added:
  auto_chunking:
    enabled: true
    max_depth: 10
    show_progress: true
    rate_limit_delay: 1.5

Script: v51_phase6_config_ui.py
Output: Config and UI updated
Commit: "Feature: Add V5.1 configuration and UI updates"
Tag: v5.1-phase6

─────────────────────────────────────────────────────────────────────────

PHASE 7: Testing Suite (v5.1-phase7)
─────────────────────────────────────────────────────────────────────────
Duration: 30 minutes
Purpose: Comprehensive test coverage

New files:
  1. tests/test_chunking_v51.py
     - Test chunking logic
     - Test rate limiting
     - Test cancellation
     - Test memory behavior

  2. tests/test_adapter.py
     - Test adapter conversions
     - Test error handling
     - Test cancellation propagation

  3. tests/test_integration_v51.py
     - Test main.py integration
     - Test V5.0 regression (ensure no breaks)
     - Test chunking vs non-chunking paths

  4. tests/test_s1_705_detection.py
     - Test S1-705 detection in endpoints.py
     - Test error response parsing

Script: v51_phase7_testing.py
Output: Complete test suite created
Commit: "Tests: Add V5.1 test coverage"
Tag: v5.1-phase7

─────────────────────────────────────────────────────────────────────────

PHASE 8: Documentation and Release (v5.1-phase8)
─────────────────────────────────────────────────────────────────────────
Duration: 20 minutes
Purpose: Final documentation and release preparation

Updates:
  1. README.md - V5.1 features
  2. USER_GUIDE.md - "Any date range" capability
  3. RELEASE_NOTES.md - V5.1 changelog
  4. V5.1_INTEGRATION_REPORT.md - Technical details
  5. DEPLOYMENT_CHECKLIST_V51.md - Deployment steps

Script: v51_phase8_documentation.py
Output: All documentation updated
Commit: "Docs: V5.1 release documentation"
Tag: v5.1.0, v5.1.0-release-candidate

─────────────────────────────────────────────────────────────────────────

═══════════════════════════════════════════════════════════════════════════
EXECUTION INSTRUCTIONS:
═══════════════════════════════════════════════════════════════════════════

Run scripts in order:

1. python v51_phase1_safety.py
   └─> Backup V5.0, create branch

2. python v51_phase2_s1_705_detection.py
   └─> Add S1-705 detection to endpoints.py

3. python v51_phase3_corrected_chunking.py
   └─> Create corrected chunking module

4. python v51_phase4_adapter.py
   └─> Create adapter layer

5. python v51_phase5_main_integration.py
   └─> Integrate into main.py

6. python v51_phase6_config_ui.py
   └─> Update config and UI

7. python v51_phase7_testing.py
   └─> Create test suite

8. python v51_phase8_documentation.py
   └─> Finalize documentation

After all phases:
  python run_all_v51_tests.py
  └─> Verify all tests pass

═══════════════════════════════════════════════════════════════════════════
ROLLBACK STRATEGY:
═══════════════════════════════════════════════════════════════════════════

Each phase is git-tagged. Rollback to any phase:
  git checkout v5.1-phase<N>

Complete rollback to V5.0:
  git checkout v5.0.0-final-stable

Disable chunking without rollback:
  Set auto_chunking.enabled: false in config.yaml

═══════════════════════════════════════════════════════════════════════════
SAFETY GUARANTEES:
═══════════════════════════════════════════════════════════════════════════

✓ Every phase creates backup before changes
✓ Every phase commits with clear message
✓ Every phase creates git tag for rollback
✓ V5.0 functionality never removed, only enhanced
✓ Chunking is optional (can be disabled)
✓ Tests verify no V5.0 regression
✓ Rate limiting preserved and enhanced

═══════════════════════════════════════════════════════════════════════════
SUCCESS CRITERIA:
═══════════════════════════════════════════════════════════════════════════

V5.1 is complete when:
  □ All 8 phases executed successfully
  □ All tests pass (100% pass rate)
  □ No V5.0 functionality broken (regression tests)
  □ Chunking works with high-volume sites
  □ Rate limiting maintained (no S1-500 errors)
  □ Documentation complete
  □ Git tags created for all phases

═══════════════════════════════════════════════════════════════════════════
TIME ESTIMATES:
═══════════════════════════════════════════════════════════════════════════

Phase 1: 15 minutes (safety setup)
Phase 2: 20 minutes (S1-705 detection)
Phase 3: 30 minutes (corrected chunking)
Phase 4: 30 minutes (adapter layer)
Phase 5: 45 minutes (main integration)
Phase 6: 20 minutes (config/UI)
Phase 7: 30 minutes (testing)
Phase 8: 20 minutes (documentation)

Total: 3 hours 30 minutes (automated execution)
Testing: 1 hour (manual verification)
Total with testing: 4.5 hours

═══════════════════════════════════════════════════════════════════════════

Ready to generate all 8 phase scripts...
