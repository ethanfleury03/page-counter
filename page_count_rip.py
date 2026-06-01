"""Minimal Page Count RIP status GUI."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import scrolledtext, ttk

from printer_status import poll_all


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
        self.connection_status_var = tk.StringVar(value="Waiting for live data connection")

        self._configure_styles()
        self._build_ui()
        self._center_window(width=560, height=430)

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
            textvariable=self.connection_status_var,
            style="Status.TLabel",
        )
        status.grid(row=2, column=0, sticky="w", pady=(12, 0))

        button_row = ttk.Frame(root, style="Root.TFrame")
        button_row.grid(row=3, column=0, sticky="ew", pady=(10, 8))

        self.test_button = ttk.Button(
            button_row,
            text="Test SSH Status",
            command=self.test_ssh_status,
        )
        self.test_button.grid(row=0, column=0, sticky="w")

        self.output_box = scrolledtext.ScrolledText(
            root,
            height=10,
            width=62,
            wrap=tk.WORD,
            font=("Consolas", 9),
        )
        self.output_box.grid(row=4, column=0, sticky="ew")
        self.output_box.insert(tk.END, "Copy printer_config.example.json to printer_config.json, fill in the hosts/usernames, set password environment variables, then click Test SSH Status.\n")
        self.output_box.configure(state=tk.DISABLED)

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

    def test_ssh_status(self) -> None:
        self.test_button.configure(state=tk.DISABLED)
        self.connection_status_var.set("Testing SSH connection...")
        self._set_output("Testing read-only SSH status...\n")
        thread = threading.Thread(target=self._test_ssh_status_worker, daemon=True)
        thread.start()

    def _test_ssh_status_worker(self) -> None:
        try:
            results = poll_all()
        except Exception as exc:
            self.after(0, self._show_poll_error, str(exc))
            return

        lines = []
        ok_count = 0
        for result in results:
            state = "OK" if result.ok else "FAILED"
            if result.ok:
                ok_count += 1
            lines.append(f"[{state}] {result.name} ({result.host})")
            lines.append(result.message)
            if result.command_output:
                lines.append(result.command_output)
            lines.append("")

        status = f"{ok_count}/{len(results)} SSH connection(s) healthy"
        self.after(0, self._show_poll_results, status, "\n".join(lines).strip())

    def _show_poll_results(self, status: str, output: str) -> None:
        self.connection_status_var.set(status)
        self._set_output(output + "\n")
        self.test_button.configure(state=tk.NORMAL)

    def _show_poll_error(self, message: str) -> None:
        self.connection_status_var.set("SSH status test failed")
        self._set_output(message + "\n")
        self.test_button.configure(state=tk.NORMAL)

    def _set_output(self, text: str) -> None:
        self.output_box.configure(state=tk.NORMAL)
        self.output_box.delete("1.0", tk.END)
        self.output_box.insert(tk.END, text)
        self.output_box.configure(state=tk.DISABLED)


def main() -> None:
    app = PageCountRipApp()
    app.mainloop()


if __name__ == "__main__":
    main()
