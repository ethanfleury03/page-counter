"""Minimal Page Count RIP status GUI.

This first version is intentionally display-only. The SSH/log reader will plug
into `set_job_status()` once we have sample logs.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


DEFAULT_JOB_ID = "--"
DEFAULT_TOTAL_PAGES_SENT = "0"


class PageCountRipApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()

        self.title("Page Count RIP")
        self.resizable(False, False)
        self.configure(bg="#f4f6f8")

        self.job_id_var = tk.StringVar(value=DEFAULT_JOB_ID)
        self.total_pages_var = tk.StringVar(value=DEFAULT_TOTAL_PAGES_SENT)

        self._configure_styles()
        self._build_ui()
        self._center_window(width=360, height=190)

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Root.TFrame", background="#f4f6f8")
        style.configure(
            "Panel.TFrame",
            background="#ffffff",
            borderwidth=1,
            relief="solid",
        )
        style.configure(
            "Title.TLabel",
            background="#f4f6f8",
            foreground="#1f2933",
            font=("Segoe UI", 14, "bold"),
        )
        style.configure(
            "FieldLabel.TLabel",
            background="#ffffff",
            foreground="#5f6b7a",
            font=("Segoe UI", 10),
        )
        style.configure(
            "Value.TLabel",
            background="#ffffff",
            foreground="#111827",
            font=("Segoe UI", 20, "bold"),
        )
        style.configure(
            "Status.TLabel",
            background="#f4f6f8",
            foreground="#6b7280",
            font=("Segoe UI", 9),
        )

    def _build_ui(self) -> None:
        root = ttk.Frame(self, style="Root.TFrame", padding=16)
        root.grid(row=0, column=0, sticky="nsew")

        title = ttk.Label(root, text="Page Count RIP", style="Title.TLabel")
        title.grid(row=0, column=0, sticky="w", pady=(0, 12))

        panel = ttk.Frame(root, style="Panel.TFrame", padding=(18, 14))
        panel.grid(row=1, column=0, sticky="ew")

        self._add_field(panel, row=0, label="Job ID", value_var=self.job_id_var)
        self._add_field(
            panel,
            row=1,
            label="Total Pages Sent",
            value_var=self.total_pages_var,
        )

        status = ttk.Label(
            root,
            text="Waiting for live data connection",
            style="Status.TLabel",
        )
        status.grid(row=2, column=0, sticky="w", pady=(12, 0))

    def _add_field(
        self,
        parent: ttk.Frame,
        row: int,
        label: str,
        value_var: tk.StringVar,
    ) -> None:
        label_widget = ttk.Label(parent, text=label, style="FieldLabel.TLabel")
        label_widget.grid(row=row, column=0, sticky="w", pady=(0, 10))

        value_widget = ttk.Label(parent, textvariable=value_var, style="Value.TLabel")
        value_widget.grid(row=row, column=1, sticky="e", padx=(28, 0), pady=(0, 10))

        parent.columnconfigure(1, minsize=160)

    def _center_window(self, width: int, height: int) -> None:
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        left = int((screen_width - width) / 2)
        top = int((screen_height - height) / 2)
        self.geometry(f"{width}x{height}+{left}+{top}")

    def set_job_status(self, job_id: str, total_pages_sent: int) -> None:
        self.job_id_var.set(job_id or DEFAULT_JOB_ID)
        self.total_pages_var.set(str(max(0, total_pages_sent)))


def main() -> None:
    app = PageCountRipApp()
    app.mainloop()


if __name__ == "__main__":
    main()
