# Adding your own scripts to CYBERNYTE

## Fastest method

1. Open the `plugins` folder.
2. Make a copy of `_template.py`.
3. Rename the copy to describe your tool, such as `my_hash_tool.py`.
4. Open the copy in Notepad or VS Code.
5. Change `PLUGIN_KEY`, `PLUGIN_NAME`, and the code inside `run(console)`.
6. Save the file and restart CYBERNYTE.

The new script appears automatically in the menu as `Custom · Your tool name`.

## The three required pieces

```python
PLUGIN_KEY = "B"                 # One unused letter
PLUGIN_NAME = "My first tool"    # Text shown in the menu

def run(console):                 # CYBERNYTE runs this function
    console.print("It works!")
```

Do not call `run()` yourself. CYBERNYTE calls it when the user presses the
plug-in's key.

## Example: SHA-256 calculator

Create `plugins/my_hash_tool.py` with this code:

```python
import hashlib
from pathlib import Path
from rich.prompt import Prompt

PLUGIN_KEY = "H"
PLUGIN_NAME = "My SHA-256 calculator"


def run(console):
    raw_path = Prompt.ask("File path").strip().strip('"')
    path = Path(raw_path).expanduser().resolve()

    if not path.is_file():
        console.print("[red]That file was not found.[/]")
        return

    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)

    console.print(f"[green]SHA-256:[/] {digest.hexdigest()}")
```

Restart CYBERNYTE and press `H` to run it.

## Using an existing script

If your current script has a function such as this:

```python
def scan_file(path):
    return "safe"
```

keep that function and add the CYBERNYTE wrapper underneath it:

```python
from rich.prompt import Prompt

PLUGIN_KEY = "S"
PLUGIN_NAME = "My file scanner"


def run(console):
    path = Prompt.ask("File to scan")
    result = scan_file(path)
    console.print(f"Result: {result}")
```

## Troubleshooting

- Use a letter that is not already shown in the menu.
- Do not use `D`; it belongs to the built-in RAT warning-sign detector.
- Make sure the filename ends in `.py` and does not begin with `_`.
- Make sure the file defines both constants and `run(console)`.
- Check that packages imported by your script are installed with `pip`.
- Restart CYBERNYTE after every script change.

Never install or run a custom script you do not understand. A Python plug-in can
access the same files and system resources as the main application.
