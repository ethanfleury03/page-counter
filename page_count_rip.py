"""Minimal Page Count RIP status GUI."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import scrolledtext, ttk

from printer_status import ConnectionResult, poll_all


DEFAULT_JOB_ID = "--"
DEFAULT_LIFETIME_PAGE_COUNT = "unknown"


class PageCountRipApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()

        self.title("Page Count RIP")
        self.resizable(False, False)
        self.configure(bg="#f4f6f8")

        self.job_id_var = tk.StringVar(value=DEFAULT_JOB_ID)
        self.total_pages_var = tk.StringVar(value=DEFAULT_LIFETIME_PAGE_COUNT)
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
            label="Lifetime Page Count",
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
        self.output_box.insert(tk.END, "Default connection is 192.168.100.200 as root/root. Click Test SSH Status to parse live read-only controller status.\n")
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
        first_ok_result = None
        for result in results:
            state = "OK" if result.ok else "FAILED"
            if result.ok:
                ok_count += 1
                first_ok_result = first_ok_result or result
            lines.append(f"[{state}] {result.name} ({result.host})")
            lines.append(result.message)
            if result.summary:
                lines.append("")
                lines.extend(_format_summary(result))
                lines.append("")
                lines.append("Raw read-only trace:")
            if result.command_output:
                lines.append(result.command_output)
            lines.append("")

        status = f"{ok_count}/{len(results)} SSH connection(s) healthy"
        lifetime_page_count = None
        if first_ok_result and first_ok_result.summary:
            lifetime_page_count = first_ok_result.summary.lifetime_page_count
        self.after(
            0,
            self._show_poll_results,
            status,
            "\n".join(lines).strip(),
            lifetime_page_count,
        )

    def _show_poll_results(
        self,
        status: str,
        output: str,
        lifetime_page_count: int | None,
    ) -> None:
        self.connection_status_var.set(status)
        if lifetime_page_count is not None:
            self.total_pages_var.set(str(lifetime_page_count))
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


def _format_summary(result: ConnectionResult) -> list[str]:
    summary = result.summary
    if not summary:
        return []

    lines = ["Parsed controller status:"]
    lines.append(f"Lifetime page count: {_format_unknown(summary.lifetime_page_count)}")
    lines.append(
        f"Printed media length: {_format_float(summary.printed_media_length_m, 'm')}"
    )
    lines.append(f"Engine state: {summary.engine_state}")
    lines.append(f"Ready for print data: {_format_bool(summary.ready_for_print_data)}")
    lines.append(f"Primed: {_format_bool(summary.is_primed)}")
    lines.append(f"Capped: {_format_bool(summary.is_capped)}")
    lines.append(f"Last print time: {summary.last_print_time}")
    lines.append(f"Last spit time: {summary.last_spit_time}")
    lines.append(f"Last declog time: {summary.last_declog_time}")
    lines.append(f"Pages since last wipe: {_format_unknown(summary.pages_since_last_wipe)}")
    lines.append(
        f"Meters since last wipe: {_format_float(summary.meters_since_last_wipe, 'm')}"
    )
    lines.append(f"Latest activity marker: {_shorten(summary.latest_activity)}")
    return lines


def _format_unknown(value: object | None) -> str:
    if value is None:
        return "unknown"
    return str(value)


def _format_bool(value: bool | None) -> str:
    if value is None:
        return "unknown"
    return "yes" if value else "no"


def _format_float(value: float | None, suffix: str) -> str:
    if value is None:
        return "unknown"
    return f"{value:.3f} {suffix}"


def _shorten(value: str, limit: int = 240) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 3] + "..."


if __name__ == "__main__":
    main()
