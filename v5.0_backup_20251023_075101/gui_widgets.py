# gui_widgets.py - V4 Compatible Version
"""
GUI Widget Library for ScholarOne API Application
Windows 11 compatible with enhanced progress tracking and V4 integration
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, List, Optional, Tuple, Callable
from endpoints import ENDPOINTS as _CATALOG  # default catalog

# ---------- Utilities ----------

def _sorted_endpoint_choices(catalog: Dict[str, Dict[str, Any]]) -> List[Tuple[str, str]]:
    """Return stable (id, name) list for dropdown, sorted numerically then lexicographically."""
    def _key(k: str):
        try:
            return (int(k), k)
        except Exception:
            return (10**9, k)
    
    return [(eid, cfg.get("name", eid)) for eid, cfg in sorted(catalog.items(), key=lambda kv: _key(kv[0]))]

# Exported for backward compatibility if something else imports these:
ENDPOINT_CHOICES: List[Tuple[str, str]] = _sorted_endpoint_choices(_CATALOG)
REQUIRED_PARAMS: Dict[str, List[str]] = {eid: list(cfg.get("req", [])) for eid, cfg in _CATALOG.items()}
OPTIONAL_PARAMS: Dict[str, List[str]] = {eid: list(cfg.get("opt", [])) for eid, cfg in _CATALOG.items()}

# ---------- Dynamic parameter form ----------

class ParamForm:
    """
    Builds (and rebuilds) a vertical form for the selected endpoint.
    - Required params always shown
    - Optional params shown when toggled
    Use .values() to fetch a dict of provided (non-empty) values.
    """
    
    def __init__(self, parent: tk.Widget, catalog: Optional[Dict[str, Dict[str, Any]]] = None):
        self.parent = parent
        self.catalog = catalog or _CATALOG
        self.frame = ttk.Frame(parent)
        
        self._required_frame = ttk.Frame(self.frame)
        self._optional_frame = ttk.Frame(self.frame)
        self._req_widgets: Dict[str, tk.Entry] = {}
        self._opt_widgets: Dict[str, tk.Entry] = {}
        self._opt_visible = tk.BooleanVar(value=False)
        
        self._opt_toggle = ttk.Checkbutton(
            self.frame,
            text="Show optional parameters",
            variable=self._opt_visible,
            command=self._toggle_optional,
        )
        
        # Layout
        self._required_frame.grid(row=0, column=0, sticky="nsew", padx=4, pady=(0, 6))
        self._opt_toggle.grid(row=1, column=0, sticky="w", padx=4, pady=(0, 2))
        self._optional_frame.grid(row=2, column=0, sticky="nsew", padx=4, pady=(0, 6))
        self._optional_frame.grid_remove()
        
        for f in (self.frame, self._required_frame, self._optional_frame):
            f.columnconfigure(1, weight=1)

    def widget(self) -> ttk.Frame:
        return self.frame

    def clear(self) -> None:
        for child in list(self._required_frame.children.values()):
            child.destroy()
        for child in list(self._optional_frame.children.values()):
            child.destroy()
        
        self._req_widgets.clear()
        self._opt_widgets.clear()

    def build_for_endpoint(self, endpoint_id: str) -> None:
        self.clear()
        cfg = self.catalog.get(endpoint_id, {})
        req = cfg.get("req", []) or []
        opt = cfg.get("opt", []) or []
        
        if req:
            ttk.Label(self._required_frame, text="Required parameters:", font=("", 10, "bold")).grid(
                row=0, column=0, columnspan=2, sticky="w", pady=(0, 4)
            )
            
            for i, p in enumerate(req, start=1):
                ttk.Label(self._required_frame, text=p).grid(row=i, column=0, sticky="w", padx=(0, 6), pady=2)
                e = ttk.Entry(self._required_frame)
                e.grid(row=i, column=1, sticky="ew", pady=2)
                self._req_widgets[p] = e

        if opt:
            ttk.Label(self._optional_frame, text="Optional parameters:", font=("", 10, "bold")).grid(
                row=0, column=0, columnspan=2, sticky="w", pady=(0, 4)
            )
            
            for i, p in enumerate(opt, start=1):
                ttk.Label(self._optional_frame, text=p).grid(row=i, column=0, sticky="w", padx=(0, 6), pady=2)
                e = ttk.Entry(self._optional_frame)
                e.grid(row=i, column=1, sticky="ew", pady=2)
                self._opt_widgets[p] = e

    def _toggle_optional(self) -> None:
        if self._opt_visible.get():
            self._optional_frame.grid()
        else:
            self._optional_frame.grid_remove()

    def values(self) -> Dict[str, str]:
        out: Dict[str, str] = {}
        for k, w in self._req_widgets.items():
            v = w.get().strip()
            if v != "":
                out[k] = v
        for k, w in self._opt_widgets.items():
            v = w.get().strip()
            if v != "":
                out[k] = v
        return out

# ---------- Endpoint picker (dropdown + form) ----------

class EndpointPicker(ttk.Frame):
    """
    Composite widget: endpoint dropdown + dynamic parameter form.
    """
    
    def __init__(self, parent: tk.Widget, catalog: Optional[Dict[str, Dict[str, Any]]] = None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.catalog = catalog or _CATALOG
        self._choices = _sorted_endpoint_choices(self.catalog)
        
        self.endpoint_var = tk.StringVar(value=self._choices[0][0] if self._choices else "")
        
        ttk.Label(self, text="Endpoint:").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=(0, 4))
        
        self.endpoint_cmb = ttk.Combobox(self, textvariable=self.endpoint_var, state="readonly")
        self.endpoint_cmb["values"] = [f"{eid} â€“ {name}" for eid, name in self._choices]
        self.endpoint_cmb.grid(row=0, column=1, sticky="ew", pady=(0, 4))
        self.endpoint_cmb.bind("<<ComboboxSelected>>", self._on_endpoint_change)
        
        self.param_form = ParamForm(self, catalog=self.catalog)
        self.param_form.widget().grid(row=1, column=0, columnspan=2, sticky="nsew")
        
        self._rebuild_form_for_current()
        
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)
        
        self.on_change: Optional[Callable[[str], None]] = None

    def _on_endpoint_change(self, _evt=None) -> None:
        self._rebuild_form_for_current()
        if callable(self.on_change):
            try:
                self.on_change(self.current_endpoint_id())
            except Exception:
                pass

    def current_endpoint_id(self) -> str:
        raw = self.endpoint_var.get()
        if "â€“" in raw:
            return raw.split("â€“", 1)[0].strip()
        if "-" in raw:
            return raw.split("-", 1)[0].strip()
        return raw.strip()

    def _rebuild_form_for_current(self) -> None:
        self.param_form.build_for_endpoint(self.current_endpoint_id())

    def params(self) -> Dict[str, str]:
        return self.param_form.values()

# Back-compat builder
def build_param_form(parent: tk.Widget) -> EndpointPicker:
    return EndpointPicker(parent, catalog=_CATALOG)

# ---------- ControlsFrame expected by main.py ----------

class ControlsFrame(ttk.Frame):
    """
    High-level control panel:
    - Credentials (username, api_key)
    - Sites multi-select
    - Endpoint picker (dropdown + dynamic params)
    - Run button
    - Progress label + bar helpers

    Exposes:
    - get_credentials() -> {"username": str, "api_key": str}
    - get_selected_sites() -> List[str]
    - get_endpoint_id() -> str
    - get_params() -> Dict[str, str]
    - bind_run(fn) / set_run_command(fn)
    - set_progress_text(text: str)
    - set_progress_fraction(f: float in [0,1])
    - get_values() -> Dict[str, Any]
    - set_running(is_running: bool)
    - progress_start(text: str|None=None)
    - progress_update(frac: float|None=None, text: str|None=None)
    - progress_finish(text: str|None=None)
    - progress_step(completed: int, text: str, total: int|None=None) # Enhanced for V4
    - progress_set_total(total: int) # Added for V4 compatibility
    """
    
    DEFAULT_SITES = [
        "deca", "ijds", "ite", "inte", "ijoc", "ijoo", "orgsci",
        "ms", "msom", "mksc", "ssy", "stratsci", "transci",
        "mathor", "opre", "isr", "serv",
    ]

    def __init__(
        self,
        parent: tk.Widget,
        *args,
        endpoints: Optional[Dict[str, Dict[str, Any]]] = None,
        **kwargs,
    ):
        """
        Accepts an optional `endpoints` dict to override the default catalog.
        We CONSUME the kwarg here so it is not forwarded to ttk.Frame (prevents TclError).
        """
        super().__init__(parent, *args, **kwargs)
        self.catalog = endpoints or _CATALOG

        # Credentials
        cred_fr = ttk.LabelFrame(self, text="Credentials")
        ttk.Label(cred_fr, text="Username:").grid(row=0, column=0, sticky="w", padx=(6, 6), pady=4)
        ttk.Label(cred_fr, text="API Key:").grid(row=1, column=0, sticky="w", padx=(6, 6), pady=4)
        
        self.username_var = tk.StringVar()
        self.apikey_var = tk.StringVar()
        
        self.username_ent = ttk.Entry(cred_fr, textvariable=self.username_var)
        self.apikey_ent = ttk.Entry(cred_fr, textvariable=self.apikey_var, show="â€¢")
        
        self.username_ent.grid(row=0, column=1, sticky="ew", padx=(0, 6), pady=4)
        self.apikey_ent.grid(row=1, column=1, sticky="ew", padx=(0, 6), pady=4)
        
        cred_fr.columnconfigure(1, weight=1)

        # Sites multi-select
        sites_fr = ttk.LabelFrame(self, text="Sites")
        ttk.Label(sites_fr, text="Select one or more:").grid(row=0, column=0, sticky="w", padx=6, pady=(4, 2))
        
        self.sites_list = tk.Listbox(sites_fr, selectmode=tk.MULTIPLE, height=8, exportselection=False)
        for s in self.DEFAULT_SITES:
            self.sites_list.insert(tk.END, s)
        
        self.sites_list.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 6))
        sites_fr.rowconfigure(1, weight=1)
        sites_fr.columnconfigure(0, weight=1)

        # Endpoint picker
        ep_fr = ttk.LabelFrame(self, text="Endpoint")
        self.endpoint_picker = EndpointPicker(ep_fr, catalog=self.catalog)
        self.endpoint_picker.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        
        ep_fr.columnconfigure(0, weight=1)
        ep_fr.rowconfigure(0, weight=1)

        # Run + progress
        actions_fr = ttk.Frame(self)
        self.run_btn = ttk.Button(actions_fr, text="Run")
        
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress = ttk.Progressbar(actions_fr, orient="horizontal", mode="determinate", 
                                       variable=self.progress_var, maximum=100.0)
        self.progress_lbl = ttk.Label(actions_fr, text="Ready")
        
        self.run_btn.grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.progress.grid(row=0, column=1, sticky="ew")
        self.progress_lbl.grid(row=0, column=2, sticky="w", padx=(8, 0))
        
        actions_fr.columnconfigure(1, weight=1)

        # Layout top-level grid
        cred_fr.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        sites_fr.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)
        ep_fr.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=6, pady=6)
        actions_fr.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=6, pady=6)
        
        self.columnconfigure(0, weight=1, uniform="cols")
        self.columnconfigure(1, weight=2, uniform="cols")
        self.rowconfigure(1, weight=1)

        self._on_run: Optional[Callable[[], None]] = None
        self.run_btn.configure(command=self._run_clicked)
        
        # V4 Enhanced Progress Tracking
        self._total_steps = 1
        self._current_step = 0

    # ---- API expected by main.py ----

    def bind_run(self, fn: Callable[[], None]) -> None:
        self._on_run = fn

    # Alias to match older main.py usage
    def set_run_command(self, fn: Callable[[], None]) -> None:
        self.bind_run(fn)

    def _run_clicked(self) -> None:
        if callable(self._on_run):
            self._on_run()

    def get_credentials(self) -> Dict[str, str]:
        return {
            "username": self.username_var.get().strip(),
            "api_key": self.apikey_var.get().strip(),
        }

    def get_selected_sites(self) -> List[str]:
        sel = [self.sites_list.get(i) for i in self.sites_list.curselection()]
        return sel or []  # empty list if none selected

    def get_endpoint_id(self) -> str:
        return self.endpoint_picker.current_endpoint_id()

    def get_params(self) -> Dict[str, str]:
        return self.endpoint_picker.params()

    def get_values(self) -> Dict[str, Any]:
        """
        Compatibility helper for main.py:
        Returns a single dict bundling creds, sites, endpoint_id, and param values.
        """
        vals: Dict[str, Any] = {}
        vals.update(self.get_credentials())
        vals["sites"] = self.get_selected_sites()
        vals["endpoint_id"] = self.get_endpoint_id()
        vals["params"] = self.get_params()
        return vals

    # ---- Progress helpers expected by main.py ----

    def set_running(self, is_running: bool) -> None:
        """
        Enable/disable inputs and change Run button label while a job is active.
        """
        state = "disabled" if is_running else "normal"
        
        # Entries / listbox
        self.username_ent.configure(state=state)
        self.apikey_ent.configure(state=state)
        self.sites_list.configure(state=state)
        self.endpoint_picker.endpoint_cmb.configure(state="readonly" if not is_running else "disabled")
        
        # Param fields
        for ent in list(self.endpoint_picker.param_form._req_widgets.values()):
            ent.configure(state=state)
        for ent in list(self.endpoint_picker.param_form._opt_widgets.values()):
            ent.configure(state=state)
        
        # Button label/state
        self.run_btn.configure(text="Runningâ€¦" if is_running else "Run", 
                              state=("disabled" if is_running else "normal"))
        
        # Visual cue
        if is_running:
            self.set_progress_text("Startingâ€¦")
            self.set_progress_fraction(0.0)

    def progress_start(self, text: Optional[str] = None) -> None:
        if text:
            self.set_progress_text(text)
        self.set_progress_fraction(0.0)
        self._current_step = 0

    def progress_update(self, frac: Optional[float] = None, text: Optional[str] = None) -> None:
        if frac is not None:
            self.set_progress_fraction(frac)
        if text is not None:
            self.set_progress_text(text)

    def progress_finish(self, text: Optional[str] = "Done") -> None:
        self.set_progress_fraction(100.0)
        if text:
            self.set_progress_text(text)

    def progress_set_total(self, total: int) -> None:
        """
        V4 Enhancement: Set the total number of steps for progress tracking.
        """
        self._total_steps = max(1, total)
        self._current_step = 0

    def progress_step(self, completed: int, text: str, total: Optional[int] = None) -> None:
        """
        Enhanced for V4: Updates progress based on completed steps.
        - completed: number of completed steps
        - text: status message to display
        - total: optional total steps (updates internal total if provided)
        """
        if total is not None:
            self._total_steps = max(1, total)
        
        self._current_step = max(0, min(completed, self._total_steps))
        
        # Calculate percentage (0-100 for progressbar)
        percentage = (self._current_step / self._total_steps) * 100.0
        
        self.set_progress_text(text)
        self.set_progress_fraction(percentage)
        
        # Force UI update
        self.update_idletasks()

    # ---- Progress primitives ----

    def set_progress_text(self, text: str) -> None:
        self.progress_lbl.configure(text=text)

    def set_progress_fraction(self, value: float) -> None:
        """
        Set progress bar value (0-100 for V4 compatibility).
        """
        try:
            # Clamp value between 0 and 100
            val = max(0.0, min(100.0, float(value)))
            self.progress_var.set(val)
        except Exception:
            self.progress_var.set(0.0)

    # Additional V4 compatibility methods
    def progress_increment(self, text: Optional[str] = None) -> None:
        """Increment progress by one step."""
        self._current_step += 1
        percentage = (self._current_step / self._total_steps) * 100.0
        self.set_progress_fraction(percentage)
        if text:
            self.set_progress_text(text)
        self.update_idletasks()