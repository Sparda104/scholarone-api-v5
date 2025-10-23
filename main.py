#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ScholarOne - Desktop App (V5.1 ENHANCED VERSION)
Enhanced with multi-site isolation, fault tolerance, and AUTO-CHUNKING
"""

from __future__ import annotations
import os
import sys
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple, Iterable
import tkinter as tk
from tkinter import messagebox, filedialog
import datetime

# Local modules
from endpoints import ENDPOINTS, EndpointExecutor, FIELD_NAME_MAPPINGS
from exporter import ExcelExporter
from gui_widgets import ControlsFrame

# V5.1: Auto-chunking imports
try:
    from chunking_v51 import fetch_with_auto_chunking
    CHUNKING_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  V5.1 Chunking not available: {e}")
    CHUNKING_AVAILABLE = False

# Try to import Planner; if unavailable we'll handle gracefully
try:
    from workflow_engine import Planner
except Exception:
    Planner = None

WEB_WRAPPER_VERSION = "V5.1 - Enhanced Version (Multi-Site Isolation + Auto-Chunking)"


class ScholarOneApp:
    def __init__(self) -> None:
        # ---- Simple Logging --------------------------------------------------
        self.logger = logging.getLogger("s1_app_v51")
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        if not self.logger.handlers:
            self.logger.addHandler(handler)

        # ---- Tk root ---------------------------------------------------------
        self.root = tk.Tk()
        self.root.title("ScholarOne API Client - V5.1 Enhanced")
        self.root.geometry("1000x700")

        # ---- GUI -------------------------------------------------------------
        self.gui = ControlsFrame(self.root, endpoints=ENDPOINTS)
        self.gui.pack(fill="both", expand=True)
        self.gui.set_run_command(self.run_job)

        # ---- Exporter --------------------------------------------------------
        self.exporter = ExcelExporter(self.logger)
        v4_dir = os.path.join(os.path.expanduser("~"), "OneDrive - Informs",
                              "S1 API GUI Project", "updated_api_files", "Current Version")
        self.default_xlsx = os.path.join(v4_dir, "scholarone_export.xlsx")

        # ---- Simple Features -------------------------------------------------
        self.last_export_path = None
        self.export_stats = {"total_records": 0, "total_calls": 0, "failed_calls": 0}

        # Add simple menu bar
        self._create_menu()

    def _create_menu(self):
        """Create simple menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Last Export", command=self._open_last_export)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Test API Connection", command=self._test_connection)

    def _open_last_export(self):
        """Open the last exported file."""
        if self.last_export_path and os.path.exists(self.last_export_path):
            try:
                os.startfile(self.last_export_path)  # Windows
            except AttributeError:
                try:
                    os.system(f"open '{self.last_export_path}'")  # macOS
                except:
                    os.system(f"xdg-open '{self.last_export_path}'")  # Linux
        else:
            messagebox.showwarning("No Export", "No recent export file found.")

    def _test_connection(self):
        """Test API connection."""
        values = self.gui.get_values()
        creds = {
            "username": values.get("username", "").strip(),
            "api_key": values.get("api_key", "").strip(),
        }

        if not creds["username"] or not creds["api_key"]:
            messagebox.showerror("Missing Credentials", "Please enter username and API key first.")
            return

        test_executor = EndpointExecutor(
            eid="20",  # Get Attribute List Configuration
            params=creds,
            logger=self.logger
        )

        try:
            result = list(test_executor.run("orgsci"))
            if result:
                messagebox.showinfo("Connection Test", "[OK] API connection successful!")
            else:
                messagebox.showwarning("Connection Test", "Connection succeeded but no data returned.")
        except Exception as e:
            messagebox.showerror("Connection Test", f"Connection failed:\n{str(e)}")

    def mainloop(self) -> None:
        self.root.mainloop()

    def _normalize_rows(self, out: Any) -> List[Dict[str, Any]]:
        """Simple row normalization."""
        rows: List[Dict[str, Any]] = []
        if out is None:
            return rows

        if isinstance(out, list):
            if out and isinstance(out[0], list):
                for batch in out:
                    rows.extend(batch)
            else:
                rows.extend(out)
            return rows

        if isinstance(out, dict):
            rows.append(out)
            return rows

        if isinstance(out, Iterable):
            for chunk in out:
                if isinstance(chunk, list):
                    rows.extend(chunk)
                elif isinstance(chunk, dict):
                    rows.append(chunk)

        return rows

    def _simple_worker(
        self,
        endpoint_id: str,
        creds: Dict[str, str],
        base_params: Dict[str, Any],
        site: str,
    ) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]]]:
        """Simple worker with basic error handling."""
        worker_params = dict(base_params)
        worker_params.update(creds)

        # Simple delay
        time.sleep(1.5)

        ex = EndpointExecutor(
            eid=endpoint_id,
            params=worker_params,
            logger=self.logger
        )

        try:
            out = ex.run(site_name=site)
            rows = self._normalize_rows(out)
            self.export_stats["total_calls"] += 1
            self.logger.info(f"Worker completed for site {site}: {len(rows)} records")
            return site, base_params, rows
        except Exception as e:
            self.export_stats["failed_calls"] += 1
            self.logger.error(f"Worker failed for site {site}: {e}")
            return site, base_params, []

    # ==================== V5.1 AUTO-CHUNKING HELPERS ====================

    def _should_use_chunking(self, endpoint_id, params):
        """
        Check if endpoint should use V5.1 auto-chunking.

        Args:
            endpoint_id: Endpoint number
            params: Parameters dict

        Returns:
            bool: True if chunking should be used
        """
        if not CHUNKING_AVAILABLE:
            return False

        # Only use chunking for date-based endpoints
        return 'from_time' in params and 'to_time' in params

    def _process_with_chunking(self, site, endpoint_id, creds, params):
        """
        Process site using V5.1 auto-chunking (handles S1-705 errors).

        Args:
            site: Site name
            endpoint_id: Endpoint number
            creds: API credentials
            params: Parameters including date range

        Returns:
            Result dict with status, rows, site, record_count
        """
        try:
            # Extract date range from params
            from_time_str = params.get('from_time', '')
            to_time_str = params.get('to_time', '')

            if not from_time_str or not to_time_str:
                # Fall back to regular processing if no dates
                return self._process_site_isolated(site, endpoint_id, creds, params)

            # Convert to datetime objects
            start_date = datetime.datetime.fromisoformat(from_time_str.replace('Z', ''))
            end_date = datetime.datetime.fromisoformat(to_time_str.replace('Z', ''))

            self.logger.info(f"[V5.1 Chunking] {site}: {start_date.date()} to {end_date.date()}")

            # Create API caller function for chunking
            def api_caller(site_name, start_dt, end_dt):
                # Prepare params with new date range
                chunk_params = dict(params)
                chunk_params['from_time'] = start_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
                chunk_params['to_time'] = end_dt.strftime('%Y-%m-%dT%H:%M:%SZ')

                try:
                    # Use existing _simple_worker
                    _, _, rows = self._simple_worker(endpoint_id, creds, chunk_params, site_name)
                    return (True, rows)
                except Exception as e:
                    # Format error for chunking detection
                    error_str = str(e).lower()
                    error_dict = {'error': str(e)}

                    # Check if S1-705 error
                    if '705' in error_str or 'too many results' in error_str:
                        error_dict = {
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

                    return (False, error_dict)

            # Execute chunking
            rows = fetch_with_auto_chunking(
                api_caller=api_caller,
                site_name=site,
                start_date=start_date,
                end_date=end_date,
                max_depth=10,
                logger=self.logger,
                rate_limit_delay=1.5
            )

            if rows:
                self.logger.info(f"[V5.1] {site}: {len(rows)} records (chunked)")
                return {
                    'status': 'success',
                    'rows': rows,
                    'site': site,
                    'record_count': len(rows),
                    'chunked': True
                }
            else:
                return {
                    'status': 'no_data',
                    'rows': [],
                    'site': site,
                    'chunked': True
                }

        except Exception as e:
            self.logger.error(f"[V5.1] Chunking failed for {site}: {e}")
            # Fall back to regular processing
            self.logger.info(f"Falling back to V5.0 processing for {site}")
            return self._process_site_isolated(site, endpoint_id, creds, params)

    # ==================== V5 MULTI-SITE ISOLATION HELPERS ====================

    def _process_site_isolated(self, site, endpoint_id, creds, params):
        """
        Process single site with error isolation (V5 Enhancement).
        Standing Order #1: Fault isolation per site.
        """
        try:
            self.logger.info(f"Processing site: {site}")
            # Call existing worker method
            site_name, site_params, rows = self._simple_worker(
                endpoint_id, creds, params, site
            )

            if rows:
                self.logger.info(f"[OK] {site}: {len(rows)} records")
                return {
                    'status': 'success',
                    'rows': rows,
                    'site': site,
                    'record_count': len(rows)
                }
            else:
                self.logger.warning(f"[WARN] {site}: No data returned")
                return {
                    'status': 'no_data',
                    'rows': [],
                    'site': site,
                    'error': 'No data returned'
                }
        except Exception as e:
            self.logger.error(f"[FAIL] {site}: {str(e)}")
            return {
                'status': 'failed',
                'rows': [],
                'site': site,
                'error': str(e)
            }

    def _create_summary(self, sites_completed, sites_failed):
        """
        Generate site-by-site summary report (V5 Enhancement).
        Standing Order #1: Report per-site success/failure.
        """
        lines = []
        lines.append("="*60)
        lines.append("SITE-BY-SITE RESULTS")
        lines.append("="*60)

        if sites_completed:
            lines.append(f"\nSuccessful Sites ({len(sites_completed)}):")
            for site_info in sites_completed:
                site = site_info['site']
                count = site_info.get('record_count', 0)
                chunked = " (chunked)" if site_info.get('chunked') else ""
                lines.append(f"  [OK] {site}: {count} records{chunked}")

        if sites_failed:
            lines.append(f"\nFailed Sites ({len(sites_failed)}):")
            for site, error in sites_failed.items():
                lines.append(f"  [FAIL] {site}: {error}")

        lines.append("="*60)
        return "\n".join(lines)

    # =========================================================================

    def run_job(self) -> None:
        """
        SIMPLIFIED job execution that won't freeze.
        Enhanced with V5.1 auto-chunking capability.
        """
        print("\n=== STARTING V5.1 ENHANCED EXPORT ===")

        # Get values
        values = self.gui.get_values()

        # Set UI to running
        self.gui.set_running(True)

        # Update progress display
        if hasattr(self.gui, 'set_progress_text'):
            self.gui.set_progress_text("Starting export...")

        try:
            # ---- Basic Validation -----------------------------------------------
            creds = {
                "username": values.get("username", "").strip(),
                "api_key": values.get("api_key", "").strip(),
            }

            if not creds["username"] or not creds["api_key"]:
                raise ValueError("Please enter your Username and API Key.")

            endpoint_id = values.get("endpoint_id")
            if endpoint_id is None:
                raise ValueError("Please select an endpoint.")

            ep_cfg = ENDPOINTS.get(endpoint_id)
            if not ep_cfg:
                raise ValueError(f"Unknown endpoint: {endpoint_id}")

            params: Dict[str, Any] = dict(values.get("params") or {})
            required_params = ep_cfg.get("req", [])
            missing = [param for param in required_params if not params.get(param)]
            if missing:
                raise ValueError(f"Missing required parameter(s): {', '.join(missing)}")

            sites: List[str] = list(values.get("sites") or [])
            if not sites:
                raise ValueError("Select at least one site.")

            print(f"Processing {len(sites)} sites...")

            # ---- V5.1 Enhanced Execution with Chunking ---------------------
            all_rows: List[Dict[str, Any]] = []
            sites_completed = []
            sites_failed = {}

            # Reset stats
            self.export_stats = {"total_records": 0, "total_calls": 0, "failed_calls": 0}

            # Process each site with chunking detection
            for i, site in enumerate(sites):
                print(f"Processing site {i+1}/{len(sites)}: {site}")
                if hasattr(self.gui, 'set_progress_text'):
                    self.gui.set_progress_text(f"Processing {site}... ({i+1}/{len(sites)})")

                # V5.1: Use chunking for date-based endpoints
                if self._should_use_chunking(endpoint_id, params):
                    self.logger.info(f"[V5.1] Using auto-chunking for {site}")
                    result = self._process_with_chunking(site, endpoint_id, creds, params)
                else:
                    result = self._process_site_isolated(site, endpoint_id, creds, params)

                if result['status'] == 'success':
                    all_rows.extend(result['rows'])
                    sites_completed.append(result)
                    print(f"  -> [OK] {len(result['rows'])} records from {site}")
                elif result['status'] == 'no_data':
                    sites_completed.append(result)
                    print(f"  -> [WARN] No data from {site}")
                else:
                    sites_failed[site] = result.get('error', 'Unknown error')
                    print(f"  -> [FAIL] {site}: {result.get('error')}")

            print(f"\nTotal records retrieved: {len(all_rows)}")

            # Print site summary
            summary = self._create_summary(sites_completed, sites_failed)
            print(f"\n{summary}")
            self.logger.info(summary)

            # ---- Excel Export ------------------------------------------------
            if all_rows:
                print("Starting Excel export...")
                if hasattr(self.gui, 'set_progress_text'):
                    self.gui.set_progress_text("Creating Excel file...")

                # Create filename
                endpoint_name = ep_cfg.get("name", f"endpoint_{endpoint_id}").replace(" ", "_")
                sites_str = "_".join(sites[:3])
                if len(sites) > 3:
                    sites_str += f"_plus{len(sites)-3}more"
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
                filename = f"scholarone_{endpoint_name}_{sites_str}_{timestamp}.xlsx"
                print(f"Filename: {filename}")

                # Export
                export_dir = os.path.dirname(self.default_xlsx)
                print(f"Export directory: {export_dir}")

                # V5.1 EXPORT with data pipeline
                out_path = self.exporter.export_to_excel(
                    all_rows,
                    filename,
                    export_dir=export_dir,
                    apply_formatting=True
                )

                self.last_export_path = out_path
                self.export_stats["total_records"] = len(all_rows)
                print(f"Excel file created: {out_path}")

                # Success message with site details
                success_msg = f"""[OK] Export Complete!

Records exported: {len(all_rows):,}
Sites successful: {len(sites_completed)}
Sites failed: {len(sites_failed)}
API calls made: {self.export_stats['total_calls']}
Failed calls: {self.export_stats['failed_calls']}

File saved as:
{out_path}

Would you like to open the file now?"""

                if messagebox.askyesno("Export Complete", success_msg):
                    self._open_last_export()
            else:
                # No data but show site summary
                summary_msg = f"""No data was retrieved from any site.

{summary}

Check the console for detailed error messages."""
                messagebox.showwarning("No Data", summary_msg)

        except Exception as e:
            self.logger.exception("Run failed")
            error_msg = f"Error: {str(e)}"
            messagebox.showerror("Run Failed", error_msg)
        finally:
            print("=== EXPORT FINISHED ===\n")
            self.gui.set_running(False)
            if hasattr(self.gui, 'set_progress_text'):
                self.gui.set_progress_text("Ready")


if __name__ == "__main__":
    print(f"Starting {WEB_WRAPPER_VERSION}")
    print("Working directory:", os.getcwd())
    app = ScholarOneApp()
    app.mainloop()
