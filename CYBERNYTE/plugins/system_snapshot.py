"""Safe example CYBERNYTE plug-in: basic local system information."""

import os
import platform
import shutil
import socket

from rich.table import Table

PLUGIN_KEY = "A"
PLUGIN_NAME = "System snapshot example"


def run(console):
    table = Table("Field", "Value", title="Local System Snapshot", border_style="#ff650d")
    total, used, free = shutil.disk_usage(os.getcwd())
    rows = [
        ("Computer", socket.gethostname()),
        ("Operating system", platform.platform()),
        ("Python", platform.python_version()),
        ("Processor", platform.processor() or "Not reported"),
        ("Disk total", f"{total / (1024 ** 3):.1f} GB"),
        ("Disk free", f"{free / (1024 ** 3):.1f} GB"),
    ]
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)

