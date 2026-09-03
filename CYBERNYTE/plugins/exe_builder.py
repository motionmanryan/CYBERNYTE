"""CYBERNYTE plug-in: package a Python script you wrote into a standalone .exe."""

import shutil
import subprocess
import sys
from pathlib import Path

from rich.prompt import Confirm, Prompt
from rich.table import Table

PLUGIN_KEY = "E"
PLUGIN_NAME = "EXE builder (PyInstaller)"


def _pyinstaller_available() -> bool:
    try:
        subprocess.run(
            [sys.executable, "-m", "PyInstaller", "--version"],
            capture_output=True,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return False


def run(console) -> None:
    console.rule("[bold #ff5a00]EXE Builder (PyInstaller)")
    console.print(
        "[dim]This packages a Python script YOU wrote into a Windows .exe using "
        "PyInstaller. It does not create, alter, or hide the script's behavior "
        "in any way -- it only bundles it.[/]"
    )

    if not _pyinstaller_available():
        console.print(
            "[red]PyInstaller isn't installed.[/] Run this first:\n"
            "  python -m pip install pyinstaller"
        )
        return

    script_raw = Prompt.ask("Path to the .py script you want to build").strip().strip('"')
    script = Path(script_raw).expanduser().resolve()
    if not script.is_file() or script.suffix.lower() != ".py":
        console.print("[red]That isn't a valid .py file.[/]")
        return

    exe_name = Prompt.ask("Name for the built program", default=script.stem).strip()
    if not exe_name:
        console.print("[red]A name is required.[/]")
        return

    onefile = Confirm.ask(
        "Build as a single .exe file? (No = a folder with the .exe plus its files)",
        default=True,
    )
    windowed = Confirm.ask(
        "Is this a GUI app that should NOT open a console window?",
        default=False,
    )

    icon_path = None
    if Confirm.ask("Add a custom .ico icon?", default=False):
        icon_raw = Prompt.ask("Path to the .ico file").strip().strip('"')
        candidate = Path(icon_raw).expanduser().resolve()
        if candidate.is_file():
            icon_path = candidate
        else:
            console.print("[yellow]Icon file not found -- continuing without one.[/]")

    extra_data = []
    if Confirm.ask("Bundle any extra files or folders (images, assets, etc.)?", default=False):
        console.print("[dim]Enter one path per line. Leave blank and press Enter to stop.[/]")
        while True:
            item = console.input("Asset path: ").strip().strip('"')
            if not item:
                break
            item_path = Path(item).expanduser().resolve()
            if not item_path.exists():
                console.print(f"[yellow]Skipping -- not found: {item_path}[/]")
                continue
            extra_data.append(item_path)

    build_root = script.parent / f"{exe_name}_build"
    dist_dir = build_root / "dist"
    work_dir = build_root / "build"
    spec_dir = build_root

    command = [
        sys.executable, "-m", "PyInstaller",
        "--name", exe_name,
        "--distpath", str(dist_dir),
        "--workpath", str(work_dir),
        "--specpath", str(spec_dir),
        "--noconfirm",
    ]
    command.append("--onefile" if onefile else "--onedir")
    if windowed:
        command.append("--windowed")
    if icon_path:
        command += ["--icon", str(icon_path)]
    sep = ";" if sys.platform.startswith("win") else ":"
    for asset in extra_data:
        command += ["--add-data", f"{asset}{sep}."]
    command.append(str(script))

    console.print(f"[dim]Running: {' '.join(command)}[/]")
    with console.status("Building... this can take a minute."):
        result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        console.print("[red]Build failed.[/]")
        console.print(result.stderr[-2000:] or result.stdout[-2000:])
        return

    built_exe = dist_dir / f"{exe_name}.exe" if onefile else dist_dir / exe_name / f"{exe_name}.exe"
    table = Table("Field", "Value", border_style="#ff650d")
    table.add_row("Source script", str(script))
    table.add_row("Output", str(built_exe if built_exe.exists() else dist_dir))
    table.add_row("Mode", "Single file" if onefile else "Folder (onedir)")
    console.print(table)
    console.print("[green]Build finished.[/]")
    console.print(
        "[dim]Antivirus tools sometimes flag freshly built, unsigned executables. "
        "Only distribute software you wrote yourself and understand -- see the main "
        "README's Ethical-use rule.[/]"
    )
