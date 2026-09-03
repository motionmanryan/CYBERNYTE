"""CYBERNYTE plug-in: create custom files (text, config, code, etc.) on demand."""

from pathlib import Path

from rich.prompt import Confirm, Prompt
from rich.table import Table

PLUGIN_KEY = "C"
PLUGIN_NAME = "Custom file creator"


def run(console) -> None:
    console.rule("[bold #ff5a00]Custom File Creator")

    folder_raw = Prompt.ask("Folder to create the file in", default=".")
    folder = Path(folder_raw).expanduser().resolve()
    if not folder.exists():
        if Confirm.ask(f"[yellow]{folder} does not exist. Create it?[/]", default=True):
            folder.mkdir(parents=True, exist_ok=True)
        else:
            console.print("[red]Cancelled.[/]")
            return
    if not folder.is_dir():
        console.print(f"[red]{folder} is not a folder.[/]")
        return

    filename = Prompt.ask("File name (include the extension, e.g. notes.txt)").strip()
    if not filename:
        console.print("[red]A file name is required.[/]")
        return

    target = folder / filename
    if target.exists():
        if not Confirm.ask(f"[yellow]{target} already exists. Overwrite it?[/]", default=False):
            console.print("[red]Cancelled.[/]")
            return

    mode = Prompt.ask(
        "How do you want to fill it?",
        choices=["type", "blank"],
        default="type",
    )

    if mode == "blank":
        content = ""
    else:
        console.print(
            "[dim]Type or paste the file content. On its own line, type END and press "
            "Enter when you're done.[/]"
        )
        lines = []
        while True:
            line = console.input()
            if line.strip() == "END":
                break
            lines.append(line)
        content = "\n".join(lines)
        if content:
            content += "\n"

    try:
        target.write_text(content, encoding="utf-8")
    except OSError as exc:
        console.print(f"[red]Could not write the file:[/] {exc}")
        return

    table = Table("Field", "Value", border_style="#ff650d")
    table.add_row("Path", str(target))
    table.add_row("Size", f"{target.stat().st_size:,} bytes")
    console.print(table)
    console.print("[green]File created successfully.[/]")
