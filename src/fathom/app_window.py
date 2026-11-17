"""The launcher's tkinter window (spec 031). Logic lives in `fathom.app`.

Work runs on worker threads; only the main thread touches Tk, through a queue
polled with `after`.
"""
from __future__ import annotations

from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from . import __version__
from . import app


class LauncherWindow:
    def __init__(self, home: Path | None = None, root: tk.Tk | None = None):
        self.home = home
        self.root = root or tk.Tk()
        self.root.title("Fathom")
        self.root.minsize(560, 420)
        self.events: queue.Queue = queue.Queue()
        self.session: app.ServeSession | None = None
        self.busy = False
        self.closing = False
        self.stopping = False
        self.csv = tk.StringVar()
        self.config = tk.StringVar()
        self.out = tk.StringVar()
        self.status = tk.StringVar(value="Choose a CSV to start. Nothing leaves this computer.")
        self._build()
        self.refresh_recent()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self._after = self.root.after(100, self._drain)

    # ---- layout -------------------------------------------------------
    def _build(self):
        frame = ttk.Frame(self.root, padding=12)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="Fathom", font=("TkDefaultFont", 16, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(frame, text=f"Know your data. Keep the evidence.  v{__version__}").grid(row=0, column=1, columnspan=2, sticky="w")

        rows = (("Table (CSV)", self.csv, self.choose_csv), ("Config (optional)", self.config, self.choose_config),
                ("Output folder", self.out, self.choose_out))
        for index, (label, var, command) in enumerate(rows, start=1):
            ttk.Label(frame, text=label).grid(row=index, column=0, sticky="w", pady=3)
            ttk.Entry(frame, textvariable=var).grid(row=index, column=1, sticky="ew", padx=6)
            ttk.Button(frame, text="Choose…", command=command).grid(row=index, column=2)

        actions = ttk.Frame(frame)
        actions.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(10, 4))
        self.buttons = {
            "look": ttk.Button(actions, text="Quick look", command=self.quick_look),
            "profile": ttk.Button(actions, text="Profile", command=self.profile),
            "serve": ttk.Button(actions, text="Configure in browser", command=self.start_serve),
            "stop": ttk.Button(actions, text="Stop browser session", command=self.stop_serve, state="disabled"),
            "folder": ttk.Button(actions, text="Open folder", command=self.open_folder),
        }
        for button in self.buttons.values():
            button.pack(side="left", padx=(0, 6))

        ttk.Label(frame, textvariable=self.status, wraplength=520, justify="left").grid(row=5, column=0, columnspan=3, sticky="w", pady=4)
        ttk.Label(frame, text="Recent reports").grid(row=6, column=0, sticky="w", pady=(8, 2))
        self.recent = tk.Listbox(frame, height=8, activestyle="dotbox")
        self.recent.grid(row=7, column=0, columnspan=3, sticky="nsew")
        self.recent.bind("<Double-Button-1>", lambda _event: self.open_recent())
        frame.rowconfigure(7, weight=1)
        bottom = ttk.Frame(frame)
        bottom.grid(row=8, column=0, columnspan=3, sticky="ew", pady=(6, 0))
        ttk.Button(bottom, text="Open", command=self.open_recent).pack(side="left")
        ttk.Button(bottom, text="Refresh", command=self.refresh_recent).pack(side="left", padx=6)
        self.recent_paths: list[Path] = []

    # ---- choosers -----------------------------------------------------
    def choose_csv(self):
        path = filedialog.askopenfilename(title="Choose a CSV", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if path:
            self.csv.set(path)
            self.out.set(str(app.default_output(path, self.home)))
            self._warn_synced()

    def choose_config(self):
        path = filedialog.askopenfilename(title="Choose a YAML config", filetypes=[("YAML", "*.yaml *.yml"), ("All files", "*.*")])
        if path:
            self.config.set(path)

    def choose_out(self):
        path = filedialog.askdirectory(title="Choose an output folder", mustexist=False)
        if path:
            self.out.set(path)
            self._warn_synced()

    def _warn_synced(self):
        if app.synced_location(self.out.get()) or app.synced_location(self.csv.get()):
            self.status.set("Note: this looks like a cloud-synced folder. Reports can contain values from the table, "
                            "so they may be copied off this computer. Choose a local output folder if that matters.")

    # ---- actions ------------------------------------------------------
    def _inputs(self):
        csv = Path(self.csv.get().strip()) if self.csv.get().strip() else None
        if csv is None or not csv.is_file():
            messagebox.showerror("Fathom", "Choose an existing CSV file first.")
            return None
        out = Path(self.out.get().strip()) if self.out.get().strip() else app.default_output(csv, self.home)
        self.out.set(str(out))
        config = Path(self.config.get().strip()) if self.config.get().strip() else None
        if config is not None and not config.is_file():
            messagebox.showerror("Fathom", "The config file doesn't exist. Clear it or choose another.")
            return None
        # Typed or pasted paths get the same check as chosen ones (Copilot review, #56).
        if (app.synced_location(out) or app.synced_location(csv)) and not messagebox.askokcancel(
                "Fathom", "This looks like a cloud-synced folder:\n" + str(out if app.synced_location(out) else csv) +
                "\n\nReports can contain values from the table, so they may be copied off this computer. Continue?"):
            self.status.set("Not started. Choose a local output folder, or continue if syncing is fine.")
            return None
        return csv, out, config

    def _work(self, label, job):
        if self.busy:
            return
        self.busy = True
        self._set_state()
        self.status.set(label + "…")

        def worker():
            try:
                self.events.put(("done", job()))
            except Exception as error:  # shown, never swallowed
                self.events.put(("error", f"{type(error).__name__}: {error}"))
        # Not a daemon: the process can't exit halfway through writing a report.
        threading.Thread(target=worker, name="fathom-work").start()

    def quick_look(self):
        inputs = self._inputs()
        if inputs:
            csv, out, _ = inputs
            self._work("Quick look (liftoff)", lambda: app.quick_look(csv, out))

    def profile(self):
        inputs = self._inputs()
        if inputs:
            csv, out, config = inputs
            self._work("Profiling", lambda: app.profile(csv, out, config))

    def start_serve(self):
        inputs = self._inputs()
        if not inputs or self.session is not None:
            return
        csv, out, config = inputs

        def job():
            return app.ServeSession(csv, out, config).start()
        self._work("Starting the local browser session", job)

    def stop_serve(self):
        # Ask, don't wait: a rerun in progress finishes first, and `_drain` clears the
        # session only once its thread has ended (Copilot review, #56).
        if self.session is not None and not self.stopping:
            self.session.request_stop()
            self.stopping = True
            self.status.set("Stopping the browser session (finishing any rerun first)…")
            self._set_state()

    def open_folder(self):
        out = Path(self.out.get().strip() or app.workspace(self.home))
        out.mkdir(parents=True, exist_ok=True)
        app.open_folder(out)

    def refresh_recent(self):
        self.recent.delete(0, "end")
        reports = app.recent_reports(self.home)
        self.recent_paths = [path for _, path in reports]
        for label, _ in reports:
            self.recent.insert("end", label)
        if not reports:
            self.recent.insert("end", "(none yet)")

    def open_recent(self):
        selection = self.recent.curselection()
        if selection and selection[0] < len(self.recent_paths):
            app.open_page(self.recent_paths[selection[0]])

    # ---- event loop ---------------------------------------------------
    def _set_state(self):
        serving = self.session is not None
        for name, button in self.buttons.items():
            if name == "stop":
                button.state(["!disabled"] if serving and not self.stopping and not self.closing else ["disabled"])
            elif name in {"look", "profile", "serve"}:
                blocked = self.busy or self.closing or (serving and name == "serve")
                button.state(["disabled"] if blocked else ["!disabled"])

    def _drain(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                self.busy = False
                if self.closing:
                    if isinstance(value, app.ServeSession):
                        self.session = value
                        value.request_stop()
                    continue
                if kind == "error":
                    self.status.set("Failed: " + value)
                    messagebox.showerror("Fathom", value)
                elif isinstance(value, app.ServeSession):
                    self.session = value
                    self.status.set("Browser session running on this computer only. Rerun from the page; Stop here or there.")
                    app.open_page_url(value.url)
                else:
                    self._finish(value)
                self._set_state()
        except queue.Empty:
            pass
        if self.session is not None and not self.session.running:
            self.session = None
            self.stopping = False
            if not self.closing:
                self.status.set("Browser session ended (stopped or idle). Saved reports stay in the output folder.")
                self._set_state()
                self.refresh_recent()
        if self.closing and not self.busy and self.session is None:
            self._after = None
            self.root.destroy()
            return
        self._after = self.root.after(200, self._drain)

    def _finish(self, outcome: app.Outcome):
        last = [line for line in outcome.messages.splitlines() if line.strip()]
        if outcome.ok:
            self.status.set("Done. Saved and opened " + str(outcome.page))
            app.open_page(outcome.page)
        else:
            detail = "\n".join(last[-6:]) or f"exit code {outcome.code}"
            self.status.set("Fathom stopped: " + (last[-1] if last else f"exit code {outcome.code}"))
            messagebox.showerror("Fathom", detail)
        self.refresh_recent()

    def close(self):
        """Close once work in progress has finished, so no report is left half-written."""
        if self.closing:
            return
        self.closing = True
        if self.session is not None:
            self.session.request_stop()
        if self.busy or self.session is not None:
            self.status.set("Finishing the current run before closing…")
        self._set_state()
        if not self.busy and self.session is None:
            self._destroy()
        # Otherwise the running `_drain` loop destroys the window once work has finished.

    def _destroy(self):
        if self._after is not None:
            self.root.after_cancel(self._after)
            self._after = None
        self.root.destroy()

    def run(self):
        self.root.mainloop()
